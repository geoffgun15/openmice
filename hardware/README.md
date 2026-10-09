# Hardware A1: routed prototype candidates

Both custom boards are routed and have zero findings in KiCad 10.0.6 ERC,
DRC, connectivity and schematic parity checks. Manufacturing exports are in
`output/hardware/` and fabrication ZIPs in `output/`. **Physical tests are NOT RUN.**

| Board | Outline | Components | Functional nets |
|---|---|---:|---:|
| Mouse | 64 × 94 mm | 51 | 39 |
| USB-C receiver | 28 × 54 mm | 18 | 13 |

Both boards use soldered Raytac MDBT50Q-1MV2 nRF52840 modules. The mouse has a
bare PAW3395DM-T6QU, 1.9 V sensor/LED rail, 3.0 V MCU/VDDIO rail, external contact
headers for five switches and a scroll encoder, USB-C, SWD and Pair/reset buttons.
The receiver connects by USB-C cable and bridges BLE input/configuration to USB.
Proprietary 1000 Hz wireless is not implemented.

BQ24072 provides charging and system power path for a protected 1S 3.7 V nominal
300 mAh LiPo pack with thermally attached compatible 10k NTC (J3 BAT+, GND, NTC).
USB100 mode caps total input at 100 mA; R_ISET 5.90k programs about 151 mA before
input/system limits, R_ILIM 3.09k is overridden, R_TMR 68k is about 9.1 hours nominal.
The switch is downstream of charging. Firmware battery telemetry is approximate;
pack protection handles over-discharge. USB suspend management is not implemented.

Sensor VDDREG is decoupled only. TLV70019 supplies sensor VDD/LED (5.6 ohm 1%
resistor); TLV70030 supplies VDDIO and MCU VDD/VDDH. DCCH is unconnected. Separate
5.1k CC resistors and USBLC6-2SC6 protect USB; no PD. External 32.768 kHz crystal
loading needs bench verification. The module includes its normal-mode DC/DC parts.

Four layers use outer signal routing and two solid inner GND reference planes,
all-layer antenna keep-outs, routed optical/mounting apertures and charger thermal
vias. USB routing is manually protected. Review the
[fabrication specification](../docs/FABRICATION.md) for stack-up, impedance, filled thermal vias, lens and BOM
requirements before a first-article order. No shell or optical fit validation exists.

Editable native schematics/boards, local libraries, routing DSN/SES, BOM, placement
CSV and CAD-check reports are included. Regeneration overwrites routing; see
[build workflow](../docs/BUILD.md). The unused MouseSwitch_D2F_DRAFT footprint is
not in either BOM and is not validated. Bench bring-up is in
[FIRST_ARTICLE.md](../docs/FIRST_ARTICLE.md).

## References and licenses

- PAW3395DM-T6QU datasheet v1.3 (8 Apr 2024): confidential reference, excluded
  from this public repository; obtain through an authorized source.
- [Raytac module datasheet](https://www.raytac.com/tw/download/index.php?index_id=24).
- [BQ2407x datasheet, including BQ24072](https://www.ti.com/lit/ds/symlink/bq24074.pdf).
- [TLV700 regulators](https://www.ti.com/product/TLV700).
- [KiCad footprints](https://github.com/KiCad/kicad-footprints) and
  [symbols](https://github.com/KiCad/kicad-symbols).

Vendored KiCad data retains upstream CC-BY-SA 4.0 licensing with the KiCad library
exception; see the [library license](https://www.kicad.org/libraries/license/).
Project code uses MIT. The confidential PixArt reference is not distributed.
