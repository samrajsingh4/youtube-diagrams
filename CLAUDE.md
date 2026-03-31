# YouTube Diagrams

Generate SVG+Gemini hybrid infographics for YouTube videos about AI, Claude Code, and tech topics.

## Architecture: WAT Framework

- **Workflows** (`workflows/`): Markdown SOPs defining each pipeline
- **Agent** (you): Orchestrate tools, make decisions, handle failures
- **Tools** (`tools/`): Python scripts for deterministic execution

## Quick Start

```
/diagram "topic"          # Generate diagrams from topic + outline
/diagram --edit           # Edit existing diagram (smart mode)
/diagram --brand          # Create/update brand kit
/diagram --auto           # Full auto mode (no pauses)
```

## Key Directories

| Path | Purpose |
|------|---------|
| `brand/brand-kit.md` | Colors, fonts, strokes, styles |
| `config/critique-rubric.yaml` | AI critic scoring criteria |
| `context/` | SVG conventions, diagram type templates (load before generation) |
| `templates/svg/` | Base canvas + section layout fragments |
| `tools/` | Python scripts for each pipeline stage |
| `workflows/` | Step-by-step SOPs |
| `videos/NNN-topic/` | Output folders, auto-numbered |
| `.tmp/` | Intermediate files, disposable |

## Rules

- ALWAYS load `context/` files before SVG generation
- ALWAYS use `--notebook` flag for NotebookLM (never `use` — parallel safety)
- ALWAYS run critique sub-agent before presenting SVG to user
- Generate illustrations in PARALLEL, not sequentially
- Min font sizes: 24px body, 48px headers at 1920x1080
- All SVG dimensions absolute (no %, no viewBox)
- Each section in `<g id="section-N">` for surgical editing
- API keys in `.env` — never commit secrets
