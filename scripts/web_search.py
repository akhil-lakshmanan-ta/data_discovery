#!/usr/bin/env python3
"""Search the web through the gateway's chat completions endpoint.

Usage:
    python scripts/web_search.py "<query>"

Environment:
    ANTHROPIC_BASE_URL     gateway base URL (required)
    ANTHROPIC_AUTH_TOKEN   bearer token (required; never printed)
    WEB_SEARCH_MODEL       optional, default gemini-3.8-flash

Standard library only. Prints the answer text, then the citation URLs.
"""
import json
import os
import sys
import urllib.error
import urllib.request

DEFAULT_MODEL = "gemini-3.8-flash"


def fail(message):
    print(message, file=sys.stderr)
    sys.exit(1)


def citation_urls(response):
    """Collect citation URLs from annotations and any top-level citations list."""
    urls = []
    try:
        message = response["choices"][0]["message"]
    except (KeyError, IndexError, TypeError):
        message = {}
    for ann in message.get("annotations") or []:
        if isinstance(ann, dict) and ann.get("type") == "url_citation":
            url = (ann.get("url_citation") or {}).get("url")
            if url:
                urls.append(url)
    for item in response.get("citations") or []:
        if isinstance(item, str):
            urls.append(item)
        elif isinstance(item, dict) and item.get("url"):
            urls.append(item["url"])
    seen = []
    for url in urls:
        if url not in seen:
            seen.append(url)
    return seen


def main():
    if len(sys.argv) != 2:
        fail('usage: python scripts/web_search.py "<query>"')
    query = sys.argv[1]

    base_url = os.environ.get("ANTHROPIC_BASE_URL")
    if not base_url:
        fail("missing environment variable: ANTHROPIC_BASE_URL")
    token = os.environ.get("ANTHROPIC_AUTH_TOKEN")
    if not token:
        fail("missing environment variable: ANTHROPIC_AUTH_TOKEN")
    model = os.environ.get("WEB_SEARCH_MODEL") or DEFAULT_MODEL

    body = {
        "model": model,
        "messages": [{"role": "user", "content": query}],
        "web_search_options": {},
    }
    request = urllib.request.Request(
        base_url.rstrip("/") + "/v1/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as resp:
            response = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        # Do not print the response body: it may echo request details.
        fail(f"gateway returned HTTP {exc.code}; no results")
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        fail(f"request failed: {type(exc).__name__}; no results")

    try:
        answer = response["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError, TypeError):
        fail("response had no answer text")

    # Consoles on Windows may not be UTF-8; never crash while printing an answer.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(answer.strip())
    urls = citation_urls(response)
    print()
    print("Citations:")
    if urls:
        for url in urls:
            print(url)
    else:
        print("(none returned)")


if __name__ == "__main__":
    main()
