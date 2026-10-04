# -*- coding: utf-8 -*-
"""한글 코드 할당 + 16x16 1bpp 폰트 생성 + _000PRG.DAT 폰트 영역 패치.

코드 공간 (게임 원본 구조에서 도출):
  1바이트 c (0x01~0xDA)      -> 글리프 c          (원래 가나/기호)
  2바이트 F0 xx (xx<0x1E)    -> 글리프 224+xx     (원래 전각 영문)
  2바이트 Fp xx (p=1..6)     -> 글리프 p*256+xx   (원래 한자 1508자)

전략: 빈출 음절은 1바이트 자리에 넣어 바이트를 절약하고,
      나머지는 2바이트 한자 자리를 쓴다.
"""
import os, json

FONT_OFF = 0x29000
GLYPH_BYTES = 32

# 보존할 1바이트 제어/기호 코드 — 재배정 금지
RESERVED_1B = set(range(0xDB, 0xE4)) | {0x00}

def glyph_index(code):
    """코드(bytes) -> 글리프 인덱스"""
    if len(code) == 1:
        return code[0]
    p, lo = code[0], code[1]
    if p == 0xF0:
        return 224 + lo
    return (p - 0xF0) * 256 + lo

def code_space(tbl):
    """사용 가능한 코드 목록을 (1바이트 우선) 순서로 반환."""
    one, two = [], []
    for k, v in sorted(tbl.items()):
        if len(k) == 1:
            if k[0] in RESERVED_1B or v.startswith('<'):
                continue
            one.append(k)
        elif len(k) == 2 and 0xF1 <= k[0] <= 0xF6 and not v.startswith('<'):
            two.append(k)
    return one, two

def assign(chars_by_freq, tbl):
    """빈도순 문자 목록 -> {문자: 코드bytes}. 1바이트 자리를 먼저 소비."""
    one, two = code_space(tbl)
    pool = one + two
    if len(chars_by_freq) > len(pool):
        raise SystemExit('코드 공간 부족: 필요 %d / 가용 %d (1바이트 %d + 2바이트 %d)'
                         % (len(chars_by_freq), len(pool), len(one), len(two)))
    return {c: pool[i] for i, c in enumerate(chars_by_freq)}, len(one), len(two)

def render_glyph(ch, font, threshold=110):
    from PIL import Image, ImageDraw
    img = Image.new('L', (16, 16), 0)
    ImageDraw.Draw(img).text((8, 8), ch, font=font, fill=255, anchor='mm')
    out = bytearray(GLYPH_BYTES)
    px = img.load()
    for y in range(16):
        for xb in range(2):
            v = 0
            for k in range(8):
                if px[xb * 8 + k, y] >= threshold:
                    v |= 1 << (7 - k)
            out[y * 2 + xb] = v
    return bytes(out)

def patch(prg_bytes, mapping, font_path, size=16):
    from PIL import ImageFont
    font = ImageFont.truetype(font_path, size)
    b = bytearray(prg_bytes)
    for ch, code in mapping.items():
        gi = glyph_index(code)
        o = FONT_OFF + gi * GLYPH_BYTES
        if o + GLYPH_BYTES > len(b):
            raise SystemExit('글리프 %d 가 파일 범위를 넘습니다' % gi)
        b[o:o + GLYPH_BYTES] = render_glyph(ch, font)
    return bytes(b)
