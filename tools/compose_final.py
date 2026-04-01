#!/usr/bin/env python3
"""
Compose final SVG by replacing illustration placeholders with generated images.

Usage:
    python tools/compose_final.py --blueprint .tmp/svg/topic_blueprint.svg --illustrations .tmp/illustrations/ --output .tmp/svg/
"""

import argparse
import base64
import json
import logging
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TMP_DIR = PROJECT_ROOT / ".tmp" / "svg"


def compose(blueprint_path: str, illustrations_dir: str, images_dir: str = None,
            credits: str = None) -> str:
    """Replace placeholders in SVG with base64-encoded illustrations."""

    tree = ET.parse(blueprint_path)
    root = tree.getroot()
    ns = "http://www.w3.org/2000/svg"
    ET.register_namespace("", ns)

    # Find illustration files
    illust_dir = Path(illustrations_dir)
    illust_map = {}
    for f in illust_dir.glob("*_section-*.png"):
        # Extract section number from filename
        match = re.search(r"section-(\d+)", f.name)
        if match:
            illust_map[int(match.group(1))] = f

    replacements = 0

    # Find all placeholder rects and replace with images
    for rect in list(root.iter(f"{{{ns}}}rect")):
        section_attr = rect.get("data-section")
        illustration_attr = rect.get("data-illustration")

        if illustration_attr and section_attr:
            section_num = int(section_attr)
            if section_num in illust_map:
                img_path = illust_map[section_num]
                img_b64 = base64.b64encode(img_path.read_bytes()).decode()

                # Get position and size from the rect
                x = rect.get("x", "0")
                y = rect.get("y", "0")
                w = rect.get("width", "100")
                h = rect.get("height", "100")

                # Create image element
                img_el = ET.SubElement(rect.getparent() if hasattr(rect, 'getparent') else root, f"{{{ns}}}image")
                img_el.set("x", x)
                img_el.set("y", y)
                img_el.set("width", w)
                img_el.set("height", h)
                img_el.set("href", f"data:image/png;base64,{img_b64}")
                img_el.set("preserveAspectRatio", "xMidYMid meet")

                # Remove the placeholder rect
                parent = root
                for g in root.iter():
                    if rect in list(g):
                        parent = g
                        break
                try:
                    parent.remove(rect)
                except ValueError:
                    pass

                # Also remove the [illustration] text label if present
                for text_el in list(parent.iter(f"{{{ns}}}text")):
                    if text_el.text and "[illustration]" in text_el.text:
                        try:
                            parent.remove(text_el)
                        except ValueError:
                            pass

                replacements += 1
                logger.info("Replaced placeholder for section %d with %s", section_num, img_path.name)

    # Update credits if provided
    if credits:
        for text_el in root.iter(f"{{{ns}}}text"):
            if text_el.text and "@YourChannel" in text_el.text:
                text_el.text = credits

    logger.info("Replaced %d illustration placeholders.", replacements)

    # Convert back to string
    return ET.tostring(root, encoding="unicode", xml_declaration=True)


def main():
    parser = argparse.ArgumentParser(description="Compose final SVG with illustrations")
    parser.add_argument("--blueprint", required=True, help="Path to SVG blueprint")
    parser.add_argument("--illustrations", default=".tmp/illustrations/", help="Illustrations directory")
    parser.add_argument("--images", default=None, help="Reference images directory (logos, icons)")
    parser.add_argument("--credits", default=None, help="Credits text (e.g., @YourChannel)")
    parser.add_argument("--output", default=None, help="Output directory")
    args = parser.parse_args()

    blueprint = Path(args.blueprint)
    if not blueprint.exists():
        logger.error("Blueprint not found: %s", args.blueprint)
        sys.exit(1)

    svg_content = compose(
        str(blueprint),
        args.illustrations,
        args.images,
        args.credits,
    )

    # Determine output path
    slug = blueprint.stem.replace("_blueprint", "")
    out_dir = Path(args.output) if args.output else TMP_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{slug}_final.svg"
    out_path.write_text(svg_content)

    logger.info("Final SVG saved to: %s", out_path)
    print(json.dumps({"output_path": str(out_path)}))


if __name__ == "__main__":
    main()
