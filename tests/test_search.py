from unittest.mock import MagicMock, patch

from search import search_university_courses


def test_search_tags_dreamapply_links_and_keeps_others():
    fake_response = MagicMock()
    fake_response.ok = True
    fake_response.json.return_value = {
        "organic": [
            {
                "title": "Logistics and Commerce - VMU",
                "link": "https://vytautasmagnus.dreamapply.com/courses/course/93-bachelor-degree-logistics-and-commerce",
            },
            {
                "title": "Trinity College Dublin - Computer Science",
                "link": "https://www.tcd.ie/courses/undergraduate/computer-science",
            },
            {"title": "Ireland - Wikipedia", "link": "https://en.wikipedia.org/wiki/Ireland"},
        ]
    }

    with patch("search.requests.post", return_value=fake_response) as mock_post:
        results = search_university_courses("Ireland", api_key="fake-key")

    assert mock_post.called
    _, kwargs = mock_post.call_args
    assert kwargs["headers"]["X-API-KEY"] == "fake-key"

    links = [r["link"] for r in results]
    assert len(results) == 2
    assert "en.wikipedia.org" not in " ".join(links)

    dreamapply_result = next(r for r in results if "dreamapply" in r["link"])
    other_result = next(r for r in results if "tcd.ie" in r["link"])
    assert dreamapply_result["is_dreamapply"] is True
    assert other_result["is_dreamapply"] is False


def test_search_deduplicates_links():
    fake_response = MagicMock()
    fake_response.ok = True
    same_link = "https://vytautasmagnus.dreamapply.com/courses/course/93-bachelor-degree-logistics-and-commerce"
    fake_response.json.return_value = {
        "organic": [
            {"title": "Result A", "link": same_link},
            {"title": "Result B (duplicate)", "link": same_link},
        ]
    }

    with patch("search.requests.post", return_value=fake_response):
        results = search_university_courses("Lithuania", api_key="fake-key")

    assert len(results) == 1


def test_search_raises_with_serper_error_body():
    fake_response = MagicMock()
    fake_response.ok = False
    fake_response.status_code = 400
    fake_response.text = '{"message":"Query pattern not allowed for free accounts."}'

    with patch("search.requests.post", return_value=fake_response):
        try:
            search_university_courses("Ireland", api_key="fake-key")
            assert False, "expected RuntimeError"
        except RuntimeError as error:
            assert "400" in str(error)
            assert "not allowed for free accounts" in str(error)
