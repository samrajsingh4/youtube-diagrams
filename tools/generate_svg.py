#!/usr/bin/env python3
"""
Generate an SVG blueprint from segmented content + brand kit.

Usage:
    python tools/generate_svg.py --segments .tmp/segments/topic_segments.json --brand brand/brand-kit.md
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
TMP_DIR = PROJECT_ROOT / ".tmp" / "svg"

# Canvas dimensions
WIDTH = 1920
HEIGHT = 1080
MARGIN = 60
CONTENT_WIDTH = WIDTH - 2 * MARGIN
CONTENT_TOP = 170  # Below title area
CONTENT_BOTTOM = HEIGHT - 80  # Above credits


def parse_brand_kit(brand_path: str) -> dict:
    """Parse brand-kit.md and extract colors, fonts, styles."""
    text = Path(brand_path).read_text()
    brand = {
        "bg": "#FAFAF8",
        "card_bg": "#FFFFFF",
        "terminal_bg": "#1E1E2E",
        "text_primary": "#1A1A1A",
        "text_body": "#3D3D3D",
        "text_muted": "#7A7A7A",
        "accent_blue": "#6CB4EE",
        "accent_orange": "#E8A848",
        "accent_green": "#5CB85C",
        "accent_red": "#E85D5D",
        "accent_purple": "#B39DDB",
        "yellow_note": "#FFF3CD",
        "heading_font": "Caveat, cursive",
        "body_font": "Patrick Hand, cursive",
    }

    # Try to extract hex codes from brand-kit.md
    hex_pattern = r"`(#[0-9A-Fa-f]{6})`"
    colors = re.findall(hex_pattern, text)

    # Map found colors to our keys (order they appear in brand-kit.md)
    color_keys = [
        "bg", "card_bg", "terminal_bg",
        "text_primary", "text_body", "text_muted", None,
        "accent_blue", "accent_orange", "accent_green",
        "accent_red", "accent_purple", "yellow_note",
    ]
    for i, color in enumerate(colors):
        if i < len(color_keys) and color_keys[i]:
            brand[color_keys[i]] = color

    return brand


def escape_xml(text: str) -> str:
    """Escape special XML characters."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def generate_defs(brand: dict) -> str:
    """Generate SVG <defs> section with markers, patterns, etc."""
    return f"""  <defs>
    <marker id="arrowhead" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto">
      <polygon points="0 0, 10 4, 0 8" fill="{brand['text_primary']}"/>
    </marker>
    <marker id="arrowhead-orange" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto">
      <polygon points="0 0, 10 4, 0 8" fill="{brand['accent_orange']}"/>
    </marker>
    <pattern id="dot-grid" width="32" height="32" patternUnits="userSpaceOnUse">
      <circle cx="16" cy="16" r="0.8" fill="#E0DDD6"/>
    </pattern>
  </defs>"""


def generate_background(brand: dict) -> str:
    """Generate background with dot grid."""
    return f"""  <rect width="{WIDTH}" height="{HEIGHT}" fill="{brand['bg']}"/>
  <rect width="{WIDTH}" height="{HEIGHT}" fill="url(#dot-grid)"/>"""


def generate_title(topic: str, brand: dict) -> str:
    """Generate the title area."""
    title = escape_xml(topic)
    return f"""  <g id="header">
    <text x="{WIDTH // 2}" y="80" text-anchor="middle" font-family="{brand['heading_font']}" font-size="64" font-weight="700" fill="{brand['text_primary']}">{title}</text>
    <path d="M {WIDTH//2 - 250} 100 Q {WIDTH//2} 115 {WIDTH//2 + 250} 100" stroke="{brand['accent_orange']}" stroke-width="3" fill="none" stroke-linecap="round"/>
  </g>"""


def generate_sparkles(brand: dict) -> str:
    """Generate decorative sparkle elements."""
    return f"""  <g class="sparkles" fill="{brand['accent_orange']}" opacity="0.5">
    <path d="M 120 50 L 124 40 L 128 50 L 138 54 L 128 58 L 124 68 L 120 58 L 110 54 Z"/>
    <path d="M {WIDTH - 130} 45 L {WIDTH - 127} 38 L {WIDTH - 124} 45 L {WIDTH - 117} 48 L {WIDTH - 124} 51 L {WIDTH - 127} 58 L {WIDTH - 130} 51 L {WIDTH - 137} 48 Z"/>
  </g>
  <g class="sparkles" fill="{brand['accent_blue']}" opacity="0.3">
    <path d="M {WIDTH - 90} 90 L {WIDTH - 88} 85 L {WIDTH - 86} 90 L {WIDTH - 81} 92 L {WIDTH - 86} 94 L {WIDTH - 88} 99 L {WIDTH - 90} 94 L {WIDTH - 95} 92 Z"/>
  </g>"""


def generate_credits(brand: dict) -> str:
    """Generate optional credits area."""
    return f"""  <g id="credits">
    <text x="{WIDTH - 80}" y="{HEIGHT - 30}" text-anchor="end" font-family="{brand['body_font']}" font-size="20" fill="#CCCCCC">@YourChannel</text>
  </g>"""


# ─── Layout generators per visual type ───

ACCENT_COLORS = ["accent_blue", "accent_orange", "accent_green", "accent_red", "accent_purple"]


def layout_flowchart(segments: list[dict], brand: dict) -> str:
    """Generate a left-to-right or wrapped flowchart layout."""
    svg_parts = []
    n = len(segments)

    if n <= 4:
        # Single row, left to right
        card_w = min(360, (CONTENT_WIDTH - (n - 1) * 60) // n)
        card_h = 340
        total_w = n * card_w + (n - 1) * 60
        start_x = (WIDTH - total_w) // 2
        y = CONTENT_TOP + 40

        for i, seg in enumerate(segments):
            x = start_x + i * (card_w + 60)
            accent = brand[ACCENT_COLORS[i % len(ACCENT_COLORS)]]
            svg_parts.append(_render_card(seg, x, y, card_w, card_h, accent, brand, i))

            # Arrow between cards
            if i < n - 1:
                ax1 = x + card_w + 5
                ax2 = x + card_w + 50
                ay = y + card_h // 2
                svg_parts.append(
                    f'  <path d="M {ax1} {ay} Q {(ax1+ax2)//2} {ay-10} {ax2} {ay}" '
                    f'stroke="{brand["text_primary"]}" stroke-width="2" fill="none" '
                    f'stroke-linecap="round" marker-end="url(#arrowhead)"/>'
                )
    else:
        # Two rows
        top_count = (n + 1) // 2
        bot_count = n - top_count
        card_w = min(340, (CONTENT_WIDTH - (top_count - 1) * 50) // top_count)
        card_h = 280

        # Top row
        total_w = top_count * card_w + (top_count - 1) * 50
        start_x = (WIDTH - total_w) // 2
        y_top = CONTENT_TOP + 20

        for i in range(top_count):
            seg = segments[i]
            x = start_x + i * (card_w + 50)
            accent = brand[ACCENT_COLORS[i % len(ACCENT_COLORS)]]
            svg_parts.append(_render_card(seg, x, y_top, card_w, card_h, accent, brand, i))

            if i < top_count - 1:
                ax1 = x + card_w + 5
                ax2 = x + card_w + 40
                ay = y_top + card_h // 2
                svg_parts.append(
                    f'  <path d="M {ax1} {ay} Q {(ax1+ax2)//2} {ay-8} {ax2} {ay}" '
                    f'stroke="{brand["text_primary"]}" stroke-width="2" fill="none" '
                    f'stroke-linecap="round" marker-end="url(#arrowhead)"/>'
                )

        # Connector from top-right to bottom-right
        last_top_x = start_x + (top_count - 1) * (card_w + 50) + card_w // 2
        y_bot = y_top + card_h + 80

        # Bottom row (reversed for flow)
        total_w_bot = bot_count * card_w + (bot_count - 1) * 50
        start_x_bot = (WIDTH - total_w_bot) // 2

        # Curved connector arrow
        svg_parts.append(
            f'  <path d="M {last_top_x} {y_top + card_h + 5} '
            f'Q {last_top_x + 30} {y_top + card_h + 40} '
            f'{start_x_bot + (bot_count - 1) * (card_w + 50) + card_w // 2} {y_bot - 10}" '
            f'stroke="{brand["accent_orange"]}" stroke-width="2.5" fill="none" '
            f'stroke-linecap="round" marker-end="url(#arrowhead-orange)"/>'
        )

        for j in range(bot_count):
            seg = segments[top_count + j]
            # Place right-to-left for natural flow continuation
            idx = bot_count - 1 - j
            x = start_x_bot + idx * (card_w + 50)
            accent = brand[ACCENT_COLORS[(top_count + j) % len(ACCENT_COLORS)]]
            svg_parts.append(_render_card(seg, x, y_bot, card_w, card_h, accent, brand, top_count + j))

            if j < bot_count - 1:
                ax1 = x - 5
                ax2 = x - 40
                ay = y_bot + card_h // 2
                svg_parts.append(
                    f'  <path d="M {ax1} {ay} Q {(ax1+ax2)//2} {ay-8} {ax2} {ay}" '
                    f'stroke="{brand["text_primary"]}" stroke-width="2" fill="none" '
                    f'stroke-linecap="round" marker-end="url(#arrowhead)"/>'
                )

    return "\n".join(svg_parts)


def layout_explainer(segments: list[dict], brand: dict) -> str:
    """Generate a hub-and-spoke or grid concept explainer."""
    # Use a grid layout — 2 or 3 columns
    return layout_flowchart(segments, brand)  # Reuse flowchart for now


def _render_card(seg: dict, x: int, y: int, w: int, h: int,
                 accent: str, brand: dict, index: int) -> str:
    """Render a single section card."""
    title = escape_xml(seg.get("title", f"Section {index + 1}"))
    content = seg.get("content", "")
    key_points = seg.get("key_points", [])

    # Wrap content text
    max_chars = max(20, w // 14)

    parts = [
        f'  <g id="section-{index + 1}">',
        # Card background
        f'    <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{brand["card_bg"]}" stroke="{brand["text_primary"]}" stroke-width="1.5"/>',
        # Colored top bar
        f'    <rect x="{x}" y="{y}" width="{w}" height="6" rx="3" fill="{accent}"/>',
        # Step number
        f'    <circle cx="{x + 30}" cy="{y + 35}" r="16" fill="{accent}" opacity="0.2" stroke="{accent}" stroke-width="1.5"/>',
        f'    <text x="{x + 30}" y="{y + 42}" text-anchor="middle" font-family="{brand["body_font"]}" font-size="22" font-weight="700" fill="{accent}">{index + 1}</text>',
        # Title
        f'    <text x="{x + 55}" y="{y + 42}" font-family="{brand["heading_font"]}" font-size="30" font-weight="700" fill="{brand["text_primary"]}">{title[:max_chars]}</text>',
    ]

    # Content text (wrapped)
    text_y = y + 80
    content_lines = _wrap_text(content, max_chars)
    for line in content_lines[:4]:  # Max 4 lines
        parts.append(
            f'    <text x="{x + 20}" y="{text_y}" font-family="{brand["body_font"]}" '
            f'font-size="20" fill="{brand["text_body"]}">{escape_xml(line)}</text>'
        )
        text_y += 28

    # Key points (if any)
    if key_points:
        text_y += 10
        for kp in key_points[:2]:  # Max 2 key points
            kp_wrapped = _wrap_text(kp, max_chars)
            for kp_line in kp_wrapped[:2]:
                parts.append(
                    f'    <text x="{x + 20}" y="{text_y}" font-family="{brand["body_font"]}" '
                    f'font-size="18" fill="{accent}">{escape_xml(kp_line)}</text>'
                )
                text_y += 24

    # Illustration placeholder
    illust_y = y + h - 100
    illust_h = 70
    if illust_y > text_y + 10:
        hint = escape_xml(seg.get("illustration_hint", f"illustration of {title}"))
        parts.append(
            f'    <rect x="{x + 20}" y="{illust_y}" width="{w - 40}" height="{illust_h}" '
            f'rx="8" fill="none" stroke="{accent}" stroke-width="1" stroke-dasharray="6,3" '
            f'data-illustration="{hint}" data-section="{index + 1}"/>'
        )
        parts.append(
            f'    <text x="{x + w // 2}" y="{illust_y + illust_h // 2 + 5}" text-anchor="middle" '
            f'font-family="{brand["body_font"]}" font-size="14" fill="{brand["text_muted"]}">[illustration]</text>'
        )

    parts.append("  </g>")
    return "\n".join(parts)


def _wrap_text(text: str, max_chars: int) -> list[str]:
    """Simple text wrapping."""
    words = text.split()
    lines = []
    current = ""
    for word in words:
        if len(current) + len(word) + 1 > max_chars:
            if current:
                lines.append(current)
            current = word
        else:
            current = f"{current} {word}".strip()
    if current:
        lines.append(current)
    return lines


def generate_svg(segments_data: dict, brand: dict) -> str:
    """Generate the complete SVG blueprint."""
    topic = segments_data.get("topic", "Untitled")
    segments = segments_data.get("segments", [])
    visual_type = segments_data.get("overall_visual_type", "flowchart")

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}">',
        generate_defs(brand),
        generate_background(brand),
        generate_sparkles(brand),
        generate_title(topic, brand),
    ]

    # Generate layout based on visual type
    if visual_type == "comparison":
        parts.append(layout_flowchart(segments, brand))  # TODO: dedicated comparison layout
    elif visual_type == "explainer":
        parts.append(layout_explainer(segments, brand))
    else:
        parts.append(layout_flowchart(segments, brand))

    parts.append(generate_credits(brand))
    parts.append("</svg>")

    return "\n".join(parts)


def main():
    parser = argparse.ArgumentParser(description="Generate SVG blueprint from segments")
    parser.add_argument("--segments", required=True, help="Path to segments JSON")
    parser.add_argument("--brand", default="brand/brand-kit.md", help="Path to brand kit")
    args = parser.parse_args()

    segments_path = Path(args.segments)
    if not segments_path.exists():
        logger.error("Segments file not found: %s", args.segments)
        sys.exit(1)

    brand_path = Path(args.brand)
    if not brand_path.is_absolute():
        brand_path = PROJECT_ROOT / brand_path

    segments_data = json.loads(segments_path.read_text())
    brand = parse_brand_kit(str(brand_path))

    svg_content = generate_svg(segments_data, brand)
    slug = segments_data.get("slug", "output")

    TMP_DIR.mkdir(parents=True, exist_ok=True)
    out_path = TMP_DIR / f"{slug}_blueprint.svg"
    out_path.write_text(svg_content)
    logger.info("SVG blueprint saved to: %s", out_path)
    print(json.dumps({"output_path": str(out_path), "segment_count": len(segments_data.get("segments", []))}))


if __name__ == "__main__":
    main()
