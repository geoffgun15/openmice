"""Prepare flat CIRCUITPY payloads. Does not build/flash the native runtime."""
from pathlib import Path
import shutil
import zipfile

root = Path(__file__).resolve().parents[1]
for role in ('mouse','receiver'):
    destination = root/'output'/('circuitpy-'+role)
    destination.mkdir(parents=True,exist_ok=True)
    for source in (root/'firmware/common').glob('*.py'):
        shutil.copy2(source,destination/source.name)
    shutil.copy2(root/'firmware'/role/'code.py',destination/'code.py')
    (destination/'INSTALL.txt').write_text('Install output/native/openmice-factory.hex over SWD for a blank board.\nFor runtime updates only, use output/native/openmice-runtime.uf2.\nCopy these files to CIRCUITPY. BLE dependencies are frozen in this runtime.\nPower-cycle after changing boot.py.\nSee docs/SETUP.md and docs/FIRST_ARTICLE.md. Physical tests are NOT RUN.\n')
    with zipfile.ZipFile(root/'output'/('openmice-'+role+'.zip'),'w',zipfile.ZIP_DEFLATED) as archive:
        for file in sorted(destination.glob('*')):
            if file.is_file():
                archive.write(file,file.name)
    print(role,'payload prepared')
