"""Build 005 from original: reproduce 004, preserve its main logo, localize the subtitle."""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys
from PIL import Image
from analyze_title import decode,encode
from build_title import emit,make_ips,apply_ips

ROOT=Path(__file__).resolve().parents[1]
SHA=lambda b:hashlib.sha256(b).hexdigest()
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--source',type=Path,default=ROOT/'original/rom/Tom & Jerry (Japan).nes');args=parser.parse_args()
    source=args.source.resolve();rom=source.read_bytes()
    manifest=json.loads((ROOT/'config/source_rom.json').read_text(encoding='utf-8'))
    assert SHA(rom)==manifest['sha256'] and len(rom)==manifest['size']
    # Reproduction is rooted in the original, not an untracked intermediate ROM.
    result=subprocess.run([sys.executable,str(ROOT/'scripts/build_title.py'),'--source',str(source)],capture_output=True,check=True)
    base=(ROOT/'build/title_kr_ai_004/Tom_Jerry_KR_title_ai_004.nes').read_bytes()
    assert SHA(base)=='de2805699cf7bdddb2f8749466b527caf6ea80f5a6444401e82e8e7ca451bfaa'
    profile=json.loads((ROOT/'assets/title/subtitle_provenance_005.json').read_text(encoding='utf-8'))
    art=ROOT/profile['generated_path'];assert SHA(art.read_bytes())==profile['generated_sha256']
    mask=Image.open(art).convert('L').point(lambda v:255 if v>120 else 0)
    assert list(mask.getbbox())==profile['crop_bbox']
    mask=mask.crop(mask.getbbox()).resize((136,28),Image.Resampling.LANCZOS).point(lambda v:1 if v>=128 else 0)
    image=Image.new('L',(216,32));image.paste(mask,(40,2))
    palette_grid=[[0]*8+[1]*6+[2]*4+[0]*9]+[[0]*6+[1]*8+[2]*4+[0]*9]*2+[[0]*8+[1]*4+[0]*2+[2]*4+[0]*9]
    tiles=[];tilemap=bytearray()
    for y in range(4):
        for x in range(27):
            index=[1,2,3,2][palette_grid[y][x]]
            tile=image.crop((x*8,y*8,x*8+8,y*8+8)).point(lambda v:index if v else 0)
            image.paste(tile,(x*8,y*8));raw=encode(tile)
            if raw==bytes(16):tilemap.append(0);continue
            if raw not in tiles:tiles.append(raw)
            tilemap.append(0x43+tiles.index(raw))
    assert len(tiles)==49 and max(tilemap)==0x73
    patterns=b''.join(tiles)
    # Plan all final writes against immutable original; the main logo is inherited byte-exactly.
    regions=[(0x2023c,135,'verified main logo tilemap','7204d21d43c067065afa6e4f06c83d124521763ef39f777f54a856fca2bb3701',base[0x2023c:0x202c3]),
             (0x202c3,108,'Korean subtitle tilemap','cd1a774b625d8632893c50e76517df9bf59107acaac6775420b8736773a78df5',bytes(tilemap)),
             (0x2c820,1056,'verified main logo CHR slots 01..42','fcdcf5a0478db7853a621cb3885f0bb40bd664190f0e1318c2ede84d33d9b504',base[0x2c820:0x2cc40]),
             (0x2cc40,784,'Korean subtitle CHR slots 43..73','74c245152dee25472b8c359a7af263940c03b253e0e864cf0a82f6f211b87a92',patterns)]
    writes=[];allowed=set()
    for off,n,owner,expected,data in regions:
        assert len(data)==n and SHA(rom[off:off+n])==expected
        area=set(range(off,off+n));assert not allowed&area;allowed|=area
        writes.append(dict(offset=off,length=n,owner=owner,expected_sha256=expected,before_hex=rom[off:off+n].hex(),after_hex=data.hex()))
    for item in writes:
        assert rom[item['offset']:item['offset']+item['length']].hex()==item['before_hex']
    final=bytearray(rom)
    for item in writes:final[item['offset']:item['offset']+item['length']]=bytes.fromhex(item['after_hex'])
    final=bytes(final);diff=[i for i,(a,b) in enumerate(zip(rom,final)) if a!=b]
    assert len(final)==len(rom) and set(diff)<=allowed and final[:0x20010]==rom[:0x20010]
    delta_allowed=set(range(0x202c3,0x2032f))|set(range(0x2cc40,0x2cf50))
    delta=[i for i,(a,b) in enumerate(zip(base,final)) if a!=b];assert set(delta)<=delta_allowed
    assert final[0x2023c:0x202c3]==base[0x2023c:0x202c3] and final[0x2c810:0x2cc40]==base[0x2c810:0x2cc40]
    assert max(final[0x2023c:0x202c3])==0x42
    # Decode the whole final main logo and subtitle through their stored tilemaps.
    decoded=Image.new('L',(216,32))
    for i,t in enumerate(tilemap):decoded.paste(decode(final[0x2c810+t*16:0x2c820+t*16]),(i%27*8,i//27*8))
    assert decoded.tobytes()==image.tobytes()
    for i in range(0x20010,len(rom),16):assert encode(decode(rom[i:i+16]))==rom[i:i+16]
    patch=make_ips(writes);assert apply_ips(rom,patch)==final
    build=ROOT/'build/title_kr_ai_005';build.mkdir(parents=True,exist_ok=True)
    emit(build/'Tom_Jerry_KR_title_ai_005.nes',final);emit(ROOT/'dist/Tom_Jerry_KR_title_ai_005.ips',patch)
    image.save(build/'subtitle_indices.png')
    image.point(lambda v:255 if v else 0).convert('RGB').resize((1296,192),Image.Resampling.NEAREST).save(build/'subtitle_mask_6x.png')
    (build/'expected_writes.json').write_text(json.dumps(writes,indent=2)+'\n',encoding='utf-8')
    report=dict(schema_version=1,candidate='title_kr_ai_005',source_sha256=SHA(rom),base004_sha256=SHA(base),rom_sha256=SHA(final),ips_sha256=SHA(patch),
                generated_sha256=SHA(art.read_bytes()),pillow_version=__import__('PIL').__version__,subtitle_canvas=[216,32],foreground=[136,28],
                subtitle_unique_tiles=len(tiles),subtitle_tile_budget=49,main_logo_unchanged=True,original_diff_bytes=len(diff),base004_diff_bytes=len(delta),
                checks=dict(source_identity=True,expected_writes=True,chr_roundtrip_8192=True,protected_bytes=True,main_logo_equal=True,prg_header_equal=True,
                            subtitle_decode_equal=True,ips_apply_equal=True),runtime_verification='qa/title_005/verification.json')
    (build/'build_report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
