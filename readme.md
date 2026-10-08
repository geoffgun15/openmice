# OpenMice Proto

Custom PAW3395 rechargeable mouse, USB wireless receiver, and browser configurator.

**A0 is a prototype design package, not a finished hardware release.** Application
logic has host tests and the editor has a browser demo. Both PCBs are **unrouted
schematic/placement drafts**. Native runtime/bootloader builds and physical testing
are outstanding. Do not order PCBs from these drafts.

| Component | Included |
|---|---|
| Mouse | Bare PAW3395, nRF52840 module, 1S LiPo charger/power path, five buttons + scroll |
| Receiver | Custom nRF52840 board, USB-C, BLE-to-USB HID and configuration bridge |
| Firmware | Corrected sensor startup/ID/timing, 16-bit motion, DPI, bindings, persistence |
| Editor | Web Serial, DPI, mouse/keyboard bindings, Apply/Save, import/export and demo |

The radio modules are soldered components on custom PCBs; nice!nano is no longer
used. BLE is the prototype radio; proprietary 1000 Hz wireless is not implemented.

- [Hardware files and remaining layout work](hardware/README.md)
- [Setup, protocol and verification](docs/SETUP.md)
- [Mouse schematic](hardware/mouse/mouse.kicad_sch) / [PCB draft](hardware/mouse/mouse.kicad_pcb)
- [Receiver schematic](hardware/receiver/receiver.kicad_sch) / [PCB draft](hardware/receiver/receiver.kicad_pcb)
- [Browser editor](web/index.html)

## Preview

```sh
python -m http.server 8765 --bind 127.0.0.1 --directory web
```

Open http://127.0.0.1:8765/ in desktop Chrome/Edge. Demo mode works without hardware.
A real connection requires the validated runtime and mouse/receiver.

## Development

```sh
python -m unittest discover -s tests -v
node --test web/test.mjs
python tools/package_firmware.py
```

`tools/build_hardware.py` regenerates the drafts and overwrites manual edits.
The original sensor PDF is unchanged. Prototype assumptions: LM19-LSI optics,
64 x 94 mm mouse outline, external switch/encoder contacts, and a protected
300 mAh cell with compatible NTC temperature sensing.

Project code: MIT. Vendored KiCad libraries retain their upstream licenses;
see hardware/README.md. The PixArt PDF retains its original restrictions.
