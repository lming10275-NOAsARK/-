# -*- coding: utf-8 -*-
"""번역 메모리: 이미 번역된 항목에서 '제어코드로 구분된 문장' 쌍을 학습해
아직 번역되지 않은 항목 중 전 문장이 학습된 것을 자동으로 채운다.

게임 대사에는 같은 문장이 상점/숙소/교회마다 반복되고, 같은 내용이
EV 파일별로 다른 제어코드로 이어붙여진 경우가 많아 재사용률이 높다.
"""
import sys, csv, re, collections, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from junk import is_junk

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
    # 같은 대사가 파일마다 표기만 다른 경우가 많아 정규화해서 대조한다
    t = t.replace('・・・・・', '¨¨¨¨¨').replace('・・・', '¨¨').replace('・・', '¨¨')
    t = t.replace('他に', 'ほかに').replace('他の', 'ほかの')
    t = t.replace('いらしゃいまし', 'いらっしゃいませ')
    t = t.replace('買い取らせてもらいもしょう', '買い取らせてもらいましょう')
    t = t.rstrip('。')
    return t.strip()

def load_glossary(path):
    """일본어조각<탭>한국어 형식. 메모리에 미리 넣어 자동 완성률을 끌어올린다."""
    g = {}
    try:
        for ln in open(path, encoding='utf-8'):
            ln = ln.rstrip('\n')
            if not ln.strip() or '\t' not in ln or ln.startswith('#'):
                continue
            a, b = ln.split('\t', 1)
            g[norm(a)] = b
    except FileNotFoundError:
        pass
    return g

def main(sheet, glossary='translation/glossary.tsv'):
    rows = list(csv.reader(open(sheet, encoding='utf-8'), delimiter='\t'))
    head, body = rows[0], rows[1:]

    # 1) 학습 — 용어집을 먼저 넣고, 번역된 항목에서 세그먼트 쌍을 추가 학습
    mem = load_glossary(glossary)
    print('용어집 %d개 선적재' % len(mem))
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
            elif is_junk(p):
                # 대사 뒤에 붙은 그래픽 바이트 조각 — 번역하지 않고 원본 그대로 둔다
                out.append(p)
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

def report(sheet, limit=60):
    """미번역 항목을 자동 완성하지 못하게 막는 '빠진 문장'을 빈도순으로 보고."""
    rows = list(csv.reader(open(sheet, encoding='utf-8'), delimiter='\t'))[1:]
    mem = set()
    for r in rows:
        if len(r) < 6 or not r[5].strip():
            continue
        jp, kr = segs(r[4]), segs(r[5])
        if len(jp[0]) != len(kr[0]) or jp[1] != kr[1]:
            continue
        for a in jp[0]:
            if norm(a):
                mem.add(norm(a))
    need = collections.Counter()
    for r in rows:
        if len(r) < 6 or r[5].strip():
            continue
        miss = [norm(p) for p in segs(r[4])[0]
                if norm(p) and norm(p) not in mem and not is_junk(p)]
        # 거의 다 아는 항목일수록 가치가 높다
        if miss and len(miss) <= 12:
            for m in miss:
                need[m] += 1
    for t, n in need.most_common(limit):
        print('%d|%s' % (n, t))

if __name__ == '__main__':
    if len(sys.argv) > 2 and sys.argv[2] == 'report':
        report(sys.argv[1], int(sys.argv[3]) if len(sys.argv) > 3 else 60)
    else:
        main(*sys.argv[1:])
