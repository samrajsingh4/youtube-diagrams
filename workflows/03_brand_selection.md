# Workflow: Brand Kit Creation

## Trigger
- `/diagram --brand`
- First run of `/diagram` when `brand/brand-kit.md` is empty

## Steps

### Step 1: Present Style Archetypes
Show 3 hand-drawn style options:

**A. Whiteboard Sketch**
- Background: Pure white (#FFFFFF)
- Strokes: Black (#1A1A1A), 2-3px weight, slightly rough edges
- Accents: One or two muted colors (e.g., blue #4A90D9, orange #E8913A)
- Font: Caveat or Architects Daughter
- Feel: Clean whiteboard marker drawing

**B. Notebook Doodle**
- Background: Warm kraft/cream (#F5F0E8)
- Strokes: Dark ink (#2C2C2C), 2px weight, natural pen feel
- Accents: Warm palette (teal #2D9CDB, coral #EB5757, amber #F2994A)
- Font: Patrick Hand or Caveat
- Feel: Personal notebook with colored highlights

**C. Blueprint Technical**
- Background: Deep navy (#0D1B2A)
- Strokes: White/cyan (#00D4FF), 1.5-2px weight, precise lines
- Accents: Bright cyan (#00D4FF), soft white (#E0E7EE)
- Font: Architects Daughter or Caveat
- Feel: Technical blueprint with neon highlights

Ask: "Pick A, B, or C — or describe a mix."

### Step 2: Refine Colors
Based on choice, present specific hex values for:
- Primary color (main strokes, headings)
- Secondary color (body text, secondary elements)
- Accent 1 (highlights, call-outs)
- Accent 2 (secondary highlights, arrows)
- Background color
- Surface color (card/box backgrounds)

### Step 3: Confirm Typography
Recommend Google Fonts that render well in SVG:
- **Caveat**: Natural handwriting, very readable
- **Patrick Hand**: Clean hand-print, good for body text
- **Architects Daughter**: Technical hand-lettering, great for headers

Ask user to pick heading font + body font.

### Step 4: Define Stroke Styles
- Stroke width: 2-3px for main elements, 1-1.5px for details
- Stroke linecap: round (hand-drawn feel) vs butt (technical feel)
- Dash patterns: solid for main, dashed for optional/future elements
- Corner radius: slightly rounded for organic feel

### Step 5: Save Brand Kit
Write to `brand/brand-kit.md` with all decisions.

### Step 6: Generate Test Swatch
Create a test SVG at 1920x1080 showing:
- Title text in heading font
- Body text in body font
- Color swatches for all defined colors
- Sample box with stroke styles
- Sample arrow with defined style
- Background with chosen treatment

Open in browser for approval.

### Step 7: Iterate
If user wants changes, update brand-kit.md and regenerate swatch.
Once approved, brand kit is locked for consistency.
