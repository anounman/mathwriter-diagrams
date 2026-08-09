"""
Glyph loading helper, extracted from render.py.
"""

import json, os
from pathlib import Path
from PIL import Image
import numpy as np
import cv2


INK_RGB = (15, 70, 180)


def recolor_to_blue(img, ink_rgb=INK_RGB):
    arr = np.array(img).astype(np.int16)
    a = arr[..., 3].astype(np.float32)
    new_a = np.where(a > 30, 255, a * 4).clip(0, 255)
    out = np.zeros_like(arr)
    out[..., 0] = ink_rgb[0]
    out[..., 1] = ink_rgb[1]
    out[..., 2] = ink_rgb[2]
    out[..., 3] = new_a
    out8 = out.astype(np.uint8)
    alpha = out8[..., 3].astype(np.float32)
    blurred = cv2.GaussianBlur(alpha, (3, 3), 0.5)
    out8[..., 3] = blurred.clip(0, 255).astype(np.uint8)
    return Image.fromarray(out8, 'RGBA')


def load_glyphs(glyphs_dir: str | None = None) -> dict:
    if glyphs_dir is None:
        glyphs_dir = os.environ.get('MATHWRITER_GLYPHS', 'glyphs')
    meta_path = Path(glyphs_dir) / 'metadata.json'
    with open(meta_path, 'r') as f:
        meta = json.load(f)
    cache = {}
    for ch, variants in meta.items():
        cache[ch] = []
        for v in variants:
            img = Image.open(v['file']).convert('RGBA')
            img = recolor_to_blue(img)
            v2 = {**v, 'img': img, 'baseline_y': v['baseline_y'] - 48}
            cache[ch].append(v2)
    return cache


def glyph_text_width(text: str, glyphs: dict, font_size: float) -> float:
    """Rough width estimate using stored glyph widths if available."""
    total = 0
    for ch in text:
        variants = glyphs.get(ch)
        if variants:
            total += variants[0].get('width', font_size * 0.6)
        else:
            total += font_size * 0.6
    return total
