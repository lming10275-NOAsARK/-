import os
d='ext/files'
def fontscore(b,gsz,rows,rb):
    # gsz bytes per glyph, rows rows, rb bytes/row
    n=len(b)//gsz; good=0; tot=0
    for g in range(n):
        gl=b[g*gsz:(g+1)*gsz]
        ink=sum(bin(x).count('1') for x in gl)
        dens=ink/(gsz*8)
        if not (0.06<dens<0.5): continue
        # top and bottom row mostly blank
        top=sum(gl[0:rb]); bot=sum(gl[(rows-1)*rb:rows*rb])
        if top==0 and bot==0: good+=1
    return good/max(n,1)
cands=[]
for f in sorted(os.listdir(d)):
    b=open(os.path.join(d,f),'rb').read()
    if len(b)<20000: continue
    for off in range(0,len(b)-16384,16384):
        w=b[off:off+16384]
        if len(set(w))<10: continue
        for gsz,rows,rb in ((32,16,2),(24,12,2),(16,16,1),(12,12,1)):
            s=fontscore(w,gsz,rows,rb)
            if s>0.45: cands.append((s,f,off,gsz))
cands.sort(reverse=True)
print('cands',len(cands))
for c in cands[:30]: print('%.2f %-14s %06X g%d'%c)
