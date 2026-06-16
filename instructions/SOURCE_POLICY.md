# Source Policy

## Source Roles

`primary_text`

Use as an authoritative source for extraction and citation when rights allow.

`primary_text_noncommercial`

Use for noncommercial research and education. Flag restrictions clearly.

`metadata`

Use for bibliographic enrichment, edition clustering, or external identifiers.

`discovery_only`

Use only to discover candidate titles, editions, or page images. Do not quote, extract, or translate from it unless rights are verified elsewhere.

`search_only`

Use to locate passages or references. Do not treat as final reusable text.

## Source Layers

Reverse-trace tasks must also classify document layer:

- `원어 원전`: original language source text
- `고전적 번역본`: influential older translation
- `현대 번역본`: modern translation
- `주석·전통 해석`: commentary or inherited interpretation
- `후대 학자 해석`: later scholar's reception or paraphrase
- `현대 해설·2차 문헌`: textbook, lecture, encyclopedia, blog, article, or summary
- `단서 자료`: clue only
- `층위 불명`: not enough evidence

For Western classics, do not treat English as automatically original. English may be a relay translation from Greek, Latin, French, German, Italian, or another source language.

## Recommended Source Handling

Wikisource:

- Good for transcribed public-domain and CC BY-SA texts.
- Use MediaWiki API.
- Record `oldid` or permanent link when possible.

Project Gutenberg:

- Good for public-domain or permission-cleared ebooks under Project Gutenberg terms.
- Remove Project Gutenberg header/footer if the final target requires clean source text.
- Record ebook number and license note.

Internet Archive:

- Good for scans, OCR, and source images.
- Check `licenseurl`, `rights`, and availability.
- Prefer items with clear public-domain or Creative Commons fields.

HathiTrust:

- Good for edition discovery and public-domain scans.
- `Full View` usually means public domain or open access, but download rules may differ by item.

Open Library:

- Good metadata and Internet Archive linking.
- Do not treat Open Library metadata as final rights proof for a text.

Perseus/Scaife:

- Good for Greek and Latin texts with stable citation schemes.
- Record CTS URNs when available.

DOAJ:

- Good for open-access journal discovery.
- Record article license and DOI if available.

DOAB/OAPEN:

- Good for peer-reviewed open-access books.
- Record book-level license, publisher, DOI, ISBN, and download URL.

Kanseki Repository:

- Good for machine-readable Chinese texts.
- Respect repository license and cite repository path/commit when possible.

CBETA:

- Strong source for Buddhist Chinese texts.
- Default handling is noncommercial because CBETA uses CC BY-NC-SA 3.0 Taiwan for most content, with explicit exclusions.

Chinese Text Project:

- Excellent search and comparison resource.
- Use cautiously for automated extraction. Prefer short lookup, citation, or manual verification unless local permission and rate limits are clear.

Scribd and similar upload platforms:

- Discovery only.
- Never use as final source without independent license verification and a better source copy.

## Rights Labels

- `public_domain`: copyright-free or public-domain mark according to source.
- `cc_by`: Creative Commons Attribution.
- `cc_by_sa`: Creative Commons Attribution ShareAlike.
- `cc_by_nc_sa`: Creative Commons Attribution NonCommercial ShareAlike.
- `open_access`: freely accessible but license must be checked.
- `search_only`: searchable, not reusable.
- `discovery_only`: clue source only.
- `unknown`: unclear or missing rights status.
