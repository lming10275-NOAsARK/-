# -*- coding: utf-8 -*-
"""3x3eyes.tbl 로더 + 최장일치 디코더/인코더."""
import os

def load(path):
    ent = {}
    for ln in open(path, encoding='utf-8'):
        ln = ln.rstrip('\r\n')
        if '=' not in ln:
            continue
        k, v = ln.split('=', 1)
        try:
            ent[bytes.fromhex(k)] = v
        except ValueError:
            continue
    maxlen = max(len(k) for k in ent)
    return ent, maxlen

def decode(data, ent, maxlen):
    """바이트열 -> (텍스트, 미지바이트수)"""
    out = []
    unknown = 0
    i = 0
    n = len(data)
    while i < n:
        for ln in range(min(maxlen, n - i), 0, -1):
            v = ent.get(data[i:i + ln])
            if v is not None:
                out.append(v)
                i += ln
                break
        else:
            out.append('{%02X}' % data[i])
            unknown += 1
            i += 1
    return ''.join(out), unknown
