#!/usr/bin/env python3
"""
Compose an Excalidraw file from segments + hero illustrations.
Produces a self-contained .excalidraw JSON with base64-embedded images.

Usage:
    python tools/compose_excalidraw.py --segments .tmp/segments/topic_segments.json --illustrations .tmp/illustrations/ --output videos/001-topic/
"""

import argparse
import base64
import json
import logging
import re
import sys
from pathlib import Path
from uuid import uuid4

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Layout constants
CANVAS_PADDING = 80
SECTION_WIDTH = 450
SECTION_HEIGHT = 500
IMAGE_HEIGHT = 280
TEXT_AREA_HEIGHT = 160
GAP_X = 80
GAP_Y = 100
MAX_COLS = 3
ARROW_LENGTH = GAP_X - 20

# Colors
ACCENT_COLORS = ["#a5d8ff", "#ffd8a8", "#b2f2bb", "#fcc2d7", "#d0bfff", "#99e9f2"]
STROKE = "#1e1e1e"
BG_COLOR = "#fafaf8"


def uid() -> str:
    return str(uuid4())[:12]


def make_rect(x, y, w, h, bg="transparent", label=None, stroke=STROKE, stroke_width=2, roundness=3):
    elem = {
        "type": "rectangle",
        "id": uid(),
        "x": x, "y": y, "width": w, "height": h,
        "backgroundColor": bg,
        "strokeColor": stroke,
        "strokeWidth": stroke_width,
        "fillStyle": "solid",
        "roughness": 1,
        "opacity": 100,
        "angle": 0,
        "version": 4,
        "versionNonce": 0,
        "isDeleted": False,
        "groupIds": [],
        "boundElements": None,
        "roundness": {"type": roundness},
    }
    if label:
        elem["label"] = {"text": label, "fontSize": 20}
    return elem


def make_text(x, y, text, font_size=20, color=STROKE, font_family=1, align="left", width=400):
    return {
        "type": "text",
        "id": uid(),
        "x": x, "y": y,
        "width": width, "height": font_size * 1.5 * max(1, len(text) // 40 + 1),
        "text": text,
        "fontSize": font_size,
        "fontFamily": font_family,  # 1=Virgil (hand-drawn), 2=Helvetica, 3=Cascadia
        "textAlign": align,
        "verticalAlign": "top",
        "strokeColor": color,
        "opacity": 100,
        "angle": 0,
        "version": 4,
        "versionNonce": 0,
        "isDeleted": False,
        "groupIds": [],
        "boundElements": None,
    }


def make_arrow(x1, y1, x2, y2, color=STROKE):
    return {
        "type": "arrow",
        "id": uid(),
        "x": min(x1, x2), "y": min(y1, y2),
        "width": abs(x2 - x1), "height": abs(y2 - y1) or 1,
        "points": [
            [x1 - min(x1, x2), y1 - min(y1, y2)],
            [x2 - min(x1, x2), y2 - min(y1, y2)],
        ],
        "strokeColor": color,
        "strokeWidth": 2,
        "strokeStyle": "solid",
        "roughness": 1,
        "opacity": 100,
        "startArrowhead": None,
        "endArrowhead": "arrow",
        "version": 4,
        "versionNonce": 0,
        "isDeleted": False,
        "groupIds": [],
        "boundElements": None,
    }


def make_image(x, y, w, h, file_id):
    return {
        "type": "image",
        "id": uid(),
        "x": x, "y": y,
        "width": w, "height": h,
        "fileId": file_id,
        "status": "saved",
        "scale": [1, 1],
        "version": 4,
        "versionNonce": 0,
        "isDeleted": False,
        "groupIds": [],
        "boundElements": None,
        "opacity": 100,
        "angle": 0,
        "strokeColor": "transparent",
        "backgroundColor": "transparent",
    }


def compose(segments_data: dict, illustrations_dir: Path) -> dict:
    """Build the Excalidraw JSON structure."""
    topic = segments_data.get("topic", "Untitled")
    segments = segments_data.get("segments", [])
    slug = segments_data.get("slug", "output")
    n = len(segments)

    elements = []
    files = {}

    # Determine grid layout
    cols = min(n, MAX_COLS)
    rows = (n + cols - 1) // cols

    # Title
    title_x = CANVAS_PADDING
    title_y = CANVAS_PADDING
    total_width = cols * SECTION_WIDTH + (cols - 1) * GAP_X
    elements.append(make_text(
        title_x, title_y, topic,
        font_size=48, font_family=1, align="left", width=total_width,
    ))

    # Subtitle line
    elements.append(make_text(
        title_x, title_y + 60,
        f"{n} key concepts explained",
        font_size=20, color="#888888", width=total_width,
    ))

    content_top = title_y + 120

    # Track section center positions for arrows
    section_centers = []

    for i, seg in enumerate(segments):
        col = i % cols
        row = i // cols

        x = CANVAS_PADDING + col * (SECTION_WIDTH + GAP_X)
        y = content_top + row * (SECTION_HEIGHT + GAP_Y)

        accent = ACCENT_COLORS[i % len(ACCENT_COLORS)]
        title = seg.get("title", f"Section {i + 1}")
        content = seg.get("content", "")

        # Truncate content to fit
        if len(content) > 200:
            content = content[:197] + "..."

        # Section background box
        elements.append(make_rect(x, y, SECTION_WIDTH, SECTION_HEIGHT, bg="#ffffff", stroke=STROKE, stroke_width=1))

        # Colored accent bar at top
        elements.append(make_rect(x, y, SECTION_WIDTH, 8, bg=accent, stroke="transparent", stroke_width=0, roundness=0))

        # Step number badge
        elements.append(make_rect(x + 15, y + 20, 36, 36, bg=accent, stroke="transparent", roundness=3))
        elements.append(make_text(x + 22, y + 24, str(i + 1), font_size=22, color=STROKE, width=24))

        # Section title
        elements.append(make_text(x + 60, y + 22, title, font_size=28, font_family=1, width=SECTION_WIDTH - 80))

        # Section content text
        elements.append(make_text(x + 15, y + 65, content, font_size=16, color="#555555", width=SECTION_WIDTH - 30))

        # Hero illustration image
        img_path = illustrations_dir / f"{slug}_section-{i + 1}.png"
        if img_path.exists():
            file_id = uid()
            img_b64 = base64.b64encode(img_path.read_bytes()).decode()

            files[file_id] = {
                "mimeType": "image/png",
                "id": file_id,
                "dataURL": f"data:image/png;base64,{img_b64}",
                "created": 1704067200000,
            }

            img_y = y + SECTION_HEIGHT - IMAGE_HEIGHT - 15
            img_w = SECTION_WIDTH - 30
            elements.append(make_image(x + 15, img_y, img_w, IMAGE_HEIGHT, file_id))
            logger.info("Embedded illustration for section %d: %s", i + 1, title)
        else:
            logger.warning("No illustration found for section %d: %s", i + 1, title)

        # Track center for arrows
        section_centers.append((x + SECTION_WIDTH, y + SECTION_HEIGHT // 2))

    # Add arrows between consecutive sections
    for i in range(n - 1):
        col_curr = i % cols
        col_next = (i + 1) % cols

        if col_next > col_curr:
            # Same row — horizontal arrow
            x1 = CANVAS_PADDING + col_curr * (SECTION_WIDTH + GAP_X) + SECTION_WIDTH + 10
            x2 = CANVAS_PADDING + col_next * (SECTION_WIDTH + GAP_X) - 10
            y_mid = content_top + (i // cols) * (SECTION_HEIGHT + GAP_Y) + SECTION_HEIGHT // 2
            elements.append(make_arrow(x1, y_mid, x2, y_mid))
        else:
            # Row wrap — arrow goes down to next row
            row_curr = i // cols
            x_end = CANVAS_PADDING + col_curr * (SECTION_WIDTH + GAP_X) + SECTION_WIDTH // 2
            y1 = content_top + row_curr * (SECTION_HEIGHT + GAP_Y) + SECTION_HEIGHT + 10
            y2 = content_top + (row_curr + 1) * (SECTION_HEIGHT + GAP_Y) - 10
            # Arrow from last col down to first col of next row
            x_start = CANVAS_PADDING + col_curr * (SECTION_WIDTH + GAP_X) + SECTION_WIDTH // 2
            x_target = CANVAS_PADDING + col_next * (SECTION_WIDTH + GAP_X) + SECTION_WIDTH // 2
            elements.append(make_arrow(x_start, y1, x_target, y2))

    return {
        "type": "excalidraw",
        "version": 2,
        "source": "youtube-diagrams",
        "elements": elements,
        "appState": {
            "zoom": {"value": 1},
            "scrollX": 0,
            "scrollY": 0,
            "gridSize": 20,
            "gridMode": False,
            "viewBackgroundColor": BG_COLOR,
        },
        "files": files,
    }


def main():
    parser = argparse.ArgumentParser(description="Compose Excalidraw file from segments + illustrations")
    parser.add_argument("--segments", required=True, help="Path to segments JSON")
    parser.add_argument("--illustrations", default=".tmp/illustrations/", help="Illustrations directory")
    parser.add_argument("--output", required=True, help="Output directory")
    args = parser.parse_args()

    segments_data = json.loads(Path(args.segments).read_text())
    slug = segments_data.get("slug", "output")

    illust_dir = Path(args.illustrations)
    excalidraw_data = compose(segments_data, illust_dir)

    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{slug}.excalidraw"
    out_path.write_text(json.dumps(excalidraw_data))

    logger.info("Excalidraw file saved: %s (%d elements, %d images)",
                out_path, len(excalidraw_data["elements"]), len(excalidraw_data["files"]))
    print(json.dumps({"output_path": str(out_path), "elements": len(excalidraw_data["elements"]), "images": len(excalidraw_data["files"])}))


if __name__ == "__main__":
    main()
