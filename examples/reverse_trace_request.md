# Reverse Trace Request Template

## User Request

Find the likely source of this Korean sentence:

```text

```

## Optional Context

- Author hint:
- Work hint:
- Period:
- Topic:
- Was this from a book, class, article, lecture, or memory?

## Agent Checklist

- [ ] Preserve the Korean sentence exactly.
- [ ] Treat it as a possible paraphrase until proven otherwise.
- [ ] Generate Korean direct searches.
- [ ] Generate English bridge searches.
- [ ] Generate source-language concept searches.
- [ ] Separate original, translation, commentary, later interpretation, and modern explanation.
- [ ] Return no more than five candidates.
- [ ] Ask the user to select the closest candidate before finalizing.

## Commands

```bash
python scripts/expand_korean_keywords.py "KOREAN SENTENCE" --author "AUTHOR_HINT" --work "WORK_HINT"
python scripts/reverse_trace_multilingual.py "KOREAN SENTENCE" --author "AUTHOR_HINT" --work "WORK_HINT"
python scripts/make_trace_report.py results/reverse_trace_results.json
```
