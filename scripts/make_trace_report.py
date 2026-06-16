from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Dict, List

from common import PROJECT_ROOT, read_json, write_text


def candidate_block(candidate: Dict[str, Any], index: int) -> str:
    return f"""### Candidate {index}

- Source candidate: {candidate.get("title", "")}
- Source: {candidate.get("source_name", candidate.get("source_id", ""))}
- Document layer: {candidate.get("source_layer_label", "층위 불명")}
- URL: {candidate.get("url", "")}
- Stable/identifier: {candidate.get("stable_url", candidate.get("identifier", ""))}
- Rights status: {candidate.get("rights_status", "unknown")}
- Trigger query: {candidate.get("trace_query", "")}
- Query branch: {candidate.get("trace_category", "")} / {candidate.get("trace_language", "")}
- Match likelihood: {likelihood(candidate.get("trace_score", 0))}
- Why selected: It matched the reverse-trace query branch above. Inspect the source text before treating it as a quotation.
- Uncertain points: Source layer, edition, translation lineage, and exact passage alignment may still need verification.
- Next check: Build a manifest or extract the text, then compare the source passage with the Korean wording.
"""


def likelihood(score: Any) -> str:
    try:
        value = float(score)
    except (TypeError, ValueError):
        return "unknown"
    if value >= 0.75:
        return "high"
    if value >= 0.45:
        return "medium"
    return "low"


def build_report(payload: Dict[str, Any]) -> str:
    plan = payload.get("plan", {})
    candidates: List[Dict[str, Any]] = payload.get("candidates", [])
    concepts = plan.get("analysis", {}).get("matched_concepts", [])
    concept_lines = []
    for concept in concepts:
        concept_lines.append(
            f"- Korean terms: {', '.join(concept.get('ko', []))}; notes: {concept.get('notes', '')}"
        )
    query_lines = [
        f"- {q.get('category')} / {q.get('language')}: `{q.get('query')}`"
        for q in plan.get("queries", [])
    ]
    candidate_text = "\n".join(
        candidate_block(candidate, i)
        for i, candidate in enumerate(candidates, start=1)
    )
    if not candidate_text:
        candidate_text = "No candidates were produced. Review the query plan or run without `--plan-only`.\n"

    return f"""# Reverse Trace Report

## Work Overview

- Input sentence: {payload.get("input_sentence", "")}
- Author hint: {payload.get("author_hint", "")}
- Work hint: {payload.get("work_hint", "")}
- Confirmation status: not confirmed
- Summary: The items below are candidates for source tracing. They are not final answers.

## Input Analysis

{chr(10).join(concept_lines) if concept_lines else "- No configured concepts matched. Add local terms to `config/multilingual_terms.json`."}

## Search Strategy

{chr(10).join(query_lines) if query_lines else "- No queries recorded."}

## Candidate Summary

{candidate_text}
## Source Layer Separation

- 원어 원전: candidate pages in source languages such as Greek, Latin, French, German, or original English.
- 고전적 번역본: historically influential translations that may have shaped Korean wording indirectly.
- 현대 번역본: modern translations, including Korean or English translations.
- 주석·전통 해석: commentary or exegetical material.
- 현대 해설·2차 문헌: textbooks, lectures, encyclopedia entries, papers, or summaries.

## Provisional Conclusion

- Most plausible candidate: choose only after source-passage comparison.
- Conceptually similar candidate: possible when terms match but sentence structure does not.
- Not enough evidence: use this label whenever the source text cannot be aligned directly.

## User Selection Request

위 후보 중 찾고 있던 문장과 가장 가까운 쪽을 선택해 주세요. 선택 후 해당 후보를 기준으로 원문-번역 대조표, 출전 정보, 인용 가능성, 원전과 해설의 차이를 정리합니다.
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a markdown report from reverse trace results.")
    parser.add_argument("reverse_trace_json")
    parser.add_argument("--output", default=str(PROJECT_ROOT / "results" / "reverse_trace_report.md"))
    args = parser.parse_args()

    payload: Dict[str, Any] = read_json(Path(args.reverse_trace_json))
    write_text(args.output, build_report(payload))
    print(f"Wrote {args.output}.")


if __name__ == "__main__":
    main()

