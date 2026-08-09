"""
Renderer factory.
"""

from mathwriter.renderers.pil_renderer import PILRenderer
from mathwriter.renderers.svg_renderer import SVGRenderer


RENDERERS = {
    "pil": PILRenderer,
    "svg": SVGRenderer,
}


def get_renderer(name: str):
    if name not in RENDERERS:
        raise KeyError(f"Unknown renderer: {name}. Available: {list(RENDERERS)}")
    return RENDERERS[name]


def register_renderer(name: str, cls):
    RENDERERS[name] = cls
