# Rebuild and verification

The supplied native files were compiled with ARM GNU 13.2.Rel1 on Windows using
MSYS2 make 4.4.1, Python 3.12, GCC 15.3 for mpy-cross, and the source commits in
output/native/manifest.json. Flash use is recorded in runtime-size.json. Both
devices share the runtime/bootloader; their code.py payloads differ.

CircuitPython 9.2.8 commit 361dbc02066f8d2b83c3a7f1f4993a9a590d1239 and Adafruit
nRF52 Bootloader 0.11.0 commit c67f0bcf0fa8e841426335b1bbde91cda6ca1f50 are used.
S140 **6.1.1 must match in both**. The board enables internal storage, a 12 KiB
NVM allocation, the external 32.768 kHz crystal, and no LED. BLE/Register/BusDevice
libraries are frozen from CircuitPython's pinned submodule commits.

Prerequisites: git, GNU make, native GCC, Python, ARM GNU 13.2.Rel1 on PATH;
CircuitPython's requirements-dev.txt Python build dependencies, intelhex and
adafruit-nrfutil 0.5.3.post16. Pin setuptools below 81 for that older DFU utility
(the supplied build used 80.9.0). MSYS2 also needs diffutils and unzip. On MSYS2,
clear the Windows `OS` environment variable before make and use POSIX paths.

Run `bash tools/build_native.sh /absolute/path/to/new-build-directory` from a
configured shell. This creates fresh checkouts; it does not erase existing ones.
Full recursive submodules can be large. The script reflects the successful build
steps; the supplied binaries were built incrementally, not in a second clean-room
run. Exact source/submodule provenance and output SHA-256 hashes are included.

The narrowly scoped PacketBuffer header patch exposes an internal declaration
needed by _bleio when optional BLE serial/file workflows are disabled. The native
openmice_native.poll_ready helper uses the Cortex-M4 cycle counter for the PAW
startup polling cadence and detects missed deadlines; radio interrupts remain
enabled. Other sensor transactions remain Python driver code. Physical SPI
waveforms and USB enumeration must still be measured.

Host checks: `python -m unittest discover -s tests -v` and
`node --test web/test.mjs`. Regenerate the application ZIPs with
`python tools/package_firmware.py`.

CAD tooling: KiCad 10.0.6, Freerouting 2.5.0, Java 25.0.4.1.
The generator overwrites the native designs with unrouted starting placements:

1. Run tools/build_hardware.py with Python.
2. Run tools/prepare_routing.py using KiCad's Python/pcbnew.
3. Export native schematic netlists with `kicad-cli sch export netlist` into each
   board's .net file. Hand USB routes are locked and included in the DSN.
4. Run Freerouting headless with the board's routing/*.dsn to produce *.ses, or
   reuse the checked-in session if geometry and electrical model are unchanged.
   Route only outer layers; use 0.17 mm defaults with 0.125 mm minimum neckdowns.
5. Run tools/finalize_board.py using KiCad Python: import sessions, clean redundant
   vias, complete receiver power/ground, add charger thermal vias, two GND planes,
   perimeter ties, all-layer RF keep-out, and schematic NC-net assignments.
6. Using KiCad's Python/pcbnew, run
   `python tools/export_hardware.py --kicad-cli /path/to/kicad-cli`.
   It refuses fabrication exports if ERC, DRC, connectivity or parity fails.

Run `python tools/verify_release.py` to verify native image records/checksums,
UF2 family/content, nonoverlapping factory regions, native manifest, CAD results
and matching application/fabrication archives. It refreshes hardware output hashes
after optional PNG previews are rendered.

Final native reports have zero findings on both boards. Configured rule checks
are CAD checks; stack-up impedance, mechanical fit and bench operation are not
proved by these reports. Check manufacturing assumptions in FABRICATION.md.

Project code is MIT. Native bundles include CircuitPython, Adafruit bootloader,
Nordic SoftDevice and frozen-library license files. Vendored KiCad footprints
retain their upstream licensing. The confidential PixArt PDF is excluded
from this public repository and its complete Git history.
