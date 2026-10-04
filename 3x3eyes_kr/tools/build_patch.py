# -*- coding: utf-8 -*-
"""번역 시트 -> 한글 폰트 패치 + 한국어 코드표 + EV 파일 재삽입.

사용:
  python3 build_patch.py <원본files디렉터리> <script_ko.tsv> <string_map.json> <출력디렉터리>
"""
import os, sys, json, csv, collections, re, shutil
from tbl import load
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

def main(files_dir, sheet_path, map_path, out_dir):
    tbl, _ = load(os.path.join(os.path.dirname(__file__), '3x3eyes.tbl'))
    ctrl_code = {v: k for k, v in tbl.items()
                 if v.startswith('<') or v.startswith('[')}
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
                    out += mapping[ch]
        return bytes(out)

    os.makedirs(out_dir, exist_ok=True)
    # 4) EV 파일 패치
    edits = collections.defaultdict(list)
    over = []
    for sid, text in kr.items():
        rec = smap[sid]
        data = enc(text)
        budget = rec['bytes']
        if len(data) > budget:
            over.append((sid, len(data), budget, text[:30]))
            continue
        data = data + b'\x00' * (budget - len(data))   # 남는 자리는 공백코드로 패딩
        for w in rec['where']:
            edits[w['file']].append((int(w['offset'], 16), data))

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

    print('패치한 EV 파일 %d개, 교체 문자열 %d건' % (len(edits), len(kr) - len(over)))
    if over:
        print('바이트 초과로 보류 %d건 (요약):' % len(over))
        for o in over[:10]:
            print('   %s  %d>%d  %s' % o)
    print('출력: %s' % out_dir)

if __name__ == '__main__':
    main(*sys.argv[1:5])
