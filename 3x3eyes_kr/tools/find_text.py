import os,collections,math
d='ext/files'
def score(w):
    # 2-byte code stream heuristics
    best=0;bi=None
    for al in(0,1):
        pairs=[w[i]<<8|w[i+1] for i in range(al,len(w)-1,2)]
        if not pairs: continue
        c=collections.Counter(pairs)
        n=len(pairs); u=len(c)
        if u<8 or u>n*0.9: continue
        top=c.most_common(1)[0][1]
        # language-like: moderate alphabet, repeated codes, top freq 3-12%
        rep=1-u/n
        ent=-sum(v/n*math.log2(v/n) for v in c.values())
        s=rep*100
        if 0.02<top/n<0.20 and 4<ent<8.5 and rep>0.25: s+= (rep*200)+(8.5-ent)*10
        else: s=0
        if s>best: best=s;bi=(al,u,n,round(ent,2),round(rep,2))
    return best,bi
out=[]
for f in sorted(os.listdir(d)):
    b=open(os.path.join(d,f),'rb').read()
    for off in range(0,len(b),2048):
        w=b[off:off+2048]
        if len(set(w))<16: continue
        s,i=score(w)
        if s>60: out.append((s,f,off,i))
out.sort(reverse=True)
print('candidates:',len(out))
seen=collections.Counter()
for s,f,off,i in out:
    seen[f[:5] if not f.startswith('_') else f]+=1
print(seen.most_common(20))
for s,f,off,i in out[:25]: print('%6.1f %-14s %06X %s'%(s,f,off,i))
