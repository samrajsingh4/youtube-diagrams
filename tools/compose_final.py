#!/usr/bin/env python3
"""
Compose final SVG by replacing illustration placeholders with generated images.
Uses string-based replacement to avoid XML namespace issues.

Usage:
    python tools/compose_final.py --blueprint .tmp/svg/topic_blueprint.svg --illustrations .tmp/illustrations/
"""

import argparse
import base64
import json
import logging
import re
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TMP_DIR = PROJECT_ROOT / ".tmp" / "svg"


def compose(blueprint_path: str, illustrations_dir: str, credits: str = None) -> str:
    """Replace placeholder rects with base64 images using regex."""
    svg = Path(blueprint_path).read_text()

    # Find illustration files
    illust_dir = Path(illustrations_dir)
    illust_map = {}
    for f in illust_dir.glob("*_section-*.png"):
        match = re.search(r"section-(\d+)", f.name)
        if match:
            illust_map[int(match.group(1))] = f

    # Pattern to match placeholder rects with data-illustration attribute
    # Matches the full <rect ... data-illustration="..." data-section="N"/>  tag
    placeholder_pattern = re.compile(
        r'<rect\s+([^>]*?)data-illustration="([^"]*)"([^>]*?)data-section="(\d+)"([^>]*?)/?>',
        re.DOTALL,
    )

    replacements = 0

    def replace_placeholder(match):
        nonlocal replacements
        before_illust = match.group(1)
        illustration_hint = match.group(2)
        between = match.group(3)
        section_num = int(match.group(4))
        after_section = match.group(5)

        if section_num not in illust_map:
            logger.warning("No illustration found for section %d", section_num)
            return match.group(0)  # Keep original

        img_path = illust_map[section_num]
        img_b64 = base64.b64encode(img_path.read_bytes()).decode()

        # Extract position/size from the original rect attributes
        full_attrs = before_illust + between + after_section
        x = re.search(r'x="([^"]*)"', full_attrs)
        y = re.search(r'y="([^"]*)"', full_attrs)
        w = re.search(r'width="([^"]*)"', full_attrs)
        h = re.search(r'height="([^"]*)"', full_attrs)

        x_val = x.group(1) if x else "0"
        y_val = y.group(1) if y else "0"
        w_val = w.group(1) if w else "100"
        h_val = h.group(1) if h else "100"

        replacements += 1
        logger.info("Replaced section %d with %s", section_num, img_path.name)

        return (
            f'<image x="{x_val}" y="{y_val}" width="{w_val}" height="{h_val}" '
            f'href="data:image/png;base64,{img_b64}" '
            f'preserveAspectRatio="xMidYMid meet"/>'
        )

    svg = placeholder_pattern.sub(replace_placeholder, svg)

    # Also try the reverse attribute order (data-section before data-illustration)
    placeholder_pattern_rev = re.compile(
        r'<rect\s+([^>]*?)data-section="(\d+)"([^>]*?)data-illustration="([^"]*)"([^>]*?)/?>',
        re.DOTALL,
    )

    def replace_placeholder_rev(match):
        nonlocal replacements
        before = match.group(1)
        section_num = int(match.group(2))
        between = match.group(3)
        illustration_hint = match.group(4)
        after = match.group(5)

        if section_num not in illust_map:
            return match.group(0)

        img_path = illust_map[section_num]
        img_b64 = base64.b64encode(img_path.read_bytes()).decode()

        full_attrs = before + between + after
        x = re.search(r'x="([^"]*)"', full_attrs)
        y = re.search(r'y="([^"]*)"', full_attrs)
        w = re.search(r'width="([^"]*)"', full_attrs)
        h = re.search(r'height="([^"]*)"', full_attrs)

        x_val = x.group(1) if x else "0"
        y_val = y.group(1) if y else "0"
        w_val = w.group(1) if w else "100"
        h_val = h.group(1) if h else "100"

        replacements += 1
        logger.info("Replaced section %d with %s", section_num, img_path.name)

        return (
            f'<image x="{x_val}" y="{y_val}" width="{w_val}" height="{h_val}" '
            f'href="data:image/png;base64,{img_b64}" '
            f'preserveAspectRatio="xMidYMid meet"/>'
        )

    svg = placeholder_pattern_rev.sub(replace_placeholder_rev, svg)

    # Remove [illustration] text labels
    svg = re.sub(
        r'<text[^>]*>\[illustration\]</text>',
        '',
        svg,
    )

    # Update credits if provided
    if credits:
        svg = svg.replace("@YourChannel", credits)

    logger.info("Replaced %d illustration placeholders.", replacements)
    return svg


def main():
    parser = argparse.ArgumentParser(description="Compose final SVG with illustrations")
    parser.add_argument("--blueprint", required=True, help="Path to SVG blueprint")
    parser.add_argument("--illustrations", default=".tmp/illustrations/", help="Illustrations directory")
    parser.add_argument("--credits", default=None, help="Credits text")
    parser.add_argument("--output", default=None, help="Output directory")
    args = parser.parse_args()

    blueprint = Path(args.blueprint)
    if not blueprint.exists():
        logger.error("Blueprint not found: %s", args.blueprint)
        sys.exit(1)

    svg_content = compose(str(blueprint), args.illustrations, args.credits)

    slug = blueprint.stem.replace("_blueprint", "")
    out_dir = Path(args.output) if args.output else TMP_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{slug}_final.svg"
    out_path.write_text(svg_content)

    logger.info("Final SVG saved to: %s", out_path)
    print(json.dumps({"output_path": str(out_path)}))


if __name__ == "__main__":
    main()
