"""Hardware-independent configuration, framing and dual-slot persistence."""
import json
import struct

BUTTONS = ("left", "right", "middle", "back", "forward")
MOUSE_ACTIONS = ("left", "right", "middle", "back", "forward", "none")
KEYS = {chr(65+i): 4+i for i in range(26)}
KEYS.update({str((i+1) % 10): 30+i for i in range(10)})
KEYS.update({"ENTER":40, "ESC":41, "BACKSPACE":42, "TAB":43, "SPACE":44,
             "RIGHT":79, "LEFT":80, "DOWN":81, "UP":82})
MODIFIERS = {"CTRL":224, "SHIFT":225, "ALT":226, "GUI":227}
KEYS.update(MODIFIERS)

def defaults():
    return {"dpi":800, "bindings":list(BUTTONS)}

def keycodes(action):
    if not isinstance(action, str) or not action.startswith("key:"):
        raise ValueError("Use a mouse action or key:CTRL+C")
    names = action[4:].split("+")
    if not 1 <= len(names) <= 6 or len(set(names)) != len(names):
        raise ValueError("A chord needs 1 to 6 distinct keys")
    try:
        return [KEYS[name] for name in names]
    except KeyError:
        raise ValueError("Unknown key in " + action)

def validate(value):
    if not isinstance(value, dict) or set(value) != {"dpi", "bindings"}:
        raise ValueError("Expected dpi and bindings")
    dpi = value["dpi"]
    if type(dpi) is not int or not 50 <= dpi <= 26000 or dpi % 50:
        raise ValueError("DPI must be 50 to 26000 in steps of 50")
    bindings = value["bindings"]
    if not isinstance(bindings, list) or len(bindings) != 5:
        raise ValueError("Exactly five bindings required")
    for action in bindings:
        if action not in MOUSE_ACTIONS:
            keycodes(action)
    return {"dpi":dpi, "bindings":bindings[:]}

def checksum(data):
    result = 2166136261
    for byte in data:
        result = ((result ^ byte) * 16777619) & 0xffffffff
    return result

class Store:
    """First 1024 NVM bytes are reserved. Commit marker is written last."""
    SLOT = 512
    HEADER = 14
    def __init__(self, nvm):
        if len(nvm) < self.SLOT * 2:
            raise ValueError("Need 1024 NVM bytes")
        self.nvm = nvm
        self.active = -1
        self.generation = 0

    def load(self):
        selected = defaults()
        for slot in range(2):
            offset = slot * self.SLOT
            data = bytes(self.nvm[offset:offset+self.SLOT])
            if data[:4] != b"OMC1":
                continue
            generation, size, expected = struct.unpack("<IHI", data[4:14])
            if size > self.SLOT-self.HEADER:
                continue
            payload = data[14:14+size]
            if checksum(payload) != expected:
                continue
            try:
                config = validate(json.loads(payload.decode()))
            except (ValueError, UnicodeError):
                continue
            if self.active < 0 or 0 < ((generation-self.generation) & 0xffffffff) < 0x80000000:
                self.active, self.generation, selected = slot, generation, config
        return selected

    def save(self, config):
        payload = json.dumps(validate(config)).encode()
        if len(payload) > self.SLOT-self.HEADER:
            raise ValueError("Configuration too large")
        slot = 0 if self.active != 0 else 1
        generation = (self.generation + 1) & 0xffffffff
        offset = slot*self.SLOT
        self.nvm[offset:offset+4] = b"\0\0\0\0"
        body = struct.pack("<IHI", generation, len(payload), checksum(payload)) + payload
        self.nvm[offset+4:offset+4+len(body)] = body
        self.nvm[offset:offset+4] = b"OMC1"
        self.active, self.generation = slot, generation

class Lines:
    """Bounded newline frames; overflow discards through the next newline."""
    def __init__(self, maximum=480):
        self.maximum, self.buffer, self.discard = maximum, bytearray(), False
    def reset(self):
        self.buffer = bytearray()
        self.discard = False
    def feed(self, data):
        result = []
        for byte in data:
            if byte == 10:
                if not self.discard and self.buffer:
                    result.append(bytes(self.buffer))
                self.reset()
            elif not self.discard:
                if len(self.buffer) >= self.maximum:
                    self.buffer = bytearray()
                    self.discard = True
                else:
                    self.buffer.append(byte)
        return result

def frame(value):
    return (json.dumps(value)+"\n").encode()

class TxBuffer:
    """Preserve partial USB CDC writes without blocking the input loop."""
    def __init__(self, maximum=2048):
        self.maximum, self.data = maximum, b""
    def reset(self):
        self.data = b""
    def append(self, data):
        if len(self.data)+len(data) > self.maximum:
            raise RuntimeError("Configuration output queue full")
        self.data += data
    def flush(self, stream):
        if self.data:
            written = stream.write(self.data[:64]) or 0
            self.data = self.data[written:]

class ConfigAPI:
    def __init__(self, sensor, store):
        self.sensor, self.store = sensor, store
        self.config = store.load()
        self.sensor.set_dpi(self.config["dpi"])
    def handle(self, request):
        request_id = request.get("id") if isinstance(request, dict) else None
        try:
            if not isinstance(request, dict) or type(request_id) is not int:
                raise ValueError("Integer request id required")
            command = request.get("cmd")
            if command == "hello":
                result = {"device":"OpenMice", "protocol":1, "config":self.config}
            elif command == "get":
                result = {"config":self.config}
            elif command == "set":
                candidate = validate(request.get("config"))
                self.sensor.set_dpi(candidate["dpi"])
                self.config = candidate
                result = {"config":self.config, "saved":False}
            elif command == "save":
                self.store.save(self.config)
                result = {"config":self.config, "saved":True}
            else:
                raise ValueError("Unknown command")
            result.update({"id":request_id, "ok":True})
            return result
        except (ValueError, OSError, RuntimeError) as error:
            return {"id":request_id, "ok":False, "error":str(error)}
