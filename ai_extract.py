"""Use an LLM (Claude or Gemini) to pull structured course data out of a
university page that isn't DreamApply-formatted, so `dreamapply.parse_course()`
can't read it.
"""

from __future__ import annotations

from datetime import date

import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel

from dreamapply import HEADERS

ANTHROPIC_MODEL = "claude-opus-5-5"
GEMINI_MODEL = "gemini-3.8-flash"

PROMPT = (
    "This is the text of a university bachelor's degree course/programme page. "
    "Extract the fields in the schema from it. Every field is a plain string - for "
    "a number, write only the digits (and a decimal point if needed), no currency "
    "symbols, units or ranges (e.g. '12000' not '€12,000/year', '6.5' not 'IELTS 6.5'). "
    "Leave a field as an empty string if it isn't stated on the page - never guess or "
    "invent a value.\n\n"
    "PAGE TEXT:\n{page_text}"
)


class CourseInfo(BaseModel):
    """All fields are plain strings, even numeric ones.

    Structured-output APIs reject a schema built from `Optional[int/float]`
    fields as "too complex" once there are more than a few of them (each
    becomes a nullable anyOf, and those combine combinatorially). Keeping
    every field a flat string avoids that; numeric strings are parsed back
    into numbers in `_row_from_info`.
    """

    university: str = ""
    programme: str = ""
    degree: str = ""
    city: str = ""
    duration: str = ""
    ects: str = ""
    tuition_eur_per_year: str = ""
    application_fee_eur: str = ""
    min_grade_percent: str = ""
    admission_formula: str = ""
    ielts_min: str = ""
    duolingo_min: str = ""
    english_requirement: str = ""
    references_needed: str = ""
    motivation_letter: str = "No"
    other_documents: str = ""
    blocked_citizenships: str = ""
    intake: str = ""
    application_deadline: str = ""
    studies_start: str = ""
    entry_requirements_full_text: str = ""


def fetch_page_text(url: str, timeout: int = 20, max_chars: int = 15000) -> str:
    """Download a page and strip it to plain text, capped for the LLM's input."""
    response = requests.get(url.strip(), headers=HEADERS, timeout=timeout)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer"]):
        tag.decompose()
    return soup.get_text("\n", strip=True)[:max_chars]


def _as_int(text: str) -> int | None:
    text = (text or "").strip()
    try:
        return int(float(text)) if text else None
    except ValueError:
        return None


def _as_float(text: str) -> float | None:
    text = (text or "").strip()
    try:
        return float(text) if text else None
    except ValueError:
        return None


def _row_from_info(info: CourseInfo, url: str) -> dict:
    return {
        "University": info.university,
        "Programme": info.programme,
        "Degree": info.degree,
        "City": info.city,
        "Duration": info.duration,
        "ECTS": _as_int(info.ects),
        "Tuition (EUR/year)": _as_float(info.tuition_eur_per_year),
        "Application fee (EUR)": _as_float(info.application_fee_eur),
        "Min. grade (%)": _as_int(info.min_grade_percent),
        "Admission formula": info.admission_formula,
        "IELTS (min)": _as_float(info.ielts_min),
        "Duolingo (min)": _as_int(info.duolingo_min),
        "English requirement": info.english_requirement,
        "References needed": _as_int(info.references_needed) or 0,
        "Motivation letter": info.motivation_letter,
        "Other documents": info.other_documents,
        "Blocked citizenships": info.blocked_citizenships,
        "Intake": info.intake,
        "Application deadline": info.application_deadline,
        "Studies start": info.studies_start,
        "Entry requirements (full text)": info.entry_requirements_full_text,
        "URL": url.strip(),
        "Date checked": date.today().isoformat(),
    }


def extract_with_anthropic(url: str, api_key: str) -> dict:
    """Read a university page with Claude and return a row matching dreamapply.COLUMNS."""
    import anthropic

    page_text = fetch_page_text(url)
    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.parse(
        model=ANTHROPIC_MODEL,
        max_tokens=2048,
        messages=[{"role": "user", "content": PROMPT.format(page_text=page_text)}],
        output_format=CourseInfo,
    )
    return _row_from_info(response.parsed_output, url)


def extract_with_gemini(url: str, api_key: str) -> dict:
    """Read a university page with Gemini and return a row matching dreamapply.COLUMNS."""
    from google import genai

    page_text = fetch_page_text(url)
    client = genai.Client(api_key=api_key)
    interaction = client.interactions.create(
        model=GEMINI_MODEL,
        input=PROMPT.format(page_text=page_text),
        response_format={
            "type": "text",
            "mime_type": "application/json",
            "schema": CourseInfo.model_json_schema(),
        },
    )
    info = CourseInfo.model_validate_json(interaction.output_text)
    return _row_from_info(info, url)
