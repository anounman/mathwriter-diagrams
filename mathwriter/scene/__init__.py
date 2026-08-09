"""
Scene graph for mathwriter.

This is the intermediate representation that all plugins produce and all
renderers consume. It is intentionally simple and backend-agnostic.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Callable, Literal


@dataclass
class Transform:
    """2-D affine transform stored as translate + scale + rotate (radians)."""
    x: float = 0.0
    y: float = 0.0
    scale_x: float = 1.0
    scale_y: float = 1.0
    rotate: float = 0.0

    def apply(self, px: float, py: float) -> tuple[float, float]:
        sx = px * self.scale_x
        sy = py * self.scale_y
        if self.rotate:
            c, s = math.cos(self.rotate), math.sin(self.rotate)
            rx = c * sx - s * sy
            ry = s * sx + c * sy
            return (rx + self.x, ry + self.y)
        return (sx + self.x, sy + self.y)

    def clone(self, dx: float = 0, dy: float = 0) -> "Transform":
        return Transform(
            x=self.x + dx,
            y=self.y + dy,
            scale_x=self.scale_x,
            scale_y=self.scale_y,
            rotate=self.rotate,
        )


@dataclass
class Style:
    """Stroke / fill / font styling for scene elements."""
    stroke: tuple[int, int, int] | None = (15, 70, 180)
    stroke_width: float = 2.0
    stroke_dash: list[float] | None = None
    fill: tuple[int, int, int, int] | None = None
    roughness: float = 1.0
    bowing: float = 1.0
    font_size: float = 24.0
    text_anchor: Literal["start", "middle", "end"] = "start"
    opacity: float = 1.0

    def copy(self, **overrides) -> "Style":
        data = {k: v for k, v in self.__dict__.items()}
        data.update(overrides)
        return Style(**data)


@dataclass
class Point:
    x: float
    y: float


class Node:
    """Base class for anything that can live in a scene graph."""

    def __init__(self, transform: Transform | None = None, style: Style | None = None):
        self.transform = transform or Transform()
        self.style = style or Style()

    def bounds(self) -> tuple[float, float, float, float]:
        """Return (min_x, min_y, max_x, max_y). Default: empty."""
        return (0.0, 0.0, 0.0, 0.0)


class Group(Node):
    """A collection of nodes, optionally with a local transform."""

    def __init__(self, children: list[Node] | None = None, **kwargs):
        super().__init__(**kwargs)
        self.children: list[Node] = children or []

    def add(self, node: Node) -> "Group":
        self.children.append(node)
        return self

    def bounds(self) -> tuple[float, float, float, float]:
        if not self.children:
            return (0.0, 0.0, 0.0, 0.0)
        min_x = min_y = math.inf
        max_x = max_y = -math.inf
        for c in self.children:
            bx0, by0, bx1, by1 = c.bounds()
            min_x = min(min_x, bx0 + self.transform.x)
            min_y = min(min_y, by0 + self.transform.y)
            max_x = max(max_x, bx1 + self.transform.x)
            max_y = max(max_y, by1 + self.transform.y)
        return (min_x, min_y, max_x, max_y)


class Line(Node):
    def __init__(self, x1: float, y1: float, x2: float, y2: float, **kwargs):
        super().__init__(**kwargs)
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2

    def bounds(self) -> tuple[float, float, float, float]:
        pts = [self.transform.apply(self.x1, self.y1),
               self.transform.apply(self.x2, self.y2)]
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        return (min(xs), min(ys), max(xs), max(ys))


class Polyline(Node):
    def __init__(self, points: list[tuple[float, float]], closed: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.points = points
        self.closed = closed

    def bounds(self) -> tuple[float, float, float, float]:
        xs = [self.transform.apply(p[0], p[1])[0] for p in self.points]
        ys = [self.transform.apply(p[0], p[1])[1] for p in self.points]
        return (min(xs), min(ys), max(xs), max(ys))


class Polygon(Node):
    def __init__(self, points: list[tuple[float, float]], **kwargs):
        super().__init__(**kwargs)
        self.points = points

    def bounds(self) -> tuple[float, float, float, float]:
        xs = [self.transform.apply(p[0], p[1])[0] for p in self.points]
        ys = [self.transform.apply(p[0], p[1])[1] for p in self.points]
        return (min(xs), min(ys), max(xs), max(ys))


class Rect(Node):
    def __init__(self, x: float, y: float, w: float, h: float, **kwargs):
        super().__init__(**kwargs)
        self.x = x
        self.y = y
        self.w = w
        self.h = h

    def bounds(self) -> tuple[float, float, float, float]:
        p0 = self.transform.apply(self.x, self.y)
        p1 = self.transform.apply(self.x + self.w, self.y + self.h)
        return (min(p0[0], p1[0]), min(p0[1], p1[1]),
                max(p0[0], p1[0]), max(p0[1], p1[1]))


class Circle(Node):
    def __init__(self, cx: float, cy: float, r: float, **kwargs):
        super().__init__(**kwargs)
        self.cx = cx
        self.cy = cy
        self.r = r

    def bounds(self) -> tuple[float, float, float, float]:
        cx, cy = self.transform.apply(self.cx, self.cy)
        r = self.r * max(self.transform.scale_x, self.transform.scale_y)
        return (cx - r, cy - r, cx + r, cy + r)


class Ellipse(Node):
    def __init__(self, cx: float, cy: float, rx: float, ry: float, **kwargs):
        super().__init__(**kwargs)
        self.cx = cx
        self.cy = cy
        self.rx = rx
        self.ry = ry

    def bounds(self) -> tuple[float, float, float, float]:
        cx, cy = self.transform.apply(self.cx, self.cy)
        rx = self.rx * self.transform.scale_x
        ry = self.ry * self.transform.scale_y
        return (cx - rx, cy - ry, cx + rx, cy + ry)


class Text(Node):
    def __init__(self, x: float, y: float, text: str, **kwargs):
        super().__init__(**kwargs)
        self.x = x
        self.y = y
        self.text = text

    def bounds(self) -> tuple[float, float, float, float]:
        # Placeholder until text metrics are available.
        size = self.style.font_size
        w = len(self.text) * size * 0.6
        h = size
        p0 = self.transform.apply(self.x, self.y - h)
        p1 = self.transform.apply(self.x + w, self.y)
        return (min(p0[0], p1[0]), min(p0[1], p1[1]),
                max(p0[0], p1[0]), max(p0[1], p1[1]))


class Image(Node):
    def __init__(self, x: float, y: float, w: float, h: float, src: str | Any, **kwargs):
        super().__init__(**kwargs)
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.src = src

    def bounds(self) -> tuple[float, float, float, float]:
        p0 = self.transform.apply(self.x, self.y)
        p1 = self.transform.apply(self.x + self.w, self.y + self.h)
        return (min(p0[0], p1[0]), min(p0[1], p1[1]),
                max(p0[0], p1[0]), max(p0[1], p1[1]))


class Path(Node):
    """Generic SVG-style path."""

    def __init__(self, d: str, **kwargs):
        super().__init__(**kwargs)
        self.d = d

    def bounds(self) -> tuple[float, float, float, float]:
        # Conservative fallback; renderer-specific path parsing can improve.
        return (0.0, 0.0, 100.0, 100.0)


def make_group(children: list[Node] | None = None) -> Group:
    return Group(children=children)
