# OpenMice

Custom PAW3395 rechargeable mouse, USB wireless receiver, and browser configurator.

Standalone repository: https://github.com/geoffgun15/openmice.
Migrated from the original fork with all eight commits retained and the
confidential PixArt PDF removed from every commit. Historical commit IDs changed.

**A1 is a routed prototype package.** Both boards pass KiCad electrical,
clearance, connectivity and schematic parity checks. Custom runtime and
bootloader builds, factory HEX, runtime UF2 and fabrication exports are included.
**Physical tests are NOT RUN: there is no assembled board.** Review the
[first-article procedure](docs/FIRST_ARTICLE.md) and
[fabrication requirements](docs/FABRICATION.md) before a prototype order.

| Component | Included |
|---|---|
| Mouse | Bare PAW3395, nRF52840 module, 1S LiPo charger/power path, five buttons + scroll |
| Receiver | Custom nRF52840 board, USB-C, BLE-to-USB HID and configuration bridge |
| Firmware | Corrected sensor startup/ID/timing, 16-bit motion, DPI, bindings, persistence |
| Editor | Web Serial, DPI, mouse/keyboard bindings, Apply/Save, import/export and demo |

The radio modules are soldered components on custom PCBs; nice!nano is no longer
used. BLE is the prototype radio; proprietary 1000 Hz wireless is not implemented.

- [Hardware files and validation status](hardware/README.md)
- [Setup, protocol and verification](docs/SETUP.md)
- [Mouse schematic](hardware/mouse/mouse.kicad_sch) / [PCB](hardware/mouse/mouse.kicad_pcb)
- [Receiver schematic](hardware/receiver/receiver.kicad_sch) / [PCB](hardware/receiver/receiver.kicad_pcb)
- [Browser editor](web/index.html)

## Preview

```sh
python -m http.server 8765 --bind 127.0.0.1 --directory web
```

Open http://127.0.0.1:8765/ in desktop Chrome/Edge. Demo mode works without hardware.
A real connection requires the supplied runtime and mouse/receiver.

Native build details, hashes and CAD export workflow: [BUILD.md](docs/BUILD.md).

## Development

```sh
python -m unittest discover -s tests -v
node --test web/test.mjs
python tools/package_firmware.py
```

`tools/build_hardware.py` regenerates starting placements and overwrites manual edits.
The confidential sensor PDF is excluded from this public repository and its Git history.
Prototype assumptions: LM19-LSI optics,
64 x 94 mm mouse outline, external switch/encoder contacts, and a protected
300 mAh cell with compatible NTC temperature sensing.

Project code: MIT. Vendored KiCad libraries retain their upstream licenses;
see hardware/README.md. Obtain sensor documentation through an authorized source.
