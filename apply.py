"""Apply the v1.0 patch using Python 3's standard library only."""
from pathlib import Path
import argparse,hashlib,json,sys

ROOT=Path(__file__).resolve().parent
def sha(data):return hashlib.sha256(data).hexdigest()
def apply(source,patch):
    if patch[:5]!=b'PATCH':raise ValueError('Invalid IPS header')
    result=bytearray(source);pos=5
    while patch[pos:pos+3]!=b'EOF':
        if pos+5>len(patch):raise ValueError('Truncated IPS record')
        offset=int.from_bytes(patch[pos:pos+3],'big');length=int.from_bytes(patch[pos+3:pos+5],'big');pos+=5
        if length:
            if pos+length>len(patch):raise ValueError('Truncated IPS payload')
            data=patch[pos:pos+length];pos+=length
        else:
            if pos+3>len(patch):raise ValueError('Truncated IPS RLE')
            length=int.from_bytes(patch[pos:pos+2],'big');data=patch[pos+2:pos+3]*length;pos+=3
        if not length or offset+length>len(result):raise ValueError('IPS record outside supported ROM')
        result[offset:offset+length]=data
    if pos+3!=len(patch):raise ValueError('Unexpected IPS trailer')
    return bytes(result)
def main():
    parser=argparse.ArgumentParser(description='Tom & Jerry Korean patch v1.0. Original ROM is required separately.')
    parser.add_argument('source',type=Path);parser.add_argument('output',type=Path,nargs='?');args=parser.parse_args()
    profile=json.loads((ROOT/'release.json').read_text(encoding='utf-8'))
    src=args.source.resolve();out=(args.output or src.with_name(src.stem+'_KR_v1.0.nes')).resolve()
    if src==out:raise ValueError('Output must differ from the original ROM')
    source=src.read_bytes()
    if len(source)!=profile['source']['size'] or sha(source)!=profile['source']['sha256']:
        raise ValueError('Unsupported source. Use the unmodified headered Tom & Jerry (Japan).nes matching the README SHA-256.')
    patch=(ROOT/profile['patch']['path']).read_bytes()
    if sha(patch)!=profile['patch']['sha256']:raise ValueError('Patch checksum mismatch. Extract a fresh release ZIP.')
    result=apply(source,patch)
    if len(result)!=profile['target']['size'] or sha(result)!=profile['target']['sha256']:raise ValueError('Patched ROM verification failed')
    if out.exists():
        if out.read_bytes()!=result:raise ValueError('Output already exists with different content; choose a new path')
    else:out.write_bytes(result)
    print('Patch v1.0 applied and verified: '+str(out))
    print('SHA-256: '+sha(result))
if __name__=='__main__':
    try:main()
    except (OSError,ValueError,KeyError) as error:
        print('ERROR: '+str(error),file=sys.stderr);sys.exit(1)
