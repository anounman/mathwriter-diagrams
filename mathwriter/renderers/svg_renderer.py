"""
SVG renderer: vector output from the scene graph.
"""

import math
from xml.etree.ElementTree import Element, SubElement, tostring

from mathwriter.scene import (
    Node, Group, Transform,
    Line, Rect, Circle, Ellipse, Polygon, Polyline, Text, Image as ImageNode, Path
)


def _rgb(c):
    if c is None:
        return "none"
    return f"rgb({c[0]},{c[1]},{c[2]})"


def _rgba(c):
    if c is None:
        return "none"
    if len(c) == 4:
        return f"rgba({c[0]},{c[1]},{c[2]},{c[3]/255:.2f})"
    return f"rgb({c[0]},{c[1]},{c[2]})"


class SVGRenderer:
    def __init__(self, settings):
        self.settings = settings

    def render(self, scene: Group) -> str:
        w = self.settings.page.width
        h = self.settings.page.height
        svg = Element(
            "svg",
            xmlns="http://www.w3.org/2000/svg",
            width=str(w),
            height=str(h),
            viewBox=f"0 0 {w} {h}",
        )
        # white background rect
        SubElement(svg, "rect", x="0", y="0", width=str(w), height=str(h), fill="white")
        self._draw_group(svg, scene)
        return tostring(svg, encoding="unicode")

    def _draw_group(self, parent: Element, group: Group):
        for node in group.children:
            self._draw_node(parent, node)

    def _draw_node(self, parent: Element, node: Node):
        if isinstance(node, Group):
            g = SubElement(parent, "g")
            # simple translate transform
            if node.transform.x or node.transform.y:
                g.set("transform", f"translate({node.transform.x},{node.transform.y})")
            self._draw_group(g, node)
        elif isinstance(node, Line):
            p1 = node.transform.apply(node.x1, node.y1)
            p2 = node.transform.apply(node.x2, node.y2)
            SubElement(
                parent, "line",
                {"x1": f"{p1[0]:.2f}", "y1": f"{p1[1]:.2f}",
                 "x2": f"{p2[0]:.2f}", "y2": f"{p2[1]:.2f}",
                 "stroke": _rgb(node.style.stroke),
                 "stroke-width": str(node.style.stroke_width),
                 "fill": "none"},
            )
        elif isinstance(node, Rect):
            x, y = node.transform.apply(node.x, node.y)
            w = node.w * node.transform.scale_x
            h = node.h * node.transform.scale_y
            SubElement(
                parent, "rect",
                {"x": f"{x:.2f}", "y": f"{y:.2f}",
                 "width": f"{w:.2f}", "height": f"{h:.2f}",
                 "stroke": _rgb(node.style.stroke),
                 "stroke-width": str(node.style.stroke_width),
                 "fill": _rgba(node.style.fill) if node.style.fill else "none"},
            )
        elif isinstance(node, Circle):
            cx, cy = node.transform.apply(node.cx, node.cy)
            r = node.r * max(node.transform.scale_x, node.transform.scale_y)
            SubElement(
                parent, "circle",
                {"cx": f"{cx:.2f}", "cy": f"{cy:.2f}", "r": f"{r:.2f}",
                 "stroke": _rgb(node.style.stroke),
                 "stroke-width": str(node.style.stroke_width),
                 "fill": _rgba(node.style.fill) if node.style.fill else "none"},
            )
        elif isinstance(node, Ellipse):
            cx, cy = node.transform.apply(node.cx, node.cy)
            rx = node.rx * node.transform.scale_x
            ry = node.ry * node.transform.scale_y
            SubElement(
                parent, "ellipse",
                {"cx": f"{cx:.2f}", "cy": f"{cy:.2f}",
                 "rx": f"{rx:.2f}", "ry": f"{ry:.2f}",
                 "stroke": _rgb(node.style.stroke),
                 "stroke-width": str(node.style.stroke_width),
                 "fill": _rgba(node.style.fill) if node.style.fill else "none"},
            )
        elif isinstance(node, Polygon):
            pts = [node.transform.apply(p[0], p[1]) for p in node.points]
            d = " ".join(f"{x:.2f},{y:.2f}" for x, y in pts)
            SubElement(
                parent, "polygon",
                {"points": d,
                 "stroke": _rgb(node.style.stroke),
                 "stroke-width": str(node.style.stroke_width),
                 "fill": _rgba(node.style.fill) if node.style.fill else "none"},
            )
        elif isinstance(node, Polyline):
            pts = [node.transform.apply(p[0], p[1]) for p in node.points]
            d = " ".join(f"{x:.2f},{y:.2f}" for x, y in pts)
            SubElement(
                parent, "polyline",
                {"points": d,
                 "stroke": _rgb(node.style.stroke),
                 "stroke-width": str(node.style.stroke_width),
                 "fill": "none"},
            )
        elif isinstance(node, Text):
            x, y = node.transform.apply(node.x, node.y)
            el = SubElement(
                parent, "text",
                {"x": f"{x:.2f}", "y": f"{y:.2f}",
                 "fill": _rgb(node.style.stroke),
                 "font-size": str(node.style.font_size),
                 "text-anchor": node.style.text_anchor},
            )
            el.text = node.text
        elif isinstance(node, ImageNode):
            x, y = node.transform.apply(node.x, node.y)
            w = node.w * node.transform.scale_x
            h = node.h * node.transform.scale_y
            SubElement(
                parent, "image",
                {"x": f"{x:.2f}", "y": f"{y:.2f}",
                 "width": f"{w:.2f}", "height": f"{h:.2f}",
                 "href": str(node.src)},
            )
        elif isinstance(node, Path):
            SubElement(
                parent, "path",
                {"d": node.d,
                 "stroke": _rgb(node.style.stroke),
                 "stroke-width": str(node.style.stroke_width),
                 "fill": "none"},
            )

    def save(self, scene: Group, path: str) -> None:
        with open(path, "w") as f:
            f.write(self.render(scene))
