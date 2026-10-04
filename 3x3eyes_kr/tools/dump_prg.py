import re
b=open('ext/files/_000PRG.DAT','rb').read()
def ok(h,l):
    if not (0x81<=h<=0x9f or 0xe0<=h<=0xea): return False
    return 0x40<=l<=0xfc and l!=0x7f
runs=[];i=0
while i+1<len(b):
    if ok(b[i],b[i+1]):
        j=i
        while j+1<len(b) and ok(b[j],b[j+1]): j+=2
        if j-i>=6: runs.append((i,b[i:j]))
        i=j
    else: i+=1
print('runs:',len(runs),'bytes:',sum(len(r[1]) for r in runs))
good=0
for off,r in runs:
    try: s=r.decode('shift_jis')
    except: continue
    hira=sum(1 for c in s if '぀'<=c<='ゟ')
    if hira*3>=len(s) or len(s)>=8:
        good+=1
        if good<=60: print('%06X %s'%(off,s))
print('printable runs:',good)
