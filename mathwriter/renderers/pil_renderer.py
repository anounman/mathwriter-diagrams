"""
PIL renderer: raster output from the scene graph.

This renderer walks the scene graph and draws to a PIL Image. It reuses the
anti-aliased line drawing and glyph compositing logic from the original
mathwriter/render.py.
"""

import math, random
from typing import Any
from PIL import Image, ImageDraw

from mathwriter.scene import (
    Node, Group, Transform, Style,
    Line, Rect, Circle, Ellipse, Polygon, Polyline, Text, Image as ImageNode, Path
)
from mathwriter.glyphs import recolor_to_blue


INK_RGB = (15, 70, 180)
AA_SS = 3


def _ink_jit(ink=INK_RGB, jitter=5):
    return tuple(max(0, min(255, c + random.randint(-jitter, jitter))) for c in ink)


def aa_line(target_img, pts, fill, width=3, joint='curve'):
    if not pts or len(pts) < 2:
        return
    fpts = [(float(p[0]), float(p[1])) for p in pts]
    min_x = min(p[0] for p in fpts)
    min_y = min(p[1] for p in fpts)
    max_x = max(p[0] for p in fpts)
    max_y = max(p[1] for p in fpts)
    pad = max(int(width * 2), 6)
    bbox_w = int(math.ceil(max_x - min_x + 2 * pad))
    bbox_h = int(math.ceil(max_y - min_y + 2 * pad))
    if bbox_w <= 0 or bbox_h <= 0:
        return
    temp = Image.new('RGBA', (bbox_w * AA_SS, bbox_h * AA_SS), (0, 0, 0, 0))
    td = ImageDraw.Draw(temp)
    ss_pts = [((p[0] - min_x + pad) * AA_SS,
               (p[1] - min_y + pad) * AA_SS) for p in fpts]
    if joint:
        td.line(ss_pts, fill=fill, width=max(1, int(width * AA_SS)), joint=joint)
    else:
        td.line(ss_pts, fill=fill, width=max(1, int(width * AA_SS)))
    small = temp.resize((bbox_w, bbox_h), getattr(Image, 'Resampling', Image).LANCZOS if hasattr(getattr(Image, 'Resampling', None), 'LANCZOS') else 1)
    target_img.alpha_composite(small, (int(min_x - pad), int(min_y - pad)))


def _to_global(node: Node, x: float, y: float) -> tuple[float, float]:
    return node.transform.apply(x, y)


class PILRenderer:
    def __init__(self, settings):
        self.settings = settings

    def render(self, scene: Group) -> Image.Image:
        w = self.settings.page.width
        h = self.settings.page.height
        canvas = Image.new('RGBA', (w, h), (255, 255, 255, 0))
        self._draw_group(canvas, scene)
        # composite on white paper
        paper = Image.new('RGBA', (w, h), (255, 255, 255, 255))
        paper.alpha_composite(canvas)
        return paper.convert('RGB')

    def _draw_group(self, canvas: Image.Image, group: Group):
        for node in group.children:
            self._draw_node(canvas, node)

    def _draw_node(self, canvas: Image.Image, node: Node):
        if isinstance(node, Group):
            self._draw_group(canvas, node)
        elif isinstance(node, Line):
            p1 = _to_global(node, node.x1, node.y1)
            p2 = _to_global(node, node.x2, node.y2)
            aa_line(canvas, [p1, p2], _ink_jit(), width=node.style.stroke_width)
        elif isinstance(node, Rect):
            x, y = _to_global(node, node.x, node.y)
            w = node.w * node.transform.scale_x
            h = node.h * node.transform.scale_y
            pts = [(x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)]
            aa_line(canvas, pts, _ink_jit(), width=node.style.stroke_width, joint=None)
        elif isinstance(node, Circle):
            cx, cy = _to_global(node, node.cx, node.cy)
            r = node.r * max(node.transform.scale_x, node.transform.scale_y)
            n = 32
            pts = []
            for k in range(n + 1):
                a = 2 * math.pi * k / n
                pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
            aa_line(canvas, pts, _ink_jit(), width=node.style.stroke_width, joint=None)
        elif isinstance(node, Ellipse):
            cx, cy = _to_global(node, node.cx, node.cy)
            rx = node.rx * node.transform.scale_x
            ry = node.ry * node.transform.scale_y
            n = 32
            pts = []
            for k in range(n + 1):
                a = 2 * math.pi * k / n
                pts.append((cx + rx * math.cos(a), cy + ry * math.sin(a)))
            aa_line(canvas, pts, _ink_jit(), width=node.style.stroke_width, joint=None)
        elif isinstance(node, Polygon):
            pts = [_to_global(node, p[0], p[1]) for p in node.points]
            if pts and pts[0] != pts[-1]:
                pts.append(pts[0])
            aa_line(canvas, pts, _ink_jit(), width=node.style.stroke_width, joint=None)
        elif isinstance(node, Polyline):
            pts = [_to_global(node, p[0], p[1]) for p in node.points]
            aa_line(canvas, pts, _ink_jit(), width=node.style.stroke_width, joint='curve' if not node.closed else None)
        elif isinstance(node, Text):
            self._draw_text(canvas, node)
        elif isinstance(node, ImageNode):
            self._draw_image(canvas, node)
        elif isinstance(node, Path):
            # Fallback: render as text placeholder for now.
            pass

    def _draw_text(self, canvas: Image.Image, node: Text):
        x, y = _to_global(node, node.x, node.y)
        text = node.text
        size = node.style.font_size
        # Use a simple system-font fallback until real glyph integration.
        from PIL import ImageFont
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", int(size))
        except Exception:
            font = ImageFont.load_default()
        draw = ImageDraw.Draw(canvas)
        color = node.style.stroke or INK_RGB
        draw.text((x, y), text, fill=color, font=font)

    def _draw_image(self, canvas: Image.Image, node: ImageNode):
        x, y = _to_global(node, node.x, node.y)
        w = int(node.w * node.transform.scale_x)
        h = int(node.h * node.transform.scale_y)
        if isinstance(node.src, Image.Image):
            canvas.alpha_composite(node.src.resize((w, h)), (int(x), int(y)))

    def save_pdf(self, images: list[Image.Image], path: str) -> None:
        images[0].save(path, save_all=True, append_images=images[1:], resolution=150.0)
