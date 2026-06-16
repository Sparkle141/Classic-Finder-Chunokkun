# Agent Instructions

You are working inside the Classic Finder Agent Kit. Your task is to find openly usable classical or scholarly texts, verify their source and rights status, prepare bibliographic citation, and support Korean translation.

Always follow these files first:

1. `instructions/COMMON_WORKFLOW.md`
2. `instructions/SOURCE_POLICY.md`
3. `instructions/TRANSLATION_KO.md`
4. `instructions/REVERSE_TRACE_MULTILINGUAL.md` when the input is a Korean translation, paraphrase, or remembered quote.

## Operating Rules

- Do not translate immediately from a random web page.
- First identify the work, edition, section, source URL, stable URL or revision ID, and rights status.
- Prefer structured APIs over scraping HTML.
- Treat Scribd and similar upload platforms as discovery-only unless the document itself contains a verifiable license and the same text is confirmed from a trusted source.
- For Chinese, Korean, Japanese, and Classical Chinese materials, normalize variants and search multiple names.
- Save intermediate artifacts to `work/`.
- Save final artifacts to `results/`.
- When unsure about a source's rights status, mark it `unknown` or `search_only` and explain why.

## Standard Commands

```bash
python scripts/search_all.py "QUERY"
python scripts/resolve_work.py results/search_results.json "TARGET SECTION"
python scripts/build_manifest.py "SOURCE_URL"
python scripts/rights_check.py results/selected_work.json
python scripts/extract_text.py "SOURCE_URL"
python scripts/make_citation.py results/extracted_text.json
python scripts/translate_ko.py results/extracted_text.json
```

For reverse tracing from a Korean sentence:

```bash
python scripts/expand_korean_keywords.py "KOREAN SENTENCE" --author "AUTHOR_HINT" --work "WORK_HINT"
python scripts/expand_multilingual_queries.py "KOREAN SENTENCE" --author "AUTHOR_HINT" --work "WORK_HINT"
python scripts/reverse_trace_multilingual.py "KOREAN SENTENCE" --author "AUTHOR_HINT" --work "WORK_HINT"
python scripts/make_trace_report.py results/reverse_trace_results.json
```

## Completion Criteria

A task is complete only when the result includes:

- source title
- author or editor if available
- edition or publication year if available
- source URL
- stable URL, oldid, item identifier, DOI, URN, or equivalent if available
- rights status
- citation
- extracted source text or a clear reason extraction was not allowed
- Korean translation worksheet or finished Korean translation

For reverse-trace tasks, completion also requires:

- Korean input preserved exactly
- Korean keyword expansion plan
- multilingual query plan
- source-layer labels
- up to five candidates
- uncertainty notes
- user-facing selection request
