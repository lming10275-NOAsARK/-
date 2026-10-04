import os,collections
d='ext/files'
res=[]
for f in sorted(os.listdir(d)):
    b=open(os.path.join(d,f),'rb').read()
    if len(b)<20000: continue
    for off in range(0,len(b)-8192,8192):
        w=b[off:off+8192]
        if len(set(w))<6: continue
        nib=collections.Counter()
        for x in w: nib[x>>4]+=1; nib[x&15]+=1
        used=[k for k,v in nib.items() if v>len(w)*2*0.002]
        if len(used)<=3 and nib[0]>len(w)*2*0.4 and nib[0]<len(w)*2*0.93:
            res.append((f,off,sorted(used),round(nib[0]/(len(w)*2),2)))
print('regions',len(res))
agg=collections.Counter(r[0] for r in res)
print(agg.most_common(25))
for r in res[:30]: print(r)
