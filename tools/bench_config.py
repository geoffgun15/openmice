"""Run nonpersistent configuration checks on an assembled board; requires pyserial."""
import argparse
import copy
import json
import time
from pathlib import Path

def main():
    import serial
    parser=argparse.ArgumentParser();parser.add_argument('--port',required=True)
    parser.add_argument('--report',required=True,type=Path);args=parser.parse_args()
    result={'port':args.port,'started_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'checks':[],'status':'FAIL'}
    original=None;sequence=0
    try:
        with serial.Serial(args.port,115200,timeout=.1,write_timeout=2) as connection:
            time.sleep(1);connection.reset_input_buffer()
            def request(cmd,**fields):
                nonlocal sequence
                sequence+=1
                connection.write((json.dumps(dict(id=sequence,cmd=cmd,**fields))+'\n').encode())
                deadline=time.monotonic()+5;pending=bytearray()
                while time.monotonic()<deadline:
                    pending.extend(connection.read(128))
                    if len(pending)>4096:raise RuntimeError('Response overflow')
                    while b'\n' in pending:
                        line,_,pending=pending.partition(b'\n')
                        try:reply=json.loads(line)
                        except (ValueError,UnicodeError):continue
                        if reply.get('id')==sequence:return reply
                raise TimeoutError(cmd)
            def check(label,condition):
                result['checks'].append({'name':label,'passed':bool(condition)})
                if not condition:raise RuntimeError(label)
            try:
                reply=request('hello');check('handshake',reply.get('ok') and reply.get('device')=='OpenMice' and reply.get('protocol')==1)
                reply=request('get');check('read',reply.get('ok'));original=reply['config']
                changed=copy.deepcopy(original);changed['dpi']=1600 if original['dpi']!=1600 else 800
                invalid=copy.deepcopy(original);invalid['dpi']=51
                check('invalid DPI rejected',request('set',config=invalid).get('ok') is False)
                check('apply',request('set',config=changed).get('ok'))
                reply=request('get');check('readback',reply.get('ok') and reply.get('config')==changed)
                result['status']='PASS'
            finally:
                if original is not None:check('original live profile restored',request('set',config=original).get('ok'))
    except Exception as error:
        result['status']='FAIL';result['error']=str(error)
    finally:
        args.report.parent.mkdir(parents=True,exist_ok=True)
        args.report.write_text(json.dumps(result,indent=2)+'\n')
    print(result['status']);return 0 if result['status']=='PASS' else 1

if __name__=='__main__':raise SystemExit(main())
