import os,sys
d='ext/files'
HIRA=lambda h,l: h==0x82 and 0x9f<=l<=0xf1
KANJI=lambda h,l: (0x88<=h<=0x9f or 0xe0<=h<=0xea) and (0x40<=l<=0xfc and l!=0x7f)
KATA=lambda h,l: h==0x83 and 0x40<=l<=0x96
PUNC=lambda h,l: h==0x81 and 0x40<=l<=0xac
ZEN =lambda h,l: h==0x82 and (0x4f<=l<=0x58 or 0x60<=l<=0x79 or 0x81<=l<=0x9a)
res=[]
for f in sorted(os.listdir(d)):
    p=os.path.join(d,f); b=open(p,'rb').read()
    # count hiragana pairs on even and odd alignment, and punctuation marks
    best=None
    for al in (0,1):
        hi=ka=kj=pu=0
        i=al
        while i+1<len(b):
            h,l=b[i],b[i+1]
            if HIRA(h,l): hi+=1
            elif KATA(h,l): ka+=1
            elif PUNC(h,l): pu+=1
            elif KANJI(h,l): kj+=1
            i+=2
        tot=hi+ka+kj+pu
        if best is None or hi>best[1]: best=(al,hi,ka,kj,pu,tot)
    if best[1]>20: res.append((f,)+best)
res.sort(key=lambda r:-r[2])
print('file align hira kata kanji punc tot')
for r in res[:40]: print('%-14s %d %5d %5d %5d %5d %6d'%r)
print('total files with hira>20:',len(res))
