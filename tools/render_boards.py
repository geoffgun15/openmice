"""Render all installed PCB components; run with KiCad's bundled Python."""
import argparse
import json
import subprocess
from pathlib import Path
import pcbnew

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--kicad-cli', default='kicad-cli')
args = parser.parse_args()
for name, width, height, zoom in [('mouse', 1800, 1800, '.75'),
                                   ('receiver', 1400, 1600, '.7')]:
    source = ROOT / f'hardware/{name}/{name}.kicad_pcb'
    output = ROOT / f'output/hardware/{name}'
    board = pcbnew.LoadBoard(str(source))
    coverage = []
    for footprint in sorted(board.GetFootprints(), key=lambda f: f.GetReference()):
        models = list(footprint.Models())
        assert models, f'Missing model: {name} {footprint.GetReference()}'
        paths = [Path(model.m_Filename.replace('${KIPRJMOD}', str(source.parent)))
                 for model in models]
        assert all(path.is_file() for path in paths), f'Missing model file: {paths}'
        coverage.append({'reference': footprint.GetReference(), 'value': footprint.GetValue(),
                         'models': [str(path.resolve().relative_to(ROOT)).replace('\\', '/') for path in paths],
                         'simplified': any('visual-proxy' in path.name for path in paths)})
    (output / 'render-models.json').write_text(json.dumps(coverage, indent=2) + '\n')
    subprocess.run([args.kicad_cli, 'pcb', 'render', '--width', str(width),
                    '--height', str(height), '--quality', 'high', '--background', 'opaque',
                    '--rotate', '25,0,-25', '--zoom', zoom, '-o',
                    str(output / 'board-populated-3d.png'), str(source)], check=True)
    print(f'{name}: all {len(coverage)} footprints have installed models')
