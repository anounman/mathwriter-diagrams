# Modular Mathwriter / Hand-Drawn Diagram Engine — Plan

## Goal

Turn the current monolithic `mathwriter` script bundle into a **reusable, pluggable engine** that other applications can import and drive like a model:

```python
from mathwriter import Engine, Page, HandStyle

engine = Engine(style=HandStyle.blue_pen, backend='pil')
page = engine.new_page()
page.write("~~Kirchhoff's Law~~")
page.draw({"type": "logic_circuit", ...})
page.write("The sum of currents into a node equals zero.")
page.render("pdf", "kirchhoff.pdf")
```

The same engine should be usable from Python, via a CLI, via a small HTTP server, and eventually via a JS/WASM build.

---

## What exists today

| Component | File(s) | State |
|-----------|---------|-------|
| Glyph backend | `glyphs/` + `render.py::load_glyphs()` | Works, but hard-coded path + recoloring |
| Text renderer | `render.py` (700+ lines) | Monolithic, mixed markup tokenizing + drawing |
| Fixed diagram types | `diagrams.py`, `diagrams_extra.py` | Function-based, return `(PIL.Image, baseline)` |
| Low-level draw engine | `draw_engine.py`, `[DRAW]` markup | Standalone, but not a first-class API |
| Markup parser | `render.py`, `validate.py` | Regex tokenizer; multi-letter tags added recently |
| Generators | `generate_dataset.py`, `generate_image_mode_dataset.py`, `generate_draw_dataset.py` | Ollama-driven, script-heavy |
| Output formats | PDF and PNG | PDF built manually page-by-page |

Current problems for external reuse:

1. **Global state** — font path, color constants, page size, dropped-char log are globals or module-level.
2. **No separation of concerns** — tokenizing, layout, drawing, and output are interleaved in `render.py`.
3. **Hard-coded backends** — PIL-only; SVG/Canvas paths are not produced.
4. **Implicit coordinate system** — diagrams return images that the renderer pastes; no shared scene graph.
5. **No public API** — using it requires importing `render_pages()` and passing markup strings.
6. **Plugin/diagram types are hard-wired** — adding a new diagram shape means editing `render.py` and `diagrams*.py`.

---

## Open-source alternatives researched

### 1. RoughJS (`roughjs` on npm, MIT)
- **What it does:** Hand-drawn SVG/Canvas primitives (line, curve, rect, circle, ellipse, polygon, path). Works in browser and Node.
- **Strengths:** Tiny, fast, deterministic sketchiness, excellent SVG output.
- **Weaknesses:** No text/handwriting engine; no high-level diagram types; JS-only.
- **How we can use it:** Make SVG the **primary scene format** and use RoughJS (or a Python port like `rough` 1.6) for the sketchy stroke generation. Then we only need to build a *layout and handwriting* layer on top.

### 2. Excalidraw (React / browser, MIT)
- **What it does:** Full whiteboard app with hand-drawn shapes, libraries, collaboration.
- **Strengths:** Rich shape library, proven UI, export to SVG/PNG.
- **Weaknesses:** Not a headless engine; deeply React/browser-oriented; hard to drive programmatically from Python.
- **How we can use it:** Borrow its **scene JSON** format for shape definitions; do not depend on it as a runtime.

### 3. tldraw (React SDK, MIT)
- **What it does:** Infinite canvas SDK, shapes, arrows, binding, persistence.
- **Strengths:** Modern architecture, shape definitions, bindings between shapes.
- **Weaknesses:** Same as Excalidraw — browser/React runtime required.
- **How we can use it:** Study its `Shape` / `Binding` abstraction for our own plugin API.

### 4. Manim (Python, MIT)
- **What it does:** Programmatic animation and math-diagram rendering.
- **Strengths:** Excellent for math notation, coordinate systems, camera/scene abstraction.
- **Weaknesses:** Heavy, video-first, not handwriting style, steep learning curve.
- **How we can use it:** Borrow the **Scene/Mobject/Camera** pattern for our engine core.

### 5. `handright` (Python)
- **What it does:** Renders text onto paper image by combining a font with hand-drawn distortion.
- **Weaknesses:** Raster-only, no diagram integration.

### 6. `matplotlib` + `xkcd` style
- **What it does:** Sketchy line style.
- **Weaknesses:** Not real handwriting; text is still fonts.

### Conclusion

There is **no single open-source project** that combines all three needs: (a) sketchy vector strokes, (b) real handwriting glyphs, (c) high-level diagram types, (d) headless pluggable engine. We should build the engine ourselves, but **use SVG as the intermediate scene graph** and optionally delegate sketchy strokes to RoughJS (or a Python rough port) instead of re-implementing wobble in PIL.

---

## Proposed architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Consumer App                              │
│         (CLI / Python import / HTTP server / JS binding)         │
└─────────────────────┬───────────────────────────────────────────┘
                      │  Engine.render(document, options)
┌─────────────────────▼───────────────────────────────────────────┐
│                     Mathwriter Engine                            │
│  - Document model (pages, blocks, style, metadata)               │
│  - Plugin registry                                               │
│  - Layout engine (flow text + inline math + floating diagrams)   │
│  - Style system (ink color, paper, roughness, glyph jitter)      │
└─────────────────────┬───────────────────────────────────────────┘
                      │  scene graph (SVG-like primitives + glyphs)
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
┌────────────┐  ┌────────────┐  ┌────────────┐
│  Renderer  │  │  Renderer  │  │  Renderer  │
│    PIL     │  │    SVG     │  │  RoughJS   │
│  (current) │  │  (vector)  │  │  (browser) │
└────────────┘  └────────────┘  └────────────┘
```

### Core abstractions

#### 1. `Document`
A list of `Page`s + metadata.

```python
class Document:
    pages: list[Page]
    style: Style
    title: str | None
```

#### 2. `Page`
A vertical list of `Block`s.

```python
class Page:
    blocks: list[Block]
    width: int
    height: int
    margin: tuple[int, int, int, int]
```

#### 3. `Block` (union of)
- `TextBlock(text: str, markup: bool = True)`
- `MathBlock(latex: str)`
- `DiagramBlock(spec: dict)`  # [G]
- `DrawingBlock(commands: list[DrawCommand])`  # [DRAW]
- `ImageBlock(src: str, caption: str | None)`
- `TableBlock(rows, cols)`

#### 4. `Style`
- `ink_color: tuple[int,int,int]`
- `paper: Paper | Color`
- `roughness: float`
- `handwriting_scale: float`
- `glyph_jitter: float`
- `line_width: float`

#### 5. `Plugin` interface
Every diagram type is a plugin:

```python
class DiagramPlugin(Protocol):
    name: str  # e.g. "logic_gate", "tree"

    def draw(self, spec: dict, ctx: RenderContext) -> Group:
        """Return a scene-graph Group (SVG-like) for the diagram."""
        ...
```

This removes the hard-coded `render_diagram()` dispatcher.

#### 6. `RenderContext`
Provides to plugins:
- `style`
- `glyphs`
- text measurement helpers
- low-level draw helpers (line, rect, circle, arrow, text, curve, path)
- coordinate/layout helpers (box packing, anchors)

#### 7. `Renderer` backends
- `PILRenderer` — current raster output, useful for PDF pages.
- `SVGRenderer` — primary vector target, uses RoughJS-style paths.
- `CanvasRenderer` — for browser preview.

### Plugin registry example

```python
engine = Engine()
engine.register(LogicGatePlugin())
engine.register(ERDiagramPlugin())
engine.register(TreeDiagramPlugin())
engine.register(CircuitPlugin())
engine.register(MapReducePlugin())
# third-party apps can register their own
engine.register(MyCustomPlugin())
```

---

## Recommended migration plan

### Phase 0: Stabilize current codebase (now)
- Keep the current `main` branch working for your dataset generation.
- Add tests for every existing diagram type so we can refactor safely.
- Freeze `[DRAW]` engine as the low-level primitive spec.

### Phase 1: Extract the scene graph
1. Define `SceneGraph` classes in a new `mathwriter/scene/` package:
   - `Point`, `Path`, `Line`, `Rect`, `Circle`, `Ellipse`, `Polygon`, `Text`, `Group`, `Image`.
   - Every element stores style and transforms.
2. Refactor `diagrams.py` + `diagrams_extra.py` so each `draw_*` function returns a `Group` instead of a PIL image.
3. Add `SVGRenderer` that walks the scene graph and emits SVG.
4. Make `PILRenderer` render the same scene graph to raster (reusing existing glyph compositing).
5. At this point the output is still the same, but the internals are backend-agnostic.

### Phase 2: Public Engine API
1. Create `mathwriter/engine.py` with `Engine`, `Document`, `Page`, `Style`.
2. Create `mathwriter/plugins/__init__.py` and move all diagram types into plugin modules:
   - `plugins/text.py`, `plugins/math.py`, `plugins/gates.py`, `plugins/er.py`, `plugins/bigdata.py`, `plugins/trees.py`, etc.
3. Replace the hard-coded `[G]` dispatcher with the plugin registry.
4. Add `render_cli.py`, `render_server.py` (FastAPI), and Python usage examples.

### Phase 3: Content format redesign
1. Keep `[G]` and `[DRAW]` as supported legacy formats.
2. Add a cleaner Python-native format:
   ```python
   doc = Document()
   doc.add_text("The AND gate")
   doc.add_diagram(type="logic_gate", gate="AND", inputs=["A","B"], output="Y")
   ```
3. Add Markdown extension so apps can write:
   ```markdown
   # The AND gate

   ![diagram:logic_gate](gate.json)

   Output is high only when all inputs are high.
   ```
4. Provide a JSON/YAML schema for documents so non-Python apps can generate content.

### Phase 4: Alternative backend integration
1. Add `RoughJSRenderer` by serializing the scene graph to SVG and running RoughJS path generation server-side via Node or via the Python `rough` port.
2. Add `ExcalidrawExporter` that writes tldraw/Excalidraw-compatible scene JSON.
3. Add `ManimSceneExporter` for animation output.

### Phase 5: Packaging
1. Split into a proper Python package: `pip install mathwriter`.
2. Ship optional extras:
   - `mathwriter[pil]` — PIL backend
   - `mathwriter[svg]` — SVG backend
   - `mathwriter[server]` — FastAPI server
   - `mathwriter[rough]` — rough sketchy strokes
3. Publish to PyPI.

---

## Concrete first steps (what to do next)

1. **Create a new branch `refactor/scene-graph`.**
2. **Write the scene graph classes** in `mathwriter/scene.py` (or `scene/` package).
3. **Pick one diagram type** (e.g., `logic_gate`) and rewrite it to return a `Group`.
4. **Add an `SVGRenderer`** that draws that single diagram to SVG.
5. **Add an `Engine` shell** that can render a one-page document with one `DiagramBlock`.
6. **Verify** both PIL and SVG output look equivalent.
7. **Port remaining diagram types** one by one.

This keeps the project functional throughout the refactor and gives you a real pluggable engine at the end.

---

## Open questions to decide

1. Do we want to keep PIL as the **primary** backend, or move to SVG-first and rasterize SVG to PDF/PNG?
2. Do we want to adopt RoughJS's SVG path generator, or keep the current home-grown wobble logic?
3. Should the handwriting layer remain glyph-based (current `glyphs/` directory) or train/render a neural handwriting model later?
4. Do we need animation output (Manim-style), or only static pages?
5. Should the engine expose an OpenAI-style `/v1/images/generations` HTTP API so other apps can call it easily?

---

## Files this plan adds/changes

New files:
- `mathwriter/engine.py`
- `mathwriter/scene.py`
- `mathwriter/plugins/__init__.py`
- `mathwriter/plugins/gates.py`
- `mathwriter/plugins/relational.py`
- `mathwriter/plugins/bigdata.py`
- `mathwriter/plugins/trees.py`
- `mathwriter/renderers/__init__.py`
- `mathwriter/renderers/pil.py`
- `mathwriter/renderers/svg.py`
- `mathwriter/server.py`

Changed files:
- `render.py` becomes a thin compatibility wrapper around `Engine` + `PILRenderer`.
- `diagrams.py` / `diagrams_extra.py` become the plugin implementations.
- `draw_engine.py` becomes the low-level scene-graph builder.

---

## Why this is better than alternatives

- **RoughJS only:** no handwriting text, no high-level diagrams.
- **Excalidraw/tldraw only:** browser-only, hard to automate.
- **Manim only:** not handwriting, too heavy.
- **Current mathwriter:** works but not reusable.
- **This plan:** keeps what mathwriter already does well (handwriting glyphs + procedural diagrams) and wraps it in a clean, backend-agnostic, pluggable engine that other apps can import or call over HTTP.
