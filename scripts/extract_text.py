from __future__ import annotations

import argparse
import re
import urllib.parse
from html.parser import HTMLParser
from typing import Any, Dict, List, Tuple

from common import (
    PROJECT_ROOT,
    compact_whitespace,
    http_get_json,
    http_get_text,
    today,
    write_json,
)


class BlockTextExtractor(HTMLParser):
    block_tags = {
        "p",
        "div",
        "section",
        "article",
        "blockquote",
        "li",
        "br",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
    }
    skip_tags = {"script", "style", "noscript", "table", "nav", "figure", "footer"}

    def __init__(self) -> None:
        super().__init__()
        self.parts: List[str] = []
        self.skip_depth = 0

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, str | None]]) -> None:
        attrs_dict = {k: v or "" for k, v in attrs}
        classes = attrs_dict.get("class", "")
        if tag in self.skip_tags or "mw-editsection" in classes or "noprint" in classes:
            self.skip_depth += 1
            return
        if tag in self.block_tags:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if self.skip_depth:
            if tag in self.skip_tags or tag in {"span", "div"}:
                self.skip_depth = max(0, self.skip_depth - 1)
            return
        if tag in self.block_tags:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self.skip_depth:
            self.parts.append(data)

    def text(self) -> str:
        return compact_whitespace("".join(self.parts))


def html_to_text(markup: str) -> str:
    parser = BlockTextExtractor()
    parser.feed(markup)
    return parser.text()


def split_passages(text: str) -> List[Dict[str, str]]:
    chunks = [chunk.strip() for chunk in re.split(r"\n{2,}", text) if chunk.strip()]
    return [
        {
            "id": f"P{i:04d}",
            "source": chunk,
        }
        for i, chunk in enumerate(chunks, start=1)
    ]


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


def extract_wikisource(url: str) -> Dict[str, Any]:
    api = mediawiki_api_for_url(url)
    title = mediawiki_title_from_url(url)
    parsed = http_get_json(
        api,
        {
            "action": "parse",
            "page": title,
            "prop": "text|displaytitle|revid",
            "format": "json",
        },
    ).get("parse", {})
    text_html = parsed.get("text", {}).get("*", "")
    text = html_to_text(text_html)
    oldid = parsed.get("revid")
    return {
        "source_card": {
            "source_id": "wikisource",
            "source_name": urllib.parse.urlparse(url).netloc,
            "title": title,
            "url": url,
            "stable_url": mediawiki_oldid_url(url, oldid) if oldid else url,
            "identifier": str(oldid or ""),
            "rights_status": "cc_by_sa",
            "rights_note": "Wikisource text pages are generally CC BY-SA with public-domain source works where applicable; verify page footer for final reuse.",
            "accessed": today(),
        },
        "text": text,
        "passages": split_passages(text),
    }


def gutenberg_id_from_url(url: str) -> str:
    match = re.search(r"/ebooks/(\d+)", url)
    if not match:
        raise ValueError("Not a Gutenberg ebook URL")
    return match.group(1)


def extract_gutenberg(url: str) -> Dict[str, Any]:
    ebook_id = gutenberg_id_from_url(url)
    candidates = [
        f"https://www.gutenberg.org/cache/epub/{ebook_id}/pg{ebook_id}.txt",
        f"https://www.gutenberg.org/files/{ebook_id}/{ebook_id}-0.txt",
        f"https://www.gutenberg.org/files/{ebook_id}/{ebook_id}.txt",
    ]
    last_error = ""
    text = ""
    source_url = candidates[0]
    for candidate in candidates:
        try:
            text = http_get_text(candidate)
            source_url = candidate
            break
        except Exception as exc:  # noqa: BLE001 - keep fallback broad for mirrors.
            last_error = str(exc)
    if not text:
        raise RuntimeError(f"Could not fetch Gutenberg text: {last_error}")
    text = compact_whitespace(text)
    return {
        "source_card": {
            "source_id": "gutenberg",
            "source_name": "Project Gutenberg",
            "title": f"Project Gutenberg ebook {ebook_id}",
            "url": url,
            "stable_url": url,
            "identifier": ebook_id,
            "download_url": source_url,
            "rights_status": "public_domain",
            "rights_note": "Project Gutenberg items are public-domain or permission-cleared in the United States; verify ebook license header.",
            "accessed": today(),
        },
        "text": text,
        "passages": split_passages(text),
    }


def archive_identifier_from_url(url: str) -> str:
    match = re.search(r"/details/([^/?#]+)", urllib.parse.urlparse(url).path)
    if not match:
        raise ValueError("Not an Internet Archive details URL")
    return urllib.parse.unquote(match.group(1))


def extract_archive(url: str) -> Dict[str, Any]:
    identifier = archive_identifier_from_url(url)
    metadata = http_get_json(f"https://archive.org/metadata/{identifier}")
    files = metadata.get("files", [])
    text_file = None
    for item in files:
        name = item.get("name", "")
        if name.endswith("_djvu.txt"):
            text_file = name
            break
    if not text_file:
        for item in files:
            name = item.get("name", "")
            if name.endswith(".txt") and "meta" not in name.lower():
                text_file = name
                break
    if not text_file:
        raise RuntimeError("No OCR text file found in Internet Archive item.")
    download_url = f"https://archive.org/download/{identifier}/{urllib.parse.quote(text_file)}"
    text = compact_whitespace(http_get_text(download_url))
    md = metadata.get("metadata", {})
    return {
        "source_card": {
            "source_id": "internet_archive",
            "source_name": "Internet Archive",
            "title": md.get("title", identifier),
            "author": md.get("creator"),
            "date": md.get("date"),
            "url": url,
            "stable_url": f"https://archive.org/details/{identifier}",
            "identifier": identifier,
            "download_url": download_url,
            "license_url": md.get("licenseurl"),
            "rights": md.get("rights"),
            "rights_status": "unknown",
            "rights_note": "Check Internet Archive item metadata before reuse.",
            "accessed": today(),
        },
        "text": text,
        "passages": split_passages(text),
    }


def extract_generic_html(url: str) -> Dict[str, Any]:
    text = html_to_text(http_get_text(url))
    return {
        "source_card": {
            "source_id": "generic",
            "source_name": urllib.parse.urlparse(url).netloc,
            "title": url,
            "url": url,
            "stable_url": url,
            "rights_status": "unknown",
            "rights_note": "Generic extraction cannot verify rights.",
            "accessed": today(),
        },
        "text": text,
        "passages": split_passages(text),
    }


def extract(url: str) -> Dict[str, Any]:
    host = urllib.parse.urlparse(url).netloc
    if "wikisource.org" in host:
        return extract_wikisource(url)
    if "gutenberg.org" in host and "/ebooks/" in url:
        return extract_gutenberg(url)
    if host == "archive.org" or host.endswith(".archive.org"):
        return extract_archive(url)
    return extract_generic_html(url)


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract clean text from a supported source URL.")
    parser.add_argument("url")
    parser.add_argument("--max-chars", type=int, default=0)
    parser.add_argument("--output", default=str(PROJECT_ROOT / "results" / "extracted_text.json"))
    args = parser.parse_args()

    payload = extract(args.url)
    if args.max_chars and len(payload.get("text", "")) > args.max_chars:
        payload["text"] = payload["text"][: args.max_chars]
        payload["passages"] = split_passages(payload["text"])
        payload["truncated"] = True
    write_json(args.output, payload)
    print(f"Wrote {args.output}. Passages: {len(payload.get('passages', []))}")


if __name__ == "__main__":
    main()
