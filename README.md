# Mathwriter Diagrams

Hand-drawn, procedurally generated CS teaching diagrams. Text markup in, PDF/PNG image out.

## Quick start

```bash
# 1. Install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Render a single dataset entry to PDF or PNG
python render_cli.py datasets/generated/logic_gate_and.txt output/and.pdf
python render_cli.py --png datasets/generated/logic_gate_and.txt output/and.png

# 3. Render preview PNGs next to every source file
python render_previews.py

# 4. Run validation + render all datasets
python review_dataset.py
```

## Repository layout

```
mathwriter/
├── datasets/generated/          # source markup files (*.txt)
│   ├── logic_gate_and.txt       # example: AND gate
│   └── logic_gate_and.page1.png # rendered preview image
├── datasets/draw_generated/     # [DRAW] low-level vector examples
├── datasets/reviewed/           # reviewed / curated entries
├── output/reviewed/             # rendered PDFs and PNGs
├── glyphs/                      # handwriting glyph images used for text
├── diagrams.py                  # fixed [G] diagram builders (trees, arrays, graphs, DP, ...)
├── diagrams_extra.py            # fixed [G] builders for gates, ER, relational, big data
├── render.py                    # tokenizer + dispatcher + PDF renderer
├── validate.py                  # markup validator
├── generate_dataset.py          # generator for classic CS topics
├── generate_image_mode_dataset.py  # generator for gates / ER / big data
├── DRAW_REFERENCE.md            # API for [DRAW] low-level primitives
└── MARKUP.md                    # full markup tag reference
```

## Two markup modes

### 1. Fixed high-level diagrams — `[G]...[/G]`

Use JSON specs. Fast and stable for known diagram types.

```text
[G]{
  "type": "logic_gate",
  "gate": "AND",
  "inputs": ["A", "B"],
  "output": "Y",
  "truth_table": [
    ["A", "B", "Y"],
    ["0", "0", "0"],
    ["0", "1", "0"],
    ["1", "0", "0"],
    ["1", "1", "1"]
  ]
}[/G]
```

Supported `[G]` types include:
- Logic: `logic_gate` (AND, OR, NOT, XOR, NAND, NOR), `logic_circuit` (half/full adder, SR latch, ...)
- Databases: `er_diagram`, `relational_schema`, `sql_join_venn` (INNER, LEFT, RIGHT, FULL)
- Big data: `mapreduce`, `cap_theorem`, `database_sharding`, `consistent_hashing`, `hdfs_architecture`, `kafka_pipeline`, `spark_lineage`
- Classic CS: `tree`, `array`, `dp_table`, `linked_list`, `graph`, `stack`, `queue`, `memory_layout`, `pointer_diagram`, `sorting`, `recursion`, `hashing`

### 2. Low-level vector drawing — `[DRAW]...[/DRAW]`

Use when you need an arbitrary shape not covered by `[G]`.

```text
[DRAW]
LINE 50,50 150,50 width=2
CIRCLE 200,50 radius=30
RECT 50,120 120,170
TEXT 75,145 "box"
[/DRAW]
```

See `DRAW_REFERENCE.md` for the full primitive list.

## How to add a new topic

1. Create a `.txt` file in `datasets/generated/` with a `~~Title~~`, prose, and `[G]` or `[DRAW]` blocks.
2. Run `python review_dataset.py` to validate and render it to `output/reviewed/`.
3. Generate a PNG preview:
   ```bash
   python render_cli.py --png your_file.txt your_file.png
   # or regenerate all previews:
   python render_previews.py
   ```
4. Commit both the `.txt` source and the rendered `.pdf`/`.png` outputs.

## Regenerating all previews

```bash
python render_previews.py
```

This writes one `.page{N}.png` next to every `datasets/generated/*.txt` source file.

## Testing

```bash
python test_validate.py      # validator unit tests
python /tmp/hermes-verify-image-mode.py  # image-mode ad-hoc verification
```

## Model / environment

- Python 3.10+
- No API keys required; all rendering is local PIL.
- Optional Ollama generators use `glm-5.2:cloud` at `http://localhost:11434`.

## Public repo

`https://github.com/anounman/mathwriter-diagrams`
