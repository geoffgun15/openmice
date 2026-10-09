"""Install portable component models without changing PCB electrical geometry.

Upstream files are pinned to a KiCad library revision. Custom models are visual
proxies, not mechanical clearance references. Run with ordinary Python.
"""
import hashlib
import json
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODELS = ROOT / 'hardware/libraries/3dmodels'
REVISION = 'b8b3cfdfad88ba66f21002b3de51dc6f7d55ba5a'
BASE = f'https://raw.githubusercontent.com/KiCad/kicad-packages3D/{REVISION}/'
PREFIX = '${KIPRJMOD}/../libraries/3dmodels/'
CUSTOM = {'PAW3395DM_T6QU': 'OpenMice/PAW3395-visual-proxy.wrl',
          'BQ24072_RGT0016C': 'OpenMice/BQ24072-visual-proxy.wrl'}
PROXY_REPLACEMENTS = {
    'Connector_USB.3dshapes/USB_C_Receptacle_HRO_TYPE-C-31-M-12.wrl': 'OpenMice/USB-C-visual-proxy.wrl',
    'RF_Module.3dshapes/Raytac_MDBT50Q.wrl': 'OpenMice/MDBT50Q-visual-proxy.wrl',
    'Crystal.3dshapes/Crystal_SMD_3215-2Pin_3.2x1.5mm.wrl': 'OpenMice/Crystal-3215-visual-proxy.wrl',
}


def box(x, y, z, sx, sy, sz, color):
    # Explicit meshes avoid differences in VRML primitive handling by importers.
    vertices = [(x + dx * sx / 2, y + dy * sy / 2, z + dz * sz / 2)
                for dx, dy, dz in [(-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
                                   (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)]]
    points = ', '.join(' '.join(f'{v / 2.54:.8f}' for v in point) for point in vertices)
    return (f'Shape {{ appearance Appearance {{ material Material {{ diffuseColor {color} }} }} '
            f'geometry IndexedFaceSet {{ solid TRUE creaseAngle 0 coord Coordinate {{ point [{points}] }} '
            'coordIndex [0,3,2,1,-1,4,5,6,7,-1,0,1,5,4,-1,1,2,6,5,-1,2,3,7,6,-1,3,0,4,7,-1] } }\n')


def proxy(path, shapes):
    path.parent.mkdir(parents=True, exist_ok=True)
    # Legacy KiCad VRML coordinates are inches / 0.1 (2.54 mm per unit).
    path.write_text('#VRML V2.0 utf8\n# OpenMice visual proxy; MIT license.\n'
                    + ''.join(shapes), encoding='utf-8', newline='\n')


def main():
    boards = [ROOT / f'hardware/{n}/{n}.kicad_pcb' for n in ('mouse', 'receiver')]
    libraries = list((ROOT / 'hardware/libraries/OpenMice.pretty').glob('*.kicad_mod'))
    files = boards + libraries
    pattern = r'\$\{(?:KISYS3DMOD|KIPRJMOD)\}/(?:\.\./libraries/3dmodels/)?([^"\s)]+\.wrl)'
    paths = sorted({m for p in boards for m in re.findall(pattern, p.read_text())
                    if not m.startswith('OpenMice/') and m not in PROXY_REPLACEMENTS})
    MODELS.mkdir(parents=True, exist_ok=True)
    for relative in paths + ['LICENSE.md']:
        destination = MODELS / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        if not destination.exists():
            with urllib.request.urlopen(BASE + relative, timeout=60) as response:
                destination.write_bytes(response.read())
        print(relative)
    # Body silhouette, staggered pin positions and optical location follow the
    # existing footprint. Height and molded details are illustrative assumptions.
    sensor = [box(-.92, 0, 3, 17.2, 8.6, 4, '.055 .055 .065')]
    for row, xs in ((5.35, [5.66 - i * 1.78 for i in range(8)]),
                    (-5.35, [-7.85 + i * 1.78 for i in range(8)])):
        for x in xs:
            sensor.extend([box(x, row, -.2, .35, .35, 6, '.65 .65 .68'),
                           box(x, row / 2 + (2.15 if row > 0 else -2.15),
                               2.6, .35, 2.1, .35, '.65 .65 .68')])
    sensor.append(box(5.66, 3.2, 5.015, .6, .6, .03, '.7 .7 .7'))
    proxy(MODELS / CUSTOM['PAW3395DM_T6QU'], sensor)
    charger = [box(0, 0, .55, 3, 3, .9, '.07 .07 .08'),
               box(-1, .95, 1.005, .2, .2, .01, '.7 .7 .7')]
    for position in (-.75, -.25, .25, .75):
        for edge in (-1.4, 1.4):
            charger.extend([box(edge, position, .08, .2, .24, .16, '.65 .65 .68'),
                            box(position, edge, .08, .24, .2, .16, '.65 .65 .68')])
    proxy(MODELS / CUSTOM['BQ24072_RGT0016C'], charger)
    # Shell walls, open mouth and tongue: dimensions follow the local footprint.
    usb = [box(0, 0, 3.12, 8.94, 7.3, .3, '.68 .69 .72'),
           box(0, 0, .35, 8.94, 7.3, .3, '.68 .69 .72'),
           box(-4.32, 0, 1.73, .3, 7.3, 2.5, '.68 .69 .72'),
           box(4.32, 0, 1.73, .3, 7.3, 2.5, '.68 .69 .72'),
           box(0, 3.5, 1.73, 8.6, .3, 2.5, '.68 .69 .72'),
           box(0, -.3, 1.73, 6.7, 5.7, .65, '.06 .06 .07')]
    for x in (-3.25, -2.75, -2.25, -1.75, -1.25, -.75, -.25, .25, .75, 1.25, 1.75, 2.25, 2.75, 3.25):
        usb.append(box(x, -1, 2.07, .25, 2.5, .025, '.8 .65 .25'))
    proxy(MODELS / 'OpenMice/USB-C-visual-proxy.wrl', usb)
    # Outline follows the footprint; shield and antenna appearance simplified.
    radio = [box(0, 0, .4, 10.5, 15.5, .8, '.13 .22 .15'),
             box(0, -1.3, 1.55, 9.7, 12.2, 1.5, '.6 .61 .63'),
             box(0, 6.55, 1.15, 6.2, 1.1, .7, '.78 .78 .72')]
    for side in (-4.85, 4.85):
        for y in range(-7, 7):
            radio.append(box(side, y, .4, .3, .45, .7, '.76 .61 .22'))
    proxy(MODELS / 'OpenMice/MDBT50Q-visual-proxy.wrl', radio)
    proxy(MODELS / 'OpenMice/Crystal-3215-visual-proxy.wrl', [
        box(0, 0, .65, 3.2, 1.5, 1.3, '.67 .67 .7'),
        box(-1.45, 0, .1, .3, 1.5, .2, '.7 .7 .72'),
        box(1.45, 0, .1, .3, 1.5, .2, '.7 .7 .72')])
    for path in files:
        content = path.read_text()
        original = content
        for relative in paths + list(PROXY_REPLACEMENTS):
            content = content.replace('${KISYS3DMOD}/' + relative, PREFIX + relative)
        for original, replacement in PROXY_REPLACEMENTS.items():
            content = content.replace(PREFIX + original, PREFIX + replacement)
        for name, relative in CUSTOM.items():
            if relative in content:
                continue
            model = (f'\n(model "{PREFIX}{relative}" (offset (xyz 0 0 0)) '
                     '(scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))\n')
            if path.suffix == '.kicad_mod' and path.stem == name:
                end = content.rfind(')')
                content = content[:end] + model + content[end:]
            elif path.suffix == '.kicad_pcb':
                start = content.find(f'(footprint "OpenMice:{name}"')
                if start >= 0:
                    # Find the enclosing footprint without matching quoted text.
                    depth = 0
                    quoted = False
                    escaped = False
                    for end in range(start, len(content)):
                        char = content[end]
                        if escaped:
                            escaped = False
                            continue
                        if char == '\\' and quoted:
                            escaped = True
                        elif char == '"':
                            quoted = not quoted
                        elif not quoted:
                            depth += (char == '(') - (char == ')')
                            if depth == 0:
                                break
                    content = content[:end] + model + content[end:]
        if content == original:
            continue
        content = '\n'.join(line.rstrip() for line in content.splitlines()) + '\n'
        path.write_text(content, encoding='utf-8', newline='\n')
    manifest = {str(p.relative_to(MODELS)).replace('\\', '/'): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(MODELS.rglob('*.wrl'))}
    (MODELS / 'manifest.json').write_text(json.dumps({'upstream_revision': REVISION, 'sha256': manifest}, indent=2) + '\n', newline='\n')


if __name__ == '__main__':
    main()
