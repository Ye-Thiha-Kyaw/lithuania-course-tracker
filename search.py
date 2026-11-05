"""Find DreamApply course pages for a country using the Serper.dev web search API."""

from __future__ import annotations

import requests

from dreamapply import is_dreamapply_course_url

SERPER_URL = "https://google.serper.dev/search"


def search_dreamapply_courses(country: str, api_key: str, num_results: int = 20) -> list[dict]:
    """Search the web for DreamApply bachelor course pages in the given country.

    Returns a list of {"title": str, "link": str}, filtered to links that
    `dreamapply.scrape()` can read.
    """
    query = f'{country} bachelor degree "courses/course" dreamapply'
    response = requests.post(
        SERPER_URL,
        headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
        json={"q": query, "num": num_results},
        timeout=20,
    )
    response.raise_for_status()
    data = response.json()

    seen: set[str] = set()
    results = []
    for item in data.get("organic", []):
        link = (item.get("link") or "").strip()
        if link and is_dreamapply_course_url(link) and link not in seen:
            seen.add(link)
            results.append({"title": item.get("title", link), "link": link})
    return results
