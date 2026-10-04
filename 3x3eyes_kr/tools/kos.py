import sys
class BR:
    def __init__(s,d,p): s.d=d;s.p=p;s.b=0;s.c=0
    def bit(s):
        if s.c==0:
            if s.p+1>=len(s.d): raise EOFError
            s.b=s.d[s.p]|(s.d[s.p+1]<<8); s.p+=2; s.c=16
        v=s.b&1; s.b>>=1; s.c-=1; return v
    def byte(s):
        if s.p>=len(s.d): raise EOFError
        v=s.d[s.p]; s.p+=1; return v
def kosinski(d,p=0,limit=1<<20):
    r=BR(d,p); out=bytearray()
    while True:
        if len(out)>limit: break
        if r.bit(): out.append(r.byte()); continue
        if r.bit():
            lo=r.byte(); hi=r.byte()
            cnt=hi&7; off=((hi&0xF8)<<5)|lo; off-=0x2000
            if cnt==0:
                cnt=r.byte()
                if cnt==0: break
                if cnt==1: continue
                cnt+=1
            else: cnt+=2
        else:
            cnt=(r.bit()<<1)|r.bit(); cnt+=2
            off=r.byte()-0x100
        base=len(out)+off
        if base<0: raise ValueError('neg')
        for i in range(cnt): out.append(out[base+i])
    return bytes(out),r.p
def comper(d,p=0,limit=1<<20):
    out=bytearray()
    while len(out)<limit:
        if p+1>=len(d): break
        desc=(d[p]<<8)|d[p+1]; p+=2
        for i in range(16):
            bit=(desc>>(15-i))&1
            if p+1>=len(d): return bytes(out),p
            if bit==0:
                out+=d[p:p+2]; p+=2
            else:
                off=d[p]; cnt=d[p+1]; p+=2
                if cnt==0: return bytes(out),p
                off=(off-0x100)*2
                base=len(out)+off
                if base<0: return bytes(out),p
                for k in range(cnt+1): out+=out[base+k*2:base+k*2+2]
    return bytes(out),p
if __name__=='__main__':
    b=open('shared.bin','rb').read()
    for seg,segstart in [('s0',0x0000),('s1',0x0D00),('s2',0x1A00)]:
        for name,fn in [('kos',kosinski),('comper',comper)]:
            for hd in (0x15,0x14,0x13,0x12,0x00):
                try:
                    o,end=fn(b,segstart+hd)
                    if len(o)>512: print('%s hdr=%02X %-6s -> %d bytes, consumed %d'%(seg,hd,name,len(o),end-segstart-hd))
                except Exception as e: pass
