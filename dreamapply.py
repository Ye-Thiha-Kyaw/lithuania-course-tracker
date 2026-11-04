"""Read a DreamApply course page and turn it into one row of course data.

Many universities (e.g. Vytautas Magnus, VILNIUS TECH) publish courses on
DreamApply. Every course page uses the same labels ("Tuition fee",
"Entry qualification", ...), so one parser works for all of them.
"""

from __future__ import annotations

import re
from datetime import date
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

# Column order used in the table and the Excel file.
COLUMNS = [
    "University",
    "Programme",
    "Degree",
    "City",
    "Duration",
    "ECTS",
    "Tuition (EUR/year)",
    "Application fee (EUR)",
    "Min. grade (%)",
    "Admission formula",
    "IELTS (min)",
    "English requirement",
    "References needed",
    "Motivation letter",
    "Other documents",
    "Blocked citizenships",
    "Intake",
    "Application deadline",
    "Studies start",
    "Entry requirements (full text)",
    "URL",
    "Date checked",
]

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; LithuaniaCourseTracker/1.0)"}


def is_dreamapply_course_url(url: str) -> bool:
    parsed = urlparse(url.strip())
    return parsed.scheme in ("http", "https") and "/courses/course/" in parsed.path


def fetch_html(url: str, timeout: int = 20) -> str:
    response = requests.get(url.strip(), headers=HEADERS, timeout=timeout)
    response.raise_for_status()
    return response.text


def _clean(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n", text)
    return text.strip()


def _label_value_pairs(soup: BeautifulSoup) -> dict[str, str]:
    """Collect every 'label | value' row from the page's tables (and dl lists)."""
    pairs: dict[str, str] = {}
    for tr in soup.find_all("tr"):
        cells = tr.find_all(["th", "td"], recursive=False)
        if len(cells) >= 2:
            label = _clean(cells[0].get_text(" ", strip=True)).lower()
            value = _clean(cells[1].get_text("\n", strip=True))
            if label and label not in pairs:
                pairs[label] = value
    for dt in soup.find_all("dt"):
        dd = dt.find_next_sibling("dd")
        if dd:
            label = _clean(dt.get_text(" ", strip=True)).lower()
            pairs.setdefault(label, _clean(dd.get_text("\n", strip=True)))
    return pairs


def _get(pairs: dict[str, str], *labels: str) -> str:
    for label in labels:
        for key, value in pairs.items():
            if key.startswith(label):
                return value
    return ""


def _euro_amount(text: str) -> float | None:
    match = re.search(r"€\s?([\d][\d,\.\s]*)", text) or re.search(r"([\d][\d,\.]*)\s?(?:EUR|€)", text)
    if not match:
        return None
    raw = match.group(1).strip().replace(" ", "")
    # "3,400" or "3.400" -> 3400 ; "3400.50" -> 3400.5
    if re.fullmatch(r"\d{1,3}([,\.]\d{3})+", raw):
        raw = re.sub(r"[,\.]", "", raw)
    else:
        raw = raw.replace(",", "")
    try:
        return float(raw)
    except ValueError:
        return None


def _date_after(label: str, text: str) -> str:
    match = re.search(label + r"\s*\n?\s*(\d{1,2}\s+[A-Za-z]{3,9}\.?\s+\d{4})", text, re.IGNORECASE)
    return match.group(1) if match else ""


def parse_course(html: str, url: str = "") -> dict:
    soup = BeautifulSoup(html, "html.parser")
    pairs = _label_value_pairs(soup)
    page_text = _clean(soup.get_text("\n"))

    # Title looks like: "[Bachelor Degree] Logistics and Commerce - Vytautas Magnus University"
    title = _clean(soup.title.get_text()) if soup.title else ""
    degree, programme, university = "", "", ""
    match = re.match(r"\[(.+?)\]\s*(.+?)\s+-\s+(.+)$", title)
    if match:
        degree, programme, university = (part.strip() for part in match.groups())
    else:
        h1 = soup.find("h1")
        programme = _clean(h1.get_text(" ", strip=True)) if h1 else title

    location = _get(pairs, "study location")
    city = location.split(",")[-1].strip() if location else ""

    duration_text = _get(pairs, "nominal duration")
    ects = re.search(r"(\d+)\s*ECTS", duration_text)
    duration = re.sub(r"\(.*?\)", "", duration_text).strip()

    tuition_text = _get(pairs, "tuition fee")
    fee_text = _get(pairs, "application fee")
    entry_text = _get(pairs, "entry qualification")
    language_text = _get(pairs, "language requirements")
    other_text = _get(pairs, "other requirements")
    territory_text = _get(pairs, "territory requirements")

    min_grade = re.search(r"(?:minimum|min\.?)\s*(\d{2})\s?%", entry_text, re.IGNORECASE) or re.search(
        r"(\d{2})\s?%", entry_text
    )
    formula = next(
        (line.strip() for line in entry_text.split("\n") if re.search(r"admission score|score counting", line, re.I)),
        "",
    )
    min_score = re.search(r"minimum admission score[^\d]*([\d][,\.]?\d*)", entry_text, re.IGNORECASE)
    if min_score:
        formula = f"{formula} (min. score {min_score.group(1)})".strip()

    ielts = re.search(r"IELTS\s*([\d](?:[,\.]\d)?)", language_text)
    references = re.search(r"at least (\d+) reference", other_text, re.IGNORECASE)

    blocked = ""
    if territory_text:
        blocked = territory_text.split(":", 1)[-1].strip() if ":" in territory_text else territory_text

    other_docs = [
        doc
        for doc, pattern in [
            ("CV", r"curriculum vitae|\bcv\b"),
            ("Passport copy", r"copy of passport|passport copy"),
            ("Passport photo", r"passport photo"),
            ("Police clearance (apostille)", r"police clearance|non.conviction"),
            ("Portfolio", r"portfolio"),
            ("Interview", r"interview"),
        ]
        if re.search(pattern, other_text + "\n" + entry_text, re.IGNORECASE)
    ]

    intake = re.search(r"Apply now!\s*([^\n]+)", page_text)

    return {
        "University": university,
        "Programme": programme,
        "Degree": degree,
        "City": city,
        "Duration": duration,
        "ECTS": int(ects.group(1)) if ects else None,
        "Tuition (EUR/year)": _euro_amount(tuition_text),
        "Application fee (EUR)": _euro_amount(fee_text),
        "Min. grade (%)": int(min_grade.group(1)) if min_grade else None,
        "Admission formula": formula,
        "IELTS (min)": float(ielts.group(1).replace(",", ".")) if ielts else None,
        "English requirement": language_text,
        "References needed": int(references.group(1)) if references else 0,
        "Motivation letter": "Yes" if re.search(r"motivation letter", other_text, re.I) else "No",
        "Other documents": ", ".join(other_docs),
        "Blocked citizenships": blocked,
        "Intake": intake.group(1).strip() if intake else "",
        "Application deadline": _date_after("Application deadline", page_text),
        "Studies start": _date_after("Studies commence", page_text),
        "Entry requirements (full text)": entry_text,
        "URL": url.strip(),
        "Date checked": date.today().isoformat(),
    }


def scrape(url: str) -> dict:
    """Download one DreamApply course page and return its row."""
    if not is_dreamapply_course_url(url):
        raise ValueError("This doesn't look like a DreamApply course link (it should contain /courses/course/).")
    return parse_course(fetch_html(url), url)
