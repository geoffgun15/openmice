"""Debounced contacts and binding aggregation, independent of GPIO/HID."""
from config import MOUSE_ACTIONS, keycodes

class Debounce:
    def __init__(self, interval=0.005):
        self.interval = interval
        self.raw = self.stable = False
        self.changed = 0
    def update(self, pressed, now):
        if pressed != self.raw:
            self.raw, self.changed = pressed, now
        if now-self.changed >= self.interval:
            self.stable = self.raw
        return self.stable

def aggregate(pressed, bindings):
    buttons, keys = 0, set()
    for down, action in zip(pressed, bindings):
        if not down or action == "none":
            continue
        if action in MOUSE_ACTIONS[:5]:
            buttons |= 1 << MOUSE_ACTIONS.index(action)
        else:
            keys.update(keycodes(action))
    # USB boot keyboard supports six non-modifier keys; reject rollover safely.
    if len([key for key in keys if key < 224]) > 6:
        keys = {key for key in keys if key >= 224}
    return buttons, sorted(keys)

class Quadrature:
    TABLE = (0,-1,1,0, 1,0,0,-1, -1,0,0,1, 0,1,-1,0)
    def __init__(self, initial, steps=4):
        self.previous, self.total, self.steps = initial, 0, steps
    def update(self, state):
        if state ^ self.previous == 3:
            self.total = 0
        else:
            self.total += self.TABLE[self.previous*4+state]
        self.previous = state
        if abs(self.total) >= self.steps:
            tick = 1 if self.total > 0 else -1
            self.total -= tick*self.steps
            return tick
        return 0
