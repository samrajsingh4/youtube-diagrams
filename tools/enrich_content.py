#!/usr/bin/env python3
"""
Enrich a topic outline with NotebookLM research.

Usage:
    python tools/enrich_content.py --topic "How RAG Works" --outline outline.md
    python tools/enrich_content.py --topic "How RAG Works" --outline outline.md --notebook <id>
"""

import argparse
import json
import logging
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TMP_DIR = PROJECT_ROOT / ".tmp" / "research"


def slugify(text: str) -> str:
    return text.lower().replace(" ", "-").replace("'", "")[:50]


def run_nlm(args: list[str], timeout: int = 60) -> dict | None:
    """Run a notebooklm CLI command and return parsed JSON or None."""
    cmd = ["notebooklm"] + args + ["--json"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if result.returncode != 0:
            logger.warning("notebooklm %s failed (rc=%d): %s", args[0], result.returncode, result.stderr.strip())
            return None
        return json.loads(result.stdout)
    except FileNotFoundError:
        logger.warning("notebooklm CLI not found on PATH.")
        return None
    except subprocess.TimeoutExpired:
        logger.warning("notebooklm command timed out after %ds.", timeout)
        return None
    except json.JSONDecodeError:
        logger.warning("Failed to parse notebooklm JSON output.")
        return None


def create_or_reuse_notebook(topic: str, notebook_id: str | None) -> str | None:
    """Create a new notebook or verify an existing one. Returns notebook ID."""
    if notebook_id:
        # Verify it exists
        data = run_nlm(["source", "list", "--notebook", notebook_id])
        if data:
            logger.info("Using existing notebook: %s", notebook_id)
            return notebook_id
        logger.warning("Notebook %s not found, creating new one.", notebook_id)

    # Create new notebook
    title = f"YouTube Diagrams: {topic}"
    result = subprocess.run(
        ["notebooklm", "create", title, "--json"],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        logger.error("Failed to create notebook: %s", result.stderr.strip())
        return None

    data = json.loads(result.stdout)
    nb_id = data.get("id")
    logger.info("Created notebook '%s' (%s)", title, nb_id)
    return nb_id


def add_research(notebook_id: str, topic: str) -> bool:
    """Add web research sources to the notebook."""
    result = subprocess.run(
        ["notebooklm", "source", "add-research", topic,
         "--mode", "fast", "--notebook", notebook_id],
        capture_output=True, text=True, timeout=120,
    )
    if result.returncode != 0:
        logger.warning("Research add failed: %s", result.stderr.strip())
        return False
    logger.info("Added research sources for '%s'", topic)
    return True


def ask_questions(notebook_id: str, topic: str, outline: str) -> list[dict]:
    """Ask targeted questions to enrich the outline."""
    questions = [
        f"What are the key concepts someone needs to understand about {topic}? List them with brief explanations.",
        f"What are common misconceptions about {topic}? What do beginners get wrong?",
        f"What are the most important statistics, numbers, or benchmarks related to {topic}?",
        f"Can you explain the step-by-step process or workflow of {topic}? Break it into clear stages.",
        f"Given this outline, what additional details or examples would make each section more informative?\n\nOutline:\n{outline}",
    ]

    answers = []
    for q in questions:
        data = run_nlm(["ask", q, "--notebook", notebook_id])
        if data:
            answers.append({
                "question": q[:200],  # Truncate for readability
                "answer": data.get("answer", ""),
                "references": data.get("references", []),
            })
            logger.info("Got answer for: %s...", q[:60])
        else:
            logger.warning("No answer for: %s...", q[:60])

    return answers


def save_note(notebook_id: str, topic: str, enriched_content: str) -> bool:
    """Save enriched content as a NotebookLM note."""
    result = subprocess.run(
        ["notebooklm", "ask", enriched_content,
         "--save-as-note", "--note-title", f"Diagram Content: {topic}",
         "--notebook", notebook_id],
        capture_output=True, text=True, timeout=60,
    )
    if result.returncode != 0:
        logger.warning("Failed to save note: %s", result.stderr.strip())
        return False
    logger.info("Saved enriched note to NotebookLM.")
    return True


def main():
    parser = argparse.ArgumentParser(description="Enrich topic outline with NotebookLM research")
    parser.add_argument("--topic", required=True, help="Video topic")
    parser.add_argument("--outline", required=True, help="Path to outline/bullet points file")
    parser.add_argument("--notebook", default=None, help="Existing NotebookLM notebook ID")
    args = parser.parse_args()

    # Read outline
    outline_path = Path(args.outline)
    if not outline_path.exists():
        logger.error("Outline file not found: %s", args.outline)
        sys.exit(1)
    outline_text = outline_path.read_text()

    # Create/reuse notebook
    nb_id = create_or_reuse_notebook(args.topic, args.notebook)
    if not nb_id:
        logger.error("Could not create or access notebook. Proceeding with outline only.")
        # Still produce output with just the outline
        answers = []
    else:
        # Add research sources
        add_research(nb_id, args.topic)

        # Ask enrichment questions
        answers = ask_questions(nb_id, args.topic, outline_text)

        # Save enriched content as note
        summary = f"Summarize the key information about {args.topic} that would be useful for creating an infographic diagram. Include key stats, steps, and concepts."
        save_note(nb_id, args.topic, summary)

    # Build output
    slug = slugify(args.topic)
    output = {
        "topic": args.topic,
        "slug": slug,
        "researched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "notebook_id": nb_id,
        "original_outline": outline_text,
        "enrichment": {
            "answers": answers,
            "source_count": len(answers),
        },
    }

    # Write output
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    out_path = TMP_DIR / f"{slug}_enriched.json"
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    logger.info("Enriched content saved to: %s", out_path)
    print(json.dumps({"output_path": str(out_path), "topic": args.topic, "slug": slug}, indent=2))


if __name__ == "__main__":
    main()
