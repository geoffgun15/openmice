# Portable assembly visualization

All 51 mouse and 18 receiver footprints have local 3D models. Board and library
references resolve from each KiCad project's directory without a system model
installation. The battery cell, click switches and scroll encoder are external
assemblies connected to headers; they are not mounted parts of these boards.

Standard models come from the [official KiCad model library](https://github.com/KiCad/kicad-packages3D),
pinned at `b8b3cfdfad88ba66f21002b3de51dc6f7d55ba5a`. Their author notices
remain in the files; see [LICENSE.md](LICENSE.md) for CC-BY-SA 4.0 and the library
exception. SHA-256 hashes and the upstream revision are in [manifest.json](manifest.json).

The five original MIT-licensed models under `OpenMice/` are simplified visual
proxies for PAW3395, BQ24072, MDBT50Q, HRO USB-C and the 3215 crystal. They use
footprint outlines and pad locations; body heights, shield details and molded
features are illustrative. They are **not mechanical clearance validation**.
The PAW3395 lens assembly is not modeled. No confidential reference is included.

`python tools/populate_3d.py` restores downloaded models if missing and generates
the proxies. With KiCad's Python, run `tools/render_boards.py --kicad-cli PATH`
to check every footprint's model and produce both populated renders. KiCad needs
write access to its normal 3D model cache. Per-board model coverage is saved as
`output/hardware/<board>/render-models.json`.
