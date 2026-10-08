# Setup, protocol and verification

**A1 status:** routed boards pass KiCad ERC/DRC and schematic parity. Native
runtime and bootloader are compiled and packaged. Physical tests are NOT RUN.
Read [first-article procedure](FIRST_ARTICLE.md) before powering an assembled board.

## Runtime and application

Both devices use the custom openmice_nrf52840 runtime, not a nice!nano runtime.
P0.15 is sensor MISO and must not drive a status LED. The runtime includes frozen
BLE dependencies and the native PAW startup polling helper.

For a blank board, use an SWD probe to program and verify
`output/native/openmice-factory.hex`. It includes MBR, S140 6.1.1, bootloader,
application and UICR/valid-bank settings. Confirm probe voltage and target pinout.
No board has yet been flashed. Do not use a commercial-board bootloader.

For runtime updates after provisioning, hold Pair during reset to enter the
bootloader and copy `output/native/openmice-runtime.uf2` to its UF2 drive.
The bootloader update UF2 in the native bundle is a different image and is
only for bootloader maintenance. SWD is the recovery path.

Copy contents of `output/openmice-mouse.zip` or `output/openmice-receiver.zip`
to the corresponding CIRCUITPY drive. No external BLE bundle is needed.
Power-cycle after changing boot.py. Mouse report ID 2 and keyboard ID 1 share
one HID interface; the configuration CDC channel and recovery storage remain
enabled. Enumeration and recovery must be verified on the first physical board.

The USB ID 1209:0001 is a shared private-test ID; allocate a unique ID for wider
distribution. Source/build steps and hashes are in [BUILD.md](BUILD.md).

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

Config uses two checksummed 4096-byte NVM slots on separate flash erase pages,
bytes 0–8191. Receiver peer identity starts at offset 8192 in a third page.
The native runtime reserves 12 KiB. Preserve this layout; smaller generic-runtime
allocations are incompatible.

## Verification

Completed: 18 host Python tests and five JavaScript tests. Coverage includes
sensor startup/fallback, signed motion, SPI cleanup, DPI/ripple control, validation,
page-erasure power interruption, duplicate bindings, debounce, quadrature, HID
lengths/distinct report IDs, partial CDC writes and hardware pin mapping.
The browser demo was exercised with DPI and a keyboard side-button binding.

Both boards pass native KiCad 10.0.6 ERC, DRC, connectivity and schematic parity.
ARM GNU 13.2.Rel1 compiled the custom CircuitPython 9.2.8 runtime and Adafruit
0.11.0 bootloader with matching S140 6.1.1. These are build/host checks only.

Physical tests are NOT RUN. USB enumeration, SPI timing, optics/CPI, input behavior,
persistence on hardware, pairing/reconnect, charging/NTC/thermal behavior, current,
range and latency remain in [FIRST_ARTICLE.md](FIRST_ARTICLE.md). The serial bench
harness is supplied but has not been run against a board. PAW rest mode is retained;
MCU deep sleep and firmware low-battery shutdown are not implemented. Pack
protection is required, and battery life is not measured.
