#!/usr/bin/env python3
"""
Generate rich hero illustrations for each diagram segment using Gemini Flash.
Each segment gets a full, detailed illustration — not a tiny icon.

Usage:
    python tools/generate_diagram.py --segments .tmp/segments/topic_segments.json --style notebook
    python tools/generate_diagram.py --segments .tmp/segments/topic_segments.json --style dark --section 3
"""

import argparse
import json
import logging
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODEL = "gemini-2.5-flash-image"

STYLE_PROMPTS = {
    "notebook": """Generate a detailed hand-drawn sketch illustration in a notebook doodle style.

Style rules:
- Hand-drawn with ink pen strokes on off-white/cream paper background
- Warm, approachable aesthetic like a personal notebook sketch
- Use soft blue (#6CB4EE) and warm orange (#E8A848) as accent colors
- Include relevant icons, diagrams, and visual metaphors for the concept
- Slightly whimsical, organic hand-drawn quality — NOT computer-generated looking
- Rich detail — include small annotations, arrows, labels within the illustration
- The illustration should visually EXPLAIN the concept, not just decorate
- NO large blocks of paragraph text — visual storytelling with minimal labels
- Clean composition that works at roughly 500x400 pixels in a larger layout""",

    "dark": """Generate a detailed technical illustration in a dark blueprint style.

Style rules:
- Dark navy/charcoal background (#0D1B2A)
- Cyan (#00D4FF) and white line art, neon glow effects
- Technical, precise aesthetic — like a blueprint or system diagram
- Circuit board / neural network decorative elements
- Sharp clean lines, geometric shapes
- Include relevant technical diagrams and visual metaphors
- Rich detail with annotations and connection lines
- Clean composition that works at roughly 500x400 pixels""",

    "mono": """Generate a detailed minimalist illustration in clean monochrome style.

Style rules:
- Pure white background
- Black ink strokes only, with soft blue (#6CB4EE) as single accent
- Clean, professional, minimal aesthetic
- Simple line drawings with clear visual hierarchy
- Include relevant diagrams and visual metaphors
- Generous whitespace, uncluttered composition
- Clean composition that works at roughly 500x400 pixels""",
}


def load_api_key() -> str:
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("GEMINI_API_KEY=") and not line.endswith("="):
                return line.split("=", 1)[1].strip()
    key = os.environ.get("GEMINI_API_KEY", "")
    if not key:
        logger.error("GEMINI_API_KEY not found.")
        sys.exit(1)
    return key


def generate_one(client, segment: dict, style_key: str, output_dir: Path, slug: str) -> dict:
    """Generate one hero illustration for a segment."""
    from google.genai import types

    index = segment["index"]
    title = segment.get("title", f"Section {index}")
    content = segment.get("content", "")
    hint = segment.get("illustration_hint", title)

    prompt = f"""{STYLE_PROMPTS[style_key]}

SUBJECT: {title}
CONTEXT: {content[:300]}
VISUAL FOCUS: Create a rich illustration that visually explains "{title}".
Include relevant icons, mini-diagrams, arrows, and visual metaphors that help someone understand this concept at a glance. The illustration should tell a visual story about {hint}."""

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
            ),
        )

        for part in response.candidates[0].content.parts:
            if part.inline_data:
                img_path = output_dir / f"{slug}_section-{index}.png"
                img_path.write_bytes(part.inline_data.data)
                logger.info("Section %d (%s): %d bytes", index, title, len(part.inline_data.data))
                return {"section": index, "title": title, "path": str(img_path), "status": "success"}

        return {"section": index, "title": title, "status": "no_image"}
    except Exception as e:
        logger.error("Section %d failed: %s", index, e)
        return {"section": index, "title": title, "status": "error", "error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Generate hero illustrations via Gemini")
    parser.add_argument("--segments", required=True, help="Path to segments JSON")
    parser.add_argument("--style", default="notebook", choices=list(STYLE_PROMPTS.keys()))
    parser.add_argument("--output", default=".tmp/illustrations/", help="Output directory")
    parser.add_argument("--section", type=int, default=None, help="Generate only this section")
    parser.add_argument("--max-parallel", type=int, default=2, help="Max parallel API calls")
    args = parser.parse_args()

    segments_data = json.loads(Path(args.segments).read_text())
    slug = segments_data.get("slug", "output")
    segments = segments_data.get("segments", [])

    if args.section:
        segments = [s for s in segments if s["index"] == args.section]

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    api_key = load_api_key()
    from google import genai
    client = genai.Client(api_key=api_key)

    results = []
    with ThreadPoolExecutor(max_workers=args.max_parallel) as executor:
        futures = {
            executor.submit(generate_one, client, seg, args.style, output_dir, slug): seg
            for seg in segments
        }
        for future in as_completed(futures):
            results.append(future.result())

    results.sort(key=lambda r: r["section"])
    success = sum(1 for r in results if r["status"] == "success")
    logger.info("Generated %d/%d illustrations", success, len(results))
    print(json.dumps({"slug": slug, "style": args.style, "success": success, "total": len(results), "illustrations": results}, indent=2))


if __name__ == "__main__":
    main()
