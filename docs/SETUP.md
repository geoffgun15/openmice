# Setup, protocol and verification

**A0 status:** application code tested on a host, custom CircuitPython board
definition prepared, no compiled native firmware/bootloader, no physical tests,
and unrouted PCB drafts. The application ZIPs are not flashable UF2 files.

## Runtime and application

The custom PCB is not a nice!nano. Do not use a nice!nano runtime: P0.15 is MISO
here, while that board's runtime uses it as a status LED.
`firmware/board/openmice_nrf52840` is a native board definition prepared against
CircuitPython 9.2.8's Nordic port. Both devices use this target, internal flash,
an external 32.768 kHz crystal, and no status LED. It has not been compiled.

On a supported build host, check out the official CircuitPython 9.2.8 tag, install
its documented prerequisites/submodules, copy the board folder to
`ports/nordic/boards/`, and build:

```sh
make -C mpy-cross
make -C ports/nordic BOARD=openmice_nrf52840
```

See [building CircuitPython](https://docs.circuitpython.org/en/stable/BUILDING.html)
and the [Nordic flashing guide](https://learn.adafruit.com/circuitpython-on-the-nrf52/build-flash-circuitpython).
First programming needs an SWD probe and a compatible bootloader/SoftDevice
memory layout. A bootloader definition/build for these pins is **outstanding**.
Confirm reset P0.18 configuration in UICR. Do not assume a commercial-board
bootloader is suitable.

The runtime uses [1209:0001](https://pid.codes/1209/0001/), a shared private-test
USB ID. It is not unique and must be replaced by an assigned ID for distribution
or manufacture beyond private test units.

Run `python tools/package_firmware.py`. Copy the matching application ZIP's
contents to CIRCUITPY after the validated runtime is installed. Add `adafruit_ble`
and its dependencies from the CircuitPython 9.x library bundle to `lib/`.
Power-cycle after boot.py changes. Boot enables 16-bit mouse/keyboard HID, one
data serial channel and recovery storage; serial REPL is disabled. Endpoint
allocation and safe-mode recovery still need verification on the actual runtime.

## Pairing and browser

Connect the receiver using a USB-C data cable, power the mouse, and hold Pair on
both devices until discovery/bonding completes. The receiver then stores the
mouse's address and reconnects to it. Hold both Pair buttons to replace the peer.
Address rotation/privacy support is not implemented; firmware changes that alter
the mouse's static address require pairing again.

The mouse gates application traffic on paired state. Initial bonding uses
Just Works with no authenticated identity confirmation; pair in a controlled
setting. This is a prototype trust model that needs physical verification.

USB on the mouse selects wired input. The receiver bridges configuration to the
wireless mouse. It releases held inputs after 500 ms without a report. Wireless
motion is scheduled at 16 ms intervals and input-state changes are sent sooner;
BLE/Python add variable latency. No 1000 Hz wireless performance is claimed.

Start the editor from the repository:

```sh
python -m http.server 8765 --bind 127.0.0.1 --directory web
```

Open [OpenMice Studio](http://127.0.0.1:8765/) in desktop Chrome/Edge, choose
Connect device and select the mouse/receiver configuration serial port. Web
Serial needs localhost or HTTPS. A handshake validates name and protocol.
An offline mouse produces an explicit receiver error.

Apply changes updates live settings; Save to mouse applies the displayed profile
and persists it. Read device replaces displayed edits with device settings.
Demo mode changes only browser state and disables device Save/Read.

## Protocol v1

Newline-delimited UTF-8 JSON, incoming device frames bounded at 480 bytes.
Integer IDs are echoed in replies.

```json
{"id":1,"cmd":"hello"}
{"id":2,"cmd":"get"}
{"id":3,"cmd":"set","config":{"dpi":1600,"bindings":["left","right","middle","key:CTRL+C","forward"]}}
{"id":4,"cmd":"save"}
```

Replies have ok/config or ok:false/error. Hello includes device:OpenMice and
protocol:1; mouse replies include approximate battery_mv. The receiver consumes
wireless `motion:[dx,dy,wheel,button_mask,keycodes]` and forwards command replies.
DPI is 50–26000 in steps of 50. Bindings are mouse actions, none, or key: plus
1–6 distinct UI-supported key names joined by +.

Config uses two checksummed 512-byte NVM slots with a final commit marker, in
bytes 0–1023. Receiver peer identity starts at offset 1024; preserve this layout.

## Verification

Completed: 16 Python tests for sensor startup/fallback, signed extremes, SPI error
cleanup, DPI/ripple control, validation, torn/corrupt storage, duplicate bindings,
debounce, quadrature, HID report shape, partial CDC writes and PCB pin mapping.
Five JavaScript tests cover validation, split/correlated responses, errors,
timeouts, overflow and disconnect cancellation. Browser demo was exercised with
1600 DPI and a CTRL+C side-button binding. Hardware checks are structural only.

Still required: native runtime/bootloader builds and USB endpoint enumeration;
real BLE pairing/reconnect/fragmentation and transport fault tests; logic-analyser
SPI timing (including the datasheet ±1% 1 ms startup cadence, best effort in
Python); calibrated CPI/optical alignment; switch/encoder behavior; NTC, charging,
power-path transition and temperature tests; RF range, current and latency;
complete routing, stack-up/mechanical review, ERC/DRC and first article.
PAW3395 rest mode is retained, but MCU deep sleep and firmware low-battery shutdown
are not implemented. Pack protection is required. Battery life is not measured.
