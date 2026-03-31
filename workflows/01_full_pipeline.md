# Workflow: Full Diagram Pipeline

## Trigger
- `/diagram "topic"` — generate from topic + outline
- `/diagram --auto` — same but skip all pauses

## Prerequisites
- Brand kit approved (`brand/brand-kit.md` exists and is non-empty)
- Load ALL context files in `context/` before generation
- API keys in `.env` (GEMINI_API_KEY, TAVILY_API_KEY)

## Modes

**Collab (default):** Pause at each marked stage for user approval.
**Auto:** Run end-to-end. AI critic enforces quality. Only pause if critique fails 3x.

## Steps

### Step 1: Gather Input
Ask user for:
1. Topic / video title
2. Outline or bullet points (paste or point to a file)
3. Existing NotebookLM notebook ID (optional — system creates one if not provided)
4. Number of diagrams: "auto" (system decides based on segments) or specific count

### Step 2: Enrich Content via NotebookLM
```bash
python tools/enrich_content.py --topic "<topic>" --outline "<outline_file>" [--notebook <id>]
```
Output: `.tmp/research/<slug>_enriched.json`

Show enriched summary to user.

### Step 3: Segment Content
```bash
python tools/segment_content.py --input .tmp/research/<slug>_enriched.json
```
Output: `.tmp/segments/<slug>_segments.json`

Show segments to user: section titles, key points, suggested visual types.

**--- PAUSE (collab): User approves segments ---**

### Step 4: Generate SVG Blueprint
```bash
python tools/generate_svg.py --segments .tmp/segments/<slug>_segments.json --brand brand/brand-kit.md
```
Output: `.tmp/svg/<slug>_blueprint.svg`

### Step 5: AI Critique
```bash
python tools/critique_svg.py --svg .tmp/svg/<slug>_blueprint.svg --rubric config/critique-rubric.yaml
```
If critique fails: auto-fix and retry (max 3 attempts).

Show critique results + blueprint preview to user.

**--- PAUSE (collab): User approves blueprint ---**

### Step 6: Generate Illustrations (PARALLEL)
```bash
python tools/generate_illustration.py --segments .tmp/segments/<slug>_segments.json --brand brand/brand-kit.md --output .tmp/illustrations/
```
Run all Gemini API calls in parallel (not sequential).

### Step 7: Search Reference Images (PARALLEL with Step 6)
```bash
python tools/search_images.py --segments .tmp/segments/<slug>_segments.json --output .tmp/images/
```

### Step 8: Compose Final SVG + Export PNG
```bash
python tools/compose_final.py --blueprint .tmp/svg/<slug>_blueprint.svg --illustrations .tmp/illustrations/ --images .tmp/images/ [--credits "Channel Name"]
python tools/export_png.py --svg .tmp/svg/<slug>_final.svg --output videos/<NNN>-<slug>/
```

Show final PNG to user.

**--- PAUSE (collab): User approves or requests edits ---**

If edits requested: route to `workflows/02_edit_diagram.md`.

### Step 9: Generate 3 Style Variants
```bash
python tools/generate_variants.py --svg .tmp/svg/<slug>_final.svg --brand brand/brand-kit.md --output videos/<NNN>-<slug>/
```
Output: `diagram-v1.png`, `diagram-v2.png`, `diagram-v3.png`

Show all 3 variants.

**--- PAUSE (collab): User picks final variant ---**

### Step 10: Clean Up
Move chosen variant to `diagram-final.png`. Keep all variants for reference.

## Error Handling
- **NotebookLM auth expired**: Run `notebooklm login`, retry
- **Gemini rate limit**: Wait 60s, retry once. If still failing, skip illustrations and deliver SVG-only
- **Tavily failure**: Skip reference images, proceed without logos/icons
- **Critique fails 3x**: Present SVG with critique notes, let user decide
- **cairosvg not installed**: `pip install cairosvg` and retry

## Output Structure
```
videos/NNN-topic-slug/
  diagram-v1.png
  diagram-v2.png
  diagram-v3.png
  diagram-final.png
  source.svg
  segments.json
```
