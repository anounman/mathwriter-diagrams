"""
Example: using the new modular engine directly.
"""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from mathwriter import create_engine

engine = create_engine()
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
pil_img.save("output/reviewed/engine_example.png")
print("PIL output: output/reviewed/engine_example.png")

svg = page.render("svg")
with open("output/reviewed/engine_example.svg", "w") as f:
    f.write(svg)
print("SVG output: output/reviewed/engine_example.svg")
