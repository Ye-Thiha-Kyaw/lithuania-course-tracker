from unittest.mock import MagicMock, patch

from ai_extract import CourseInfo, extract_with_anthropic, extract_with_gemini

FAKE_PAGE_HTML = """
<html><body>
<script>ignored()</script>
<h1>BSc Computer Science - Trinity College Dublin</h1>
<p>Tuition: EUR 12000 per year. IELTS 6.5 required.</p>
</body></html>
"""

FAKE_INFO = CourseInfo(
    university="Trinity College Dublin",
    programme="Computer Science",
    degree="Bachelor",
    tuition_eur_per_year="12000",
    ielts_min="6.5",
)


def _fake_get_response():
    fake = MagicMock()
    fake.text = FAKE_PAGE_HTML
    fake.raise_for_status = lambda: None
    return fake


def test_extract_with_anthropic_builds_row_from_parsed_output():
    fake_message = MagicMock()
    fake_message.parsed_output = FAKE_INFO

    mock_client = MagicMock()
    mock_client.messages.parse.return_value = fake_message

    with patch("ai_extract.requests.get", return_value=_fake_get_response()):
        with patch("anthropic.Anthropic", return_value=mock_client):
            row = extract_with_anthropic("https://www.tcd.ie/courses/computer-science", api_key="fake-key")

    assert row["University"] == "Trinity College Dublin"
    assert row["Programme"] == "Computer Science"
    assert row["Tuition (EUR/year)"] == 12000
    assert row["IELTS (min)"] == 6.5
    assert row["URL"] == "https://www.tcd.ie/courses/computer-science"
    assert "Date checked" in row

    # The page text passed to the model should have the script tag stripped.
    _, kwargs = mock_client.messages.parse.call_args
    prompt_text = kwargs["messages"][0]["content"]
    assert "ignored()" not in prompt_text
    assert "Computer Science" in prompt_text
    assert kwargs["output_format"] is CourseInfo


def test_extract_with_gemini_builds_row_from_parsed_json():
    fake_interaction = MagicMock()
    fake_interaction.output_text = FAKE_INFO.model_dump_json()

    mock_client = MagicMock()
    mock_client.interactions.create.return_value = fake_interaction

    with patch("ai_extract.requests.get", return_value=_fake_get_response()):
        with patch("google.genai.Client", return_value=mock_client):
            row = extract_with_gemini("https://www.tcd.ie/courses/computer-science", api_key="fake-key")

    assert row["University"] == "Trinity College Dublin"
    assert row["Tuition (EUR/year)"] == 12000
    assert row["URL"] == "https://www.tcd.ie/courses/computer-science"

    _, kwargs = mock_client.interactions.create.call_args
    assert kwargs["response_format"]["mime_type"] == "application/json"


def test_schema_has_no_nullable_unions():
    # Optional[int]/[float] fields produce nullable "anyOf" unions, which
    # structured-output APIs have rejected as "schema too complex" once there
    # are several of them. Every field must be a flat string instead.
    schema = CourseInfo.model_json_schema()
    for name, prop in schema["properties"].items():
        assert "anyOf" not in prop, f"{name} should not be a nullable union"
        assert prop.get("type") == "string", f"{name} should be type 'string', got {prop.get('type')}"
