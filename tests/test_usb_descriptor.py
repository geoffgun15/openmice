"""Validate composite report IDs and descriptor bit lengths before USB bring-up."""
import runpy
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

class DescriptorTest(unittest.TestCase):
    def test_mouse_and_keyboard_have_distinct_ids_and_correct_lengths(self):
        class Device:
            def __init__(self,**kwargs):self.__dict__.update(kwargs)
        Device.KEYBOARD=types.SimpleNamespace(report_ids=(1,))
        captured=[]
        usb=types.SimpleNamespace(Device=Device,enable=lambda value:captured.extend(value))
        stubs={'usb_hid':usb,'usb_cdc':types.SimpleNamespace(enable=lambda **_:None),'supervisor':types.SimpleNamespace(disable_autoreload=lambda:None)}
        with patch.dict(sys.modules,stubs):
            runpy.run_path(str(Path(__file__).resolve().parents[1]/'firmware/common/boot.py'))
        ids=[i for device in captured for i in device.report_ids]
        self.assertEqual(len(ids),len(set(ids)))
        descriptor=captured[0].report_descriptor;position=0;count=size=0;bits={};report_id=0
        while position<len(descriptor):
            prefix=descriptor[position];position+=1
            length=(0,1,2,4)[prefix&3];value=int.from_bytes(descriptor[position:position+length],'little');position+=length
            if prefix==0x75:size=value
            elif prefix==0x95:count=value
            elif prefix==0x85:report_id=value
            elif prefix&0xfc==0x80:bits[report_id]=bits.get(report_id,0)+count*size
        self.assertEqual(bits,{2:48})
        self.assertEqual(captured[0].in_report_lengths,(6,))
