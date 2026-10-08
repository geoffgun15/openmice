"""BLE central -> USB HID and bidirectional configuration bridge."""
import time
import json
import digitalio
import microcontroller
import usb_cdc
from adafruit_ble import BLERadio
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.services.nordic import UARTService
from config import Lines,TxBuffer,frame
from hid_output import Output

hid = Output()
ble = BLERadio()
pair_button = digitalio.DigitalInOut(microcontroller.pin.P0_27)
pair_button.switch_to_input(pull=digitalio.Pull.UP)
cdc = usb_cdc.data
cdc.timeout = 0
cdc.write_timeout = 0
peer_offset = 8192 # dedicated third erase page, separate from config slots
raw_peer = bytes(microcontroller.nvm[peer_offset:peer_offset+10])
peer = raw_peer[4:] if raw_peer[:4] == b"OMP1" else None
connection = uart = None
usb_lines,radio_lines = Lines(),Lines()
last_motion = time.monotonic()
usb_connected = False
usb_tx = TxBuffer()

def reply(data):
    try:
        usb_tx.append(data)
    except RuntimeError:
        usb_tx.reset()

while True:
    if not connection or not connection.connected:
        hid.release()
        radio_lines.reset()
        if uart:
            uart.deinit()
            uart = None
        connection = None
        for adv in ble.start_scan(ProvideServicesAdvertisement,timeout=0.25):
            address = bytes(adv.address.address_bytes)
            known = peer is not None and address == peer
            pairing = not pair_button.value
            if UARTService not in adv.services or not (known or (pairing and adv.complete_name == "OpenMice")):
                continue
            ble.stop_scan()
            try:
                candidate = ble.connect(adv,timeout=2)
                # Hold mouse and receiver Pair buttons for first bond.
                candidate.pair(bond=True)
                if not candidate.paired:
                    candidate.disconnect()
                    break
                connection = candidate
                uart = connection[UARTService]
                connection.connection_interval = 7.5
                if pairing:
                    microcontroller.nvm[peer_offset:peer_offset+10] = b"OMP1"+address
                    peer = address
                last_motion = time.monotonic()
            except (OSError,RuntimeError):
                if connection and connection.connected:
                    connection.disconnect()
                connection = None
            break
    if cdc.connected != usb_connected:
        usb_lines.reset()
        usb_tx.reset()
        usb_connected = cdc.connected
    if cdc.connected and cdc.in_waiting:
        for raw in usb_lines.feed(cdc.read(min(128,cdc.in_waiting)) or b""):
            try:
                request = json.loads(raw.decode())
                request_id = request.get("id") if isinstance(request,dict) else None
                if connection and connection.connected and uart:
                    uart.write(raw+b"\n")
                else:
                    reply(frame({"id":request_id,"ok":False,"error":"Mouse offline. Pair or power on the mouse."}))
            except (ValueError,UnicodeError,OSError,RuntimeError):
                reply(frame({"id":None,"ok":False,"error":"Invalid request or wireless write failed"}))
    if connection and connection.connected and uart and uart.in_waiting:
        for raw in radio_lines.feed(uart.read(min(128,uart.in_waiting)) or b""):
            try:
                message = json.loads(raw.decode())
                if isinstance(message,dict) and "motion" in message:
                    motion = message["motion"]
                    if not isinstance(motion,list) or len(motion)!=5:
                        raise ValueError("Invalid wireless motion")
                    hid.report(*motion)
                    last_motion = time.monotonic()
                elif cdc.connected and isinstance(message,dict) and "ok" in message:
                    reply(raw+b"\n")
            except (ValueError,UnicodeError,OSError,RuntimeError):
                hid.release()
    # Full button/key snapshots + watchdog prevent stuck keys on radio loss.
    if time.monotonic()-last_motion > 0.5:
        hid.release()
        last_motion = time.monotonic()
    if cdc.connected:
        try:
            usb_tx.flush(cdc)
        except OSError:
            usb_tx.reset()
    time.sleep(0.001)
