# Modular Engine Stress Test Review

Date: 2026-08-09
Branch: `feature/extended-dataset`
Commit tested: Phase 1 modular engine

## How the test was run

```bash
cd /home/ankush/mathwriter
venv/bin/python3 tests/stress_test_engine.py
```

Output files:
- `output/reviewed/stress_test_engine.png` — PIL render
- `output/reviewed/stress_test_engine.svg` — SVG render
- `output/reviewed/stress_test_engine_report.json` — machine report

## What the test covers

1. Every scene-graph primitive:
   - `Line`, `Rect`, `Circle`, `Ellipse`, `Polygon`, `Polyline`, `Text`, `Path`
2. Every registered plugin:
   - `text`, `image`, `group`, `logic_gate`
3. Both render backends:
   - `PIL` (raster PNG)
   - `SVG` (vector)

## Machine report (summary)

```json
{
  "engine_plugins": ["text", "image", "group", "logic_gate"],
  "primitives": {
    "raw_scene_graph": "ok",
    "text": "ok",
    "logic_gate": "ok"
  },
  "backends": {
    "pil": {"status": "ok", "path": "output/reviewed/stress_test_engine.png", "size": [1654, 2339]},
    "svg": {"status": "ok", "path": "output/reviewed/stress_test_engine.svg", "length": 4472}
  },
  "errors": []
}
```

**Status: zero crashes, zero exceptions.**

## Manual inspection findings

### What works
- All primitives are emitted to both backends.
- The AND gate shape is clean (no internal X artifact).
- SVG output is valid and contains all expected elements.
- PIL output is the correct page size (1654×2339).

### What does NOT work yet (expected for Phase 1)
1. **No real layout engine**
   - Blocks are stacked by simple bounding-box height.
   - Text height estimation is based on font size, not actual glyph metrics.
   - Result: primitives, text plugin block, and AND gate all overlap in the stress test image.

2. **No real handwriting text**
   - `PILRenderer` falls back to `PIL.ImageFont` system font.
   - The existing `glyphs/` asset pipeline has been extracted to `mathwriter/glyphs.py` but is not yet wired into the new renderer.

3. **No anti-aliased sketchy strokes in SVG**
   - SVG lines are clean vectors, not hand-drawn wobbly strokes.
   - The sketchy look from `aa_line` is PIL-only.

4. **Path primitive bounds are wrong**
   - `Path.bounds()` returns a hard-coded placeholder.
   - Does not break rendering, but layout will be incorrect for paths.

5. **Only one diagram plugin exists**
   - `logic_gate` is ported.
   - All other diagram types (trees, graphs, ER diagrams, relational schemas, big-data pipelines) are still in `diagrams.py` / `diagrams_extra.py` and not registered as plugins.

6. **No support for legacy `[G]` / `[DRAW]` markup in the new engine**
   - The old `render.py` still works.
   - A migration shim is needed if we want the new engine to consume old markup files.

7. **No text flow / wrapping / alignment**
   - Multi-line text, centered headings, inline math, and paragraph layout are not implemented.

8. **No PDF output in the new engine**
   - `Document.save_pdf()` is stubbed and untested.

## Gap analysis

| Capability | Old renderer | New engine | Gap |
|------------|--------------|------------|-----|
| Handwriting glyphs | Yes | No | Must wire `glyphs.py` into `PILRenderer` |
| `[G]` markup | Yes | No | Add parser + adapter to new `Engine` |
| `[DRAW]` markup | Yes | No | Re-implement or bridge `draw_engine.py` |
| Multi-page PDF | Yes | Partial | `Document.save_pdf()` stubbed |
| Layout / wrapping | Partial | None | Implement real block layout |
| All diagram types | Yes | 1/12+ | Port remaining plugins |
| SVG wobbly strokes | No | No | Integrate RoughJS or port wobble algorithm |
| HTTP server / CLI | CLI only | None | Add FastAPI + OpenAI-style API |

## Score

- **Crash-free rendering:** 10/10
- **Backend coverage:** 6/10 (PIL + SVG, no RoughJS, no Canvas, no PDF)
- **Diagram variety:** 2/10 (only `logic_gate`)
- **Layout quality:** 2/10 (overlap is unusable for real pages)
- **Handwriting fidelity:** 2/10 (system fonts instead of glyphs)
- **Overall Phase 1 readiness:** 4/10

Phase 1 proves the architecture works. Phase 2 needs to focus on layout and glyph integration before the engine can replace the old renderer.

## Recommended next steps

1. **Port the glyph renderer** to `PILRenderer._draw_text()`.
2. **Implement a real block layout engine** in `Page._build_scene()`:
   - measure text/diagram blocks
   - support vertical flow, centering, padding
   - handle page breaks for multi-page documents
3. **Port remaining diagram plugins** from `diagrams.py` and `diagrams_extra.py`.
4. **Add a markup adapter** so `[G]` and `[DRAW]` blocks route through the new engine.
5. **Implement `Document.save_pdf()`**.
6. **Add wobbly SVG strokes** via RoughJS or a custom SVG path filter.

## Conclusion

The modular engine successfully renders a page with all primitives and the first plugin through both PIL and SVG backends without errors. It is not yet a replacement for the old renderer because layout and handwriting text are missing. The architecture, however, is clean enough that other applications can already import it and register their own plugins.
