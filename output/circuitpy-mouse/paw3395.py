"""PAW3395DM-T6QU driver, datasheet v1.3 sections 5, 6, 8.

SPI mode 3. All transactions release CS and the bus, including failures.
Initialization values are in init_sequence.py, checked against section 6.2.
"""
import time
from microcontroller import delay_us
from init_sequence import INIT_SEQUENCE

def signed16(low, high):
    value = low | high << 8
    return value-65536 if value & 0x8000 else value

class PAW3395:
    def __init__(self, spi, cs, reset):
        self.spi, self.cs, self.reset = spi, cs, reset
        self.burst = bytearray(6)
        self.one = bytearray(1)

    def _begin(self):
        deadline = time.monotonic()+0.05
        while not self.spi.try_lock():
            if time.monotonic() >= deadline:
                raise RuntimeError("SPI lock timeout")
        try:
            self.spi.configure(baudrate=4_000_000, polarity=1, phase=1)
            self.cs.value = False
            delay_us(1)
        except Exception:
            self.cs.value = True
            self.spi.unlock()
            raise

    def _end(self):
        self.cs.value = True
        self.spi.unlock()
        delay_us(5)

    def write(self, address, value):
        self._begin()
        try:
            self.spi.write(bytes((address | 0x80, value)))
            delay_us(1)
        finally:
            self._end()

    def read(self, address):
        self._begin()
        try:
            self.spi.write(bytes((address & 0x7f,)))
            delay_us(2)
            self.spi.readinto(self.one, write_value=0)
            delay_us(1)
            return self.one[0]
        finally:
            self._end()

    def initialize(self):
        self.reset.value = False
        delay_us(10)
        self.reset.value = True
        time.sleep(0.05)
        self.cs.value = True
        delay_us(5)
        self.cs.value = False
        delay_us(5)
        self.cs.value = True
        self.write(0x3a, 0x5a)
        time.sleep(0.005)
        for address, value in INIT_SEQUENCE:
            self.write(address, value)
        delay_us(1000)
        ready = False
        for _ in range(60):
            started = time.monotonic_ns()
            if self.read(0x6c) == 0x80:
                ready = True
                break
            # Best effort 1ms cadence; verify ±1% requirement on a logic analyser.
            elapsed = (time.monotonic_ns()-started)//1000
            if elapsed < 1000:
                delay_us(1000-elapsed)
        if not ready:
            self.write(0x7f, 0x14)
            self.write(0x6c, 0)
            self.write(0x7f, 0)
        for address, value in ((0x22,0), (0x55,0), (0x7f,7), (0x40,0x40), (0x7f,0), (0x68,1)):
            self.write(address, value)
        if self.read(0) != 0x51 or self.read(0x5f) != 0xae:
            raise RuntimeError("PAW3395 product/inverse ID mismatch")
        for address in range(2,7):
            self.read(address)

    def set_dpi(self, dpi):
        if type(dpi) is not int or not 50 <= dpi <= 26000 or dpi % 50:
            raise ValueError("Invalid DPI")
        resolution = dpi//50-1
        self.write(0x7f, 0)
        for address in (0x48,0x4a):
            self.write(address, resolution & 255)
            self.write(address+1, resolution >> 8)
        self.write(0x47, 1)
        self.write(0x5a, 0x90 if dpi >= 9000 else 0x10)

    def motion(self):
        self._begin()
        try:
            self.spi.write(b"\x16")
            delay_us(2)
            self.spi.readinto(self.burst, write_value=0)
            delay_us(1)
        finally:
            self._end()
        if not self.burst[0] & 0x80:
            return 0,0
        return signed16(self.burst[2],self.burst[3]), signed16(self.burst[4],self.burst[5])
