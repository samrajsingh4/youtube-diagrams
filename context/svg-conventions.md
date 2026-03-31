# SVG Conventions

## Canvas
- Base size: 1920x1080 (16:9)
- All coordinates are absolute pixels (no %, no em, no viewBox scaling)
- Background is a full-canvas `<rect>` as the first element

## Structure
```xml
<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080">
  <rect width="1920" height="1080" fill="{bg_color}"/>  <!-- background -->
  <g id="header">...</g>                                  <!-- title area -->
  <g id="section-1">...</g>                               <!-- first content section -->
  <g id="section-2">...</g>                               <!-- second content section -->
  <g id="credits">...</g>                                 <!-- optional watermark -->
</svg>
```

## Text Rules
- All `<text>` elements must have explicit `x`, `y`, `font-family`, `font-size`, `fill`
- Minimum font sizes: 48px headers, 32px subheaders, 24px body
- Use `text-anchor="middle"` for centered text
- Line breaks via multiple `<tspan>` elements with `dy` offsets
- Font families from brand kit (Google Fonts loaded externally for PNG render)

## Illustration Placeholders
When a section needs a Gemini-generated illustration:
```xml
<rect x="100" y="200" width="400" height="300"
      fill="none" stroke="{accent}" stroke-dasharray="8,4"
      data-illustration="hand-drawn sketch of a neural network"
      data-section="1"/>
```
The `data-illustration` attribute is the Gemini prompt hint.
The `data-section` maps back to the segment JSON.

## Spacing
- Minimum 40px margin from canvas edges
- Minimum 30px gap between sections
- Minimum 20px padding inside boxes/cards
- Consistent gutters between columns

## Arrows and Connectors
```xml
<line x1="100" y1="200" x2="300" y2="200"
      stroke="{primary}" stroke-width="2" stroke-linecap="round"
      marker-end="url(#arrowhead)"/>
```
Define arrowhead marker in `<defs>` section.

## Colors
All colors reference the brand kit. Use semantic names in comments:
```xml
<rect fill="#1A1A1A"/> <!-- primary -->
<text fill="#4A90D9"/> <!-- accent-1 -->
```

## Groups for Surgical Editing
Every section is a `<g>` with a unique ID. This enables:
- Finding and editing specific sections without touching others
- Replacing illustration placeholders per-section
- Re-positioning sections by changing the group's `transform`
