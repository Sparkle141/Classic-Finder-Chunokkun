from __future__ import annotations

import argparse
import urllib.parse
from typing import Any, Dict, List

from common import (
    PROJECT_ROOT,
    ensure_dirs,
    fetch_safely,
    http_get_json,
    load_sources,
    make_record,
    score_candidate,
    unique_records,
    write_json,
)


def search_wikisource(source: Dict[str, Any], query: str, limit: int) -> List[Dict[str, Any]]:
    data = http_get_json(
        source["api_url"],
        {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srlimit": limit,
            "format": "json",
            "utf8": 1,
        },
    )
    records = []
    for item in data.get("query", {}).get("search", []):
        title = item.get("title", "")
        url = f'{source["base_url"]}/wiki/{urllib.parse.quote(title.replace(" ", "_"))}'
        records.append(
            make_record(
                source,
                title=title,
                url=url,
                identifier=str(item.get("pageid", "")),
                snippet=item.get("snippet", ""),
            )
        )
    return records


def search_gutenberg(source: Dict[str, Any], query: str, limit: int) -> List[Dict[str, Any]]:
    data = http_get_json(source["api_url"], {"search": query})
    records = []
    for item in data.get("results", [])[:limit]:
        authors = item.get("authors") or []
        author = "; ".join(a.get("name", "") for a in authors if a.get("name"))
        ebook_id = item.get("id")
        rights = "public domain" if item.get("copyright") is False else "permission or unknown"
        records.append(
            make_record(
                source,
                title=item.get("title", ""),
                url=f'https://www.gutenberg.org/ebooks/{ebook_id}',
                identifier=str(ebook_id),
                author=author,
                language=", ".join(item.get("languages") or []),
                rights=rights,
                formats=item.get("formats", {}),
            )
        )
    return records


def search_internet_archive(source: Dict[str, Any], query: str, limit: int) -> List[Dict[str, Any]]:
    params = {
        "q": f'({query}) AND mediatype:texts',
        "fl[]": [
            "identifier",
            "title",
            "creator",
            "date",
            "licenseurl",
            "rights",
            "mediatype",
            "downloads",
            "publicdate",
            "language",
            "subject",
        ],
        "rows": limit,
        "page": 1,
        "output": "json",
    }
    data = http_get_json(source["api_url"], params)
    records = []
    for item in data.get("response", {}).get("docs", []):
        identifier = item.get("identifier", "")
        records.append(
            make_record(
                source,
                title=item.get("title", identifier),
                url=f"https://archive.org/details/{identifier}",
                identifier=identifier,
                author=item.get("creator"),
                date=item.get("date"),
                license_url=item.get("licenseurl"),
                rights=item.get("rights"),
                raw=item,
            )
        )
    return records


def search_openlibrary(source: Dict[str, Any], query: str, limit: int) -> List[Dict[str, Any]]:
    data = http_get_json(
        source["api_url"],
        {
            "q": query,
            "limit": limit,
            "fields": "key,title,author_name,first_publish_year,ia,ebook_access,language",
        },
    )
    records = []
    for item in data.get("docs", [])[:limit]:
        key = item.get("key", "")
        ia_ids = item.get("ia") or []
        records.append(
            make_record(
                source,
                title=item.get("title", ""),
                url=f'https://openlibrary.org{key}',
                identifier=key,
                author="; ".join(item.get("author_name") or []),
                date=item.get("first_publish_year"),
                internet_archive_ids=ia_ids,
                ebook_access=item.get("ebook_access"),
                raw=item,
            )
        )
    return records


def search_doaj(source: Dict[str, Any], query: str, limit: int) -> List[Dict[str, Any]]:
    encoded = urllib.parse.quote(query)
    url = f'{source["api_url"].rstrip("/")}/{encoded}'
    data = http_get_json(url, {"pageSize": limit})
    records = []
    for item in data.get("results", [])[:limit]:
        bibjson = item.get("bibjson", {})
        links = bibjson.get("link") or []
        fulltext = next((x.get("url") for x in links if x.get("url")), "")
        records.append(
            make_record(
                source,
                title=bibjson.get("title", ""),
                url=fulltext or item.get("id", ""),
                identifier=item.get("id"),
                author="; ".join(
                    a.get("name", "") for a in bibjson.get("author", []) if a.get("name")
                ),
                date=bibjson.get("year"),
                license_url=(bibjson.get("license") or [{}])[0].get("url"),
                raw=item,
            )
        )
    return records


def manual_hint(source: Dict[str, Any], query: str) -> List[Dict[str, Any]]:
    quoted = urllib.parse.quote(query)
    url = source.get("base_url", "")
    if source["id"] == "scribd":
        url = f"https://www.scribd.com/search?query={quoted}"
    elif source["id"] == "ctext":
        url = f"https://ctext.org/searchbooks.pl?if=en&searchu={quoted}"
    elif source["id"] == "hathitrust":
        url = f"https://catalog.hathitrust.org/Search/Home?lookfor={quoted}&searchtype=all"
    elif source["id"] == "perseus_scaife":
        url = f"https://scaife.perseus.org/search/?q={quoted}"
    elif source["id"] == "doab":
        url = f"https://directory.doabooks.org/discover?query={quoted}"
    elif source["id"] == "oapen":
        url = f"https://library.oapen.org/discover?query={quoted}"
    return [
        make_record(
            source,
            title=f"Manual search: {query}",
            url=url,
            snippet="This source has no default automated extractor in the starter kit.",
        )
    ]


SEARCHERS = {
    "wikisource_en": search_wikisource,
    "wikisource_zh": search_wikisource,
    "gutenberg": search_gutenberg,
    "internet_archive": search_internet_archive,
    "openlibrary": search_openlibrary,
    "doaj": search_doaj,
}


def run(query: str, limit: int, source_ids: List[str]) -> Dict[str, Any]:
    ensure_dirs()
    records: List[Dict[str, Any]] = []
    errors: List[str] = []
    for source in load_sources():
        if source_ids and source["id"] not in source_ids:
            continue
        searcher = search_wikisource if source["id"].startswith("wikisource_") else SEARCHERS.get(source["id"])
        if searcher:
            result = fetch_safely(source["id"], searcher, source, query, limit)
            if result["ok"]:
                records.extend(result["value"])
            else:
                errors.append(result["error"])
        else:
            records.extend(manual_hint(source, query))
    records = unique_records(records)
    for record in records:
        record["score"] = round(score_candidate(query, record), 4)
    records.sort(key=lambda x: x.get("score", 0), reverse=True)
    return {
        "query": query,
        "count": len(records),
        "results": records,
        "errors": errors,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Search multiple open text sources.")
    parser.add_argument("query")
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--sources", default="", help="Comma-separated source IDs.")
    parser.add_argument("--output", default=str(PROJECT_ROOT / "results" / "search_results.json"))
    args = parser.parse_args()

    source_ids = [x.strip() for x in args.sources.split(",") if x.strip()]
    payload = run(args.query, args.limit, source_ids)
    write_json(args.output, payload)
    print(f"Wrote {args.output} with {payload['count']} records.")
    if payload["errors"]:
        print("Some sources returned errors. See JSON for details.")


if __name__ == "__main__":
    main()
