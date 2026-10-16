"""Pure build dependencies extracted from the verified working survey."""
import hashlib
SHA=lambda data:hashlib.sha256(data).hexdigest()
COMMANDS={0x80:('end',0),0x81:('cursor_xy',2),0x82:('centered_row',1),
          0x83:('disable_rendering',0),0x84:('enable_rendering',0),
          0x85:('attribute_selector',1),0x86:('palette_four_bytes',4)}

def parse(rom,call):
    pos=call+3;start=pos;tokens=[];lines=[];cursor=None
    while pos-start<512:
        value=rom[pos]
        if value>=128:
            assert value in COMMANDS,(hex(call),hex(pos),hex(value))
            name,n=COMMANDS[value];args=list(rom[pos+1:pos+1+n]);tokens.append(dict(offset=pos,kind=name,opcode=value,args=args))
            pos+=1+n
            if value==0x80:break
            if value==0x81:cursor=dict(x=args[0],y=args[1],alignment='absolute')
            if value==0x82:cursor=dict(x=None,y=args[0],alignment='center')
        else:
            first=pos
            while rom[pos]<128:pos+=1
            raw=rom[first:pos];assert cursor is not None
            line=dict(offset=first,raw_hex=raw.hex(),length=len(raw),**cursor)
            if line['alignment']=='center':line['x']=(32-len(raw))//2
            lines.append(line);tokens.append(dict(offset=first,kind='characters',raw_hex=raw.hex()))
    else:raise AssertionError('Unterminated inline script')
    rebuilt=bytearray()
    for tok in tokens:
        if tok['kind']=='characters':rebuilt+=bytes.fromhex(tok['raw_hex'])
        else:rebuilt+=bytes([tok['opcode'],*tok['args']])
    assert bytes(rebuilt)==rom[start:pos]
    return dict(call_offset=call,start_offset=start,end_exclusive=pos,raw_hex=rom[start:pos].hex(),
                sha256=SHA(rom[start:pos]),roundtrip_equal=True,tokens=tokens,lines=lines)
