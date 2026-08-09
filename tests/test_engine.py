"""
Quick verification of the new modular engine.
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from mathwriter import create_engine


def main():
    engine = create_engine()
    assert engine.has_plugin("logic_gate"), "logic_gate plugin missing"

    page = engine.new_page()
    page.draw({
        "type": "logic_gate",
        "gate": "AND",
        "inputs": ["A", "B"],
        "output": "Y",
        "truth_table": [
            ["A", "B", "Y"],
            ["0", "0", "0"],
            ["0", "1", "0"],
            ["1", "0", "0"],
            ["1", "1", "1"],
        ],
    })

    pil_img = page.render("pil")
    assert pil_img.size == (1654, 2339), f"unexpected PIL size {pil_img.size}"

    svg = page.render("svg")
    assert "<svg" in svg and "</svg>" in svg, "invalid SVG output"
    assert "AND" in svg or "A" in svg, "SVG missing expected text"

    print("engine verification passed")


if __name__ == "__main__":
    main()
