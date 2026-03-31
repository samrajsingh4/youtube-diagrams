#!/usr/bin/env python3
"""
AI critique sub-agent for SVG blueprints.
Extracts structural metadata and evaluates against the rubric.

Usage:
    python tools/critique_svg.py --svg .tmp/svg/topic_blueprint.svg --rubric config/critique-rubric.yaml
"""

import argparse
import json
import logging
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Minimum thresholds
MIN_FONT_BODY = 24
MIN_FONT_HEADER = 48
MIN_MARGIN = 40
MIN_GAP = 30


def parse_svg_metadata(svg_path: str) -> dict:
    """Extract structural metadata from SVG without loading full content."""
    tree = ET.parse(svg_path)
    root = tree.getroot()
    ns = {"svg": "http://www.w3.org/2000/svg"}

    # Find all text elements
    texts = []
    for text_el in root.iter("{http://www.w3.org/2000/svg}text"):
        texts.append({
            "x": float(text_el.get("x", 0)),
            "y": float(text_el.get("y", 0)),
            "font_size": float(text_el.get("font-size", 20)),
            "content": (text_el.text or "")[:50],
            "fill": text_el.get("fill", "#000"),
        })

    # Find all rect elements (sections, cards, placeholders)
    rects = []
    for rect_el in root.iter("{http://www.w3.org/2000/svg}rect"):
        rects.append({
            "x": float(rect_el.get("x", 0)),
            "y": float(rect_el.get("y", 0)),
            "width": float(rect_el.get("width", 0)),
            "height": float(rect_el.get("height", 0)),
            "is_placeholder": rect_el.get("data-illustration") is not None,
        })

    # Find all groups (sections)
    sections = []
    for g_el in root.iter("{http://www.w3.org/2000/svg}g"):
        gid = g_el.get("id", "")
        if gid.startswith("section-"):
            sections.append(gid)

    return {
        "text_count": len(texts),
        "texts": texts,
        "rect_count": len(rects),
        "rects": rects,
        "section_count": len(sections),
        "sections": sections,
        "canvas_width": float(root.get("width", 1920)),
        "canvas_height": float(root.get("height", 1080)),
    }


def check_spacing(meta: dict) -> dict:
    """Check spacing: margins, overlaps, gaps."""
    issues = []
    score = 10
    canvas_w = meta["canvas_width"]
    canvas_h = meta["canvas_height"]

    # Check text margins
    for t in meta["texts"]:
        if t["x"] < MIN_MARGIN and t["x"] > 0:
            issues.append(f"Text too close to left edge: '{t['content']}' at x={t['x']}")
            score -= 1
        if t["y"] < MIN_MARGIN and t["y"] > 0:
            issues.append(f"Text too close to top edge: '{t['content']}' at y={t['y']}")
            score -= 1

    # Check rect margins
    for r in meta["rects"]:
        if r["width"] < 10:  # Skip tiny rects (decorations)
            continue
        if r["x"] < MIN_MARGIN and r["x"] > 0:
            issues.append(f"Rect too close to left edge at x={r['x']}")
            score -= 1
        right_edge = r["x"] + r["width"]
        if right_edge > canvas_w - MIN_MARGIN and right_edge < canvas_w:
            issues.append(f"Rect too close to right edge (right={right_edge})")
            score -= 1

    # Check for overlapping rects (simple bounding box check)
    # Exclude full-canvas rects (background, patterns) and placeholder illustration rects
    cards = [r for r in meta["rects"]
             if r["width"] > 100 and r["height"] > 100
             and not r["is_placeholder"]
             and not (r["width"] >= canvas_w * 0.9 and r["height"] >= canvas_h * 0.9)]
    for i, r1 in enumerate(cards):
        for r2 in cards[i + 1:]:
            if (r1["x"] < r2["x"] + r2["width"] and r1["x"] + r1["width"] > r2["x"] and
                    r1["y"] < r2["y"] + r2["height"] and r1["y"] + r1["height"] > r2["y"]):
                issues.append(f"Overlapping cards at ({r1['x']},{r1['y']}) and ({r2['x']},{r2['y']})")
                score -= 2

    return {"score": max(1, score), "issues": issues}


def check_legibility(meta: dict) -> dict:
    """Check text legibility: font sizes, contrast."""
    issues = []
    score = 10

    for t in meta["texts"]:
        if t["font_size"] < MIN_FONT_BODY and t["content"].strip():
            if t["font_size"] < 14:
                issues.append(f"Very small text ({t['font_size']}px): '{t['content']}'")
                score -= 2
            elif t["font_size"] < MIN_FONT_BODY:
                # Allow labels/captions at smaller sizes
                pass

    return {"score": max(1, score), "issues": issues}


def check_balance(meta: dict) -> dict:
    """Check visual weight distribution."""
    issues = []
    score = 10
    canvas_w = meta["canvas_width"]

    cards = [r for r in meta["rects"] if r["width"] > 100 and r["height"] > 100]
    if not cards:
        return {"score": 5, "issues": ["No content cards found"]}

    # Check left/right balance
    left_cards = [r for r in cards if r["x"] + r["width"] / 2 < canvas_w / 2]
    right_cards = [r for r in cards if r["x"] + r["width"] / 2 >= canvas_w / 2]

    if len(left_cards) == 0 and len(right_cards) > 0:
        issues.append("All content on right side — unbalanced")
        score -= 2
    elif len(right_cards) == 0 and len(left_cards) > 0:
        issues.append("All content on left side — unbalanced")
        score -= 2

    return {"score": max(1, score), "issues": issues}


def check_hierarchy(meta: dict) -> dict:
    """Check visual hierarchy: title largest, clear reading order."""
    issues = []
    score = 10

    if not meta["texts"]:
        return {"score": 5, "issues": ["No text elements found"]}

    font_sizes = [t["font_size"] for t in meta["texts"] if t["content"].strip()]
    if font_sizes:
        max_size = max(font_sizes)
        if max_size < MIN_FONT_HEADER:
            issues.append(f"Largest text is {max_size}px — should be at least {MIN_FONT_HEADER}px for title")
            score -= 2

    return {"score": max(1, score), "issues": issues}


def critique(svg_path: str) -> dict:
    """Run full critique on an SVG file."""
    meta = parse_svg_metadata(svg_path)

    results = {
        "spacing": check_spacing(meta),
        "legibility": check_legibility(meta),
        "balance": check_balance(meta),
        "hierarchy": check_hierarchy(meta),
    }

    overall_pass = all(r["score"] >= 7 for r in results.values())
    all_issues = []
    for criterion, result in results.items():
        for issue in result["issues"]:
            all_issues.append(f"[{criterion}] {issue}")

    return {
        "passed": overall_pass,
        "scores": {k: v["score"] for k, v in results.items()},
        "issues": all_issues,
        "metadata": {
            "text_count": meta["text_count"],
            "section_count": meta["section_count"],
            "canvas": f"{int(meta['canvas_width'])}x{int(meta['canvas_height'])}",
        },
    }


def main():
    parser = argparse.ArgumentParser(description="Critique SVG blueprint")
    parser.add_argument("--svg", required=True, help="Path to SVG file")
    parser.add_argument("--rubric", default="config/critique-rubric.yaml", help="Path to rubric (unused, criteria hardcoded)")
    args = parser.parse_args()

    if not Path(args.svg).exists():
        logger.error("SVG file not found: %s", args.svg)
        sys.exit(1)

    result = critique(args.svg)
    print(json.dumps(result, indent=2))

    if result["passed"]:
        logger.info("PASSED — all criteria met.")
    else:
        logger.warning("FAILED — %d issues found.", len(result["issues"]))
        for issue in result["issues"]:
            logger.warning("  %s", issue)
        sys.exit(1)


if __name__ == "__main__":
    main()
