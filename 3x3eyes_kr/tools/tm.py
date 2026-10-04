# -*- coding: utf-8 -*-
"""번역 메모리: 이미 번역된 항목에서 '제어코드로 구분된 문장' 쌍을 학습해
아직 번역되지 않은 항목 중 전 문장이 학습된 것을 자동으로 채운다.

게임 대사에는 같은 문장이 상점/숙소/교회마다 반복되고, 같은 내용이
EV 파일별로 다른 제어코드로 이어붙여진 경우가 많아 재사용률이 높다.
"""
import sys, csv, re, collections

CTRL = re.compile(r'<[^<>]{1,24}>|\[[^\[\]]{1,24}\]')

def segs(s):
    """(세그먼트목록, 구분자목록). 세그먼트는 제어코드 사이의 본문."""
    parts, seps, i = [], [], 0
    for m in CTRL.finditer(s):
        parts.append(s[i:m.start()])
        seps.append(m.group())
        i = m.end()
    parts.append(s[i:])
    return parts, seps

def norm(t):
    return t.replace('・・・', '¨¨').replace('・・', '¨¨').strip()

def main(sheet):
    rows = list(csv.reader(open(sheet, encoding='utf-8'), delimiter='\t'))
    head, body = rows[0], rows[1:]

    # 1) 학습 — 세그먼트 수와 구분자가 일치하는 쌍만 신뢰
    mem = {}
    for r in body:
        if len(r) < 6 or not r[5].strip():
            continue
        jp, kr = segs(r[4]), segs(r[5])
        if len(jp[0]) != len(kr[0]) or jp[1] != kr[1]:
            continue
        for a, b in zip(jp[0], kr[0]):
            a = norm(a)
            if a and a not in mem:
                mem[a] = b
    print('학습한 문장 %d개' % len(mem))

    # 2) 적용 — 모든 세그먼트가 메모리에 있는 항목만 채운다
    filled = 0
    for r in body:
        if len(r) < 6 or r[5].strip():
            continue
        parts, seps = segs(r[4])
        out, ok = [], True
        for p in parts:
            n = norm(p)
            if n == '':
                out.append(p)
            elif n in mem:
                out.append(mem[n])
            else:
                ok = False
                break
        if not ok:
            continue
        s = ''
        for i, p in enumerate(out):
            s += p
            if i < len(seps):
                s += seps[i]
        r[5] = s
        filled += 1
    csv.writer(open(sheet, 'w', encoding='utf-8', newline=''),
               delimiter='\t').writerows([head] + body)
    print('자동 번역 %d건' % filled)
    print('남은 미번역 %d건' % sum(1 for r in body if len(r) < 6 or not r[5].strip()))

if __name__ == '__main__':
    main(sys.argv[1])
