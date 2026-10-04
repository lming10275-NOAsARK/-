# -*- coding: utf-8 -*-
"""패치 결과 역검증: 패치된 EV 파일에서 다시 읽어 한국어가 들어갔는지 확인."""
import sys, json, os
from tbl import load, decode

def main(build_dir, map_path, sheet_path):
    ko, kmax = load(os.path.join(build_dir, 'korean.tbl'))
    jp, jmax = load(os.path.join(os.path.dirname(__file__), '3x3eyes.tbl'))
    # 한국어표 + 원본 제어코드표 합본으로 디코딩
    merged = dict(jp)
    merged.update(ko)
    mmax = max(kmax, jmax)
    smap = json.load(open(map_path, encoding='utf-8'))
    ok = miss = 0
    for sid, rec in smap.items():
        w = rec['where'][0]
        path = os.path.join(build_dir, w['file'])
        if not os.path.exists(path):
            continue
        b = open(path, 'rb').read()
        off = int(w['offset'], 16)
        raw = b[off:off + rec['bytes']]
        if raw == bytes.fromhex(rec['raw']):
            continue           # 미번역 — 원본 그대로
        txt, _ = decode(raw, merged, mmax)
        has_ko = any('가' <= c <= '힣' for c in txt)
        if has_ko:
            ok += 1
            if ok <= 8:
                print('%s %s@%s  %s' % (sid, w['file'], w['offset'],
                                        txt.rstrip('\x00').replace('{00}', '')[:70]))
        else:
            miss += 1
            print('!! %s 한글 없음: %r' % (sid, txt[:50]))
    print('\n검증: 한국어 확인 %d건 / 실패 %d건' % (ok, miss))

if __name__ == '__main__':
    main(*sys.argv[1:4])
