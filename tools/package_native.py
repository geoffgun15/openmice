"""Package compiled runtime/bootloader; merge factory HEX without overlapping bytes.

Requires intelhex. Paths identify existing build checkouts, not untrusted releases.
"""
import argparse
import hashlib
import json
import shutil
import struct
import subprocess
from pathlib import Path
from intelhex import IntelHex

ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('circuitpython',type=Path);p.add_argument('bootloader',type=Path)
a=p.parse_args();cp=a.circuitpython.resolve();bl=a.bootloader.resolve()
out=ROOT/'output'/'native';out.mkdir(parents=True,exist_ok=True)
runtime=cp/'ports/nordic/build-openmice611';boot=bl/'_build/build-openmice_nrf52840'
for original,target in [('firmware.uf2','openmice-runtime.uf2'),('firmware.hex','openmice-runtime.hex'),('firmware.elf','openmice-runtime.elf'),('firmware.size.json','runtime-size.json')]:
    shutil.copy2(runtime/original,out/target)
for source in boot.glob('*'):
    if source.suffix in ('.hex','.zip','.uf2'):shutil.copy2(source,out/source.name)
combined=IntelHex(str(out/'openmice-runtime.hex'))
loader=IntelHex(str(out/'openmice_nrf52840_bootloader-0.11.0_s140_6.1.1.hex'))
# ARM starts through the MBR vector table; ELF entry metadata differs per image.
# Drop type-05 metadata, preserving strict overlap checking of programmed bytes.
combined.start_addr=None;loader.start_addr=None
combined.merge(loader,overlap='error')
# SDK11 bootloader_settings_t starts with uint16 bank_0, uint16 CRC.
# Valid bank with CRC=0 matches CircuitPython's documented Nordic SWD flow.
assert all(address not in combined.addresses() for address in range(0xff000,0xff004))
combined.puts(0xff000,struct.pack('<I',1))
assert combined[0x10001014]!=255,'Bootloader UICR address missing'
combined.write_hex_file(str(out/'openmice-factory.hex'))
licenses=out/'licenses';licenses.mkdir(exist_ok=True)
shutil.copy2(cp/'LICENSE',licenses/'CircuitPython-LICENSE')
shutil.copy2(bl/'LICENSE',licenses/'Adafruit-bootloader-LICENSE')
for library in ('Adafruit_CircuitPython_BLE','Adafruit_CircuitPython_Register','Adafruit_CircuitPython_BusDevice'):
    for source in (cp/'frozen'/library).glob('LICENSE*'):
        if source.is_file():shutil.copy2(source,licenses/(library+'-'+source.name))
        elif source.is_dir():shutil.copytree(source,licenses/(library+'-'+source.name),dirs_exist_ok=True)
for source in (bl/'lib/softdevice/s140_nrf52_6.1.1').rglob('*'):
    if source.is_file() and ('license' in source.name.lower()):shutil.copy2(source,licenses/source.name)
def git(path,*args):return subprocess.check_output(['git','-C',str(path),*args],text=True).strip()
manifest={'status':'compiled; physical tests NOT RUN','target':'openmice_nrf52840','compiler':'arm-none-eabi-gcc 13.2.Rel1','softdevice':'S140 6.1.1','circuitpython_commit':git(cp,'rev-parse','HEAD'),'bootloader_commit':git(bl,'rev-parse','HEAD'),'circuitpython_submodules':git(cp,'submodule','status'),'bootloader_submodules':git(bl,'submodule','status'),'sha256':{str(file.relative_to(out)):hashlib.sha256(file.read_bytes()).hexdigest() for file in sorted(out.rglob('*')) if file.is_file() and file.name!='manifest.json'}}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Native package and nonoverlapping factory HEX prepared')
