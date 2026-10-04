# -*- coding: utf-8 -*-
"""EV*.DAT 대사 추출기.

텍스트 블록(0x14800)의 포인터 테이블을 읽고, 각 엔트리 안에서
'실제 화면에 출력되는 문자열 런'만 분리해 번역용 레코드로 만든다.

보존 항목: 파일명 / 블록 / 엔트리번호 / 런의 절대오프셋 / 원본바이트(hex)
         / 일본어 / 제어코드 / 바이트길이(재삽입 한계)
"""
import os, sys, json, glob
from tbl import load, decode

TEXT_BLOCK = 0x14800
MIN_RUN = 3          # 이 글자 수 미만의 런은 버린다
PAD = 0xFF

def be16(b, o):
    return (b[o] << 8) | b[o + 1]

def pointer_table(b, base):
    """유효한 포인터 테이블이면 포인터 목록, 아니면 None."""
    if base + 0x10 > len(b) or be16(b, base) != 0x0008:
        return None
    first = be16(b, base + 8)
    if not (0x10 <= first <= 0x4000) or first % 2:
        return None
    cnt = (first - 8) // 2
    if not (1 <= cnt <= 2000):
        return None
    p = [be16(b, base + 8 + i * 2) for i in range(cnt)]
    if any(p[i] > p[i + 1] for i in range(cnt - 1)) or max(p) > 0x8000:
        return None
    return p

def block_end(b, base):
    run = 0
    for i in range(base, len(b)):
        if b[i] == PAD:
            run += 1
            if run >= 64:
                return i - 63
        else:
            run = 0
    return len(b)

def classify(ent, maxlen, data):
    """data를 (토큰, 바이트길이, 종류) 목록으로 분해. 종류: 'c'=문자 'k'=제어 'u'=미지"""
    toks = []
    i, n = 0, len(data)
    while i < n:
        for ln in range(min(maxlen, n - i), 0, -1):
            v = ent.get(data[i:i + ln])
            if v is not None:
                toks.append((v, i, ln, 'k' if v.startswith('<') else 'c'))
                i += ln
                break
        else:
            toks.append(('{%02X}' % data[i], i, 1, 'u'))
            i += 1
    return toks

def runs_of(toks):
    """문자 토큰이 MIN_RUN 이상 연속되는 구간을 추출. 구간 내부의 제어코드는 포함."""
    out = []
    cur = []
    for t in toks:
        if t[3] == 'c':
            cur.append(t)
        elif t[3] == 'k' and cur:
            cur.append(t)
        else:
            if sum(1 for x in cur if x[3] == 'c') >= MIN_RUN:
                while cur and cur[-1][3] == 'k':
                    cur.pop()
                out.append(cur)
            cur = []
    if sum(1 for x in cur if x[3] == 'c') >= MIN_RUN:
        while cur and cur[-1][3] == 'k':
            cur.pop()
        out.append(cur)
    return out

def jp_count(s):
    return sum(1 for c in s if '\u3040' <= c <= '\u30ff' or '\u4e00' <= c <= '\u9fff')

def hira_count(s):
    return sum(1 for c in s if '\u3040' <= c <= '\u309f')

def kanji_count(s):
    return sum(1 for c in s if '\u4e00' <= c <= '\u9fff')

def is_dialogue(s):
    """실제 대사인지 판정 — 그래픽 바이트의 우연한 디코딩을 걸러낸다."""
    if jp_count(s) < 6 or hira_count(s) < 3:
        return False
    return kanji_count(s) > 0 or any(p in s for p in '。、？！')

def main(files_dir, tbl_path, out_path):
    ent, maxlen = load(tbl_path)
    recs = []
    st = {'files': 0, 'with_text': 0, 'pointers': 0, 'runs': 0, 'dialogue': 0, 'chars': 0}
    for path in sorted(glob.glob(os.path.join(files_dir, 'EV*.DAT'))):
        name = os.path.basename(path)
        b = open(path, 'rb').read()
        st['files'] += 1
        ptrs = pointer_table(b, TEXT_BLOCK)
        if ptrs is None:
            continue
        st['with_text'] += 1
        st['pointers'] += len(ptrs)
        base = TEXT_BLOCK
        start = base + min(ptrs)
        end = block_end(b, base)
        region = b[start:end]
        toks = classify(ent, maxlen, region)
        ptrset = {base + p for p in ptrs}
        for r in runs_of(toks):
            s = r[0][1]
            e = r[-1][1] + r[-1][2]
            sub = region[s:e]
            jp = ''.join(t[0] for t in r)
            st['runs'] += 1
            if not is_dialogue(jp):
                continue
            st['dialogue'] += 1
            st['chars'] += jp_count(jp)
            off = start + s
            recs.append({
                'id': '%s:%06X' % (name[2:7], off),
                'file': name,
                'offset': '0x%X' % off,
                'is_entry': off in ptrset,
                'bytes': len(sub),
                'raw': sub.hex(),
                'jp': jp,
                'kr': '',
            })
    os.makedirs(os.path.dirname(out_path) or '.', exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    print(json.dumps(st, ensure_ascii=False))
    print('wrote', out_path)

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3])
