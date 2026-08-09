"""
Core Engine: public API, plugin registry, document model.
"""

from __future__ import annotations

import json, os, math
from dataclasses import dataclass, field
from typing import Any, Protocol
from pathlib import Path

from mathwriter.scene import (
    Group, Transform, Style,
    Line, Rect, Circle, Ellipse, Polygon, Polyline, Text, Image, Path
)
from mathwriter.glyphs import load_glyphs


@dataclass
class PageSettings:
    width: int = 1654
    height: int = 2339
    margin_top: int = 120
    margin_bottom: int = 120
    margin_left: int = 120
    margin_right: int = 120
    line_height: float = 64.0


@dataclass
class DocumentSettings:
    page: PageSettings = field(default_factory=PageSettings)
    style: Style = field(default_factory=Style)


class RenderContext:
    """Context passed to every plugin draw() call."""

    def __init__(self, settings: DocumentSettings, glyphs: dict | None = None):
        self.settings = settings
        self.style = settings.style
        self.glyphs = glyphs or {}

    def text_width(self, text: str, font_size: float | None = None) -> float:
        size = font_size or self.style.font_size
        return len(text) * size * 0.6

    def text_height(self, font_size: float | None = None) -> float:
        return font_size or self.style.font_size


class DiagramPlugin(Protocol):
    """Every diagram type implements this."""

    name: str

    def draw(self, spec: dict, ctx: RenderContext) -> Group:
        ...


class TextPlugin:
    name = "text"

    def draw(self, spec: dict, ctx: RenderContext) -> Group:
        text = spec.get("text", "")
        x = spec.get("x", 0)
        y = spec.get("y", 0)
        g = Group(transform=Transform(x=x, y=y))
        g.add(Text(0, 0, text, style=ctx.style.copy(text_anchor="start")))
        return g


class ImagePlugin:
    name = "image"

    def draw(self, spec: dict, ctx: RenderContext) -> Group:
        x = spec.get("x", 0)
        y = spec.get("y", 0)
        w = spec.get("w", 100)
        h = spec.get("h", 100)
        src = spec.get("src", "")
        return Group(children=[Image(x, y, w, h, src)], transform=Transform())


class Engine:
    """Public entry point for rendering documents."""

    def __init__(self, settings: DocumentSettings | None = None):
        self.settings = settings or DocumentSettings()
        self._plugins: dict[str, DiagramPlugin] = {}
        self._register_builtins()

    def _register_builtins(self):
        self.register(TextPlugin())
        self.register(ImagePlugin())

    def register(self, plugin: DiagramPlugin):
        self._plugins[plugin.name] = plugin
        return self

    def has_plugin(self, name: str) -> bool:
        return name in self._plugins

    def get_plugin(self, name: str) -> DiagramPlugin:
        return self._plugins[name]

    def plugins(self) -> list[str]:
        return list(self._plugins.keys())

    def render_diagram(self, spec: dict, ctx: RenderContext | None = None) -> Group:
        ctx = ctx or RenderContext(self.settings)
        plugin_name = spec.get("type", "text")
        plugin = self._plugins.get(plugin_name)
        if plugin is None:
            raise KeyError(f"No plugin registered for diagram type: {plugin_name}")
        return plugin.draw(spec, ctx)

    def new_page(self) -> "Page":
        return Page(self)


class Page:
    """One page of a document."""

    def __init__(self, engine: Engine):
        self.engine = engine
        self.settings = engine.settings.page
        self.blocks: list[dict] = []

    def write(self, text: str, x: float | None = None, y: float | None = None) -> "Page":
        self.blocks.append({
            "type": "text",
            "text": text,
            "x": x,
            "y": y,
        })
        return self

    def draw(self, spec: dict, x: float | None = None, y: float | None = None) -> "Page":
        block = dict(spec)
        if x is not None:
            block.setdefault("x", x)
        if y is not None:
            block.setdefault("y", y)
        self.blocks.append(block)
        return self

    def render(self, backend: str = "pil") -> Any:
        from mathwriter.renderers import get_renderer
        renderer = get_renderer(backend)(self.engine.settings)
        ctx = RenderContext(self.engine.settings, glyphs=load_glyphs())
        scene = self._build_scene(ctx)
        return renderer.render(scene)

    def _build_scene(self, ctx: RenderContext) -> Group:
        root = Group()
        y = self.settings.margin_top
        x = self.settings.margin_left
        for block in self.blocks:
            bx = block.get("x", x)
            by = block.get("y", y)
            spec = dict(block)
            spec.setdefault("x", bx)
            spec.setdefault("y", by)
            group = self.engine.render_diagram(spec, ctx)
            root.add(group)
            # Simple vertical flow: advance y by bounding-box height.
            b = group.bounds()
            height = max(1, b[3] - b[1])
            if block.get("y") is None:
                y += height + self.engine.settings.page.line_height
        return root

    def render_to_pdf(self, path: str) -> None:
        from mathwriter.renderers import get_renderer
        renderer = get_renderer("pil")(self.engine.settings)
        img = self.render("pil")
        renderer.save_pdf([img], path)


class Document:
    def __init__(self, engine: Engine | None = None):
        self.engine = engine or Engine()
        self.pages: list[Page] = []

    def new_page(self) -> Page:
        page = self.engine.new_page()
        self.pages.append(page)
        return page

    def render_all(self, backend: str = "pil") -> list[Any]:
        return [p.render(backend) for p in self.pages]

    def save_pdf(self, path: str) -> None:
        from mathwriter.renderers import get_renderer
        renderer = get_renderer("pil")(self.engine.settings)
        imgs = [p.render("pil") for p in self.pages]
        renderer.save_pdf(imgs, path)
