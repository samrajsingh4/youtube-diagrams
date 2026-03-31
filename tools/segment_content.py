#!/usr/bin/env python3
"""
Segment enriched content into visual diagram sections.

Usage:
    python tools/segment_content.py --input .tmp/research/topic_enriched.json
"""

import argparse
import json
import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TMP_DIR = PROJECT_ROOT / ".tmp" / "segments"

# Visual type suggestions based on content patterns
VISUAL_TYPES = {
    "process": "flowchart",       # Steps, stages, pipelines
    "components": "explainer",    # Parts of a whole
    "comparison": "comparison",   # X vs Y, pros/cons
    "list": "numbered_list",      # Top N, tips, checklist
    "architecture": "architecture",  # System diagrams, data flows
}


def detect_visual_type(title: str, content: str) -> str:
    """Auto-detect the best visual layout type based on content."""
    text = (title + " " + content).lower()

    if any(w in text for w in ["step", "stage", "pipeline", "process", "flow", "how", "workflow"]):
        return "flowchart"
    if any(w in text for w in ["vs", "versus", "compared", "difference", "pros", "cons"]):
        return "comparison"
    if any(w in text for w in ["component", "part", "element", "consist", "made up"]):
        return "explainer"
    if any(w in text for w in ["architecture", "system", "layer", "stack", "infrastructure"]):
        return "architecture"
    if any(w in text for w in ["top", "best", "tip", "rule", "way"]):
        return "numbered_list"

    return "flowchart"  # Default


def segment_from_outline(enriched: dict) -> list[dict]:
    """Parse outline text into segments, enriched with research answers."""
    outline = enriched.get("original_outline", "")
    answers = enriched.get("enrichment", {}).get("answers", [])
    topic = enriched.get("topic", "")

    # Parse outline into sections (split on headers, numbers, or double newlines)
    lines = outline.strip().split("\n")
    sections = []
    current_section = {"title": "", "content": []}

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Detect section headers (markdown headers, numbered items, or ALL CAPS)
        is_header = (
            stripped.startswith("#") or
            stripped.startswith("- **") or
            (len(stripped) > 3 and stripped[0].isdigit() and stripped[1] in ".):") or
            (stripped.isupper() and len(stripped) > 5)
        )

        if is_header and current_section["content"]:
            sections.append(current_section)
            current_section = {"title": stripped.lstrip("#-* 0123456789.)").strip(), "content": []}
        elif is_header:
            current_section["title"] = stripped.lstrip("#-* 0123456789.)").strip()
        else:
            current_section["content"].append(stripped)

    if current_section["title"] or current_section["content"]:
        sections.append(current_section)

    # If no clear sections found, create segments from the outline as a whole
    if len(sections) <= 1:
        # Try to split into roughly equal chunks of 3-5
        all_lines = [l.strip() for l in lines if l.strip()]
        chunk_size = max(2, len(all_lines) // 4)
        sections = []
        for i in range(0, len(all_lines), chunk_size):
            chunk = all_lines[i:i + chunk_size]
            sections.append({
                "title": chunk[0].lstrip("#-* 0123456789.)").strip(),
                "content": chunk[1:] if len(chunk) > 1 else [chunk[0]],
            })

    # Build structured segments
    segments = []
    for i, sec in enumerate(sections[:8]):  # Cap at 8 sections
        content_text = " ".join(sec["content"])
        title = sec["title"] or f"Section {i + 1}"

        # Find matching enrichment answers
        key_points = []
        for ans in answers:
            answer_text = ans.get("answer", "").lower()
            if any(word in answer_text for word in title.lower().split()[:3]):
                # Extract a useful point from this answer
                sentences = ans["answer"].split(". ")
                for s in sentences[:2]:
                    if len(s) > 20:
                        key_points.append(s.strip().rstrip(".") + ".")
                        break

        segment = {
            "index": i + 1,
            "title": title,
            "content": content_text,
            "key_points": key_points[:3],  # Max 3 enriched points per section
            "visual_type": detect_visual_type(title, content_text),
            "illustration_hint": f"hand-drawn sketch illustration of {title.lower()} concept",
        }
        segments.append(segment)

    return segments


def main():
    parser = argparse.ArgumentParser(description="Segment enriched content into visual sections")
    parser.add_argument("--input", required=True, help="Path to enriched JSON file")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        logger.error("Input file not found: %s", args.input)
        sys.exit(1)

    enriched = json.loads(input_path.read_text())
    slug = enriched.get("slug", "unknown")
    topic = enriched.get("topic", "Unknown Topic")

    segments = segment_from_outline(enriched)

    output = {
        "topic": topic,
        "slug": slug,
        "segment_count": len(segments),
        "overall_visual_type": detect_visual_type(topic, enriched.get("original_outline", "")),
        "segments": segments,
    }

    TMP_DIR.mkdir(parents=True, exist_ok=True)
    out_path = TMP_DIR / f"{slug}_segments.json"
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    logger.info("Segmented into %d sections. Saved to: %s", len(segments), out_path)
    print(json.dumps({"output_path": str(out_path), "segment_count": len(segments)}, indent=2))


if __name__ == "__main__":
    main()
