"""Licence and structured-metadata extraction from dataset landing pages."""
from __future__ import annotations

import json
import re
from urllib.parse import urlsplit


def jsonld_datasets(html: str) -> list[dict]:
    """Return every schema.org Dataset object embedded as JSON-LD in a page.

    Many portals (Kaggle, Zenodo, data.gov, Hugging Face, Dataverse, CKAN sites) embed one.
    It is the most reliable machine-readable description of a dataset when it exists.
    """
    found = []
    for m in re.finditer(r"""(?is)<script[^>]*type=["']application/ld\+json["'][^>]*>(.*?)</script>""", html):
        try:
            data = json.loads(m.group(1).strip())
        except json.JSONDecodeError:
            continue
        items = data if isinstance(data, list) else data.get("@graph", [data]) if isinstance(data, dict) else []
        for item in items:
            if isinstance(item, dict) and "Dataset" in str(item.get("@type", "")):
                found.append(item)
    return found


def summarise_jsonld_dataset(d: dict) -> dict:
    """Keep the fields that matter for discovery, clipped for the model."""
    def name_of(v):
        if isinstance(v, list):
            return [name_of(x) for x in v][:5]
        if isinstance(v, dict):
            return v.get("name") or v.get("url") or v.get("@id")
        return v

    def clip(v, n=600):
        v = re.sub(r"<[^>]+>", " ", str(v)) if v is not None else None
        return None if v is None else (" ".join(v.split())[:n])

    dist = d.get("distribution") or []
    dist = dist if isinstance(dist, list) else [dist]
    return {
        "name": d.get("name"), "description": clip(d.get("description")),
        "license": d.get("license"), "creator": name_of(d.get("creator")), "publisher": name_of(d.get("publisher")),
        "datePublished": d.get("datePublished"), "dateModified": d.get("dateModified"),
        "temporalCoverage": d.get("temporalCoverage"), "spatialCoverage": name_of(d.get("spatialCoverage")),
        "isAccessibleForFree": d.get("isAccessibleForFree"), "keywords": clip(d.get("keywords"), 300),
        "variableMeasured": name_of(d.get("variableMeasured")),
        "distribution": [{k: x.get(k) for k in ("contentUrl", "encodingFormat", "fileFormat", "contentSize", "requiresSubscription", "name")
                          if isinstance(x, dict) and x.get(k) is not None} for x in dist[:10]],
    }


# Without this, every dataset link ends up LIC-UNKNOWN (a blocker) and verdicts are wrong.
#
# Contract (tests/test_learner_gaps.py::test_g1_* checks it):
#   extract_licence(html: str, jsonld: list[dict] | None = None) -> dict with EXACTLY these keys
#     licence_name : normalised name, one of e.g. "CC BY 4.0", "CC BY-SA 4.0", "CC BY-NC 4.0", "CC BY-NC-SA 4.0",
#                    "CC BY-ND 4.0", "CC0 1.0", "ODbL 1.0", "OGL v3.0", "MIT", "Apache-2.0"; None if not found
#                    or if the page says the licence is unknown/unspecified
#     licence_url  : the licence URL you found, or None
#     snippet      : the text or JSON-LD value you read it from (<= 400 chars), or None
#     found_in     : "json-ld" | "link" | "text" | None
#
# Order of evidence: JSON-LD "license" (string URL, or {"name", "url"}) first; then links to
# creativecommons.org / opendatacommons.org / nationalarchives.gov.uk (OGL) / choosealicense.com;
# then sentences such as "licensed under a Creative Commons Attribution 4.0 International (CC BY 4.0) license".
# jsonld defaults to jsonld_datasets(html) when None. Never guess: return None values when unsure.
LICENCE_LINK_HOSTS = ("creativecommons.org", "opendatacommons.org", "nationalarchives.gov.uk", "choosealicense.com")
UNKNOWN_LICENCE_WORDS = {"", "unknown", "unspecified", "not specified", "none", "null", "n/a", "not found"}
_CC_TEXT = re.compile(r"\bCC\s*(BY(?:[- ](?:NC|SA|ND))*)\s*(\d\.\d)\b", re.I)
_CC_LONG = re.compile(r"Creative Commons (Attribution(?:-NonCommercial)?(?:-ShareAlike|-NoDerivatives)?) (\d\.\d)", re.I)
_CC_LONG_CODES = {
    "attribution": "BY", "attribution-noncommercial": "BY-NC", "attribution-sharealike": "BY-SA",
    "attribution-noderivatives": "BY-ND", "attribution-noncommercial-sharealike": "BY-NC-SA",
    "attribution-noncommercial-noderivatives": "BY-NC-ND",
}
_CC0_TEXT = re.compile(r"\bCC0\s*(1\.0)\b", re.I)
_OGL_TEXT = re.compile(r"Open Government Licence\s*v?(\d\.\d)", re.I)
_CC_PATH = re.compile(r"/licenses/(by(?:-(?:nc|sa|nd))*)/(\d\.\d)", re.I)
_CC_SLUG = re.compile(r"cc-(by(?:-(?:nc|sa|nd))*)-(\d\.\d)", re.I)
_CHOOSE_SLUGS = {"mit": "MIT", "apache-2.0": "Apache-2.0", "cc0-1.0": "CC0 1.0"}


def _name_from_url(url: str) -> str | None:
    """Licence name from a licence URL on a known host, or None."""
    parts = urlsplit(url)
    host, path = (parts.hostname or ""), parts.path
    if host.endswith("creativecommons.org"):
        m = _CC_PATH.match(path)
        if m:
            return f"CC {m.group(1).upper()} {m.group(2)}"
        if path.lower().startswith("/publicdomain/zero/1.0"):
            return "CC0 1.0"
        return None
    if host.endswith("opendatacommons.org"):
        return "ODbL 1.0" if path.lower().startswith("/licenses/odbl") else None
    if host.endswith("nationalarchives.gov.uk"):
        return "OGL v3.0" if path.lower().startswith("/doc/open-government-licence/version/3") else None
    if host.endswith("choosealicense.com"):
        slug = path.strip("/").split("/")[-1].lower()
        if slug in _CHOOSE_SLUGS:
            return _CHOOSE_SLUGS[slug]
        m = _CC_SLUG.fullmatch(slug)
        if m:
            return f"CC {m.group(1).upper()} {m.group(2)}"
    return None


def _name_from_text(text: str) -> str | None:
    """Licence name from free text or a JSON-LD name, or None."""
    m = _CC_TEXT.search(text)
    if m:
        return f"CC {m.group(1).upper().replace(' ', '-')} {m.group(2)}"
    m = _CC_LONG.search(text)
    if m and m.group(1).lower() in _CC_LONG_CODES:
        return f"CC {_CC_LONG_CODES[m.group(1).lower()]} {m.group(2)}"
    if _CC0_TEXT.search(text):
        return "CC0 1.0"
    if re.search(r"\bODbL\b|Open Database License", text, re.I):
        return "ODbL 1.0"
    m = _OGL_TEXT.search(text)
    if m:
        return f"OGL v{m.group(1)}"
    if re.search(r"\bMIT License\b", text, re.I):
        return "MIT"
    if re.search(r"Apache License,? (?:version )?2\.0", text, re.I):
        return "Apache-2.0"
    return None


def _normalise_name(name) -> str | None:
    if not name or not str(name).strip() or str(name).strip().lower() in UNKNOWN_LICENCE_WORDS:
        return None
    return _name_from_text(str(name))


def _licence_fields(lic) -> tuple[str | None, str | None]:
    """(url, name) from a JSON-LD license value: a URL string, a name string, or {"name", "url"}."""
    if isinstance(lic, str):
        s = lic.strip()
        return (s, None) if s.startswith("http") else (None, s)
    if isinstance(lic, dict):
        return (lic.get("url") or lic.get("@id") or None), lic.get("name")
    return None, None


def _clip(text: str | None, n: int = 400) -> str | None:
    cleaned = " ".join((text or "").split())[:n]
    return cleaned or None


def _plain(html: str) -> str:
    html = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", html)
    return " ".join(re.sub(r"<[^>]+>", " ", html).split())


def _is_licence_host(href: str) -> bool:
    host = urlsplit(href).hostname or ""
    return any(host == h or host.endswith("." + h) for h in LICENCE_LINK_HOSTS)


def extract_licence(html: str, jsonld: list[dict] | None = None) -> dict:
    """Order: JSON-LD licence, then licence links, then licence sentences in the text.

    A JSON-LD licence that says "Unknown" does not stop the search: a licence link or sentence
    later in the page can still establish the licence. It is returned only if nothing else is found.
    """
    if jsonld is None:
        jsonld = jsonld_datasets(html)

    unknown_jsonld = None
    for ds in jsonld:
        lic = ds.get("license")
        if lic in (None, "", []):
            continue
        url, name = _licence_fields(lic)
        name_norm = (_name_from_url(url) if url else None) or _normalise_name(name)
        hit = {"licence_name": name_norm, "licence_url": url or None,
               "snippet": _clip(json.dumps(lic, ensure_ascii=False)), "found_in": "json-ld"}
        if name_norm:
            return hit
        unknown_jsonld = unknown_jsonld or hit

    for m in re.finditer(r"""<a\b[^>]*\bhref=["']([^"']+)["']""", html, re.I):
        href = m.group(1)
        if not _is_licence_host(href):
            continue
        name = _name_from_url(href)
        if name:
            window = html[max(0, m.start() - 400): m.end() + 400]
            return {"licence_name": name, "licence_url": href, "snippet": _clip(_plain(window)), "found_in": "link"}

    for sentence in re.split(r"(?<=[.!?])\s+", _plain(html)):
        name = _name_from_text(sentence)
        if name:
            return {"licence_name": name, "licence_url": None, "snippet": _clip(sentence), "found_in": "text"}

    if unknown_jsonld:
        return unknown_jsonld
    return {"licence_name": None, "licence_url": None, "snippet": None, "found_in": None}
