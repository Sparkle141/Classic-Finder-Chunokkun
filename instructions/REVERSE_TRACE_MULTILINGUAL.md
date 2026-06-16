# Multilingual Reverse Trace

Use this workflow when the user gives a Korean sentence that may be a translation, paraphrase, lecture note, textbook formulation, or remembered version of a classical passage.

## Core Idea

Do not assume the Korean sentence is a direct translation of the source text. It may derive from:

- source-language original
- influential old translation
- modern English/French/German/Korean translation
- commentary or traditional interpretation
- later scholar's paraphrase
- lecture, textbook, encyclopedia, or blog summary

The correct output is a candidate report, not a single asserted answer.

## Standard Flow

```bash
python scripts/expand_korean_keywords.py "KOREAN SENTENCE" --author "AUTHOR_HINT" --work "WORK_HINT"
python scripts/expand_multilingual_queries.py "KOREAN SENTENCE" --author "AUTHOR_HINT" --work "WORK_HINT"
python scripts/reverse_trace_multilingual.py "KOREAN SENTENCE" --author "AUTHOR_HINT" --work "WORK_HINT"
python scripts/make_trace_report.py results/reverse_trace_results.json
```

Use `--plan-only` when you want to inspect search terms without network search:

```bash
python scripts/reverse_trace_multilingual.py "KOREAN SENTENCE" --plan-only
```

## Search Branches

1. Korean wording as-is
2. Korean body text without author/test-label prefix
3. Korean content words
4. Korean paraphrase and synonym bundles
5. Known cross-language quote bridges
6. English concept terms
7. French concept terms
8. German concept terms
9. Latin concept terms
10. Greek concept terms
11. Classical Chinese terms when relevant

## Korean Keyword Expansion

`expand_korean_keywords.py` is the recall booster. It does not translate authoritatively. It creates broad search bundles from:

- author/title prefixes such as `홉스:`
- content words after removing light particles and endings
- Korean paraphrase variants
- mixed Korean-English concepts
- known bridge recipes such as Hobbes's state of nature or Rousseau's born-free passage

Use its output to inspect whether the search plan is wide enough before judging the reverse trace.

## Western Classics Layering

Always distinguish:

- `원어 원전`: Greek, Latin, French, German, source-language English, Italian, etc.
- `고전적 번역본`: influential older translation, such as a public-domain English translation
- `현대 번역본`: modern translation
- `주석·전통 해석`: commentary, scholia, gloss, exegetical tradition
- `후대 학자 해석`: later reception or scholarly interpretation
- `현대 해설·2차 문헌`: textbook, lecture, encyclopedia, summary
- `단서 자료`: useful clue only

## Examples

Korean:

```text
인간은 자유롭게 태어났지만 어디에서나 사슬에 묶여 있다.
```

Likely query branches:

```text
인간은 자유롭게 태어났지만 어디에서나 사슬에 묶여 있다 Rousseau
Man is born free and everywhere he is in chains Rousseau
L'homme est ne libre et partout il est dans les fers
liberty chains Rousseau
liberte fers Rousseau
```

Potential layers:

- Rousseau's French original
- public-domain English translation
- Korean translation
- textbook summary

## Prohibited Moves

- Do not call a candidate "confirmed" without passage-level alignment.
- Do not treat a famous English translation as the original when the original is French, German, Latin, Greek, etc.
- Do not flatten technical terms across languages: `reason`, `ratio`, `raison`, `Vernunft`, `Verstand`, `logos`, and `nous` may differ.
- Do not use a clue source as final citation evidence.
- Do not merge direct quotation and conceptual source.
