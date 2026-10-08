"""Check native KiCad designs before exporting prototype manufacturing bundles."""
import argparse
import hashlib
import json
import shutil
import subprocess
import zipfile
from pathlib import Path
import pcbnew

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--kicad-cli',default='kicad-cli')
args=parser.parse_args()
def run(*arguments):subprocess.run([args.kicad_cli,*map(str,arguments)],check=True)
for name in ('mouse','receiver'):
    source=ROOT/'hardware'/name
    destination=ROOT/'output'/'hardware'/name
    destination.mkdir(parents=True,exist_ok=True)
    board=source/(name+'.kicad_pcb');sch=source/(name+'.kicad_sch')
    erc=destination/'erc.json';drc=destination/'drc.json'
    run('sch','erc','--format','json','-o',erc,sch)
    run('pcb','drc','--schematic-parity','--format','json','-o',drc,board)
    assert not any(sheet['violations'] for sheet in json.loads(erc.read_text())['sheets']),'ERC failed'
    result=json.loads(drc.read_text())
    assert not any(result[key] for key in ('violations','unconnected_items','schematic_parity')),'DRC failed'
    fab=destination/'fabrication';fab.mkdir(exist_ok=True)
    run('pcb','export','gerbers','--layers','F.Cu,In1.Cu,In2.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,F.Paste,B.Paste,Edge.Cuts','--subtract-soldermask','-o',fab,board)
    run('pcb','export','drill','--excellon-separate-th','--generate-map','--map-format','svg','-o',fab,board)
    run('pcb','export','pos','--format','csv','--units','mm','-o',destination/'placement.csv',board)
    # Hide long procurement values in the assembly view; BOM retains full values.
    view=pcbnew.LoadBoard(str(board))
    for footprint in view.GetFootprints():
        footprint.Value().SetVisible(False)
        footprint.Reference().SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(.65),pcbnew.FromMM(.65)))
    temporary=source/(name+'-assembly-view.kicad_pcb')
    try:
        pcbnew.SaveBoard(str(temporary),view)
        run('pcb','export','svg','--layers','F.Cu,F.Fab,Edge.Cuts','--mode-single','--fit-page-to-board','--exclude-drawing-sheet','-o',destination/'assembly-top.svg',temporary)
    finally:
        temporary.unlink(missing_ok=True)
        temporary.with_suffix('.kicad_pro').unlink(missing_ok=True)
    run('pcb','export','svg','--layers','B.Cu,Edge.Cuts','--mode-single','--fit-page-to-board','--exclude-drawing-sheet','-o',destination/'copper-bottom.svg',board)
    shutil.copy2(source/'bom.csv',destination/'bom.csv')
    shutil.copy2(ROOT/'docs'/'FABRICATION.md',fab/'FABRICATION.md')
    with zipfile.ZipFile(ROOT/'output'/('openmice-'+name+'-A1-fabrication.zip'),'w',zipfile.ZIP_DEFLATED) as archive:
        for file in sorted(fab.iterdir()):archive.write(file,file.name)
    manifest={str(p.relative_to(destination)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(destination.rglob('*')) if p.is_file() and p.name!='sha256.json'}
    (destination/'sha256.json').write_text(json.dumps(manifest,indent=2)+'\n')
