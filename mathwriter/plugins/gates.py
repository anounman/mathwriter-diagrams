"""
Logic-gate plugin for the new scene-graph engine.
"""

import math
from mathwriter.scene import (
    Group, Transform, Style, Line, Polygon, Circle, Text, Rect, Polyline
)
from mathwriter.core.engine import DiagramPlugin, RenderContext


class LogicGatePlugin(DiagramPlugin):
    name = "logic_gate"

    def draw(self, spec: dict, ctx: RenderContext) -> Group:
        gate = spec.get("gate", "AND")
        inputs = spec.get("inputs", ["A", "B"])
        output = spec.get("output", "Y")
        truth_table = spec.get("truth_table", [])
        x = spec.get("x", 0)
        y = spec.get("y", 0)
        scale = spec.get("scale", 1.0)

        g = Group(transform=Transform(x=x, y=y, scale_x=scale, scale_y=scale))
        style = Style(stroke=ctx.style.stroke, stroke_width=2.5)

        body_x, body_y, body_w, body_h = 140, 50, 140, 90

        if gate == "AND":
            g.add(_and_shape(body_x, body_y, body_w, body_h, style))
        elif gate == "OR":
            g.add(_or_shape(body_x, body_y, body_w, body_h, style))
        elif gate == "NOT":
            g.add(_not_shape(body_x, body_y + 20, body_w, body_h - 40, style))
        elif gate == "XOR":
            g.add(_xor_shape(body_x, body_y, body_w, body_h, style))
        elif gate == "NAND":
            g.add(_nand_shape(body_x, body_y, body_w, body_h, style))
        elif gate == "NOR":
            g.add(_nor_shape(body_x, body_y, body_w, body_h, style))
        else:
            g.add(_and_shape(body_x, body_y, body_w, body_h, style))

        # gate label
        g.add(Text(body_x + body_w / 2, body_y + body_h / 2, gate,
                   style=Style(stroke=ctx.style.stroke, font_size=20)))

        # input lines
        n_in = max(1, len(inputs))
        for i, inp in enumerate(inputs):
            iy = body_y + (i + 1) * body_h / (n_in + 1)
            g.add(Line(body_x - 50, iy, body_x, iy, style=style))
            g.add(Text(body_x - 70, iy, inp, style=Style(stroke=ctx.style.stroke, font_size=16)))

        # output line + label
        out_y = body_y + body_h / 2
        g.add(Line(body_x + body_w, out_y, body_x + body_w + 50, out_y, style=style))
        g.add(Text(body_x + body_w + 70, out_y, output, style=Style(stroke=ctx.style.stroke, font_size=16)))

        # truth table
        if truth_table:
            table_y = body_y + body_h + 30
            cell_w, cell_h = 40, 28
            start_x = 210 - (len(inputs) + 1) * cell_w / 2
            for r, row in enumerate(truth_table[:5]):
                for c, val in enumerate(row):
                    xx = start_x + c * cell_w
                    yy = table_y + r * cell_h
                    g.add(Rect(xx + 2, yy + 2, cell_w - 4, cell_h - 4,
                               style=Style(stroke=ctx.style.stroke, stroke_width=1.5)))
                    g.add(Text(xx + cell_w / 2, yy + cell_h / 2 + 6, str(val),
                               style=Style(stroke=ctx.style.stroke, font_size=14, text_anchor="middle")))

        return g

def _and_shape(x, y, w, h, style):
    """D-shaped AND gate body as two separate strokes to avoid closing artifacts."""
    g = Group()
    g.add(Line(x, y, x, y + h, style=style))
    arc = []
    n = 32
    for k in range(n + 1):
        t = k / n
        angle = -math.pi / 2 + math.pi * t
        cx = x + w * 0.45
        cy = y + h / 2
        r = h / 2
        arc.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    g.add(Polyline(arc, style=style))
    return g


def _or_shape(x, y, w, h, style):
    """Curved OR gate body."""
    n = 24
    pts = []
    for k in range(n // 2 + 1):
        t = k / (n // 2)
        px = x + w * 0.15 * (1 - math.cos(math.pi * t))
        py = y + h * t
        pts.append((px, py))
    for k in range(n // 2, n + 1):
        t = (k - n // 2) / (n // 2)
        angle = -math.pi / 2 + math.pi * t
        cx = x + w * 0.35
        cy = y + h / 2
        r = h / 2
        pts.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    return Polyline(pts, style=style)


def _not_shape(x, y, w, h, style):
    g = Group()
    pts = [(x, y), (x + w * 0.7, y + h / 2), (x, y + h), (x, y)]
    g.add(Polygon(pts, style=style))
    g.add(Circle(x + w * 0.85, y + h / 2, 6, style=style))
    return g


def _xor_shape(x, y, w, h, style):
    g = Group()
    g.add(_or_shape(x + 10, y, w - 10, h, style))
    n = 12
    pts = []
    for k in range(n + 1):
        t = k / n
        px = x + 8 + 6 * (1 - math.cos(math.pi * t))
        py = y + h * t
        pts.append((px, py))
    g.add(Polyline(pts, style=style))
    return g


def _nand_shape(x, y, w, h, style):
    g = Group()
    g.add(_and_shape(x, y, w - 15, h, style))
    g.add(Circle(x + w - 8, y + h / 2, 7, style=style))
    return g


def _nor_shape(x, y, w, h, style):
    g = Group()
    g.add(_or_shape(x, y, w - 15, h, style))
    g.add(Circle(x + w - 8, y + h / 2, 7, style=style))
    return g
