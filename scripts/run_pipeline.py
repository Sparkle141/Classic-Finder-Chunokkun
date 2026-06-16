from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from common import PROJECT_ROOT


def run_step(args: list[str]) -> None:
    print("Running:", " ".join(args))
    subprocess.run([sys.executable, *args], cwd=PROJECT_ROOT, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a basic search-to-worksheet pipeline.")
    parser.add_argument("query")
    parser.add_argument("--target", default="")
    parser.add_argument("--url", default="", help="Known source URL. If omitted, only search/resolve runs.")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--reverse-trace", action="store_true", help="Treat query as Korean translated or remembered wording.")
    parser.add_argument("--author", default="")
    parser.add_argument("--work", default="")
    args = parser.parse_args()

    if args.reverse_trace:
        run_step(
            [
                "scripts/expand_korean_keywords.py",
                args.query,
                "--author",
                args.author,
                "--work",
                args.work,
            ]
        )
        run_step(
            [
                "scripts/reverse_trace_multilingual.py",
                args.query,
                "--author",
                args.author,
                "--work",
                args.work,
                "--query-limit",
                str(args.limit),
            ]
        )
        run_step(["scripts/make_trace_report.py", "results/reverse_trace_results.json"])
        return

    target = args.target or args.query
    run_step(["scripts/search_all.py", args.query, "--limit", str(args.limit)])
    run_step(["scripts/resolve_work.py", "results/search_results.json", target])
    if args.url:
        run_step(["scripts/build_manifest.py", args.url])
        run_step(["scripts/extract_text.py", args.url])
        run_step(["scripts/make_citation.py", "results/extracted_text.json"])
        run_step(["scripts/translate_ko.py", "results/extracted_text.json"])
    else:
        print("No URL supplied. Review results/selected_work.json, then rerun with --url.")


if __name__ == "__main__":
    main()
