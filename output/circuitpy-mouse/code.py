"""Wired USB + BLE prototype. No guaranteed gaming polling rate."""
import time
import json
import busio
import digitalio
import microcontroller
import supervisor
import usb_cdc
import analogio
from adafruit_ble import BLERadio
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.services.nordic import UARTService
from paw3395 import PAW3395
from config import Store, ConfigAPI, Lines, TxBuffer, frame
from inputs import Debounce, Quadrature, aggregate
from hid_output import Output

def output(pin, value):
    port = digitalio.DigitalInOut(pin)
    port.switch_to_output(value=value)
    return port
def input_pin(pin):
    port = digitalio.DigitalInOut(pin)
    port.switch_to_input(pull=digitalio.Pull.UP)
    return port

p = microcontroller.pin
spi = busio.SPI(p.P0_14,MOSI=p.P0_13,MISO=p.P0_15)
sensor = PAW3395(spi,output(p.P0_16,True),output(p.P0_17,True))
irq = input_pin(p.P0_11)
contacts = [input_pin(pin) for pin in (p.P0_20,p.P0_21,p.P0_23,p.P0_22,p.P0_24)]
encoder_a, encoder_b = input_pin(p.P0_25),input_pin(p.P0_26)
pair_button = input_pin(p.P0_27)
battery = analogio.AnalogIn(p.P0_04)
debouncers = [Debounce() for _ in contacts]
encoder = Quadrature((int(encoder_a.value)<<1)|int(encoder_b.value))
sensor.initialize()
api = ConfigAPI(sensor,Store(microcontroller.nvm))
hid = Output()
ble = BLERadio()
ble.name = "OpenMice"
uart = UARTService()
advertisement = ProvideServicesAdvertisement(uart)
advertisement.complete_name = "OpenMice"
usb_lines, ble_lines = Lines(),Lines()
cdc = usb_cdc.data
cdc.timeout = 0
cdc.write_timeout = 0
next_report, next_recovery = 0,0
dx = dy = wheel = 0
previous = None
last_state = 0
was_usb, was_ble, was_cdc = False,False,False
usb_tx = TxBuffer()
errors = 0

def command(raw):
    try:
        result = api.handle(json.loads(raw.decode()))
        result["battery_mv"] = int(battery.value/65535*battery.reference_voltage*2000)
        return result
    except (ValueError, UnicodeError):
        return {"id":None,"ok":False,"error":"Invalid JSON"}

while True:
    now = time.monotonic()
    wired = supervisor.runtime.usb_connected
    wireless = ble.connected and all(connection.paired for connection in ble.connections)
    if wired and not was_usb:
        try:
            hid.release()
        except (OSError,RuntimeError):
            pass
        previous = None
    if wired and not was_usb and wireless:
        try:
            uart.write(frame({"motion":[0,0,0,0,[]]}))
        except (OSError,RuntimeError):
            pass
    if not ble.connected and not ble.advertising:
        # Name-based discovery is for prototype use; receiver stores peer address.
        ble.start_advertising(advertisement,interval=0.1)
    if ble.connected and not wireless and not pair_button.value:
        for connection in ble.connections:
            if not connection.paired:
                connection.pair(bond=True)
    if (was_usb and not wired) or (was_ble and not wireless):
        dx = dy = wheel = 0
        previous = None
        if wired:
            hid.release()
    if cdc.connected != was_cdc:
        usb_lines.reset()
        usb_tx.reset()
        was_cdc = cdc.connected
    if wireless != was_ble:
        ble_lines.reset()
    was_usb,was_ble = wired,wireless
    if cdc.connected and cdc.in_waiting:
        for line in usb_lines.feed(cdc.read(min(cdc.in_waiting,128)) or b""):
            try:
                usb_tx.append(frame(command(line)))
            except RuntimeError:
                usb_tx.reset()
    if cdc.connected:
        try:
            usb_tx.flush(cdc)
        except OSError:
            usb_tx.reset()
    if wireless:
        try:
            if uart.in_waiting:
                for line in ble_lines.feed(uart.read(min(uart.in_waiting,128)) or b""):
                    uart.write(frame(command(line)))
        except (OSError,RuntimeError):
            ble_lines.reset()
            for connection in ble.connections:
                if connection.connected:
                    connection.disconnect()
    pressed = [debounce.update(not port.value,now) for debounce,port in zip(debouncers,contacts)]
    buttons,keys = aggregate(pressed,api.config["bindings"])
    wheel += encoder.update((int(encoder_a.value)<<1)|int(encoder_b.value))
    if now >= next_recovery and not irq.value:
        try:
            x,y = sensor.motion()
            dx += x
            dy += y
            errors = 0
        except (OSError,RuntimeError):
            errors += 1
            if errors >= 3:
                if wired:
                    hid.release()
                try:
                    sensor.initialize()
                    sensor.set_dpi(api.config["dpi"])
                    errors = 0
                except (OSError,RuntimeError):
                    next_recovery = now+1
    interval = 0.001 if wired else 0.016
    state = (buttons,keys)
    if now >= next_report or state != previous:
        if dx or dy or wheel or state != previous or now-last_state > 0.1:
            x,y,w = max(-32768,min(32767,dx)),max(-32768,min(32767,dy)),max(-127,min(127,wheel))
            try:
                if wired:
                    hid.report(x,y,w,buttons,keys)
                elif wireless:
                    uart.write(frame({"motion":[x,y,w,buttons,keys]}))
                else:
                    dx = dy = wheel = 0
                if wired or wireless:
                    dx -= x
                    dy -= y
                    wheel -= w
                previous,last_state = state,now
            except (OSError,RuntimeError):
                dx = dy = wheel = 0
                previous = None
        next_report = now+interval
    time.sleep(0.0005)
