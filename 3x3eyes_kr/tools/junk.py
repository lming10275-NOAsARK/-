# -*- coding: utf-8 -*-
"""그래픽 바이트가 우연히 문자로 풀린 '가짜 대사'를 판정한다.

문자 테이블이 거의 모든 바이트값을 문자로 매핑하기 때문에, 그래픽 데이터도
일본어처럼 디코딩된다. 실제 대사가 가진 성질로 걸러낸다.
"""
import re, collections

CTRL = re.compile(r'<[^<>]{1,24}>|\[[^\[\]]{1,24}\]')
# 일본어 문장이면 거의 반드시 하나는 나오는 조사/어미/문장부호
MARKERS = 'のにをはがでとも、。？！『』「」♥'

def body(s):
    return CTRL.sub('', s)

def is_junk(s):
    t = body(s)
    if len(t) < 4:
        return True
    c = collections.Counter(t)
    # 1) 한 글자가 과도하게 반복 — 타일맵이 교대로 디코딩된 전형적 패턴
    if len(t) >= 6 and c.most_common(1)[0][1] / len(t) >= 0.45:
        return True
    if len(t) >= 12 and c.most_common(1)[0][1] / len(t) >= 0.30:
        return True
    # 2) 조사/문장부호가 하나도 없음
    if not any(m in t for m in MARKERS):
        return True
    # 3) 한자 비율이 비정상적으로 높음 (난수 바이트의 특징)
    kanji = sum(1 for ch in t if '一' <= ch <= '鿿')
    hira = sum(1 for ch in t if '぀' <= ch <= 'ゟ')
    if kanji and hira / (kanji + hira) < 0.25:
        return True
    return False
