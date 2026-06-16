from __future__ import annotations

import argparse
import itertools
import re
from typing import Any, Dict, List

from common import PROJECT_ROOT, load_aliases, load_multilingual_terms, normalize_text, today, write_json
from expand_korean_keywords import expand_keywords


LANG_SOURCE_HINTS = {
    "ko": ["wikisource_en", "openlibrary", "internet_archive", "doaj"],
    "en": ["wikisource_en", "gutenberg", "internet_archive", "openlibrary"],
    "fr": ["wikisource_fr", "internet_archive", "openlibrary"],
    "de": ["wikisource_de", "internet_archive", "openlibrary"],
    "la": ["wikisource_la", "perseus_scaife", "internet_archive"],
    "grc": ["perseus_scaife", "wikisource_el", "internet_archive"],
    "zh": ["wikisource_zh", "ctext", "kanripo"],
}


def split_korean_fragments(sentence: str) -> List[str]:
    raw = [sentence.strip()]
    raw.extend(x.strip() for x in re.split(r"[,.!?;:，。！？；：\n]+", sentence) if x.strip())
    fragments = []
    for item in raw:
        if item and item not in fragments:
            fragments.append(item)
    return fragments[:6]


def detect_concepts(sentence: str) -> List[Dict[str, Any]]:
    data = load_multilingual_terms()
    norm_sentence = normalize_text(sentence)
    found = []
    for concept in data.get("concepts", []):
        ko_terms = concept.get("ko", [])
        if any(normalize_text(term) in norm_sentence for term in ko_terms):
            found.append(concept)
    return found


def matched_known_patterns(sentence: str) -> List[Dict[str, Any]]:
    data = load_multilingual_terms()
    norm_sentence = normalize_text(sentence)
    matched = []
    for pattern in data.get("known_quote_patterns", []):
        hints = [normalize_text(x) for x in pattern.get("ko_hint", [])]
        if hints and all(hint in norm_sentence for hint in hints):
            matched.append(pattern)
    return matched


def make_query(
    text: str,
    category: str,
    language: str,
    sources: List[str],
    purpose: str,
) -> Dict[str, Any]:
    return {
        "query": text,
        "category": category,
        "language": language,
        "source_hints": sources,
        "purpose": purpose,
    }


def append_missing_context(query: str, context_bits: List[str]) -> str:
    combined = query
    for bit in context_bits:
        if bit and normalize_text(bit) not in normalize_text(combined):
            combined = f"{combined} {bit}".strip()
    return combined


def infer_context_bits(sentence: str, author: str = "", work: str = "") -> List[str]:
    aliases = load_aliases()
    norm_sentence = normalize_text(sentence)
    bits = [author, work]
    matched_authors = []
    for canonical, names in aliases.get("author_aliases", {}).items():
        all_names = [canonical, *names]
        if any(normalize_text(name) in norm_sentence for name in all_names):
            matched_authors.append(canonical)
            bits.append(canonical)
            bits.extend(
                name
                for name in names
                if name.isascii() and normalize_text(name) not in normalize_text(canonical)
            )
    for canonical, names in aliases.get("title_aliases", {}).items():
        all_names = [canonical, *names]
        if any(normalize_text(name) in norm_sentence for name in all_names):
            bits.append(canonical)
            bits.extend(name for name in names if name.isascii())
    for author_name in matched_authors:
        bits.extend(aliases.get("author_default_works", {}).get(author_name, []))
    clean_bits = []
    seen = set()
    for bit in bits:
        key = normalize_text(bit)
        if bit and key and key not in seen:
            clean_bits.append(bit)
            seen.add(key)
    return clean_bits


def expand_queries(
    sentence: str,
    author: str = "",
    work: str = "",
    max_per_language: int = 8,
) -> Dict[str, Any]:
    keyword_plan = expand_keywords(sentence, author=author, work=work)
    concepts = detect_concepts(sentence)
    known_patterns = matched_known_patterns(sentence)
    queries: List[Dict[str, Any]] = []

    context_bits = infer_context_bits(sentence, author, work)
    context = " ".join(context_bits)

    for item in keyword_plan.get("queries", []):
        language = item.get("language", "ko")
        source_hints = LANG_SOURCE_HINTS.get(language, [])
        if language == "multi":
            source_hints = [
                "wikisource_en",
                "wikisource_fr",
                "wikisource_de",
                "wikisource_la",
                "gutenberg",
                "internet_archive",
                "openlibrary",
            ]
        queries.append(
            make_query(
                item["query"],
                item.get("category", "ko_keyword_expanded"),
                language,
                source_hints,
                item.get("purpose", "Expanded Korean keyword search."),
            )
        )

    for fragment in split_korean_fragments(sentence):
        q = f"{fragment} {context}".strip()
        queries.append(
            make_query(
                q,
                "ko_direct",
                "ko",
                LANG_SOURCE_HINTS["ko"],
                "Search the Korean wording as given or remembered.",
            )
        )

    for pattern in known_patterns:
        for q in pattern.get("queries", []):
            q = append_missing_context(q, context_bits)
            queries.append(
                make_query(
                    q,
                    "known_quote_bridge",
                    "multi",
                    ["wikisource_en", "wikisource_fr", "wikisource_de", "wikisource_la", "gutenberg", "internet_archive", "openlibrary"],
                    "Use a known cross-language quote bridge.",
                )
            )

    for lang in ("en", "fr", "de", "la", "grc", "zh"):
        lang_terms = []
        for concept in concepts:
            lang_terms.extend(concept.get(lang, []))
        lang_terms = list(dict.fromkeys(lang_terms))
        single_terms = lang_terms[:max_per_language]
        for term in single_terms:
            q = f"{term} {context}".strip()
            queries.append(
                make_query(
                    q,
                    "concept_term",
                    lang,
                    LANG_SOURCE_HINTS.get(lang, []),
                    "Search a likely source-language concept term.",
                )
            )
        for pair in itertools.combinations(single_terms[:5], 2):
            q = f"{pair[0]} {pair[1]} {context}".strip()
            queries.append(
                make_query(
                    q,
                    "concept_combination",
                    lang,
                    LANG_SOURCE_HINTS.get(lang, []),
                    "Search a combination of likely source-language terms.",
                )
            )

    deduped = []
    seen = set()
    for query in queries:
        key = normalize_text(query["query"])
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(query)

    return {
        "input_sentence": sentence,
        "author_hint": author,
        "work_hint": work,
        "created": today(),
        "analysis": {
            "matched_concepts": [
                {
                    "ko": concept.get("ko", []),
                    "notes": concept.get("notes", ""),
                    "source_terms": {
                        lang: concept.get(lang, [])
                        for lang in ("en", "fr", "de", "la", "grc", "zh")
                        if concept.get(lang)
                    },
                }
                for concept in concepts
            ],
            "known_patterns": known_patterns,
            "korean_keyword_plan": {
                "prefix": keyword_plan.get("prefix", ""),
                "body": keyword_plan.get("body", ""),
                "tokens": keyword_plan.get("tokens", []),
                "inferred_context": keyword_plan.get("inferred_context", []),
                "keyword_groups": keyword_plan.get("keyword_groups", []),
            },
            "provisional_judgment": "Treat the input as a remembered translation or paraphrase until source evidence proves otherwise.",
        },
        "queries": deduped,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Expand a Korean translated sentence into multilingual trace queries.")
    parser.add_argument("sentence")
    parser.add_argument("--author", default="")
    parser.add_argument("--work", default="")
    parser.add_argument("--output", default=str(PROJECT_ROOT / "results" / "trace_query_plan.json"))
    args = parser.parse_args()

    payload = expand_queries(args.sentence, args.author, args.work)
    write_json(args.output, payload)
    print(f"Wrote {args.output}. Queries: {len(payload['queries'])}")


if __name__ == "__main__":
    main()
