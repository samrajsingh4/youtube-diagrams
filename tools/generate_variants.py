#!/usr/bin/env python3
"""
Generate 3 style variants of a final SVG by applying color transformations.

Usage:
    python tools/generate_variants.py --svg .tmp/svg/topic_final.svg --brand brand/brand-kit.md --output videos/001-topic/
"""

import argparse
import json
import logging
import re
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Variant color schemes
VARIANTS = {
    "v1-light": {
        "name": "Light",
        "bg": "#FAFAF8",
        "card_bg": "#FFFFFF",
        "text_primary": "#1A1A1A",
        "text_body": "#3D3D3D",
        "text_muted": "#7A7A7A",
        "accent_blue": "#6CB4EE",
        "accent_orange": "#E8A848",
        "accent_green": "#5CB85C",
        "accent_red": "#E85D5D",
        "accent_purple": "#B39DDB",
    },
    "v2-dark": {
        "name": "Dark",
        "bg": "#1A1D27",
        "card_bg": "#242836",
        "text_primary": "#E4E6ED",
        "text_body": "#B8BAC4",
        "text_muted": "#6B6E7B",
        "accent_blue": "#74B9FF",
        "accent_orange": "#FDCB6E",
        "accent_green": "#55EFC4",
        "accent_red": "#FF7675",
        "accent_purple": "#A29BFE",
    },
    "v3-warm": {
        "name": "Warm",
        "bg": "#F5F0E8",
        "card_bg": "#FFF9F0",
        "text_primary": "#2C2C2C",
        "text_body": "#555555",
        "text_muted": "#8B7E6A",
        "accent_blue": "#2D9CDB",
        "accent_orange": "#F2994A",
        "accent_green": "#27AE60",
        "accent_red": "#EB5757",
        "accent_purple": "#9B59B6",
    },
}

# Original brand colors to find and replace
ORIGINAL_COLORS = {
    "#FAFAF8": "bg",
    "#FFFFFF": "card_bg",
    "#1A1A1A": "text_primary",
    "#3D3D3D": "text_body",
    "#7A7A7A": "text_muted",
    "#6CB4EE": "accent_blue",
    "#E8A848": "accent_orange",
    "#5CB85C": "accent_green",
    "#E85D5D": "accent_red",
    "#B39DDB": "accent_purple",
}


def apply_variant(svg_content: str, variant: dict) -> str:
    """Apply a color variant to SVG content via string replacement."""
    result = svg_content

    # Also handle the dot grid and other hardcoded colors
    for original_hex, color_key in ORIGINAL_COLORS.items():
        if color_key in variant:
            # Case-insensitive replacement
            result = result.replace(original_hex, variant[color_key])
            result = result.replace(original_hex.lower(), variant[color_key])

    # Fix the dot grid color for dark mode
    if variant.get("bg", "").startswith("#1"):
        result = result.replace("#E0DDD6", "#2E3345")

    # Fix yellow note background for dark mode
    if variant.get("bg", "").startswith("#1"):
        result = result.replace("#FFF3CD", "#3D3520")
        result = result.replace("#E8C96B", "#8B7530")

    return result


def main():
    parser = argparse.ArgumentParser(description="Generate 3 style variants")
    parser.add_argument("--svg", required=True, help="Path to final SVG")
    parser.add_argument("--brand", default="brand/brand-kit.md", help="Path to brand kit")
    parser.add_argument("--output", required=True, help="Output directory")
    args = parser.parse_args()

    svg_path = Path(args.svg)
    if not svg_path.exists():
        logger.error("SVG not found: %s", args.svg)
        sys.exit(1)

    svg_content = svg_path.read_text()
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for variant_key, variant in VARIANTS.items():
        transformed = apply_variant(svg_content, variant)
        out_path = output_dir / f"diagram-{variant_key}.svg"
        out_path.write_text(transformed)
        logger.info("Generated %s variant: %s", variant["name"], out_path)
        results.append({
            "variant": variant_key,
            "name": variant["name"],
            "path": str(out_path),
        })

    print(json.dumps({"variants": results}, indent=2))


if __name__ == "__main__":
    main()
