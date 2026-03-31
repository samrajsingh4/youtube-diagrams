# Workflow: Edit Existing Diagram

## Trigger
- `/diagram --edit`
- User requests changes to a generated diagram

## Smart Edit Decision Tree

| Change Type | Action | Regenerate? |
|------------|--------|-------------|
| Text content | Edit SVG `<text>` element directly | No |
| Colors / styles | Edit SVG fill/stroke attributes | No |
| Font size / spacing | Edit SVG attributes, re-run critique | No |
| Layout / structure | Regenerate blueprint from segments, preserve illustrations | Partial |
| Single illustration | Regenerate only that illustration via Gemini | Partial |
| Full redo | Re-run pipeline from Step 4 | Yes |

## Steps

### Step 1: Identify Change Type
Ask user what they want to change. Categorize into one of the types above.

### Step 2: Apply Change

**For SVG-only edits (text, color, style, spacing):**
1. Read the source SVG from `videos/<NNN>-<slug>/source.svg`
2. Find the target `<g id="section-N">` group
3. Make the edit using Edit tool on the SVG file
4. Re-run critique: `python tools/critique_svg.py --svg <path>`
5. Re-export PNG: `python tools/export_png.py --svg <path>`

**For layout changes:**
1. Read `.tmp/segments/<slug>_segments.json`
2. Re-run: `python tools/generate_svg.py --segments <path> --brand brand/brand-kit.md`
3. Re-run critique
4. Re-compose with existing illustrations (skip Gemini)
5. Re-export PNG

**For illustration changes:**
1. Identify which section needs a new illustration
2. Re-run: `python tools/generate_illustration.py --section N --segments <path> --brand brand/brand-kit.md`
3. Re-compose and re-export

### Step 3: Show Updated Result
Present the updated PNG. Ask if further edits are needed.

### Step 4: Update Variants (if requested)
Re-run `python tools/generate_variants.py` with the updated SVG.
