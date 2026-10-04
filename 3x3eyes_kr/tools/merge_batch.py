# -*- coding: utf-8 -*-
"""ID<탭>한국어 배치 파일을 번역 시트에 병합한다."""
import sys, csv

def main(batch, sheet):
    tr = {}
    for ln in open(batch, encoding='utf-8'):
        ln = ln.rstrip('\n')
        if not ln.strip() or '\t' not in ln:
            continue
        k, v = ln.split('\t', 1)
        tr[k.strip()] = v.strip()
    rows = list(csv.reader(open(sheet, encoding='utf-8'), delimiter='\t'))
    n = 0
    for r in rows[1:]:
        if len(r) >= 6 and r[0] in tr:
            r[5] = tr[r[0]]
            n += 1
    csv.writer(open(sheet, 'w', encoding='utf-8', newline=''),
               delimiter='\t').writerows(rows)
    print('병합 %d건 / 배치 %d건' % (n, len(tr)))

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
