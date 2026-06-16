from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Dict, List

from common import PROJECT_ROOT, flatten_results, read_json, score_candidate, write_json


def resolve(payload: Any, target: str, top: int) -> Dict[str, Any]:
    candidates: List[Dict[str, Any]] = flatten_results(payload)
    for candidate in candidates:
        candidate["resolve_score"] = round(score_candidate(target, candidate), 4)
    candidates.sort(key=lambda x: x.get("resolve_score", 0), reverse=True)
    selected = candidates[0] if candidates else {}
    return {
        "target": target,
        "selected": selected,
        "alternatives": candidates[1:top],
        "note": "Review alternatives manually when scores are close or editions differ.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Choose the best candidate from search results.")
    parser.add_argument("search_results_json")
    parser.add_argument("target")
    parser.add_argument("--top", type=int, default=10)
    parser.add_argument("--output", default=str(PROJECT_ROOT / "results" / "selected_work.json"))
    args = parser.parse_args()

    payload = read_json(Path(args.search_results_json))
    result = resolve(payload, args.target, args.top)
    write_json(args.output, result)
    title = result["selected"].get("title", "none")
    print(f"Wrote {args.output}. Selected: {title}")


if __name__ == "__main__":
    main()

