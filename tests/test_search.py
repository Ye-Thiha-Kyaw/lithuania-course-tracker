from unittest.mock import MagicMock, patch

from search import search_dreamapply_courses


def test_search_filters_to_dreamapply_course_links():
    fake_response = MagicMock()
    fake_response.raise_for_status = lambda: None
    fake_response.json.return_value = {
        "organic": [
            {
                "title": "Logistics and Commerce - VMU",
                "link": "https://vytautasmagnus.dreamapply.com/courses/course/93-bachelor-degree-logistics-and-commerce",
            },
            {"title": "University homepage", "link": "https://vytautasmagnus.dreamapply.com/"},
            {
                "title": "Transport Management - VilniusTech",
                "link": "https://apply.vilniustech.lt/courses/course/209-bachelor-logistics-and-transport-management",
            },
        ]
    }

    with patch("search.requests.post", return_value=fake_response) as mock_post:
        results = search_dreamapply_courses("Lithuania", api_key="fake-key")

    assert mock_post.called
    _, kwargs = mock_post.call_args
    assert kwargs["headers"]["X-API-KEY"] == "fake-key"

    links = [r["link"] for r in results]
    assert len(results) == 2
    assert all("/courses/course/" in link for link in links)
    assert "https://vytautasmagnus.dreamapply.com/" not in links


def test_search_deduplicates_links():
    fake_response = MagicMock()
    fake_response.raise_for_status = lambda: None
    same_link = "https://vytautasmagnus.dreamapply.com/courses/course/93-bachelor-degree-logistics-and-commerce"
    fake_response.json.return_value = {
        "organic": [
            {"title": "Result A", "link": same_link},
            {"title": "Result B (duplicate)", "link": same_link},
        ]
    }

    with patch("search.requests.post", return_value=fake_response):
        results = search_dreamapply_courses("Lithuania", api_key="fake-key")

    assert len(results) == 1
