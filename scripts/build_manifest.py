from __future__ import annotations

import argparse
import re
import urllib.parse
from typing import Any, Dict, List

from common import PROJECT_ROOT, http_get_json, today, write_json


def mediawiki_api_for_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}/w/api.php"


def mediawiki_oldid_url(url: str, oldid: Any) -> str:
    parsed = urllib.parse.urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}/w/index.php?oldid={oldid}"


def mediawiki_title_from_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    match = re.search(r"/wiki/(.+)$", parsed.path)
    if not match:
        raise ValueError("Not a MediaWiki /wiki/ URL")
    return urllib.parse.unquote(match.group(1)).replace("_", " ")


def build_mediawiki_manifest(url: str) -> Dict[str, Any]:
    api = mediawiki_api_for_url(url)
    title = mediawiki_title_from_url(url)
    info = http_get_json(
        api,
        {
            "action": "query",
            "titles": title,
            "prop": "info|revisions",
            "rvprop": "ids|timestamp|user",
            "inprop": "url",
            "format": "json",
        },
    )
    page = next(iter(info.get("query", {}).get("pages", {}).values()), {})
    parsed = http_get_json(
        api,
        {
            "action": "parse",
            "page": title,
            "prop": "sections|links|displaytitle",
            "format": "json",
        },
    ).get("parse", {})
    base_work = title.split("/")[0]
    links = []
    for link in parsed.get("links", []):
        link_title = link.get("*", "")
        if link.get("ns") == 0 and (link_title == base_work or link_title.startswith(base_work + "/")):
            links.append(
                {
                    "label": link_title.split("/")[-1],
                    "title": link_title,
                    "url": f"{urllib.parse.urlparse(url).scheme}://{urllib.parse.urlparse(url).netloc}/wiki/{urllib.parse.quote(link_title.replace(' ', '_'))}",
                    "depth": link_title.count("/"),
                    "kind": "subpage",
                }
            )
    sections = []
    for section in parsed.get("sections", []):
        sections.append(
            {
                "label": section.get("line", ""),
                "anchor": section.get("anchor", ""),
                "level": int(section.get("level", 0) or 0),
                "number": section.get("number", ""),
                "kind": "section",
            }
        )
    oldid = page.get("lastrevid")
    stable_url = mediawiki_oldid_url(url, oldid) if oldid else page.get("fullurl", url)
    return {
        "source_type": "mediawiki",
        "title": title,
        "display_title": parsed.get("displaytitle"),
        "url": url,
        "stable_url": stable_url,
        "oldid": oldid,
        "pageid": page.get("pageid"),
        "last_touched": page.get("touched"),
        "accessed": today(),
        "toc": sections + links,
    }


def archive_identifier_from_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    match = re.search(r"/details/([^/?#]+)", parsed.path)
    if not match:
        raise ValueError("Not an Internet Archive details URL")
    return urllib.parse.unquote(match.group(1))


def build_archive_manifest(url: str) -> Dict[str, Any]:
    identifier = archive_identifier_from_url(url)
    data = http_get_json(f"https://archive.org/metadata/{identifier}")
    metadata = data.get("metadata", {})
    files = []
    for item in data.get("files", []):
        name = item.get("name", "")
        files.append(
            {
                "label": name,
                "format": item.get("format"),
                "size": item.get("size"),
                "url": f"https://archive.org/download/{identifier}/{urllib.parse.quote(name)}",
            }
        )
    return {
        "source_type": "internet_archive",
        "title": metadata.get("title", identifier),
        "identifier": identifier,
        "url": url,
        "stable_url": f"https://archive.org/details/{identifier}",
        "creator": metadata.get("creator"),
        "date": metadata.get("date"),
        "license_url": metadata.get("licenseurl"),
        "rights": metadata.get("rights"),
        "accessed": today(),
        "toc": files,
    }


def build_generic_manifest(url: str) -> Dict[str, Any]:
    return {
        "source_type": "generic",
        "title": url,
        "url": url,
        "stable_url": url,
        "accessed": today(),
        "toc": [],
        "note": "No specialized manifest builder matched this URL.",
    }


def build_manifest(url: str) -> Dict[str, Any]:
    host = urllib.parse.urlparse(url).netloc
    if "wikisource.org" in host:
        return build_mediawiki_manifest(url)
    if host == "archive.org" or host.endswith(".archive.org"):
        return build_archive_manifest(url)
    return build_generic_manifest(url)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a source manifest from a URL.")
    parser.add_argument("url")
    parser.add_argument("--output", default=str(PROJECT_ROOT / "results" / "manifest.json"))
    args = parser.parse_args()
    manifest = build_manifest(args.url)
    write_json(args.output, manifest)
    print(f"Wrote {args.output}. Entries: {len(manifest.get('toc', []))}")


if __name__ == "__main__":
    main()
