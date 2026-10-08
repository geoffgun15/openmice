"""Verify packaged HEX/UF2 bytes, CAD checks, hashes and application payloads."""
import hashlib
import json
import struct
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def read_hex(path):
    memory={};base=0;eof=False
    for line in path.read_text().splitlines():
        assert line.startswith(':')
        raw=bytes.fromhex(line[1:]);assert sum(raw)%256==0 and len(raw)==raw[0]+5
        count=raw[0];address=int.from_bytes(raw[1:3],'big');kind=raw[3];data=raw[4:4+count]
        if kind==0:
            for offset,value in enumerate(data):
                absolute=base+address+offset;assert absolute not in memory;memory[absolute]=value
        elif kind==4:base=int.from_bytes(data,'big')<<16
        elif kind==2:base=int.from_bytes(data,'big')<<4
        elif kind==1:eof=True
        elif kind not in (3,5):raise AssertionError('Unexpected HEX record')
    assert eof;return memory

native=ROOT/'output/native'
factory=read_hex(native/'openmice-factory.hex');runtime=read_hex(native/'openmice-runtime.hex')
boot=read_hex(native/'openmice_nrf52840_bootloader-0.11.0_s140_6.1.1.hex')
assert not set(runtime).intersection(boot)
assert all(factory[address]==byte for image in (runtime,boot) for address,byte in image.items())
assert bytes(factory[x] for x in range(0xff000,0xff004))==b'\x01\0\0\0'
assert min(runtime)==0x26000
assert 0 in boot and 0xf4000 in boot and 0x10001014 in boot
raw=(native/'openmice-runtime.uf2').read_bytes();assert len(raw)%512==0
seen=set()
for offset in range(0,len(raw),512):
    block=raw[offset:offset+512]
    first,second,flags,address,size,index,total,family=struct.unpack('<8I',block[:32])
    assert (first,second)==(0x0a324655,0x9e5d5157)
    assert struct.unpack('<I',block[508:])[0]==0x0ab16f30
    assert flags&0x2000 and family==0xada52840 and size<=476
    assert total==len(raw)//512 and index not in seen;seen.add(index)
    # objcopy's binary/UF2 zero-fills section alignment gaps absent from HEX.
    assert all(runtime.get(address+i,0)==value for i,value in enumerate(block[32:32+size]))
size=json.loads((native/'runtime-size.json').read_text());assert size['used_flash']<size['firmware_region']
manifest=json.loads((native/'manifest.json').read_text())
for name,digest in manifest['sha256'].items():assert hashlib.sha256((native/name).read_bytes()).hexdigest()==digest,name
for role in ('mouse','receiver'):
    destination=ROOT/'output/hardware'/role
    erc=json.loads((destination/'erc.json').read_text());drc=json.loads((destination/'drc.json').read_text())
    assert not any(sheet['violations'] for sheet in erc['sheets'])
    assert not any(drc[key] for key in ('violations','unconnected_items','schematic_parity'))
    hashes={str(file.relative_to(destination)):hashlib.sha256(file.read_bytes()).hexdigest() for file in sorted(destination.rglob('*')) if file.is_file() and file.name!='sha256.json'}
    (destination/'sha256.json').write_text(json.dumps(hashes,indent=2)+'\n')
    with zipfile.ZipFile(ROOT/'output'/('openmice-'+role+'.zip')) as archive:
        assert archive.testzip() is None
        assert archive.read('code.py')==(ROOT/'firmware'/role/'code.py').read_bytes()
        for file in (ROOT/'firmware/common').glob('*.py'):assert archive.read(file.name)==file.read_bytes()
    with zipfile.ZipFile(ROOT/'output'/('openmice-'+role+'-A1-fabrication.zip')) as archive:
        assert archive.testzip() is None
        assert any(name.endswith('.gbr') or name.endswith('.gtl') for name in archive.namelist())
        assert any(name.endswith('.drl') for name in archive.namelist())
assert json.loads((ROOT/'output/physical-status.json').read_text())['status']=='NOT_RUN'
print('PASS: factory/runtime/UF2 contents, firmware hashes, CAD reports and application/fabrication packages. Physical tests NOT RUN.')
