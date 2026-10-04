b=open('ext/files/EV00000.DAT','rb').read()
print('fill byte at 0x5000:',hex(b[0x5000]),len(set(b[0x5000:0x6000])))
print('fill at 0x1f000:',hex(b[0x1f000]))
# find real end of data
import re
print('--- 0x4000 region')
print(b[0x4000:0x4200].hex(' ',1))
print('--- 0x13000 region')
print(b[0x13000:0x13200].hex(' ',1))
print('--- 0xb000')
print(b[0xb000:0xb100].hex(' ',1))
print('--- 0xc000')
print(b[0xc000:0xc200].hex(' ',1))
