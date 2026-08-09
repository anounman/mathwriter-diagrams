"""
Stress test for the modular engine.

This script renders a single page containing every scene-graph primitive
and every available plugin type. It outputs both PNG (PIL) and SVG and
reports whether each element rendered without error.
"""

import sys, os, json, traceback
from pathlib import Path

sys.path.insert(0, '/home/ankush/mathwriter')
os.chdir('/home/ankush/mathwriter')

from mathwriter import create_engine, Engine, Style
from mathwriter.scene import (
    Group, Transform, Line, Rect, Circle, Ellipse, Polygon, Polyline, Text, Path
)
from mathwriter.renderers import get_renderer


OUT_DIR = 'output/reviewed'
if not os.path.isdir(OUT_DIR):
    os.makedirs(OUT_DIR, exist_ok=True)


def draw_primitives_test(page):
    """Add raw scene-graph primitives to a page."""
    x = 120
    y = 200
    primitives = Group(transform=Transform(x=x, y=y))

    # line
    primitives.add(Line(0, 0, 200, 0, style=Style(stroke=(15, 70, 180), stroke_width=3)))
    # rect
    primitives.add(Rect(220, -20, 120, 60, style=Style(stroke=(15, 70, 180), stroke_width=2)))
    # circle
    primitives.add(Circle(430, 10, 35, style=Style(stroke=(15, 70, 180), stroke_width=2)))
    # ellipse
    primitives.add(Ellipse(560, 10, 50, 25, style=Style(stroke=(15, 70, 180), stroke_width=2)))
    # polygon
    primitives.add(Polygon(
        [(0, 100), (60, 80), (100, 140), (40, 160)],
        style=Style(stroke=(15, 70, 180), stroke_width=2),
    ))
    # polyline
    primitives.add(Polyline(
        [(140, 100), (180, 80), (220, 140), (260, 90)],
        style=Style(stroke=(15, 70, 180), stroke_width=2),
    ))
    # text
    primitives.add(Text(0, 200, "Raw primitives test", style=Style(stroke=(15, 70, 180), font_size=28)))
    # path
    primitives.add(Path("M 300 100 Q 350 50 400 100 T 500 100", style=Style(stroke=(15, 70, 180), stroke_width=2)))

    page.draw({"type": "group", "children": primitives})


def main():
    engine = create_engine()
    results = {
        "engine_plugins": engine.plugins(),
        "primitives": {},
        "backends": {},
        "errors": [],
    }

    page = engine.new_page()

    # 1. Raw primitives through the generic group/text plugins
    try:
        draw_primitives_test(page)
        results["primitives"]["raw_scene_graph"] = "ok"
    except Exception as e:
        results["primitives"]["raw_scene_graph"] = f"error: {e}"
        results["errors"].append(traceback.format_exc())

    # 2. Every available plugin type
    plugin_specs = {
        "text": {"type": "text", "text": "Hello from text plugin", "x": 120, "y": 500},
        "logic_gate": {
            "type": "logic_gate", "gate": "AND", "inputs": ["A", "B"], "output": "Y",
            "truth_table": [["A", "B", "Y"], ["0", "0", "0"], ["1", "1", "1"]],
            "x": 120, "y": 600,
        },
    }
    for name, spec in plugin_specs.items():
        if not engine.has_plugin(name):
            results["primitives"][name] = "skipped: plugin not registered"
            continue
        try:
            page.draw(spec)
            results["primitives"][name] = "ok"
        except Exception as e:
            results["primitives"][name] = f"error: {e}"
            results["errors"].append(traceback.format_exc())

    # 3. Render full stress-test page
    try:
        pil_img = page.render("pil")
        pil_path = os.path.join(OUT_DIR, 'stress_test_engine.png')
        pil_img.save(pil_path)
        results["backends"]["pil"] = {"status": "ok", "path": pil_path, "size": pil_img.size}
    except Exception as e:
        results["backends"]["pil"] = {"status": "error", "error": str(e)}
        results["errors"].append(traceback.format_exc())

    try:
        svg = page.render("svg")
        svg_path = os.path.join(OUT_DIR, 'stress_test_engine.svg')
        with open(svg_path, 'w') as f:
            f.write(svg)
        results["backends"]["svg"] = {"status": "ok", "path": svg_path, "length": len(svg)}
    except Exception as e:
        results["backends"]["svg"] = {"status": "error", "error": str(e)}
        results["errors"].append(traceback.format_exc())

    # 4. Summary report
    report_path = os.path.join(OUT_DIR, 'stress_test_engine_report.json')
    with open(report_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(json.dumps(results, indent=2))
    if results["errors"]:
        print(f"\n{len(results['errors'])} errors recorded")
    else:
        print("\nNo errors")


if __name__ == "__main__":
    main()
