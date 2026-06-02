#!/usr/bin/env python3
"""Export the compiled story agent graph to Mermaid (.mmd) and PNG."""

from __future__ import annotations

import argparse
import base64
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from urllib.error import URLError
from urllib.request import urlopen

DEFAULT_OUT_DIR = ROOT / "docs"


def _write_png_via_mermaid_ink(mermaid: str, png_path: Path) -> None:
    """Fallback when langgraph's draw_mermaid_png API is unavailable or times out."""
    encoded = base64.urlsafe_b64encode(mermaid.encode("utf-8")).decode("ascii")
    encoded += "=" * ((4 - len(encoded) % 4) % 4)
    url = f"https://mermaid.ink/img/{encoded}?type=png&bgColor=white"
    try:
        with urlopen(url, timeout=30) as resp:
            png_path.write_bytes(resp.read())
    except URLError as e:
        raise RuntimeError(f"mermaid.ink render failed: {e}") from e


def _write_png(drawable, mermaid: str, png_path: Path) -> None:
    draw_png = getattr(drawable, "draw_mermaid_png", None)
    if draw_png is None:
        _write_png_via_mermaid_ink(mermaid, png_path)
        return

    try:
        result = draw_png()
    except TypeError:
        draw_png(output_file_path=str(png_path))
        if png_path.exists():
            return
        raise

    if isinstance(result, (bytes, bytearray)):
        png_path.write_bytes(result)
        return
    if png_path.exists():
        return

    _write_png_via_mermaid_ink(mermaid, png_path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Mermaid and PNG from the story agent graph.")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=DEFAULT_OUT_DIR,
        help=f"Output directory (default: {DEFAULT_OUT_DIR})",
    )
    args = parser.parse_args()

    from agent.agent import compile_graph

    compiled = compile_graph()
    drawable = compiled.get_graph()
    mermaid = drawable.draw_mermaid()

    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    mmd_path = out_dir / "graph.mmd"
    png_path = out_dir / "graph.png"

    mmd_path.write_text(mermaid, encoding="utf-8")
    print(f"Wrote {mmd_path}")

    try:
        _write_png(drawable, mermaid, png_path)
    except Exception as e:
        print(f"PNG export failed: {e}", file=sys.stderr)
        print(f"Mermaid source is still at {mmd_path}", file=sys.stderr)
        return 1

    print(f"Wrote {png_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
