from __future__ import annotations

import argparse
from typing import Any, Dict, List

from common import (
    PROJECT_ROOT,
    classify_source_layer,
    ensure_dirs,
    score_candidate,
    unique_records,
    write_json,
)
from expand_multilingual_queries import expand_queries
from search_all import run as run_search


LAYER_SCORE_BONUS = {
    "original_language_primary": 0.18,
    "early_or_classic_translation": 0.12,
    "modern_translation": 0.03,
    "commentary_or_traditional_interpretation": 0.02,
    "later_scholar_interpretation": 0.0,
    "modern_secondary_explanation": -0.05,
    "discovery_only": -0.2,
    "unknown": -0.03,
}


def source_ids_for_query(query: Dict[str, Any], override: str = "") -> List[str]:
    if override:
        return [x.strip() for x in override.split(",") if x.strip()]
    return query.get("source_hints") or []


def trace(
    sentence: str,
    author: str = "",
    work: str = "",
    query_limit: int = 10,
    per_query_limit: int = 4,
    source_override: str = "",
    plan_only: bool = False,
) -> Dict[str, Any]:
    ensure_dirs()
    plan = expand_queries(sentence, author, work)
    selected_queries = plan["queries"][:query_limit]
    if plan_only:
        return {
            "input_sentence": sentence,
            "author_hint": author,
            "work_hint": work,
            "plan": plan,
            "candidates": [],
            "note": "Plan only. No source search was run.",
        }

    all_candidates: List[Dict[str, Any]] = []
    errors: List[str] = []
    for query in selected_queries:
        source_ids = source_ids_for_query(query, source_override)
        try:
            result = run_search(query["query"], per_query_limit, source_ids)
        except Exception as exc:  # noqa: BLE001 - keep source failures isolated.
            errors.append(f"{query['query']}: {exc}")
            continue
        for candidate in result.get("results", []):
            item = dict(candidate)
            item["trace_query"] = query["query"]
            item["trace_category"] = query["category"]
            item["trace_language"] = query["language"]
            item["trace_purpose"] = query["purpose"]
            item.update(classify_source_layer(item))
            score = max(
                score_candidate(query["query"], item),
                score_candidate(sentence, item),
            )
            score += LAYER_SCORE_BONUS.get(item.get("source_layer", "unknown"), 0.0)
            if item.get("rights_status") in {"unknown", "metadata_only"}:
                score -= 0.03
            item["trace_score"] = round(score, 4)
            all_candidates.append(item)
        errors.extend(result.get("errors", []))

    candidates = unique_records(all_candidates)
    candidates.sort(key=lambda x: x.get("trace_score", 0), reverse=True)
    top = candidates[:5]
    return {
        "input_sentence": sentence,
        "author_hint": author,
        "work_hint": work,
        "plan": {**plan, "queries": selected_queries},
        "candidate_count": len(candidates),
        "candidates": top,
        "errors": errors,
        "caution": "These are source candidates, not confirmed answers. Distinguish source-language originals, translations, commentaries, and modern explanations before citation.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Reverse trace a Korean translated sentence to multilingual source candidates.")
    parser.add_argument("sentence")
    parser.add_argument("--author", default="")
    parser.add_argument("--work", default="")
    parser.add_argument("--query-limit", type=int, default=10)
    parser.add_argument("--per-query-limit", type=int, default=4)
    parser.add_argument("--sources", default="", help="Comma-separated source IDs overriding query source hints.")
    parser.add_argument("--plan-only", action="store_true")
    parser.add_argument("--output", default=str(PROJECT_ROOT / "results" / "reverse_trace_results.json"))
    args = parser.parse_args()

    payload = trace(
        args.sentence,
        author=args.author,
        work=args.work,
        query_limit=args.query_limit,
        per_query_limit=args.per_query_limit,
        source_override=args.sources,
        plan_only=args.plan_only,
    )
    write_json(args.output, payload)
    print(f"Wrote {args.output}. Candidates: {len(payload.get('candidates', []))}")


if __name__ == "__main__":
    main()
