import os,collections
d='ext/files'
# size groups
sz=collections.Counter()
for f in os.listdir(d): sz[(f[:2],os.path.getsize(os.path.join(d,f)))]+=1
for k,v in sorted(sz.items()): print(k,v)
print('--- EV00000 non-zero map (16KB blocks)')
for name in ['EV00000.DAT','EV00001.DAT','EV00100.DAT']:
    b=open(os.path.join(d,name),'rb').read()
    print(name,len(b))
    for i in range(0,len(b),4096):
        ch=b[i:i+4096]
        nz=sum(1 for x in ch if x)
        print('  %06x nz=%4d entropy_bytes=%3d'%(i,nz,len(set(ch))))
