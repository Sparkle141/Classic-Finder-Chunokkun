from __future__ import annotations

import datetime as _dt
import html
import json
import re
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = PROJECT_ROOT / "config"
RESULTS_DIR = PROJECT_ROOT / "results"
WORK_DIR = PROJECT_ROOT / "work"

USER_AGENT = (
    "ClassicFinderAgentKit/0.1 "
    "(research and citation workflow; contact: local-user)"
)


def today() -> str:
    return _dt.date.today().isoformat()


def ensure_dirs() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    WORK_DIR.mkdir(parents=True, exist_ok=True)


def read_json(path: Path | str) -> Any:
    with Path(path).open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path | str, data: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def write_text(path: Path | str, text: str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load_sources() -> List[Dict[str, Any]]:
    return read_json(CONFIG_DIR / "sources.json")["sources"]


def load_rights_policy() -> Dict[str, Any]:
    return read_json(CONFIG_DIR / "rights_policy.json")


def load_aliases() -> Dict[str, Any]:
    return read_json(CONFIG_DIR / "aliases.json")


def load_korean_keyword_expansion() -> Dict[str, Any]:
    return read_json(CONFIG_DIR / "korean_keyword_expansion.json")


def load_multilingual_terms() -> Dict[str, Any]:
    return read_json(CONFIG_DIR / "multilingual_terms.json")


def load_source_layers() -> Dict[str, Any]:
    return read_json(CONFIG_DIR / "source_layers.json")


def http_get_text(
    url: str,
    params: Optional[Dict[str, Any]] = None,
    timeout: int = 30,
) -> str:
    if params:
        query = urllib.parse.urlencode(params, doseq=True)
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}{query}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        raw = response.read()
        charset = response.headers.get_content_charset() or "utf-8"
    return raw.decode(charset, errors="replace")


def http_get_json(
    url: str,
    params: Optional[Dict[str, Any]] = None,
    timeout: int = 30,
) -> Any:
    text = http_get_text(url, params=params, timeout=timeout)
    return json.loads(text)


def normalize_text(text: Any) -> str:
    if text is None:
        return ""
    text = html.unescape(str(text))
    text = unicodedata.normalize("NFKC", text)
    text = text.lower()
    text = re.sub(r"[_\-/,:;()\[\]{}'\".!?]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def compact_whitespace(text: str) -> str:
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    lines = [line for line in lines if line]
    return "\n\n".join(lines)


def slugify(text: str, max_len: int = 80) -> str:
    text = normalize_text(text)
    text = re.sub(r"[^a-z0-9가-힣一-龥ぁ-んァ-ン]+", "-", text).strip("-")
    return (text[:max_len] or "untitled").strip("-")


def source_by_id(source_id: str) -> Optional[Dict[str, Any]]:
    for source in load_sources():
        if source["id"] == source_id:
            return source
    return None


def maybe_path(value: str) -> Optional[Path]:
    path = Path(value)
    if path.exists():
        return path
    root_path = PROJECT_ROOT / value
    if root_path.exists():
        return root_path
    return None


def score_candidate(query: str, candidate: Dict[str, Any]) -> float:
    fields = [
        candidate.get("title"),
        candidate.get("author"),
        candidate.get("date"),
        candidate.get("section"),
        candidate.get("identifier"),
        candidate.get("snippet"),
        candidate.get("url"),
    ]
    haystack = normalize_text(" ".join(str(x) for x in fields if x))
    needle = normalize_text(query)
    if not needle or not haystack:
        return 0.0
    q_refs = extract_section_refs(needle)
    h_refs = extract_section_refs(haystack)
    ref_adjustment = section_ref_adjustment(q_refs, h_refs)
    if needle in haystack:
        return max(0.0, min(1.0, 1.0 + ref_adjustment))
    q_tokens = set(needle.split())
    h_tokens = set(haystack.split())
    overlap = len(q_tokens & h_tokens)
    base = overlap / max(len(q_tokens), 1)
    title = normalize_text(candidate.get("title", ""))
    title_bonus = 0.2 if any(token in title for token in q_tokens) else 0.0
    source_bonus = {
        "primary_text": 0.12,
        "primary_text_noncommercial": 0.08,
        "metadata": 0.04,
        "search_only": -0.05,
        "discovery_only": -0.15,
    }.get(candidate.get("source_role", ""), 0.0)
    return max(0.0, min(1.0, base + title_bonus + source_bonus + ref_adjustment))


ROMAN = {
    "i": 1,
    "ii": 2,
    "iii": 3,
    "iv": 4,
    "v": 5,
    "vi": 6,
    "vii": 7,
    "viii": 8,
    "ix": 9,
    "x": 10,
    "xi": 11,
    "xii": 12,
    "xiii": 13,
    "xiv": 14,
    "xv": 15,
    "xvi": 16,
    "xvii": 17,
    "xviii": 18,
    "xix": 19,
    "xx": 20,
    "xxi": 21,
    "xxii": 22,
    "xxiii": 23,
    "xxiv": 24,
    "xxv": 25,
    "xxvi": 26,
    "xxvii": 27,
    "xxviii": 28,
    "xxix": 29,
    "xxx": 30,
    "xxxix": 39,
}


def _number_value(value: str) -> Optional[int]:
    value = normalize_text(value)
    if value.isdigit():
        return int(value)
    return ROMAN.get(value)


def extract_section_refs(text: str) -> Dict[str, set[int]]:
    text = normalize_text(text)
    refs: Dict[str, set[int]] = {}
    patterns = {
        "chapter": r"\b(?:chapter|chap|ch)\s+([0-9]+|[ivxlcdm]+)\b",
        "book": r"\b(?:book)\s+([0-9]+|[ivxlcdm]+)\b",
        "volume": r"\b(?:volume|vol|v)\s+([0-9]+|[ivxlcdm]+)\b",
        "part": r"\b(?:part|pt)\s+([0-9]+|[ivxlcdm]+)\b",
    }
    for kind, pattern in patterns.items():
        for match in re.finditer(pattern, text):
            number = _number_value(match.group(1))
            if number is not None:
                refs.setdefault(kind, set()).add(number)
    return refs


def section_ref_adjustment(
    query_refs: Dict[str, set[int]],
    candidate_refs: Dict[str, set[int]],
) -> float:
    adjustment = 0.0
    for kind, q_numbers in query_refs.items():
        h_numbers = candidate_refs.get(kind)
        if not h_numbers:
            continue
        if q_numbers & h_numbers:
            adjustment += 0.25
        else:
            adjustment -= 0.45
    return adjustment


def classify_rights_from_text(
    text: str,
    source_role: str = "",
    rights_default: str = "",
) -> Dict[str, str]:
    policy = load_rights_policy()
    text_norm = normalize_text(f"{text} {rights_default}")
    if "cc_by_sa_or_public_domain" in rights_default:
        return {
            "rights_status": "cc_by_sa",
            "rights_note": "Source default is CC BY-SA site text with public-domain source works where applicable.",
        }
    for status, patterns in policy["license_patterns"].items():
        for pattern in patterns:
            if normalize_text(pattern) in text_norm:
                return {"rights_status": status, "rights_note": f"Matched pattern: {pattern}"}
    if source_role == "discovery_only":
        return {"rights_status": "discovery_only", "rights_note": "Source role is discovery-only."}
    if source_role == "search_only":
        return {"rights_status": "search_only", "rights_note": "Source role is search-only."}
    if rights_default == "cc_by_sa" or "cc_by_sa" in rights_default:
        return {"rights_status": "cc_by_sa", "rights_note": "Source default indicates CC BY-SA handling."}
    if "cc_by_nc_sa" in rights_default:
        return {"rights_status": "cc_by_nc_sa", "rights_note": "Source default indicates CC BY-NC-SA handling."}
    if "public_domain" in rights_default:
        return {"rights_status": "public_domain", "rights_note": "Source default indicates public-domain-oriented collection."}
    if "metadata" in rights_default:
        return {"rights_status": "metadata_only", "rights_note": "Metadata source, not final text source."}
    return {"rights_status": "unknown", "rights_note": "No clear rights pattern found."}


def classify_source_layer(record: Dict[str, Any]) -> Dict[str, str]:
    layers = load_source_layers()
    source_id = str(record.get("source_id", ""))
    role = str(record.get("source_role", ""))
    text = normalize_text(
        " ".join(
            str(record.get(k, ""))
            for k in ("title", "snippet", "url", "source_name", "notes")
        )
    )
    if role == "discovery_only":
        layer_id = "discovery_only"
    elif source_id in {"doaj", "doab", "openlibrary", "hathitrust"}:
        layer_id = "modern_secondary_explanation" if source_id == "doaj" else "unknown"
    elif source_id in {"perseus_scaife", "wikisource_la", "wikisource_el"}:
        layer_id = "original_language_primary"
    elif source_id in {"wikisource_fr", "wikisource_de"}:
        layer_id = "original_language_primary"
    elif source_id == "wikisource_en":
        layer_id = "original_language_primary"
        if "translation" in text or "translated" in text:
            layer_id = "early_or_classic_translation"
    elif source_id in {"gutenberg", "internet_archive"}:
        layer_id = "unknown"
    else:
        layer_id = "unknown"
    for candidate_layer, hints in layers.get("keyword_hints", {}).items():
        if any(normalize_text(hint) in text for hint in hints):
            layer_id = candidate_layer
            break
    layer = next((x for x in layers["layers"] if x["id"] == layer_id), None)
    return {
        "source_layer": layer_id,
        "source_layer_label": layer["label"] if layer else "층위 불명",
    }


def make_record(
    source: Dict[str, Any],
    title: str,
    url: str,
    **extra: Any,
) -> Dict[str, Any]:
    rights_info = classify_rights_from_text(
        " ".join(str(extra.get(k, "")) for k in ("license_url", "rights", "notes")),
        source_role=source.get("role", ""),
        rights_default=source.get("rights_default", ""),
    )
    record = {
        "source_id": source["id"],
        "source_name": source["name"],
        "source_role": source.get("role", ""),
        "title": title,
        "url": url,
        "rights_status": rights_info["rights_status"],
        "rights_note": rights_info["rights_note"],
        "accessed": today(),
    }
    record.update({k: v for k, v in extra.items() if v is not None})
    return record


def flatten_results(payload: Any) -> List[Dict[str, Any]]:
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if isinstance(payload, dict):
        if "results" in payload and isinstance(payload["results"], list):
            return [x for x in payload["results"] if isinstance(x, dict)]
        if "alternatives" in payload and isinstance(payload["alternatives"], list):
            items = []
            if isinstance(payload.get("selected"), dict):
                items.append(payload["selected"])
            items.extend(x for x in payload["alternatives"] if isinstance(x, dict))
            return items
        return [payload]
    return []


def unique_records(records: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    unique = []
    for record in records:
        key = (
            record.get("source_id"),
            record.get("identifier") or record.get("url") or record.get("title"),
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(record)
    return unique


def fetch_safely(label: str, func, *args, **kwargs) -> Dict[str, Any]:
    try:
        return {"ok": True, "value": func(*args, **kwargs)}
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        return {"ok": False, "error": f"{label}: {exc}"}
