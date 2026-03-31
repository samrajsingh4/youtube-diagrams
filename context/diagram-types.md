# Diagram Types

## Supported Layout Types

### 1. Flowchart / Pipeline
Best for: "How X works", step-by-step processes, system architecture
Layout: Left-to-right or top-to-bottom connected boxes with arrows
Sections: 4-8 steps, each in a rounded rectangle with title + brief description
Hero illustrations: One per major step

### 2. Concept Explainer
Best for: "What is X?", breaking down a concept into components
Layout: Central title with radiating sections (hub-and-spoke or grid)
Sections: 3-6 components, each with icon placeholder + title + 2-3 bullet points
Hero illustrations: One central illustration + small icons per component

### 3. Comparison / Versus
Best for: "X vs Y", feature comparisons, before/after
Layout: Two-column split with shared header
Sections: Left side vs right side, each with matching rows
Hero illustrations: One per side

### 4. Numbered List / Steps
Best for: "5 ways to...", "Top N tips", tutorials
Layout: Vertical stack with large numbers + content blocks
Sections: 3-7 items, each with number + title + description
Hero illustrations: One per item or one hero at top

### 5. Architecture / System Diagram
Best for: Technical architecture, data flows, system components
Layout: Multi-layer boxes with connecting arrows showing data flow
Sections: 3-5 layers (e.g., Frontend → API → Database)
Hero illustrations: Component logos/icons from Tavily search

## Auto-Detection Rules

Given the segment content, choose the layout type:
- If segments describe sequential steps → Flowchart
- If segments describe parts of a whole → Concept Explainer
- If segments compare two things → Comparison
- If segments are a ranked/numbered list → Numbered List
- If segments describe system components → Architecture Diagram

When uncertain, default to Flowchart (most versatile).
