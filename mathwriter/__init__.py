"""
Public convenience imports for the mathwriter engine.
"""

from mathwriter.core.engine import Engine, Document, Page, RenderContext
from mathwriter.core.engine import DiagramPlugin, DocumentSettings, PageSettings
from mathwriter.scene import (
    Group, Transform, Style,
    Line, Rect, Circle, Ellipse, Polygon, Polyline, Text, Image, Path
)

__all__ = [
    "Engine", "Document", "Page", "RenderContext",
    "DiagramPlugin", "DocumentSettings", "PageSettings",
    "Group", "Transform", "Style",
    "Line", "Rect", "Circle", "Ellipse", "Polygon", "Polyline", "Text", "Image", "Path",
]


def create_engine() -> Engine:
    """Factory that registers all built-in plugins."""
    from mathwriter.plugins.gates import LogicGatePlugin
    engine = Engine()
    engine.register(LogicGatePlugin())
    return engine
