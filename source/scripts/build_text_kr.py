"""Deterministic fixed-slot Korean text insertion; 008 is current, 006/007 preserved."""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys
from PIL import Image,ImageDraw,ImageFont
from analyze_title import encode,decode
from build_title import emit,make_ips,apply_ips
from extract_japanese import parse

ROOT=Path(__file__).resolve().parents[1]
SHA=lambda b:hashlib.sha256(b).hexdigest()
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--revision',choices=['006','007','008'],default='008');args=parser.parse_args()
    revision=args.revision;ink=1 if revision=='006' else 3
    source=ROOT/'original/rom/Tom & Jerry (Japan).nes';rom=source.read_bytes()
    assert SHA(rom)=='aaeceb811865b9f4736670b55cbfd4a3deae5d26374e9d10d744fc44055b524f'
    subprocess.run([sys.executable,str(ROOT/'scripts/build_title_subtitle.py')],capture_output=True,check=True)
    base=(ROOT/'build/title_kr_ai_005/Tom_Jerry_KR_title_ai_005.nes').read_bytes()
    assert SHA(base)=='4c20f312f5326d738c570ccfeb4c51c0aba1356151173215c7c13d03cd0c906a'
    selected=json.loads((ROOT/'assets/text/ko_selected_006.json').read_text(encoding='utf8'))
    assert selected['build_eligible'] and selected['user_authorization']=='이제 번역한 텍스트 삽입 작업하자'
    catalog=ROOT/'extracted/text_survey_001/japanese_catalog.json'
    assert SHA(catalog.read_bytes())==selected['source_catalog_sha256']
    draft=json.loads((ROOT/'assets/text/ja_ko_draft_001.json').read_text(encoding='utf8'))
    assert SHA((ROOT/'assets/text/ja_ko_draft_001.json').read_bytes())==selected['source_draft_sha256']
    entries={e['id']:e['ko'] for e in draft['entries']}
    assert entries=={e['id']:e['ko'] for e in selected['entries']}
    rows=[v for page in selected['pages'] for v in page['rows']]
    for key,text in entries.items():assert ' '.join(v['text'] for v in rows if v['source_id']==key)==text
    repertoire=sorted(set(''.join(v['text'] for v in rows))-{' '})
    assert len(repertoire)+1<=128
    mapping={' ':0,**{c:i+1 for i,c in enumerate(repertoire)}}
    profile=json.loads((ROOT/'assets/fonts/text_006/provenance.json').read_text(encoding='utf8'))
    for name,sha in profile['inputs'].items():assert SHA((ROOT/name).read_bytes())==sha
    sheet=Image.open(ROOT/'assets/fonts/text_006/Galmuri7_8x8.png').convert('L')
    font=ImageFont.truetype(str(ROOT/'assets/fonts/text_006/Galmuri7.ttf'),8)
    masks=[];patterns=[];font_check=[]
    for c in repertoire:
        # At 8 px and y=-1 the full 8x8 ink fits; at 7 px some distinct finals collapse.
        large=Image.new('L',(24,24));ImageDraw.Draw(large).text((8,7),c,font=font,fill=255)
        large=large.point(lambda v:255 if v>=128 else 0)
        assert large.getbbox() and large.getbbox()[0]>=8 and large.getbbox()[1]>=8
        assert large.getbbox()[2]<=16 and large.getbbox()[3]<=16,(c,large.getbbox())
        raster=large.crop((8,8,16,16))
        if 0xac00<=ord(c)<=0xd7a3:
            n=ord(c)-0xac00;x=n%64*8;y=n//64*8
            glyph=sheet.crop((x,y,x+8,y+8)).point(lambda v:255 if v>30 else 0)
            assert glyph.tobytes()==raster.tobytes(),c
        else:glyph=raster
        assert glyph.getbbox(),c
        assert glyph.tobytes() not in masks,('glyph collision',c)
        masks.append(glyph.tobytes());tile=glyph.point(lambda v:ink if v else 0)
        raw=encode(tile);assert decode(raw).tobytes()==tile.tobytes();patterns.append(raw)
        font_check.append(dict(character=c,code=mapping[c],bbox=glyph.getbbox(),mask_sha256=SHA(glyph.tobytes())))
    writes=[];layout=[]
    for page in selected['pages']:
        original=parse(rom,page['call_offset']);body=bytearray.fromhex(page['prefix_hex'])
        for row in page['rows']:
            value=bytes(mapping[c] for c in row['text'])
            if revision=='008' and row['source_id']=='JP_INTRO_02_L02':
                # Preserve the original row's 17-cell attribute footprint. Without these
                # two blank cells, four pixels on Jerry's cheek inherit another palette.
                value=value.ljust(17,b'\x00')
            x=(32-len(value))//2 if row['align']=='center' else row['x'];y=row['y']
            assert 2<=x and x+len(value)<=30 and 0<=y<30,(row,x)
            body+=bytes([0x82,y]) if row['align']=='center' else bytes([0x81,x,y])
            body+=value
            layout.append(dict(page_id=page['id'],source_id=row['source_id'],text=row['text'],x=x,y=y,raw_hex=value.hex()))
        # Preserve the inline end byte's original address: F256 jumps to the following code.
        # Redundant cursor/attribute commands consume slack without rendering padding glyphs.
        slack=original['end_exclusive']-original['start_offset']-len(body)-1
        assert slack>=0,(page['id'],slack)
        padding=bytearray()
        if slack%2:
            assert slack>=3;padding+=bytes([0x81,0,0]);slack-=3
        padding+=bytes([0x85,page['attribute']])*(slack//2)
        prefix_len=len(bytes.fromhex(page['prefix_hex']))
        body[prefix_len:prefix_len]=padding;body.append(0x80)
        assert len(body)==original['end_exclusive']-original['start_offset']
        assert original['end_exclusive']-1==original['start_offset']+len(body)-1
        writes.append(dict(offset=original['start_offset'],length=len(body),owner=page['id'],
                           expected_sha256=original['sha256'],before_hex=original['raw_hex'],after_hex=body.hex()))
    # Slot zero stays byte-exactly original; slots 01..61 hold 97 required nonspace glyphs.
    writes.append(dict(offset=0x2a820,length=len(patterns)*16,owner='Korean glyphs 01..61',
                       expected_sha256=SHA(rom[0x2a820:0x2a820+len(patterns)*16]),
                       before_hex=rom[0x2a820:0x2a820+len(patterns)*16].hex(),after_hex=b''.join(patterns).hex()))
    final=bytearray(base);allowed=set()
    for w in writes:
        a=w['offset'];b=a+w['length'];assert SHA(rom[a:b])==w['expected_sha256'] and rom[a:b].hex()==w['before_hex']
        assert base[a:b]==rom[a:b];area=set(range(a,b));assert not area&allowed;allowed|=area
        final[a:b]=bytes.fromhex(w['after_hex'])
    final=bytes(final);diff=[i for i,(a,b) in enumerate(zip(base,final)) if a!=b]
    assert len(final)==len(rom) and set(diff)<=allowed and final[:16]==rom[:16]
    for page in selected['pages']:
        parsed=parse(final,page['call_offset']);assert parsed['end_exclusive']==parse(rom,page['call_offset'])['end_exclusive']
        actual=[v for v in parsed['lines'] if v['raw_hex']]
        expected=[v for v in layout if v['page_id']==page['id']]
        assert len(actual)==len(expected)
        for a,b in zip(actual,expected):assert a['raw_hex']==b['raw_hex'] and (a['x'],a['y'])==(b['x'],b['y'])
    old=json.loads((ROOT/'build/title_kr_ai_005/expected_writes.json').read_text())
    integrated=sorted(old+writes,key=lambda w:w['offset'])
    final_allowed=set()
    for w in integrated:
        area=set(range(w['offset'],w['offset']+w['length']));assert not final_allowed&area;final_allowed|=area
    assert {i for i,(a,b) in enumerate(zip(rom,final)) if a!=b}<=final_allowed
    patch=make_ips(integrated);assert apply_ips(rom,patch)==final
    out=ROOT/f'build/text_kr_{revision}';out.mkdir(parents=True,exist_ok=True)
    emit(out/f'Tom_Jerry_KR_text_{revision}.nes',final);emit(ROOT/f'dist/Tom_Jerry_KR_text_{revision}.ips',patch)
    for name,value in [('encoding_ko.json',{f'{v:02X}':k for k,v in mapping.items()}),('layout.json',layout),('glyph_audit.json',font_check),('expected_writes.json',integrated)]:
        emit(out/name,(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
    atlas=Image.new('L',(128,64))
    for c,code in mapping.items():atlas.paste(decode(final[0x2a810+code*16:0x2a820+code*16]).point(lambda v:255 if v else 0),(code%16*8,code//16*8))
    atlas.resize((768,384),Image.Resampling.NEAREST).save(out/'font_atlas_6x.png')
    report=dict(candidate=f'text_kr_{revision}',source_sha256=SHA(rom),base005_sha256=SHA(base),rom_sha256=SHA(final),ips_sha256=SHA(patch),
                source_lines=18,display_rows=len(layout),glyphs_including_space=len(mapping),glyph_budget=128,delta005_bytes=len(diff),
                checks=dict(source_identity=True,base005_reproduced=True,expected_writes=True,protected_bytes=True,header_size_equal=True,
                            all_selected_text_preserved=True,unmapped_glyphs=0,empty_glyphs=0,glyph_collisions=0,hangul_sheet_ttf_equal=93,
                            glyph_decode_equal=True,script_roundtrip=True,original_continuations_equal=True,ips_apply_equal=True),
                executable_code_modified=False,scope='Extracted 4 Japanese pages only; whole-game coverage not claimed')
    emit(out/'build_report.json',(json.dumps(report,indent=2)+'\n').encode('utf8'));print(json.dumps(report,indent=2))
if __name__=='__main__':main()
