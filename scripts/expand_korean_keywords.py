from __future__ import annotations

import argparse
import itertools
import re
from typing import Any, Dict, List

from common import CONFIG_DIR, PROJECT_ROOT, load_aliases, normalize_text, read_json, today, write_json


def load_rules() -> Dict[str, Any]:
    return read_json(CONFIG_DIR / "korean_keyword_expansion.json")


def split_prefix(sentence: str) -> Dict[str, str]:
    match = re.match(r"^\s*([^:：]{1,40})[:：]\s*(.+)$", sentence)
    if not match:
        return {"prefix": "", "body": sentence.strip()}
    return {"prefix": match.group(1).strip(), "body": match.group(2).strip()}


def strip_light_suffix(token: str, suffixes: List[str]) -> str:
    for suffix in sorted(suffixes, key=len, reverse=True):
        if token.endswith(suffix) and len(token) > len(suffix) + 1:
            return token[: -len(suffix)]
    return token


def tokenize_koreanish(text: str) -> List[str]:
    raw = re.findall(r"[0-9A-Za-z가-힣一-龥]+", text)
    rules = load_rules()
    stopwords = {normalize_text(x) for x in rules.get("meta_stopwords", [])}
    suffixes = rules.get("light_suffixes", [])
    tokens = []
    for token in raw:
        token = strip_light_suffix(token.strip(), suffixes)
        key = normalize_text(token)
        if len(key) < 2 or key in stopwords:
            continue
        if token not in tokens:
            tokens.append(token)
    return tokens[:16]


def infer_alias_context(text: str) -> List[str]:
    aliases = load_aliases()
    norm_text = normalize_text(text)
    context = []
    for canonical, names in aliases.get("author_aliases", {}).items():
        if any(normalize_text(name) in norm_text for name in [canonical, *names]):
            context.append(canonical)
            context.extend(aliases.get("author_default_works", {}).get(canonical, []))
    for canonical, names in aliases.get("title_aliases", {}).items():
        if any(normalize_text(name) in norm_text for name in [canonical, *names]):
            context.append(canonical)
    deduped = []
    seen = set()
    for item in context:
        key = normalize_text(item)
        if key and key not in seen:
            deduped.append(item)
            seen.add(key)
    return deduped


def matched_synonym_sets(text: str) -> List[Dict[str, Any]]:
    rules = load_rules()
    norm_text = normalize_text(text)
    matched = []
    for item in rules.get("korean_synonym_sets", []):
        if any(normalize_text(term) in norm_text for term in item.get("terms", [])):
            matched.append(item)
    return matched


def matched_bridge_recipes(text: str) -> List[Dict[str, Any]]:
    rules = load_rules()
    norm_text = normalize_text(text)
    matched = []
    for recipe in rules.get("bridge_recipes", []):
        requires = recipe.get("requires_any", [])
        context = recipe.get("context_any", [])
        has_required = any(normalize_text(term) in norm_text for term in requires)
        has_context = not context or any(normalize_text(term) in norm_text for term in context)
        if has_required and has_context:
            matched.append(recipe)
    return matched


def compact_phrase(items: List[str], max_items: int = 5) -> str:
    return " ".join([x for x in items if x][:max_items]).strip()


def query_priority(item: Dict[str, Any]) -> int:
    category = item.get("category", "")
    language = item.get("language", "")
    if category.startswith("bridge:"):
        return 0
    if language in {"en", "fr", "de", "la", "grc"}:
        return 1
    if category == "ko_keyword_bundle":
        return 2
    if category.startswith("ko_variant_combo"):
        return 3
    return 4


def expand_keywords(sentence: str, author: str = "", work: str = "") -> Dict[str, Any]:
    split = split_prefix(sentence)
    combined = " ".join(x for x in [sentence, author, work] if x)
    body_combined = " ".join(x for x in [split["body"], author, work] if x)
    tokens = tokenize_koreanish(split["body"])
    context = infer_alias_context(combined)
    if author:
        context.append(author)
    if work:
        context.append(work)
    context = list(dict.fromkeys(x for x in context if x))
    synonym_sets = matched_synonym_sets(body_combined)
    bridges = matched_bridge_recipes(combined)

    keyword_groups: List[Dict[str, Any]] = []
    keyword_groups.append(
        {
            "category": "ko_preserved",
            "language": "ko",
            "keywords": [sentence],
            "purpose": "Preserve the user's wording exactly.",
        }
    )
    if split["body"] != sentence:
        keyword_groups.append(
            {
                "category": "ko_body_without_prefix",
                "language": "ko",
                "keywords": [split["body"]],
                "purpose": "Search the content without an author/test-label prefix.",
            }
        )
    if tokens:
        keyword_groups.append(
            {
                "category": "ko_core_tokens",
                "language": "ko",
                "keywords": tokens,
                "purpose": "Search extracted Korean content words.",
            }
        )
    for synonym_set in synonym_sets:
        keyword_groups.append(
            {
                "category": f"ko_synonyms:{synonym_set.get('label', '')}",
                "language": "ko",
                "keywords": synonym_set.get("variants", []),
                "purpose": "Search Korean paraphrase variants and mixed bilingual terms.",
            }
        )
    for bridge in bridges:
        keyword_groups.append(
            {
                "category": f"bridge:{bridge.get('label', '')}",
                "language": "multi",
                "keywords": bridge.get("queries", []),
                "purpose": "Search a likely cross-language quote bridge.",
            }
        )

    generated_queries: List[Dict[str, Any]] = []
    context_phrase = compact_phrase(context, 4)
    for bridge in bridges:
        for query in bridge.get("queries", []):
            generated_queries.append(
                {
                    "query": compact_phrase([query, context_phrase], 14),
                    "category": f"bridge:{bridge.get('label', '')}",
                    "language": "multi",
                    "purpose": "Likely source-language bridge query.",
                }
            )

    direct_bases = [split["body"], compact_phrase(tokens, 6)]
    for base in direct_bases:
        if base:
            generated_queries.append(
                {
                    "query": compact_phrase([base, context_phrase], 12),
                    "category": "ko_keyword_bundle",
                    "language": "ko",
                    "purpose": "Broad Korean keyword bundle with inferred author/work context.",
                }
            )
    for synonym_set in synonym_sets:
        variants = synonym_set.get("variants", [])[:5]
        for size in (2, 3):
            for combo in itertools.combinations(variants, min(size, len(variants))):
                generated_queries.append(
                    {
                        "query": compact_phrase([*combo, context_phrase], 10),
                        "category": f"ko_variant_combo:{synonym_set.get('label', '')}",
                        "language": "ko",
                        "purpose": "Korean variant combination search.",
                    }
                )
    deduped = []
    seen = set()
    for item in sorted(generated_queries, key=query_priority):
        key = normalize_text(item["query"])
        if key and key not in seen:
            deduped.append(item)
            seen.add(key)

    return {
        "input_sentence": sentence,
        "created": today(),
        "prefix": split["prefix"],
        "body": split["body"],
        "tokens": tokens,
        "inferred_context": context,
        "keyword_groups": keyword_groups,
        "queries": deduped,
        "note": "This module optimizes recall. It generates plausible search keywords, not confirmed translations.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Expand Korean input into broad search keyword bundles.")
    parser.add_argument("sentence")
    parser.add_argument("--author", default="")
    parser.add_argument("--work", default="")
    parser.add_argument("--output", default=str(PROJECT_ROOT / "results" / "korean_keyword_plan.json"))
    args = parser.parse_args()

    payload = expand_keywords(args.sentence, author=args.author, work=args.work)
    write_json(args.output, payload)
    print(f"Wrote {args.output}. Queries: {len(payload['queries'])}")


if __name__ == "__main__":
    main()
