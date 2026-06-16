from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Dict

from common import (
    PROJECT_ROOT,
    classify_rights_from_text,
    flatten_results,
    maybe_path,
    read_json,
    source_by_id,
    write_json,
)


def classify_record(record: Dict[str, Any]) -> Dict[str, Any]:
    source = source_by_id(record.get("source_id", "")) or {}
    text = " ".join(
        str(record.get(k, ""))
        for k in (
            "rights",
            "license_url",
            "rights_status",
            "rights_note",
            "url",
            "notes",
            "ebook_access",
        )
    )
    info = classify_rights_from_text(
        text,
        source_role=record.get("source_role") or source.get("role", ""),
        rights_default=source.get("rights_default", ""),
    )
    checked = dict(record)
    checked.update(info)
    checked["reuse_allowed_for_translation"] = info["rights_status"] in {
        "public_domain",
        "cc_by",
        "cc_by_sa",
        "cc_by_nc_sa",
        "open_access",
    }
    checked["distribution_warning"] = info["rights_status"] in {
        "cc_by_nc_sa",
        "open_access",
    }
    return checked


def load_input(value: str) -> Any:
    path = maybe_path(value)
    if path:
        return read_json(path)
    return {"url": value, "rights_status": "unknown"}


def main() -> None:
    parser = argparse.ArgumentParser(description="Classify rights status for records.")
    parser.add_argument("input", help="JSON path or URL.")
    parser.add_argument("--output", default=str(PROJECT_ROOT / "results" / "rights_checked.json"))
    args = parser.parse_args()

    payload = load_input(args.input)
    records = flatten_results(payload)
    checked = [classify_record(record) for record in records]
    output: Any = {"count": len(checked), "results": checked}
    if len(checked) == 1:
        output = checked[0]
    write_json(args.output, output)
    print(f"Wrote {args.output}. Checked: {len(checked)}")


if __name__ == "__main__":
    main()

