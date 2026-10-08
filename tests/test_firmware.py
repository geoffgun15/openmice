import json
import struct
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'firmware/common'))
sys.modules['microcontroller'] = types.SimpleNamespace(delay_us=lambda _:None)
from config import defaults,validate,Store,Lines,TxBuffer,ConfigAPI
from inputs import aggregate,Debounce,Quadrature
import paw3395

class Pin:
    value = True

class SPI:
    def __init__(self):
        self.locked = False
        self.address = 0
        self.writes = []
        self.fail_read = False
        self.ready = True
        self.buffer = bytes((0x80,0,0,0,0,0))
    def try_lock(self):
        if self.locked:
            return False
        self.locked = True
        return True
    def configure(self,**kwargs):
        self.mode = kwargs
    def unlock(self):
        self.locked = False
    def write(self,data):
        if len(data)==1:
            self.address = data[0]
        else:
            self.writes.append((data[0]&0x7f,data[1]))
    def readinto(self,destination,write_value=0):
        if self.fail_read:
            raise OSError('SPI failure')
        if len(destination)==6:
            destination[:]=self.buffer
        else:
            destination[0]={0:0x51,0x5f:0xae,0x6c:0x80 if self.ready else 0}.get(self.address,0)

class FirmwareTests(unittest.TestCase):
    def setUp(self):
        self.spi,self.cs,self.reset=SPI(),Pin(),Pin()
        self.sensor=paw3395.PAW3395(self.spi,self.cs,self.reset)

    def test_signed_extremes(self):
        for value in (-32768,-1,0,1,32767):
            unsigned=value&65535
            self.assertEqual(paw3395.signed16(unsigned&255,unsigned>>8),value)

    def test_spi_mode_and_cleanup(self):
        self.spi.fail_read=True
        with self.assertRaises(OSError):
            self.sensor.motion()
        self.assertTrue(self.cs.value)
        self.assertFalse(self.spi.locked)
        self.assertEqual(self.spi.mode,{'baudrate':4000000,'phase':1,'polarity':1})

    def test_motion_retains_large_deltas(self):
        self.spi.buffer=bytes((0x80,0,0xff,0x7f,0,0x80))
        self.assertEqual(self.sensor.motion(),(32767,-32768))
        self.spi.buffer=b'\0'*6
        self.assertEqual(self.sensor.motion(),(0,0))

    def test_dpi_encoding_and_ripple_control(self):
        for dpi,encoded in ((50,0),(800,15),(9000,179),(26000,519)):
            self.spi.writes=[]
            self.sensor.set_dpi(dpi)
            self.assertEqual(self.spi.writes,[(0x7f,0),(0x48,encoded&255),(0x49,encoded>>8),(0x4a,encoded&255),(0x4b,encoded>>8),(0x47,1),(0x5a,0x90 if dpi>=9000 else 0x10)])
        with self.assertRaises(ValueError):
            self.sensor.set_dpi(801)

    def test_complete_startup_and_fallback(self):
        old_sleep=paw3395.time.sleep
        paw3395.time.sleep=lambda _:None
        try:
            self.sensor.initialize()
            self.assertEqual(len(paw3395.INIT_SEQUENCE),140)
            self.assertEqual(self.spi.writes[-1],(0x68,1))
            self.assertIn((0x43,0x64),self.spi.writes)
            self.assertIn((0x61,0x22),self.spi.writes)
            self.spi.ready=False
            self.spi.writes=[]
            self.sensor.initialize()
            self.assertIn((0x6c,0),self.spi.writes)
        finally:
            paw3395.time.sleep=old_sleep

    def test_validation_rejects_bad_profiles(self):
        self.assertEqual(validate(defaults()),defaults())
        for dpi in (True,0,51,26050,800.5):
            with self.assertRaises(ValueError):
                validate({'dpi':dpi,'bindings':defaults()['bindings']})
        for binding in ('key:CTRL+FAKE','key:CTRL+CTRL','key:','unknown',None):
            with self.assertRaises(ValueError):
                validate({'dpi':800,'bindings':[binding]+defaults()['bindings'][1:]})

    def test_persistence_and_corruption_fallback(self):
        nvm=bytearray(2048)
        store=Store(nvm)
        self.assertEqual(store.load(),defaults())
        store.save({'dpi':1600,'bindings':defaults()['bindings']})
        store.save({'dpi':3200,'bindings':defaults()['bindings']})
        self.assertEqual(Store(nvm).load()['dpi'],3200)
        nvm[512+20]^=0xff
        self.assertEqual(Store(nvm).load()['dpi'],1600)

    def test_interrupted_save_preserves_last_good_slot(self):
        class FailingNVM(bytearray):
            remaining=100
            def __setitem__(self,key,value):
                self.remaining-=1
                if self.remaining==0:
                    raise OSError('power cut')
                super().__setitem__(key,value)
        nvm=FailingNVM(2048)
        store=Store(nvm)
        store.load()
        store.save(defaults())
        nvm.remaining=3 # invalidation, data, interrupted commit marker
        with self.assertRaises(OSError):
            store.save({'dpi':1600,'bindings':defaults()['bindings']})
        self.assertEqual(Store(nvm).load()['dpi'],800)

    def test_protocol_framing_and_overflow(self):
        lines=Lines(12)
        self.assertEqual(lines.feed(b'{"id":'),[])
        self.assertEqual(lines.feed(b'1}\n'),[b'{"id":1}'])
        self.assertEqual(lines.feed(b'x'*20+b'\nok\n'),[b'ok'])

    def test_partial_cdc_writes_are_preserved(self):
        class Stream:
            result=b''
            def write(self,data):
                self.result+=data[:2]
                return min(2,len(data))
        queue=TxBuffer()
        queue.append(b'abcdef\n')
        stream=Stream()
        for _ in range(4):
            queue.flush(stream)
        self.assertEqual(stream.result,b'abcdef\n')
        self.assertFalse(queue.data)

    def test_rejected_config_has_no_hardware_side_effect(self):
        class Sensor:
            dpi=0
            def set_dpi(self,dpi):self.dpi=dpi
        sensor=Sensor()
        api=ConfigAPI(sensor,Store(bytearray(2048)))
        reply=api.handle({'id':3,'cmd':'set','config':{'dpi':801,'bindings':defaults()['bindings']}})
        self.assertFalse(reply['ok'])
        self.assertEqual(reply['id'],3)
        self.assertEqual(sensor.dpi,800)
        api.handle({'id':4,'cmd':'set','config':{'dpi':1600,'bindings':defaults()['bindings']}})
        self.assertEqual(sensor.dpi,1600)
        self.assertTrue(api.handle({'id':5,'cmd':'save'})['saved'])

    def test_duplicate_bindings_hold_until_both_released(self):
        bindings=['left','left','key:CTRL+C','key:CTRL+C','none']
        self.assertEqual(aggregate([True,True,True,True,False],bindings),(1,[6,224]))
        self.assertEqual(aggregate([False,True,False,True,False],bindings),(1,[6,224]))
        self.assertEqual(aggregate([False]*5,bindings),(0,[]))

    def test_contact_bounce(self):
        contact=Debounce()
        self.assertFalse(contact.update(True,0))
        self.assertFalse(contact.update(False,0.001))
        self.assertFalse(contact.update(True,0.002))
        self.assertTrue(contact.update(True,0.008))

    def test_encoder_invalid_transition(self):
        encoder=Quadrature(0)
        result=[encoder.update(value) for value in (1,3,2,0)]
        self.assertEqual(sum(result),-1)
        self.assertEqual(encoder.update(3),0)

    def test_hid_report_shape_and_keyboard_state(self):
        class Device:
            def __init__(self,usage):self.usage_page,self.usage,self.reports=1,usage,[]
            def send_report(self,data):self.reports.append(bytes(data))
        mouse,keyboard=Device(2),Device(6)
        sys.modules['usb_hid']=types.SimpleNamespace(devices=[mouse,keyboard])
        from hid_output import Output
        out=Output()
        out.report(-32768,32767,-1,31,[6,224])
        self.assertEqual(mouse.reports[-1],struct.pack('<Bhhb',31,-32768,32767,-1))
        self.assertEqual(keyboard.reports[-1],bytes((1,0,6,0,0,0,0,0)))
        out.release()
        self.assertEqual(mouse.reports[-1],b'\0'*6)
        self.assertEqual(keyboard.reports[-1],b'\0'*8)

    def test_hardware_gpio_mapping_matches_mouse(self):
        hardware=json.loads((ROOT/'hardware/mouse/connectivity.json').read_text())
        u1=hardware['parts'][0]['pins']
        expected={'36':'SPI_SCLK','37':'SPI_MOSI','39':'SPI_MISO','38':'SENSOR_NCS','41':'SENSOR_RESET','27':'SENSOR_IRQ','44':'BUTTON_LEFT','43':'BUTTON_RIGHT','45':'BUTTON_MIDDLE','46':'BUTTON_BACK','48':'BUTTON_FORWARD','49':'ENCODER_A','19':'ENCODER_B','16':'PAIR','20':'BATTERY_ADC'}
        for number,net in expected.items():
            self.assertEqual(u1[number]['net'],net)
        code=(ROOT/'firmware/mouse/code.py').read_text()
        self.assertIn('p.P0_20,p.P0_21,p.P0_23,p.P0_22,p.P0_24',code)
        self.assertIn('irq = input_pin(p.P0_11)',code)

if __name__=='__main__':
    unittest.main()
