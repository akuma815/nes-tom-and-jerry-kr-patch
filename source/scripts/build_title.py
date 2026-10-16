"""Deterministic generated-art -> NES CHR + shared tilemap -> guarded IPS build."""
from pathlib import Path
import argparse, hashlib, json
from PIL import Image
from analyze_title import decode,encode

ROOT=Path(__file__).resolve().parents[1]
SHA=lambda b:hashlib.sha256(b).hexdigest()
def emit(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists(): assert path.read_bytes()==data, f'Refusing to overwrite different artifact: {path}'
    else: path.write_bytes(data)
def make_ips(writes):
    result=bytearray(b'PATCH')
    for w in writes:
        data=bytes.fromhex(w['after_hex']);off=w['offset']
        assert off!=0x454f46 and len(data)<65536
        result+=off.to_bytes(3,'big')+len(data).to_bytes(2,'big')+data
    return bytes(result+b'EOF')
def apply_ips(source,patch):
    assert patch[:5]==b'PATCH'; out=bytearray(source); i=5
    while patch[i:i+3]!=b'EOF':
        off=int.from_bytes(patch[i:i+3],'big'); n=int.from_bytes(patch[i+3:i+5],'big');i+=5
        assert n>0
        out[off:off+n]=patch[i:i+n];i+=n
    assert i+3==len(patch)
    return bytes(out)
def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,default=ROOT/'original/rom/Tom & Jerry (Japan).nes');a=p.parse_args()
    manifest=json.loads((ROOT/'config/source_rom.json').read_text(encoding='utf-8'));rom=a.source.read_bytes()
    assert len(rom)==manifest['size'] and SHA(rom)==manifest['sha256']
    generated=ROOT/'assets/title/title_kr_ai_001_generated.png'
    assert SHA(generated.read_bytes())==json.loads((ROOT/'assets/title/provenance_001.json').read_text(encoding='utf-8'))['generated_sha256']
    # Explicit, fixed conversion. The generated bitmap is the art oracle; no AI call during rebuild.
    mask=Image.open(generated).convert('L').point(lambda v:255 if v>120 else 0)
    bbox=mask.getbbox(); assert bbox==(98,121,1962,614)
    mask=mask.crop(bbox).resize((160,32),Image.Resampling.LANCZOS).point(lambda v:1 if v>=128 else 0)
    image=Image.new('L',(216,40));image.paste(mask,(28,4))
    # Original per-cell palettes are equal in intro/main despite their different screen rows.
    # Use bright existing colors instead of palette index 1 (which is dark brown at the right).
    palettes=[[0]*10+[1]*8+[0]*2+[3]*6+[0]]*4+[[0]*8+[1]*6+[2]*4+[0]*9]
    for y in range(5):
        for x in range(27):
            index=[1,2,3,2][palettes[y][x]]
            tile=image.crop((x*8,y*8,x*8+8,y*8+8)).point(lambda v:index if v else 0)
            image.paste(tile,(x*8,y*8))
    tiles=[bytes(16)]; tilemap=bytearray()
    for y in range(0,40,8):
        for x in range(0,216,8):
            tile=encode(image.crop((x,y,x+8,y+8)))
            if tile not in tiles: tiles.append(tile)
            tilemap.append(tiles.index(tile))
    assert len(tiles)-1==66 # Slots 43/44 preserve two patterns shared by the Tuffy subtitle.
    for i in range(0x20010,len(rom),16): assert encode(decode(rom[i:i+16]))==rom[i:i+16]
    # Both source areas are confirmed by original PPU dump + visible logo consumer.
    tuffy_before=rom[0x202c3:0x2032f]
    tuffy_after=bytes({0x17:0x43,0x1e:0x44}.get(v,v) for v in tuffy_before)
    patterns=b''.join(tiles[1:])+rom[0x2c810+0x17*16:0x2c820+0x17*16]+rom[0x2c810+0x1e*16:0x2c820+0x1e*16]
    for before,after in zip(tuffy_before,tuffy_after):
        old=rom[0x2c810+before*16:0x2c820+before*16]
        new=patterns[(after-1)*16:after*16] if 1<=after<=68 else old
        assert new==old
    regions=[(0x2023c,135,'shared logo tilemap','7204d21d43c067065afa6e4f06c83d124521763ef39f777f54a856fca2bb3701',bytes(tilemap)),
             (0x202c3,108,'Tuffy shared-tile references, pixel-preserving relocation','cd1a774b625d8632893c50e76517df9bf59107acaac6775420b8736773a78df5',tuffy_after),
             (0x2c820,1088,'active raster logo CHR slots 01..44','b41ba3d7397f7df43e58a053d3bcc781a8c732771ab165af63902aed95850aed',
              patterns)]
    writes=[]; allowed=set()
    for off,n,owner,expected,data in regions:
        assert len(data)==n and SHA(rom[off:off+n])==expected
        area=set(range(off,off+n)); assert not allowed&area;allowed|=area
        writes.append(dict(offset=off,length=n,owner=owner,expected_sha256=expected,
                           before_hex=rom[off:off+n].hex(),after_hex=data.hex()))
    # Validate the entire plan against immutable source before creating output.
    out=bytearray(rom)
    for w in writes:
        off=w['offset'];n=w['length'];assert rom[off:off+n].hex()==w['before_hex']
    for w in writes: out[w['offset']:w['offset']+w['length']]=bytes.fromhex(w['after_hex'])
    out=bytes(out);diff=[i for i,(b,c) in enumerate(zip(rom,out)) if b!=c]
    assert len(out)==len(rom) and set(diff)<=allowed
    assert out[:0x20010]==rom[:0x20010] # All header and PRG are protected.
    reconstructed=Image.new('L',(216,40))
    for k,index in enumerate(tilemap):
        reconstructed.paste(decode(out[0x2c810+index*16:0x2c820+index*16]),(k%27*8,k//27*8))
    assert reconstructed.tobytes()==image.tobytes()
    patch=make_ips(writes);assert apply_ips(rom,patch)==out
    build=ROOT/'build/title_kr_ai_004';build.mkdir(parents=True,exist_ok=True)
    rompath=build/'Tom_Jerry_KR_title_ai_004.nes';ipspath=ROOT/'dist/Tom_Jerry_KR_title_ai_004.ips'
    emit(rompath,out);emit(ipspath,patch)
    image.save(build/'logo_indices.png')
    preview=image.point(lambda v:255 if v else 0).convert('RGB');preview.save(build/'logo_mask.png')
    preview.resize((1296,240),Image.Resampling.NEAREST).save(build/'logo_mask_6x.png')
    (build/'expected_writes.json').write_text(json.dumps(writes,indent=2)+'\n',encoding='utf-8')
    report=dict(schema_version=1,source_sha256=SHA(rom),rom_sha256=SHA(out),ips_sha256=SHA(patch),
                generated_sha256=SHA(generated.read_bytes()),pillow_version=__import__('PIL').__version__,
                logo_size=[216,40],foreground_size=[160,32],nonblank_unique_tiles=len(tiles)-1,
                writable_tile_budget=68,subtitle_preservation_tiles=2,diff_bytes=len(diff),expected_write_regions=[dict(offset=hex(o),size=n,owner=s) for o,n,s,_,_ in regions],
                checks=dict(chr_roundtrip_all_8192_tiles=True,source_identity=True,expected_writes=True,
                            protected_bytes=True,prg_header_unchanged=True,encoded_pixels_equal=True,ips_apply_equal=True),
                runtime_verification='separate qa/title_004/verification.json')
    (build/'build_report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
