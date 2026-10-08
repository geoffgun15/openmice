# A1 prototype fabrication specification

The supplied files are routed prototype candidates. Physical validation is NOT
RUN. Before ordering a first article, confirm the stack-up, lens fit and assembly
process below with the fabricator. This package is not a production release.

| Item | Specification |
|---|---|
| Mouse outline | 64 × 94 mm, four 2.7 mm routed mounting apertures |
| Receiver outline | 28 × 54 mm, USB-C cable connection |
| Layers | F.Cu signals / In1.Cu GND / In2.Cu GND / B.Cu signals |
| Finished thickness | Nominal 1.6 mm, confirm optics before manufacture |
| Outer copper | 35 µm nominal |
| Outer dielectric | Nominal 0.10 mm, FR4 Er approximately 4.2 |
| Inner core | Approximately 1.26 mm; vendor completes stack-up |
| USB impedance | Target 90 Ω differential; vendor must solve stack-up |
| USB geometry | 0.17 mm width / 0.15 mm gap; impedance not measured |
| Minimum track/clearance | 0.125 / 0.125 mm |
| Through vias | 0.50 mm copper / 0.20 mm finished drill |
| Copper to cut edge | 0.25 mm minimum |
| Finish | ENIG recommended for prototype assembly |

Gerbers include four copper layers, masks, silk, paste and Edge.Cuts. Excellon
files separate plated and nonplated holes. Edge.Cuts contains mouse optical and
mounting apertures: route these, do not treat them as artwork. No blind vias.
Review the exported drill-map SVG and copper layers against the native board.

The BQ24072 exposed pad is 1.68 mm square, with a 1.55 mm paste aperture
(approximately 85% coverage) and four 0.20 mm thermal vias. **Fill/plug and cap
these vias before assembly** to prevent solder loss. One corner via is replaced
by a central via to avoid the rear configuration trace. All other vias are
tented. Confirm paste thickness and reflow profile with the assembler.

The PAW3395 is through-hole and needs its matching optical assembly. The
17.26 × 8.60 mm aperture is based on the supplied sensor drawing. LM19-LSI lens,
1.6 mm board fit, sensor seating height and lens-to-surface distance require an
actual mechanical fit check. No shell is supplied. Switches and encoder attach
to headers; the bare board is not a complete enclosed mouse.

Keep copper/components/cables/metal away from the radio antenna areas on all
layers. Housing and battery placement can change antenna performance. Raytac
module approval does not establish approval of this complete product.

BOM values and placement CSV are engineering inputs, not a turnkey assembly
order. Confirm supplier part numbers/package variants, regulator pinouts, USB-C
connector HRO TYPE-C-31-M-12, PAW3395DM-T6QU and Raytac MDBT50Q-1MV2. Use 1%
charger/LED/divider resistors, X5R/X7R capacitors with voltage and DC-bias margin,
USB capacitors rated at least 10 V, and battery/system capacitors at least 6.3 V.
Do not silently substitute charger, optics or antenna modules.

Use a protected single-cell 3.7 V LiPo pack, nominal 300 mAh, with compatible
thermally attached 10 kΩ NTC. J3 is BAT+, GND, NTC. Confirm polarity before
connection. Charger USB100 selection caps total input at 100 mA; actual charge
current is lower while the system runs. See FIRST_ARTICLE.md for bring-up.

Checks: KiCad 10.0.6 ERC, DRC and schematic parity are stored under
output/hardware/{mouse,receiver}. Zero findings establish CAD consistency under
the configured rules, not optical, RF, thermal, EMC or physical functionality.
