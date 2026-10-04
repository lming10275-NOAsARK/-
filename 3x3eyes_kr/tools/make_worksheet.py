# -*- coding: utf-8 -*-
"""script.jsonl -> 번역 작업용 시트(TSV) + 중복 통합 맵(JSON).

동일 원문은 1건으로 합치고, 어느 파일/오프셋에 들어가는지 전부 기록한다.
번역은 TSV의 kr 열만 채우면 되고, 재삽입기가 맵을 보고 모든 위치에 반영한다.
"""
import json, sys, collections, os

def jpc(s):
    return sum(1 for c in s if '぀' <= c <= 'ヿ' or '一' <= c <= '鿿')

def main(src, tsv_out, map_out):
    rs = [json.loads(l) for l in open(src, encoding='utf-8')]
    groups = collections.OrderedDict()
    for r in rs:
        groups.setdefault(r['raw'], []).append(r)

    rows, mapping = [], {}
    for i, (raw, occ) in enumerate(groups.items(), 1):
        sid = 'S%04d' % i
        jp = occ[0]['jp']
        rows.append((sid, len(occ), occ[0]['bytes'], jpc(jp), jp))
        mapping[sid] = {
            'raw': raw,
            'jp': jp,
            'bytes': occ[0]['bytes'],
            'where': [{'file': o['file'], 'offset': o['offset']} for o in occ],
        }

    rows.sort(key=lambda r: (-r[1], r[0]))
    with open(tsv_out, 'w', encoding='utf-8') as f:
        f.write('id\t사용횟수\t바이트여유\t일본어글자수\t일본어\t한국어\n')
        for sid, n, by, ch, jp in rows:
            f.write('%s\t%d\t%d\t%d\t%s\t\n' % (sid, n, by, ch, jp.replace('\t', ' ')))

    os.makedirs(os.path.dirname(map_out) or '.', exist_ok=True)
    json.dump(mapping, open(map_out, 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print('고유 대사 %d건 / 총 출현 %d회 / 일본어 %d자'
          % (len(rows), len(rs), sum(r[3] for r in rows)))

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3])
