"""Write course rows to a formatted Excel file, and read them back."""

from __future__ import annotations

from io import BytesIO

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from dreamapply import COLUMNS

WIDTHS = {
    "University": 28, "Programme": 30, "Degree": 16, "City": 12, "Duration": 14, "ECTS": 8,
    "Tuition (EUR/year)": 12, "Application fee (EUR)": 12, "Min. grade (%)": 10,
    "Admission formula": 40, "IELTS (min)": 9, "Duolingo (min)": 11, "English requirement": 50, "References needed": 11,
    "Motivation letter": 11, "Other documents": 30, "Blocked citizenships": 30, "Intake": 22,
    "Application deadline": 14, "Studies start": 13, "Entry requirements (full text)": 60,
    "URL": 45, "Date checked": 12,
}


def upsert(rows: list[dict], new_row: dict) -> list[dict]:
    """Add a row, or replace the existing row with the same URL."""
    rows = [r for r in rows if r.get("URL") != new_row.get("URL")]
    rows.append(new_row)
    return rows


def to_excel_bytes(rows: list[dict]) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Courses"

    header_font = Font(name="Arial", bold=True, color="FFFFFF")
    header_fill = PatternFill("solid", start_color="1F4E78")
    body_font = Font(name="Arial", size=10)

    ws.append(COLUMNS)
    for col, name in enumerate(COLUMNS, start=1):
        cell = ws.cell(row=1, column=col)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(wrap_text=True, vertical="center")
        ws.column_dimensions[get_column_letter(col)].width = WIDTHS.get(name, 15)

    for row in rows:
        ws.append([row.get(name) for name in COLUMNS])

    for excel_row in ws.iter_rows(min_row=2):
        for cell in excel_row:
            cell.font = body_font
            cell.alignment = Alignment(wrap_text=True, vertical="top")
            header = COLUMNS[cell.column - 1]
            if header in ("Tuition (EUR/year)", "Application fee (EUR)"):
                cell.number_format = '€#,##0'
            if header == "URL" and cell.value:
                cell.hyperlink = cell.value
                cell.font = Font(name="Arial", size=10, color="0563C1", underline="single")

    ws.row_dimensions[1].height = 32
    ws.freeze_panes = "C2"
    ws.auto_filter.ref = ws.dimensions

    notes = wb.create_sheet("Notes")
    notes["A1"] = "How to use this file"
    notes["A1"].font = Font(name="Arial", bold=True, size=12)
    for i, line in enumerate([
        "Each row is one course, filled automatically from its DreamApply page.",
        "Source: the URL column. 'Date checked' is when the page was read.",
        "Fees, deadlines and requirements change every year - always confirm on the university website before applying.",
        "Requirements on DreamApply can differ by citizenship; the page shows the default view.",
        "'Min. grade (%)' and 'IELTS (min)' are pulled out of the full text - check the full text columns if a value is empty.",
    ], start=3):
        notes[f"A{i}"] = line
        notes[f"A{i}"].font = Font(name="Arial", size=10)
    notes.column_dimensions["A"].width = 110

    buffer = BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


def from_excel_bytes(data: bytes) -> list[dict]:
    """Load rows from a file this app created earlier."""
    wb = load_workbook(BytesIO(data), data_only=True)
    ws = wb["Courses"] if "Courses" in wb.sheetnames else wb.active
    header = [c.value for c in ws[1]]
    rows = []
    for values in ws.iter_rows(min_row=2, values_only=True):
        if any(v is not None for v in values):
            row = dict(zip(header, values))
            rows.append({name: row.get(name) for name in COLUMNS})
    return rows
