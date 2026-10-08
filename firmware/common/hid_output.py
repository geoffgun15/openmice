import struct
import usb_hid

class Output:
    def __init__(self):
        self.mouse = next(device for device in usb_hid.devices if device.usage_page == 1 and device.usage == 2)
        self.keyboard = next(device for device in usb_hid.devices if device.usage_page == 1 and device.usage == 6)
        self.keys = []
    def report(self, x, y, wheel, buttons, keys):
        if type(buttons) is not int or not 0 <= buttons <= 31:
            raise ValueError("Invalid buttons")
        if any(type(v) is not int for v in (x,y,wheel)):
            raise ValueError("Invalid motion")
        if not -32768 <= x <= 32767 or not -32768 <= y <= 32767 or not -127 <= wheel <= 127:
            raise ValueError("Motion report out of range")
        if not isinstance(keys,list) or len(keys)>10 or any(type(k) is not int or not 4 <= k <= 227 for k in keys):
            raise ValueError("Invalid keys")
        modifiers = 0
        ordinary = []
        for code in keys:
            if 224 <= code <= 227:
                modifiers |= 1 << (code-224)
            elif code < 224 and code not in ordinary:
                ordinary.append(code)
        if len(ordinary) > 6:
            raise ValueError("Keyboard rollover")
        if keys != self.keys:
            self.keyboard.send_report(bytes([modifiers,0]+ordinary+[0]*(6-len(ordinary))))
        self.keys = keys[:]
        self.mouse.send_report(struct.pack("<Bhhb",buttons,x,y,wheel))
    def release(self):
        self.keyboard.send_report(b"\0"*8)
        self.keys = []
        self.mouse.send_report(b"\0"*6)
