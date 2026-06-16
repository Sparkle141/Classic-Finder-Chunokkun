# Claude Instructions

This folder is a self-contained workflow for finding public-domain, Creative Commons, or open-access classical and scholarly texts, then preparing Korean translation materials.

Read `AGENTS.md` and the files under `instructions/` before acting. Use the Python scripts in `scripts/` rather than inventing a new workflow.

Default flow:

```bash
python scripts/search_all.py "QUERY"
python scripts/resolve_work.py results/search_results.json "TARGET"
python scripts/build_manifest.py "URL"
python scripts/extract_text.py "URL"
python scripts/make_citation.py results/extracted_text.json
python scripts/translate_ko.py results/extracted_text.json
```

Reverse-trace flow for Korean translated or remembered sentences:

```bash
python scripts/expand_korean_keywords.py "KOREAN SENTENCE" --author "AUTHOR_HINT" --work "WORK_HINT"
python scripts/reverse_trace_multilingual.py "KOREAN SENTENCE" --author "AUTHOR_HINT" --work "WORK_HINT"
python scripts/make_trace_report.py results/reverse_trace_results.json
```

When handling uncertain copyright status, be conservative. If a source is only useful as a clue, label it `discovery_only`.
