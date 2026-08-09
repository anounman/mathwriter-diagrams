import sys
from pathlib import Path
from render import render_pages


def main():
    if len(sys.argv) < 3:
        print("usage: python render.py input.txt output.pdf")
        print("       python render.py --png input.txt output.png")
        sys.exit(1)

    if sys.argv[1] == '--png':
        out_path = Path(sys.argv[3])
        text = Path(sys.argv[2]).read_text()
        pages = render_pages(text)
        if not pages:
            print("no pages rendered")
            sys.exit(1)
        pages[0].save(str(out_path))
        print('saved', out_path)
    else:
        from render import render_to_pdf
        in_path = Path(sys.argv[1])
        out_path = Path(sys.argv[2])
        render_to_pdf(in_path.read_text(), str(out_path))
        print('saved', out_path)


if __name__ == '__main__':
    main()
