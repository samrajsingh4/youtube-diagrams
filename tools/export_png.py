#!/usr/bin/env python3
"""
Export SVG to PNG at 1920x1080.

Usage:
    python tools/export_png.py --svg .tmp/svg/topic_final.svg --output videos/001-topic/
"""

import argparse
import logging
import subprocess
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
WIDTH = 1920
HEIGHT = 1080


def export_with_cairosvg(svg_path: str, output_path: str) -> bool:
    """Export using cairosvg Python library."""
    try:
        import cairosvg
        cairosvg.svg2png(
            url=svg_path,
            write_to=output_path,
            output_width=WIDTH,
            output_height=HEIGHT,
        )
        return True
    except ImportError:
        logger.warning("cairosvg not installed. Install with: pip install cairosvg")
        return False
    except Exception as e:
        logger.error("cairosvg export failed: %s", e)
        return False


def export_with_rsvg(svg_path: str, output_path: str) -> bool:
    """Export using rsvg-convert CLI."""
    try:
        result = subprocess.run(
            ["rsvg-convert", "-w", str(WIDTH), "-h", str(HEIGHT), svg_path, "-o", output_path],
            capture_output=True, text=True, timeout=30,
        )
        return result.returncode == 0
    except FileNotFoundError:
        logger.warning("rsvg-convert not found.")
        return False
    except subprocess.TimeoutExpired:
        logger.warning("rsvg-convert timed out.")
        return False


def main():
    parser = argparse.ArgumentParser(description="Export SVG to PNG")
    parser.add_argument("--svg", required=True, help="Path to SVG file")
    parser.add_argument("--output", required=True, help="Output directory or file path")
    parser.add_argument("--name", default="diagram.png", help="Output filename (if --output is a directory)")
    args = parser.parse_args()

    svg_path = Path(args.svg)
    if not svg_path.exists():
        logger.error("SVG not found: %s", args.svg)
        sys.exit(1)

    output = Path(args.output)
    if output.suffix != ".png":
        output.mkdir(parents=True, exist_ok=True)
        output = output / args.name

    # Copy source SVG to output dir
    if output.parent != svg_path.parent:
        source_copy = output.parent / "source.svg"
        source_copy.write_text(svg_path.read_text())

    # Try cairosvg first, fall back to rsvg-convert
    success = export_with_cairosvg(str(svg_path), str(output))
    if not success:
        success = export_with_rsvg(str(svg_path), str(output))

    if success:
        logger.info("PNG exported to: %s", output)
        print(f'{{"output_path": "{output}", "width": {WIDTH}, "height": {HEIGHT}}}')
    else:
        logger.error("Failed to export PNG. Install cairosvg: pip install cairosvg")
        sys.exit(1)


if __name__ == "__main__":
    main()
