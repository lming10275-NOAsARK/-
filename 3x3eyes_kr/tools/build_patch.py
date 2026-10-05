# -*- coding: utf-8 -*-
"""번역 시트 -> 한글 폰트 패치 + 한국어 코드표 + EV 파일 재삽입.

사용:
  python3 build_patch.py <원본files디렉터리> <script_ko.tsv> <string_map.json> <출력디렉터리>
"""
import os, sys, json, csv, collections, re, shutil
from tbl import load
from dump_text import pointer_table, TEXT_BLOCK
import kofont

# <br />, <0xdb>, <portrait_00> 같은 제어코드와 [player] 같은 치환코드
CTRL = re.compile(r'<[^<>]{1,24}>|\[[^\[\]]{1,24}\]')

def read_sheet(path):
    """id -> 한국어 (빈 값은 제외)"""
    out = {}
    with open(path, encoding='utf-8') as f:
        r = csv.reader(f, delimiter='\t')
        head = next(r)
        for row in r:
            if len(row) >= 6 and row[5].strip():
                out[row[0]] = row[5].strip()
    return out

def is_jp(ch):
    """일본어 가나/한자 — 번역되지 않고 남은 그래픽 조각의 문자."""
    return '\u3040' <= ch <= '\u30ff' or '\u4e00' <= ch <= '\u9fff'

def split_tokens(s):
    """문자열을 (텍스트|제어코드) 토큰으로 분해"""
    toks, i = [], 0
    for m in CTRL.finditer(s):
        if m.start() > i:
            toks.append(('t', s[i:m.start()]))
        toks.append(('c', m.group()))
        i = m.end()
    if i < len(s):
        toks.append(('t', s[i:]))
    return toks

def shrink_steps(text):
    """바이트 한도를 조금 넘을 때 쓰는 보수적인 축약 사다리.
    품질 손실이 적은 것부터 차례로 시도한다."""
    yield text
    t = text.replace('¨¨¨', '¨¨')
    if t != text:
        yield t
    t2 = t.replace('¨¨', '¨')
    if t2 != t:
        yield t2
    cur = t2
    # 본문 구간의 공백을 뒤에서부터 하나씩 제거 (제어코드는 건드리지 않는다)
    for _ in range(40):
        toks = split_tokens(cur)
        hit = False
        for i in range(len(toks) - 1, -1, -1):
            kind, body = toks[i]
            if kind == 't' and ' ' in body:
                j = body.rfind(' ')
                toks[i] = (kind, body[:j] + body[j + 1:])
                hit = True
                break
        if not hit:
            break
        cur = ''.join(b for _, b in toks)
        yield cur

def main(files_dir, sheet_path, map_path, out_dir):
    tbl, _ = load(os.path.join(os.path.dirname(__file__), '3x3eyes.tbl'))
    ctrl_code = {v: k for k, v in tbl.items()
                 if v.startswith('<') or v.startswith('[')}
    jp_code = {}
    for code, val in sorted(tbl.items()):
        if len(val) == 1 and is_jp(val) and val not in jp_code:
            jp_code[val] = code
    smap = json.load(open(map_path, encoding='utf-8'))
    kr = read_sheet(sheet_path)
    if not kr:
        print('번역된 줄이 없습니다. script_ko.tsv 의 한국어 열을 채우세요.')
        return

    # 1) 사용 문자 집계 (제어코드 제외)
    freq = collections.Counter()
    for sid, text in kr.items():
        n = len(smap[sid]['where'])
        for kind, t in split_tokens(text):
            if kind == 't':
                for ch in t:
                    if not is_jp(ch):      # 일본어 잔존 문자는 원본 코드를 그대로 쓴다
                        freq[ch] += n
    chars = [c for c, _ in freq.most_common()]

    # 2) 코드 할당
    mapping, n1, n2 = kofont.assign(chars, tbl)
    one_used = sum(1 for c in chars if len(mapping[c]) == 1)
    print('사용 문자 %d종 (1바이트 배정 %d / 2바이트 %d), 가용 1바이트 %d 2바이트 %d'
          % (len(chars), one_used, len(chars) - one_used, n1, n2))

    # 3) 인코딩
    def enc(text):
        out = bytearray()
        for kind, t in split_tokens(text):
            if kind == 'c':
                c = ctrl_code.get(t)
                if c is None:
                    raise ValueError('알 수 없는 제어코드 %s' % t)
                out += c
            else:
                for ch in t:
                    if ch in mapping:
                        out += mapping[ch]
                    elif ch in jp_code:    # 원본 일본어 코드 보존
                        out += jp_code[ch]
                    else:
                        raise ValueError('표현할 수 없는 문자 %r' % ch)
        return bytes(out)

    # 3-1) 안전장치 — 텍스트 opcode가 있는 '엔트리 진입점'은 절대 건드리지 않는다.
    #      런 추출이 opcode 바이트를 문자로 흡수한 경우가 드물게 있는데,
    #      거기에 번역문을 쓰면 대사 분기가 깨진다.
    entry_sites = set()
    for name in sorted(os.listdir(files_dir)):
        if not name.startswith('EV') or not name.endswith('.DAT'):
            continue
        b = open(os.path.join(files_dir, name), 'rb').read()
        ptrs = pointer_table(b, TEXT_BLOCK)
        if ptrs:
            entry_sites |= {(name, TEXT_BLOCK + p) for p in ptrs}

    os.makedirs(out_dir, exist_ok=True)
    # 4) EV 파일 패치
    edits = collections.defaultdict(list)
    over, shrunk, skipped = [], [], []
    for sid, text in kr.items():
        rec = smap[sid]
        budget = rec['bytes']
        data = enc(text)
        if len(data) > budget:
            # 자동 축약 시도
            for cand in shrink_steps(text):
                d = enc(cand)
                if len(d) <= budget:
                    shrunk.append((sid, text, cand, len(data), budget))
                    data, text = d, cand
                    break
            else:
                over.append((sid, len(data), budget, text[:30]))
                continue
        # 남는 자리는 0x00 으로 채운다. 0x00 은 이 게임의 문자열 종결자이므로
        # (문자열 앞 3153건 / 뒤 2812건에서 확인) 뒤쪽은 그대로 무시된다.
        data = data + b'\x00' * (budget - len(data))
        for w in rec['where']:
            site = (w['file'], int(w['offset'], 16))
            if site in entry_sites:
                skipped.append((sid, w['file'], w['offset']))
                continue
            edits[w['file']].append((site[1], data))

    for name, lst in edits.items():
        src = os.path.join(files_dir, name)
        b = bytearray(open(src, 'rb').read())
        for off, data in lst:
            b[off:off + len(data)] = data
        open(os.path.join(out_dir, name), 'wb').write(bytes(b))

    # 5) 폰트 패치
    fontfile = os.environ.get('KOFONT',
        '/usr/share/fonts/truetype/nanum/NanumGothicCoding.ttf')
    prg = open(os.path.join(files_dir, '_000PRG.DAT'), 'rb').read()
    open(os.path.join(out_dir, '_000PRG.DAT'), 'wb').write(
        kofont.patch(prg, mapping, fontfile))

    # 6) 한국어 코드표 저장
    with open(os.path.join(out_dir, 'korean.tbl'), 'w', encoding='utf-8') as f:
        for ch, code in sorted(mapping.items(), key=lambda kv: kv[1]):
            f.write('%s=%s\n' % (code.hex().upper(), ch))

    # 초과/축약 내역을 보고서로 남긴다 (번역자가 나중에 제대로 다듬도록)
    rep = os.path.join(os.path.dirname(sheet_path) or '.', 'overflow_report.tsv')
    with open(rep, 'w', encoding='utf-8') as f:
        f.write('구분\tid\t필요바이트\t한도\t내용\n')
        for sid, before, after, n, b in shrunk:
            f.write('자동축약\t%s\t%d\t%d\t%s\t=>\t%s\n' % (sid, n, b, before, after))
        for sid, n, b, t in over:
            f.write('보류\t%s\t%d\t%d\t%s\n' % (sid, n, b, t))

    print('패치한 EV 파일 %d개, 교체 문자열 %d건' % (len(edits), len(kr) - len(over)))
    if shrunk:
        print('자동 축약 %d건 (공백/말줄임 정리로 한도 충족)' % len(shrunk))
    if skipped:
        print('안전장치로 제외한 지점 %d곳 (엔트리 진입점 — opcode 영역)' % len(skipped))
    if over:
        print('바이트 초과로 보류 %d건 (요약):' % len(over))
        for o in over[:8]:
            print('   %s  %d>%d  %s' % o)
    print('상세 내역: %s' % rep)
    print('출력: %s' % out_dir)

if __name__ == '__main__':
    main(*sys.argv[1:5])
