from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Dict

from common import PROJECT_ROOT, read_json, today, write_text


def citation_lines(card: Dict[str, Any]) -> str:
    author = card.get("author") or "Unknown author"
    title = card.get("title") or "Untitled"
    date = card.get("date") or "n.d."
    source = card.get("source_name") or card.get("source_id") or "Unknown source"
    url = card.get("stable_url") or card.get("url") or ""
    accessed = card.get("accessed") or today()
    rights = card.get("rights_status", "unknown")
    identifier = card.get("identifier", "")

    chicago = f'{author}. "{title}." {source}, {date}. Accessed {accessed}. {url}'
    korean = f"{author}, 「{title}」, {source}, {date}, {accessed} 접속. {url}"
    machine = {
        "author": author,
        "title": title,
        "date": date,
        "source": source,
        "url": url,
        "identifier": identifier,
        "accessed": accessed,
        "rights_status": rights,
    }
    machine_lines = "\n".join(f"- {k}: {v}" for k, v in machine.items())
    return f"""# Citation

## Chicago-like

{chicago}

## Korean

{korean}

## Source Card

{machine_lines}

## Rights Note

{card.get("rights_note", "No rights note recorded.")}
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Create citation markdown from extracted text JSON.")
    parser.add_argument("extracted_json")
    parser.add_argument("--output", default=str(PROJECT_ROOT / "results" / "citation.md"))
    args = parser.parse_args()

    payload: Dict[str, Any] = read_json(Path(args.extracted_json))
    card = payload.get("source_card", payload)
    write_text(args.output, citation_lines(card))
    print(f"Wrote {args.output}.")


if __name__ == "__main__":
    main()

