"""Pure build dependencies extracted from the verified working survey."""
from PIL import Image
def decode(data):
    return Image.frombytes('L',(8,8),bytes(((data[y]>>(7-x))&1)|(((data[y+8]>>(7-x))&1)<<1) for y in range(8) for x in range(8)))

def encode(im):
    return bytes(sum(((im.getpixel((x,y))>>b)&1)<<(7-x) for x in range(8)) for b in range(2) for y in range(8))
