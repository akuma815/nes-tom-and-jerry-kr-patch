"""Build v1.0 from the tracked translation, font, art and code plus a supplied original."""
from pathlib import Path
import argparse,hashlib,importlib.metadata,json,shutil,subprocess,sys
ROOT=Path(__file__).resolve().parent
SHA=lambda data:hashlib.sha256(data).hexdigest()
def emit(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        if path.read_bytes()!=data:raise ValueError('Refusing to replace a different existing file: '+str(path))
    else:path.write_bytes(data)
def main():
    p=argparse.ArgumentParser(description='Rebuild Tom & Jerry Korean v1.0 from source inputs. Original ROM required separately.')
    p.add_argument('--source',required=True,type=Path);p.add_argument('--output',type=Path,default=ROOT/'output/Tom_Jerry_KR_v1.0.nes');a=p.parse_args()
    profile=json.loads((ROOT/'release.json').read_text(encoding='utf8'));rom=a.source.read_bytes()
    if len(rom)!=profile['source']['size'] or SHA(rom)!=profile['source']['sha256']:
        raise ValueError('Unsupported original ROM: use the unmodified headered Japanese revision specified in README.')
    if a.source.resolve()==a.output.resolve():raise ValueError('Never overwrite the original ROM')
    if importlib.metadata.version('Pillow')!='12.3.0':raise ValueError('Install the pinned dependency: python -m pip install -r source/requirements.txt')
    inputs=json.loads((ROOT/'source/BUILD_INPUTS.json').read_text(encoding='utf8'))
    for item in inputs['files']:
        path=ROOT/item['path']
        if SHA(path.read_bytes())!=item['sha256']:raise ValueError('Source input identity mismatch: '+item['path'])
    original=ROOT/'source/original/rom/Tom & Jerry (Japan).nes';emit(original,rom)
    result=subprocess.run([sys.executable,'-B',str(ROOT/'source/scripts/build_text_kr.py')],check=True,capture_output=True)
    rebuilt=(ROOT/'source/build/text_kr_008/Tom_Jerry_KR_text_008.nes').read_bytes()
    patch=(ROOT/'source/dist/Tom_Jerry_KR_text_008.ips').read_bytes()
    if SHA(rebuilt)!=profile['target']['sha256'] or len(rebuilt)!=profile['target']['size']:raise ValueError('Rebuilt ROM differs from v1.0')
    if SHA(patch)!=profile['patch']['sha256'] or patch!=(ROOT/profile['patch']['path']).read_bytes():raise ValueError('Rebuilt IPS differs from the published v1.0 patch')
    emit(a.output,rebuilt);emit(a.output.with_suffix('.ips'),patch)
    record=dict(status='PASS',original_sha256=SHA(rom),target_sha256=SHA(rebuilt),ips_sha256=SHA(patch),
                tracked_inputs_verified=len(inputs['files']),generated_from='Tracked translation, font, generated title artwork and source code; not the prebuilt IPS',
                published_ips_equal=True,original_unchanged=SHA(a.source.read_bytes())==SHA(rom),runtime='Not performed by this source build')
    emit(a.output.with_suffix('.build.json'),(json.dumps(record,indent=2)+'\n').encode('utf8'))
    print(json.dumps(record,indent=2))
if __name__=='__main__':
    try:main()
    except (OSError,ValueError,subprocess.CalledProcessError,importlib.metadata.PackageNotFoundError) as e:
        print('ERROR: '+str(e),file=sys.stderr)
        if isinstance(e,subprocess.CalledProcessError):print(e.stderr.decode('utf8',errors='replace'),file=sys.stderr)
        sys.exit(1)
