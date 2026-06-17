# Agent Starter Prompt

You are operating inside `Classic-Finder-Chunokkun`.

Goal:

Find reliable public-domain, Creative Commons, or open-access classical and scholarly texts, verify rights, extract clean source text, make citation data, and prepare Korean translation.

Workflow:

1. Read `AGENTS.md`.
2. Read `instructions/COMMON_WORKFLOW.md`.
3. Read `instructions/SOURCE_POLICY.md`.
4. Use scripts under `scripts/`.
5. Save final outputs under `results/`.

Rules:

- Do not translate from an unverified web page.
- Do not rely on Scribd or similar upload sites as final source.
- Prefer structured APIs.
- Record source URL, stable identifier, access date, and rights status.
- If rights are unclear, say so and stop before reuse.
- If the user starts from a Korean translation or remembered quote, use the multilingual reverse-trace workflow and present candidates by source layer.
