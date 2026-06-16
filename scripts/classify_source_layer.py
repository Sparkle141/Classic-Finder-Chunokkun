from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from common import PROJECT_ROOT, classify_source_layer, flatten_results, read_json, write_json


def main() -> None:
    parser = argparse.ArgumentParser(description="Annotate search results with source-layer labels.")
    parser.add_argument("input_json")
    parser.add_argument("--output", default=str(PROJECT_ROOT / "results" / "layer_classified.json"))
    args = parser.parse_args()

    payload: Any = read_json(Path(args.input_json))
    records = flatten_results(payload)
    annotated = []
    for record in records:
        item = dict(record)
        item.update(classify_source_layer(item))
        annotated.append(item)
    write_json(args.output, {"count": len(annotated), "results": annotated})
    print(f"Wrote {args.output}. Annotated: {len(annotated)}")


if __name__ == "__main__":
    main()

