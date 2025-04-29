PAW3395 Mouse Firmware
This project implements low-latency, robust firmware for a custom USB mouse using the PAW3395 optical sensor on a nice!nano (CircuitPython) board.

Features
One-time SPI configuration at 4 MHz with precise microsecond timing

Motion-ready flag polling and adjustable POLL_INTERVAL for flexible sampling rates

6-byte motion burst reads (ΔX/ΔY) with sanity checks and up to 3 retries

Automatic sensor reset/recovery on timeouts or bus errors

Optional interrupt-driven reads via the PAW3395’s MOTION/IRQ pin

Product ID verification to detect wiring or sensor mismatches

Hardware Requirements
nice!nano board running CircuitPython

PAW3395 optical mouse sensor module

Optional: push-button or switch wired to the MOTION/IRQ pin for interrupt mode

Pin Connections

nice!nano Pin	PAW3395 Signal
board.SCK	SCLK
board.MOSI	SDI
board.MISO	SDO
P0_24 (CS)	CS
P0_23 (IRQ)	MOTION / IRQ
3.3 V / GND	VCC / GND
Software Setup
Install CircuitPython on your nice!nano (v8.x or later recommended).

Copy main.py to the root of the CIRCUITPY drive.

(Optional) If using interrupt mode, wire MOTION/IRQ to P0_23 and uncomment the IRQ handler in main.py.

Configuration
At the top of main.py, adjust any of the following constants to suit your needs:

python
Copy
Edit
# Sampling interval between motion-ready checks (in seconds)
POLL_INTERVAL = 0.001      # e.g. 0.001 = 1 ms

# Chip select pin for SPI (change if P0_24 is unavailable)
CS_PIN = board.P0_24

# (Optional) IRQ pin for interrupt-driven reads
IRQ_PIN = board.P0_23
Usage
Plug the nice!nano into your host (USB).

Open a serial console (e.g. PuTTY, screen /dev/ttyACM0 115200).

Observe printed motion deltas:

makefile
Copy
Edit
[+] Sensor initialized.
ΔX: 12, ΔY: -5
ΔX: 0,  ΔY: 0
ΔX: 30, ΔY: 15
(Advanced) Replace the print() calls with adafruit_hid.mouse.Mouse.move(dx, dy) to emulate a real USB-HID mouse.

Troubleshooting
No output on serial: Verify CS wiring and power rails; check that CircuitPython is loaded.

Stuck on init timeout: Confirm register constants and that the sensor’s power-up reset (0x3A) is supported.

Packet drop symptoms: Tweak POLL_INTERVAL or enable IRQ mode.

License
This code is released under the MIT License.

