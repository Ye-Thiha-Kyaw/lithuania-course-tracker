"""Find university/college bachelor-course pages for a country using the
Serper.dev web search API. Not limited to DreamApply - any course page the
search turns up is returned, tagged with whether `dreamapply.scrape()` can
read it directly or needs AI extraction instead.
"""

from __future__ import annotations

import requests

from dreamapply import is_dreamapply_course_url

SERPER_URL = "https://google.serper.dev/search"

# Results from these domains are never course pages - drop them before they
# reach the picker.
_NOISE_DOMAINS = (
    "wikipedia.org",
    "youtube.com",
    "facebook.com",
    "instagram.com",
    "twitter.com",
    "x.com",
    "linkedin.com",
    "reddit.com",
    "tiktok.com",
)


def search_university_courses(country: str, api_key: str, num_results: int = 20) -> list[dict]:
    """Search the web for bachelor-degree course pages from any university or
    college in the given country.

    Returns a list of {"title": str, "link": str, "is_dreamapply": bool},
    deduplicated and with obvious non-course domains filtered out.
    """
    query = f"{country} bachelor degree course application university college"
    response = requests.post(
        SERPER_URL,
        headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
        json={"q": query, "num": num_results},
        timeout=20,
    )
    if not response.ok:
        raise RuntimeError(f"Serper API error {response.status_code}: {response.text.strip()}")
    data = response.json()

    seen: set[str] = set()
    results = []
    for item in data.get("organic", []):
        link = (item.get("link") or "").strip()
        if not link or link in seen:
            continue
        if any(domain in link for domain in _NOISE_DOMAINS):
            continue
        seen.add(link)
        results.append(
            {
                "title": item.get("title", link),
                "link": link,
                "is_dreamapply": is_dreamapply_course_url(link),
            }
        )
    return results
