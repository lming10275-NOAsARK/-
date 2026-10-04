import sys
from PIL import Image
PAL=[(0,0,0),(255,255,255),(255,80,80),(80,255,80),(80,80,255),(255,255,80),(255,255,255),(200,200,200)]+[(128,128,128)]*8
def tiles4(data):
    # mega drive 4bpp 8x8 tiles, 32 bytes each
    n=len(data)//32
    return n
def render(fn,off,size,cols=32,out='out.png',mode='tile'):
    b=open(fn,'rb').read()[off:off+size]
    n=len(b)//32
    rows=(n+cols-1)//cols
    img=Image.new('RGB',(cols*8,rows*8),(0,0,64))
    px=img.load()
    for t in range(n):
        tx=(t%cols)*8; ty=(t//cols)*8
        for y in range(8):
            for x in range(4):
                v=b[t*32+y*4+x]
                for k,p in enumerate(((v>>4)&15,v&15)):
                    px[tx+x*2+k,ty+y]=PAL[p] if p else (0,0,64)
    img=img.resize((img.width*2,img.height*2),Image.NEAREST)
    img.save(out)
    print(out,img.size,'tiles',n)
if __name__=='__main__':
    render(sys.argv[1],int(sys.argv[2],16),int(sys.argv[3],16),int(sys.argv[4]),sys.argv[5])
