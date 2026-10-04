import os,collections
d='ext/files'
res=[]
for f in sorted(os.listdir(d)):
    b=open(os.path.join(d,f),'rb').read()
    for off in range(0,len(b)-4096,4096):
        w=b[off:off+4096]
        for al in (0,1):
            p=[w[i]<<8|w[i+1] for i in range(al,4095,2)]
            c=collections.Counter(p); u=len(c); n=len(p)
            if not (60<=u<=700): continue
            top=c.most_common(3)
            if top[0][1]<n*0.03: continue
            # high byte diversity limited => code page like
            hb=len(set(x>>8 for x in p))
            if hb>40: continue
            res.append((f,off,al,u,hb,top[0][0],top[0][1]))
print('hits',len(res))
print(collections.Counter(r[0][:5] for r in res).most_common(15))
for r in res[:25]: print('%-14s %06X al%d u=%3d hb=%2d top=%04X x%d'%r)
