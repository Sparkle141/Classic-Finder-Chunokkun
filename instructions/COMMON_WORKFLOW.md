# Common Workflow

## 1. Clarify the Target

Extract these fields from the user request:

- author
- title
- section, book, chapter, paragraph, sutra number, fascicle, or passage
- language
- preferred source if given
- desired output: citation, Korean translation, source text, bibliography, or all

If the user provides a Korean sentence that may be a translation, paraphrase, or remembered quote, switch to the reverse-trace workflow in `REVERSE_TRACE_MULTILINGUAL.md`.

## 2. Search Multiple Sources

Run:

```bash
python scripts/search_all.py "QUERY"
```

For Western classics, prioritize:

- Wikisource
- Project Gutenberg
- Internet Archive
- HathiTrust
- Open Library
- Perseus/Scaife for Greek and Latin

For scholarship, prioritize:

- DOAJ for articles
- DOAB/OAPEN for books
- OpenAlex or Crossref only as metadata aids if added later

For Classical Chinese and East Asian materials, prioritize:

- Chinese Wikisource
- Kanseki Repository
- CBETA for Buddhist texts
- Chinese Text Project as search and comparison aid
- Korean Classics DB and Korean History DB as Korea-facing research sources

## 3. Resolve the Work

Run:

```bash
python scripts/resolve_work.py results/search_results.json "TARGET"
```

Do not merge editions casually. Keep editions separate if publication year, editor, translator, source scan, or text family differs.

## 4. Build a Manifest

Run:

```bash
python scripts/build_manifest.py "URL"
```

The manifest should capture:

- work title
- source
- stable identifier
- version or edition
- table of contents
- subpages
- sections and anchors
- parent/child structure

Use this step before extraction for works with multiple books, treatises, fascicles, chapters, or page ranges.

## 5. Check Rights

Run:

```bash
python scripts/rights_check.py results/selected_work.json
```

If the result is `unknown`, `search_only`, or `discovery_only`, do not use the text as a final source.

## 6. Extract Text

Run:

```bash
python scripts/extract_text.py "URL"
```

The extractor should remove navigation, menus, edit links, scripts, categories, and unrelated UI text. Preserve paragraph order and source section labels.

## 7. Make Citation

Run:

```bash
python scripts/make_citation.py results/extracted_text.json
```

Include at least:

- author
- title
- edition or publication year
- section
- source site
- URL
- stable URL or identifier
- accessed date
- rights status

## 8. Prepare Korean Translation

Run:

```bash
python scripts/translate_ko.py results/extracted_text.json
```

The translation worksheet should preserve paragraph IDs and include term notes for recurring concepts.

## 9. Reverse Trace From Korean

Run:

```bash
python scripts/reverse_trace_multilingual.py "KOREAN SENTENCE" --author "AUTHOR_HINT" --work "WORK_HINT"
python scripts/make_trace_report.py results/reverse_trace_results.json
```

Use this when the task starts from Korean wording rather than a known source URL. The output must remain candidate-based until passage alignment proves the source.
