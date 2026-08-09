# Mathwriter — Modular Engine (Phase 1)

This branch contains the new pluggable engine alongside the legacy renderer.

## New architecture

```
mathwriter/
├── core/
│   └── engine.py          # Engine, Page, Document, Plugin registry
├── scene/
│   └── __init__.py         # Scene graph primitives
├── renderers/
│   ├── __init__.py         # renderer factory
│   ├── pil_renderer.py     # raster backend
│   └── svg_renderer.py     # vector backend
├── plugins/
│   └── gates.py            # logic_gate plugin
├── glyphs.py               # handwriting glyph loader
└── __init__.py             # public exports + create_engine()
```

## Usage

```python
from mathwriter import create_engine

engine = create_engine()
page = engine.new_page()
page.draw({
    "type": "logic_gate",
    "gate": "AND",
    "inputs": ["A", "B"],
    "output": "Y",
    "truth_table": [["A", "B", "Y"], ["0", "0", "0"], ["1", "1", "1"]],
})
page.render("pil").save("and.png")
print(page.render("svg"))  # SVG string
```

## Adding a new plugin

```python
from mathwriter import DiagramPlugin, Group

class MyPlugin(DiagramPlugin):
    name = "my_shape"

    def draw(self, spec, ctx):
        g = Group()
        # build scene graph with primitives
        return g

engine.register(MyPlugin())
```

## Legacy renderer

The original `render.py` and markup-based pipeline still works. This new engine
is an additional, cleaner API.

## Examples

See `examples/engine_example.py`.
