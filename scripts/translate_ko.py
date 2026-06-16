from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Dict, List

from common import PROJECT_ROOT, read_json, write_text


def build_worksheet(payload: Dict[str, Any], limit: int = 0) -> str:
    card = payload.get("source_card", {})
    passages: List[Dict[str, str]] = payload.get("passages", [])
    if limit:
        passages = passages[:limit]
    title = card.get("title", "Untitled")
    url = card.get("stable_url") or card.get("url", "")
    rights = card.get("rights_status", "unknown")
    lines = [
        "# Korean Translation Worksheet",
        "",
        "## Source",
        "",
        f"- Title: {title}",
        f"- URL: {url}",
        f"- Rights status: {rights}",
        "",
        "## Term Table",
        "",
        "| Source Term | Korean Term | Note |",
        "|---|---|---|",
        "|  |  |  |",
        "",
        "## Passages",
        "",
    ]
    for passage in passages:
        lines.extend(
            [
                f"### {passage.get('id', 'P????')}",
                "",
                "Source:",
                "",
                passage.get("source", "").strip(),
                "",
                "Korean:",
                "",
                "",
                "Notes:",
                "",
                "",
            ]
        )
    lines.extend(
        [
            "## Agent Translation Instruction",
            "",
            "Fill the Korean fields above. Keep paragraph IDs unchanged. Preserve key terms consistently and add notes only when needed.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a Korean translation worksheet.")
    parser.add_argument("extracted_json")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--output", default=str(PROJECT_ROOT / "results" / "translation_worksheet.md"))
    args = parser.parse_args()

    payload: Dict[str, Any] = read_json(Path(args.extracted_json))
    write_text(args.output, build_worksheet(payload, args.limit))
    print(f"Wrote {args.output}.")


if __name__ == "__main__":
    main()

