"""Use an LLM (Claude or Gemini) to pull structured course data out of a
university page that isn't DreamApply-formatted, so `dreamapply.parse_course()`
can't read it.
"""

from __future__ import annotations

from datetime import date
from typing import Optional

import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel

from dreamapply import HEADERS

ANTHROPIC_MODEL = "claude-opus-5-5"
GEMINI_MODEL = "gemini-3.8-flash"

PROMPT = (
    "This is the text of a university bachelor's degree course/programme page. "
    "Extract the fields in the schema from it. Use an empty string, 0, or null for "
    "anything not stated on the page - never guess or invent a value.\n\n"
    "PAGE TEXT:\n{page_text}"
)


class CourseInfo(BaseModel):
    university: str = ""
    programme: str = ""
    degree: str = ""
    city: str = ""
    duration: str = ""
    ects: Optional[int] = None
    tuition_eur_per_year: Optional[float] = None
    application_fee_eur: Optional[float] = None
    min_grade_percent: Optional[int] = None
    admission_formula: str = ""
    ielts_min: Optional[float] = None
    english_requirement: str = ""
    references_needed: int = 0
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


def _row_from_info(info: CourseInfo, url: str) -> dict:
    return {
        "University": info.university,
        "Programme": info.programme,
        "Degree": info.degree,
        "City": info.city,
        "Duration": info.duration,
        "ECTS": info.ects,
        "Tuition (EUR/year)": info.tuition_eur_per_year,
        "Application fee (EUR)": info.application_fee_eur,
        "Min. grade (%)": info.min_grade_percent,
        "Admission formula": info.admission_formula,
        "IELTS (min)": info.ielts_min,
        "English requirement": info.english_requirement,
        "References needed": info.references_needed,
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
