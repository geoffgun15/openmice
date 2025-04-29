import board
import digitalio
import busio
import time
from microcontroller import delay_us

# PAW3395 register constants
REG_PRODUCT_ID     = 0x00
REG_MOTION         = 0x02
REG_MOTION_BURST   = 0x16
REG_POWER_UP_RESET = 0x3A

# Expected product ID (PAW3395)
EXPECTED_PRODUCT_ID = 0x0A

# SPI & CS setup
cs = digitalio.DigitalInOut(board.P0_24)
cs.direction = digitalio.Direction.OUTPUT
cs.value = True

spi = busio.SPI(clock=board.SCK, MOSI=board.MOSI, MISO=board.MISO)
# Lock & configure once for all transfers
while not spi.try_lock():
    pass
spi.configure(baudrate=4_000_000, phase=1, polarity=1)
spi.unlock()

# (Optional) Motion IRQ pin for interrupt-driven reads
irq_pin = digitalio.DigitalInOut(board.P0_23)
irq_pin.direction = digitalio.Direction.INPUT
irq_pin.pull = digitalio.Pull.DOWN

# Write a single register
def spi_write(register, value):
    while not spi.try_lock():
        pass
    cs.value = False
    delay_us(20)
    spi.write(bytes([register | 0x80, value]))
    delay_us(20)
    cs.value = True
    spi.unlock()

# Read a single register
def spi_read(register):
    while not spi.try_lock():
        pass
    cs.value = False
    delay_us(20)
    spi.write(bytes([register & 0x7F]))
    result = bytearray(1)
    spi.readinto(result)
    delay_us(20)
    cs.value = True
    spi.unlock()
    return result[0]

# Sensor initialization
def initialize_sensor():
    time.sleep(0.05)
    spi_write(REG_POWER_UP_RESET, 0x5A)
    time.sleep(0.005)

    # Full init sequence (abridged here; use your existing list)
    init_seq = [
        # (register, value), ...
        (0x7F, 0x07), (0x40, 0x41), # etc.
    ]
    for reg, val in init_seq:
        spi_write(reg, val)

    # Wait for "Ready" bit
    start = time.monotonic()
    while True:
        if spi_read(REG_MOTION) & 0x80:
            break
        if time.monotonic() - start > 0.060:
            raise RuntimeError("Sensor init timeout")
        time.sleep(0.001)

    # Verify Product ID
    pid = spi_read(REG_PRODUCT_ID)
    if pid != EXPECTED_PRODUCT_ID:
        raise RuntimeError(f"Unexpected PID: 0x{pid:02X}")

# Check if new motion is available
def motion_ready():
    return bool(spi_read(REG_MOTION) & 0x80)

# Parse & sanity-check a 6-byte burst
def parse_motion(data):
    dx = (data[3] << 8) | data[2]
    dy = (data[5] << 8) | data[4]
    if dx > 32767: dx -= 65536
    if dy > 32767: dy -= 65536
    # reject zeros or huge jumps
    if (dx, dy) == (0, 0) or abs(dx) > 1000 or abs(dy) > 1000:
        return None
    return dx, dy

# Read a motion burst with retries
def read_motion():
    for _ in range(3):
        try:
            while not spi.try_lock(): pass
            cs.value = False
            delay_us(20)
            spi.write(bytes([REG_MOTION_BURST & 0x7F]))
            buf = bytearray(6)
            spi.readinto(buf)
            delay_us(20)
            cs.value = True
            spi.unlock()
        except OSError:
            continue
        parsed = parse_motion(buf)
        if parsed:
            return parsed
    # recovery if all retries fail
    recover()
    return (0, 0)

# Soft recovery on errors/timeouts
def recover():
    print("[!] Recovering sensor...")
    initialize_sensor()

# Optional interrupt-driven handler
# def irq_handler(pin):
#     dx, dy = read_motion()\#     process_motion(dx, dy)
#
# irq_pin.edge = digitalio.Edge.RISING
# irq_pin.callback = irq_handler

# Main loop
initialize_sensor()
print("[+] Sensor initialized.")

while True:
    try:
        if motion_ready():
            dx, dy = read_motion()
            print(f"ΔX: {dx}, ΔY: {dy}")
        time.sleep(0.001)
    except Exception as e:
        print(f"Error: {e}")
        recover()
