"""Render preview PNGs for every dataset source file."""
from pathlib import Path
from render import render_pages


def main():
    generated = Path('datasets/generated')
    for f in sorted(generated.glob('*.txt')):
        try:
            pages = render_pages(f.read_text())
            for i, page in enumerate(pages):
                out = f.with_suffix(f'.page{i+1}.png')
                page.save(str(out))
            print(f'{f.stem}: {len(pages)} page(s)')
        except Exception as e:
            print(f'ERR {f.name}: {e}')


if __name__ == '__main__':
    main()
