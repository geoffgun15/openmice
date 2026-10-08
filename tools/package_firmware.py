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
    (destination/'INSTALL.txt').write_text('Install the custom OpenMice CircuitPython runtime first.\nCopy these files to CIRCUITPY, plus adafruit_ble and its bundle dependencies in lib/.\nPower-cycle after changing boot.py.\nSee docs/SETUP.md. Native runtime and radio behavior are not hardware-verified.\n')
    with zipfile.ZipFile(root/'output'/('openmice-'+role+'.zip'),'w',zipfile.ZIP_DEFLATED) as archive:
        for file in sorted(destination.glob('*')):
            if file.is_file():
                archive.write(file,file.name)
    print(role,'payload prepared')
