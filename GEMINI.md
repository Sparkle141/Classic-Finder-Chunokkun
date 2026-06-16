# Gemini Instructions

This project contains a standard workflow for public classical text discovery and Korean translation preparation.

Use the instructions in `AGENTS.md` and `instructions/`. Prefer the provided scripts and keep outputs in `results/`.

Never assume a text is reusable because it appears online. Record the source, edition, stable identifier, and rights status before translation.

If the user provides a Korean sentence and asks where it came from, use `scripts/reverse_trace_multilingual.py` and report candidates by source layer. Do not assert a final source without passage-level verification.
