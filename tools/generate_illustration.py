#!/usr/bin/env python3
"""
Generate hero illustrations for diagram sections using Gemini Flash (Nano Banana).

Usage:
    python tools/generate_illustration.py --segments .tmp/segments/topic_segments.json --brand brand/brand-kit.md --output .tmp/illustrations/
    python tools/generate_illustration.py --section 2 --segments ... --brand ... --output ...
"""

import argparse
import base64
import json
import logging
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Load API key from .env
def load_api_key() -> str:
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("GEMINI_API_KEY=") and not line.endswith("="):
                return line.split("=", 1)[1].strip()
    key = os.environ.get("GEMINI_API_KEY", "")
    if not key:
        logger.error("GEMINI_API_KEY not found in .env or environment.")
        sys.exit(1)
    return key


# Model: Gemini 2.5 Flash with native image generation (Nano Banana)
MODEL = "gemini-2.5-flash-image"

# Base prompt template for consistent hand-drawn style
BASE_PROMPT = """Generate a hand-drawn sketch illustration. Style requirements:
- Notebook doodle aesthetic with ink pen strokes
- Warm, approachable feel — like drawn in a personal notebook
- Use these accent colors sparingly: soft blue (#6CB4EE), warm orange (#E8A848)
- Off-white/cream background (#FAFAF8)
- Clean and simple — not cluttered
- NO text or labels in the image — purely visual illustration
- Slightly whimsical, hand-drawn quality

Subject: {subject}
"""


def generate_single_illustration(
    client,
    segment: dict,
    output_dir: Path,
    slug: str,
) -> dict:
    """Generate one illustration for a single segment."""
    from google.genai import types

    index = segment["index"]
    hint = segment.get("illustration_hint", f"illustration of {segment['title']}")
    title = segment.get("title", f"Section {index}")

    prompt = BASE_PROMPT.format(subject=hint)

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
                logger.info("Generated illustration for section %d: %s (%d bytes)",
                           index, title, len(part.inline_data.data))
                return {
                    "section": index,
                    "title": title,
                    "path": str(img_path),
                    "size_bytes": len(part.inline_data.data),
                    "status": "success",
                }

        logger.warning("No image in response for section %d: %s", index, title)
        return {"section": index, "title": title, "status": "no_image"}

    except Exception as e:
        logger.error("Failed to generate illustration for section %d: %s", index, e)
        return {"section": index, "title": title, "status": "error", "error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Generate hero illustrations via Gemini Flash")
    parser.add_argument("--segments", required=True, help="Path to segments JSON")
    parser.add_argument("--brand", default="brand/brand-kit.md", help="Path to brand kit")
    parser.add_argument("--output", default=".tmp/illustrations/", help="Output directory")
    parser.add_argument("--section", type=int, default=None, help="Generate only this section (1-indexed)")
    parser.add_argument("--max-parallel", type=int, default=3, help="Max parallel API calls")
    args = parser.parse_args()

    segments_path = Path(args.segments)
    if not segments_path.exists():
        logger.error("Segments file not found: %s", args.segments)
        sys.exit(1)

    segments_data = json.loads(segments_path.read_text())
    slug = segments_data.get("slug", "output")
    segments = segments_data.get("segments", [])

    # Filter to specific section if requested
    if args.section:
        segments = [s for s in segments if s["index"] == args.section]
        if not segments:
            logger.error("Section %d not found.", args.section)
            sys.exit(1)

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize Gemini client
    api_key = load_api_key()
    from google import genai
    client = genai.Client(api_key=api_key)

    # Generate illustrations in parallel
    results = []
    with ThreadPoolExecutor(max_workers=args.max_parallel) as executor:
        futures = {
            executor.submit(generate_single_illustration, client, seg, output_dir, slug): seg
            for seg in segments
        }
        for future in as_completed(futures):
            result = future.result()
            results.append(result)

    # Sort by section index
    results.sort(key=lambda r: r["section"])

    # Summary
    success = sum(1 for r in results if r["status"] == "success")
    failed = len(results) - success
    logger.info("Generated %d/%d illustrations (%d failed)", success, len(results), failed)

    output = {
        "slug": slug,
        "total": len(results),
        "success": success,
        "failed": failed,
        "illustrations": results,
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
