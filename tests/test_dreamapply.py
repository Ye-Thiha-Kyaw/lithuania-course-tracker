from pathlib import Path

from dreamapply import is_dreamapply_course_url, parse_course
from excel_export import from_excel_bytes, to_excel_bytes, upsert

HERE = Path(__file__).parent

VMU_HTML = """<html><head><title>[Bachelor Degree] Logistics and Commerce - Vytautas Magnus University</title></head><body>
<table><tr><th>Study location</th><td>Lithuania, Kaunas</td></tr>
<tr><th>Nominal duration</th><td>3,5 years (210 ECTS)</td></tr></table>
<table><tr><th>Tuition fee</th><td>€3,400 per year</td></tr>
<tr><th>Application fee</th><td>€150 one-time<br>Non-EU applicants shall pay through the Flywire portal.</td></tr></table>
<table><tr><th>Entry qualification</th><td>High school / secondary education (or higher)<br>Minimum 60% CGPA<br>
Admission score counting is based on: Grade for the Mathematics exam * 0.4 + Grade for the English exam * 0.4 + Motivation letter and/or interview * 0.2<br>
Minimum admission score to qualify: 5,4</td></tr></table>
<table><tr><th>Language requirements</th><td>TOEFL 87-109 iBT<br>IELTS 5,5–6,5<br>Duolingo 100-125</td></tr></table>
<table><tr><th>Other requirements</th><td>A motivation letter must be added to your application.<br>Upload your Curriculum Vitae (CV)</td></tr></table>
<a>Apply now! Fall semester 2027/28</a><p>Application deadline</p><p>1 Jul 2027, 23:59:59</p>
<p>Studies commence</p><p>23 Aug 2027</p></body></html>"""


def test_vilniustech_page():
    html = (HERE / "fixture_vilniustech.html").read_text()
    row = parse_course(html, "https://apply.vilniustech.lt/courses/course/209-x")
    assert row["University"] == "Vilnius Gediminas Technical University"
    assert row["Tuition (EUR/year)"] == 3950
    assert row["Application fee (EUR)"] == 100
    assert row["Min. grade (%)"] == 60
    assert row["References needed"] == 2
    assert "Pakistan" in row["Blocked citizenships"]
    assert row["Application deadline"] == "15 Jun 2027"


def test_vmu_page():
    row = parse_course(VMU_HTML, "https://vytautasmagnus.dreamapply.com/courses/course/93-x")
    assert row["City"] == "Kaunas"
    assert row["Duration"] == "3,5 years"
    assert row["Tuition (EUR/year)"] == 3400
    assert row["Application fee (EUR)"] == 150
    assert row["IELTS (min)"] == 5.5
    assert row["Duolingo (min)"] == 100
    assert "0.4" in row["Admission formula"] and "min. score 5,4" in row["Admission formula"]
    assert row["Motivation letter"] == "Yes"
    assert row["Blocked citizenships"] == ""
    assert row["Studies start"] == "23 Aug 2027"


def test_url_check():
    assert is_dreamapply_course_url("https://apply.vilniustech.lt/courses/course/209-abc")
    assert not is_dreamapply_course_url("https://www.vdu.lt/en/")


def test_excel_round_trip_and_upsert():
    row = parse_course(VMU_HTML, "https://example.dreamapply.com/courses/course/1-a")
    rows = upsert([], row)
    rows = upsert(rows, dict(row, **{"Tuition (EUR/year)": 3500}))  # same URL -> replaced
    assert len(rows) == 1
    back = from_excel_bytes(to_excel_bytes(rows))
    assert back[0]["Tuition (EUR/year)"] == 3500
