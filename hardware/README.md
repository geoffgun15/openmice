# Hardware A0: electrical and placement drafts

**Not for fabrication. Both PCBs are unrouted.** KiCad is not installed here;
native parsing, electrical-rule checks (ERC) and clearance checks (DRC) are pending.
No manufacturing exports are supplied.

| Board | Generic outline | Components | Connected nets |
|---|---|---:|---:|
| Mouse | 64 × 94 mm | 51 | 39 |
| USB-C receiver | 20 × 44 mm | 18 | 13 |

Both boards use a soldered Raytac MDBT50Q-1MV2 nRF52840 radio module. They do not
use a nice!nano or other development board. The receiver connects via a USB-C
data cable; it is not a direct USB-A plug dongle. BLE is the implemented radio;
proprietary 1000 Hz wireless is not implemented.

## Mouse circuit

- Bare PAW3395DM-T6QU with integrated IR emitter and a compatible LM19-LSI lens.
- TLV70019: 1.9 V sensor VDD and LED rail; 5.6 ohm, 1% LED resistor.
  VDDREG is decoupled only and must not power external loads.
- TLV70030: 3.0 V MCU and sensor VDDIO rail. Radio VDDH is tied to VDD for
  normal-voltage operation; DCCH is unconnected. USB VBUS remains a separate input.
- BQ24072: 4.2 V single-cell charger with integrated system power path. EN1/EN2
  select USB100, limiting total input to 100 mA. R_ISET=5.90k programs about
  151 mA nominal; the input limit and system load reduce actual charging current.
  R_ILIM=3.09k is installed but overridden in USB100 mode. R_TMR=68k gives about
  9.1 hours nominal; verify tolerances and charging completion on the chosen pack.
- Protected 1S 3.7 V / 300 mAh LiPo with compatible thermally attached 10k NTC.
  J3 pin order: BAT+, GND, NTC. Check actual pack polarity and charge ratings.
  Pack protection handles over-discharge. Firmware voltage telemetry is not a
  calibrated fuel gauge or low-battery cutoff.
- Downstream power switch leaves the charger active. USB current upgrades and
  suspend management are not implemented; USB-IF compliance is not claimed.
- Five external switch contact headers and an A/GND/B scroll encoder header,
  allowing switch placement to be chosen for a future shell. Pair/reset buttons
  and SWD recovery header are onboard.
- Separate 5.1k resistors on CC1/CC2 and USBLC6-2SC6 protection. No USB PD.

## Files and verification

Each board folder contains an editable schematic, PCB placement, netlist,
connectivity JSON, BOM and SVG placement overview. Standard footprints are
vendored. Boards use KiCad 5 format and schematics KiCad 8 format; newer KiCad can
migrate the board on opening. Both file structures were checked by a simple
parser, **not by KiCad**. Each named net has at least two nodes and referenced
pad numbers exist in the included footprints.

The generated schematic uses block symbols and labels on every connection.
Pin electrical types are currently passive; refine them and add power flags
before using ERC to check power sources and electrical drive.
`tools/build_hardware.py` overwrites generated files; preserve manual edits first.

## Work required before ordering

1. Open both designs in KiCad, validate syntax, refine symbols and run ERC.
   Verify every pin mapping and package against manufacturer drawings, especially
   BQ24072 exposed-pad land pattern/paste windows and USB-C connector geometry.
2. Verify PAW3395 lead staggering, pin 1 orientation and optical center against
   datasheet Figures 3–6. The approximate aperture is only on Dwgs.User. Replace
   it with the exact cutout on Edge.Cuts after confirming the lens. Set lens height,
   mounting holes and shell clearances from the actual mechanical stack.
3. Refine component placement and decoupling, courtyards and cable/battery clearance.
   Complete routing, planes and thermal vias. Proposed four-layer stack:
   signal / ground / power+signal / signal.
4. Route USB as a continuous-reference differential pair. Calculate impedance
   from the actual fabricator stack-up; length matching is insufficient alone.
5. Retain radio antenna keep-outs on all layers, verify them against Raytac's
   guidance, and keep the battery, shields and metal shell away from the antenna.
6. Resolve ERC/DRC errors, inspect exports, then perform power, NTC/charging,
   optical and RF first-article tests. No runtime, latency or range is measured.

The unused `MouseSwitch_D2F_DRAFT` footprint is not in either BOM and is not verified.

## References and licenses

- Supplied PAW3395DM-T6QU datasheet v1.3 (8 Apr 2024), unchanged in `docs/`.
- [Raytac module datasheet](https://www.raytac.com/tw/download/index.php?index_id=24).
- [BQ2407x datasheet, including BQ24072](https://www.ti.com/lit/ds/symlink/bq24074.pdf).
- [TLV700 regulators](https://www.ti.com/product/TLV700).
- [KiCad footprints](https://github.com/KiCad/kicad-footprints) and
  [symbols](https://github.com/KiCad/kicad-symbols).

Vendored KiCad data retains upstream CC-BY-SA 4.0 licensing with the KiCad library
exception; see the [library license](https://www.kicad.org/libraries/license/).
Project code uses MIT. The PixArt reference retains its original restrictions.
