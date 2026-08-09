"""
Review and validation system for mathwriter datasets.

Validates generated markup, renders to PDF, and produces a quality report.
Can also use Ollama to review the rendered output for pedagogical quality.

Usage:
    python review_dataset.py --input datasets/generated/ --render
    python review_dataset.py --input datasets/generated/dp_fibonacci.txt --render --llm-review
"""

import json, os, sys, argparse, subprocess, time, re
from pathlib import Path
from collections import Counter

HERE = Path(__file__).parent


def validate_file(filepath):
    """Run the mathwriter validator on a file. Returns (ok, issues)."""
    sys.path.insert(0, str(HERE))
    from validate import validate

    with open(filepath) as f:
        text = f.read()

    issues = validate(text)
    errors = [i for i in issues if i[0] == 'error']
    warns = [i for i in issues if i[0] == 'warn']
    ok = len(errors) == 0
    return ok, errors, warns


def render_file(filepath, output_dir=None):
    """Render a markup file to PDF. Returns (ok, pdf_path, dropped_chars)."""
    sys.path.insert(0, str(HERE))
    import render as R

    with open(filepath) as f:
        text = f.read()

    name = os.path.splitext(os.path.basename(filepath))[0]
    if output_dir:
        out_dir = output_dir
    else:
        out_dir = os.path.join(HERE, 'output', 'reviewed')
    os.makedirs(out_dir, exist_ok=True)

    out_pdf = os.path.join(out_dir, f'{name}.pdf')

    try:
        R.clear_dropped_chars()
        pages = R.render_pages(text)
        pages[0].save(out_pdf, 'PDF', resolution=200.0,
                      save_all=True, append_images=pages[1:])
        dropped = R.get_dropped_chars()
        return True, out_pdf, dropped, len(pages)
    except Exception as e:
        return False, str(e), {}, 0


def count_diagrams(text):
    """Count diagram types in the markup."""
    diagrams = re.findall(r'\[G\](\{.*?\})\[/G\]', text)
    types = Counter()
    for d in diagrams:
        try:
            spec = json.loads(d)
            types[spec.get('type', 'unknown')] += 1
        except:
            types['malformed'] += 1
    return types


def analyze_content(text):
    """Analyze the content quality metrics."""
    lines = text.split('\n')
    non_empty = [l for l in lines if l.strip()]

    metrics = {
        'total_lines': len(lines),
        'non_empty_lines': len(non_empty),
        'total_chars': len(text),
        'headers': len([l for l in non_empty if l.strip().startswith('~~')]),
        'boxed': text.count('[B]'),
        'fractions': text.count('[F]'),
        'matrices': text.count('[M]'),
        'sums': text.count('[S]'),
        'diagrams': len(re.findall(r'\[G\]', text)),
        'diagram_types': count_diagrams(text),
    }
    return metrics


def llm_review(filepath, model="glm-5.2:cloud"):
    """Use Ollama to review the generated content for pedagogical quality."""
    with open(filepath) as f:
        text = f.read()

    # Truncate if too long
    if len(text) > 6000:
        text = text[:6000] + "\n... [truncated]"

    review_prompt = f"""You are reviewing a computer science teaching note that was auto-generated
in a special markup format for handwritten rendering. Review it for:

1. **Pedagogical quality**: Is the explanation clear? Does it build intuition?
2. **Correctness**: Are the algorithms, recurrences, and examples correct?
3. **Completeness**: Does it cover the topic adequately?
4. **Diagram quality**: Are the diagrams well-chosen and correctly specified?
5. **Markup issues**: Any obvious formatting problems?

Here is the content:

{text}

Provide a concise review (5-8 bullet points) with a final rating: EXCELLENT / GOOD / NEEDS WORK / POOR.
Focus on actionable feedback."""

    import urllib.request, urllib.error

    url = "http://localhost:11434/api/generate"
    payload = {
        "model": model,
        "prompt": review_prompt,
        "stream": False,
        "options": {"num_predict": 1024, "temperature": 0.3}
    }
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode())
            return result.get("response", "No review generated")
    except Exception as e:
        return f"LLM review failed: {e}"


def review_all(input_dir, render=True, llm_review_flag=False, model="glm-5.2:cloud"):
    """Review all .txt files in a directory."""
    txt_files = sorted(Path(input_dir).glob('*.txt'))
    if not txt_files:
        print(f"No .txt files found in {input_dir}")
        return

    print(f"\n{'='*70}")
    print(f"REVIEWING {len(txt_files)} files from {input_dir}")
    print(f"{'='*70}")

    report = []
    total_ok = 0
    total_fail = 0

    for i, fp in enumerate(txt_files):
        name = fp.stem
        print(f"\n── [{i+1}/{len(txt_files)}] {name} ──")

        # 1. Validate
        ok, errors, warns = validate_file(str(fp))
        if ok:
            print(f"  ✓ Validation: PASSED ({len(warns)} warnings)")
        else:
            print(f"  ✗ Validation: {len(errors)} ERRORS, {len(warns)} warnings")
            for sev, msg in errors[:5]:
                print(f"    ERROR: {msg}")
            for sev, msg in warns[:3]:
                print(f"    WARN:  {msg}")

        # 2. Content analysis
        with open(fp) as f:
            text = f.read()
        metrics = analyze_content(text)
        print(f"  Content: {metrics['total_chars']} chars, {metrics['non_empty_lines']} lines, "
              f"{metrics['headers']} headers, {metrics['diagrams']} diagrams")
        if metrics['diagram_types']:
            print(f"  Diagram types: {dict(metrics['diagram_types'])}")

        # 3. Render
        render_ok = None
        if render:
            render_ok, pdf_path, dropped, pages = render_file(str(fp))
            if render_ok:
                print(f"  ✓ Render: {pages} pages → {pdf_path}")
                if dropped:
                    print(f"    Dropped chars: {dict(dropped)}")
            else:
                print(f"  ✗ Render FAILED: {pdf_path}")

        # 4. LLM review
        llm_result = None
        if llm_review_flag:
            print(f"  LLM review in progress...")
            llm_result = llm_review(str(fp), model=model)
            print(f"  LLM review:\n{llm_result}")

        entry = {
            'name': name,
            'validation_ok': ok,
            'errors': len(errors),
            'warnings': len(warns),
            'render_ok': render_ok,
            'metrics': metrics,
            'llm_review': llm_result,
        }
        report.append(entry)

        if ok:
            total_ok += 1
        else:
            total_fail += 1

    # Summary
    print(f"\n{'='*70}")
    print(f"SUMMARY: {total_ok} passed, {total_fail} failed out of {len(txt_files)}")
    print(f"{'='*70}")

    # Save report
    report_path = os.path.join(input_dir, 'review_report.json')
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    print(f"Report saved to {report_path}")

    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Review mathwriter dataset quality')
    parser.add_argument('--input', type=str, required=True,
                        help='Input file or directory of .txt files')
    parser.add_argument('--render', action='store_true',
                        help='Render each file to PDF for visual inspection')
    parser.add_argument('--llm-review', action='store_true',
                        help='Use LLM to review pedagogical quality')
    parser.add_argument('--model', type=str, default='glm-5.2:cloud',
                        help='Ollama model for LLM review')
    parser.add_argument('--output-dir', type=str, default=None,
                        help='Output directory for rendered PDFs')

    args = parser.parse_args()

    input_path = Path(args.input)
    if input_path.is_file():
        # Single file review
        print(f"Reviewing: {input_path}")
        ok, errors, warns = validate_file(str(input_path))
        print(f"Validation: {'PASSED' if ok else 'FAILED'}")
        for sev, msg in errors:
            print(f"  ERROR: {msg}")
        for sev, msg in warns:
            print(f"  WARN:  {msg}")

        with open(input_path) as f:
            text = f.read()
        metrics = analyze_content(text)
        print(f"\nContent metrics:")
        for k, v in metrics.items():
            if k != 'diagram_types':
                print(f"  {k}: {v}")
        if metrics['diagram_types']:
            print(f"  diagram_types: {dict(metrics['diagram_types'])}")

        if args.render:
            render_ok, pdf_path, dropped, pages = render_file(
                str(input_path), output_dir=args.output_dir)
            if render_ok:
                print(f"\nRender: {pages} pages → {pdf_path}")
                if dropped:
                    print(f"Dropped chars: {dict(dropped)}")
            else:
                print(f"\nRender FAILED: {pdf_path}")

        if args.llm_review:
            print(f"\nLLM Review:\n{llm_review(str(input_path), model=args.model)}")

    elif input_path.is_dir():
        review_all(str(input_path), render=args.render,
                   llm_review_flag=args.llm_review, model=args.model)
    else:
        print(f"Input not found: {args.input}")
        sys.exit(1)
