"""Lithuania Course Tracker - paste DreamApply course links, get an Excel sheet.

Run locally:  streamlit run app.py
"""

import pandas as pd
import streamlit as st

from ai_extract import extract_with_anthropic, extract_with_gemini
from dreamapply import COLUMNS, scrape
from excel_export import from_excel_bytes, to_excel_bytes, upsert
from search import search_university_courses

st.set_page_config(page_title="Lithuania Course Tracker", page_icon="🎓", layout="wide")

st.markdown(
    """
    <style>
    [data-testid="stDataFrame"] ::-webkit-scrollbar {
        height: 16px;
        width: 16px;
    }
    [data-testid="stDataFrame"] ::-webkit-scrollbar-track {
        background: rgba(128, 128, 128, 0.15);
    }
    [data-testid="stDataFrame"] ::-webkit-scrollbar-thumb {
        background: rgba(128, 128, 128, 0.8);
        border-radius: 8px;
        border: 3px solid transparent;
        background-clip: padding-box;
    }
    [data-testid="stDataFrame"] ::-webkit-scrollbar-thumb:hover {
        background: rgba(128, 128, 128, 1);
        background-clip: padding-box;
    }
    [data-testid="stDataFrame"] * {
        scrollbar-width: auto;
        scrollbar-color: rgba(128, 128, 128, 0.8) rgba(128, 128, 128, 0.15);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if "rows" not in st.session_state:
    st.session_state.rows = []
if "search_results" not in st.session_state:
    st.session_state.search_results = []
if "add_queue" not in st.session_state:
    st.session_state.add_queue = []
if "add_queue_total" not in st.session_state:
    st.session_state.add_queue_total = 0


def _secret(name: str) -> str:
    try:
        return st.secrets.get(name, "")
    except Exception:
        return ""


def _ai_extractor():
    """Return (extract_function, api_key, provider_name) for whichever AI
    secret is configured, preferring Anthropic. None if neither is set."""
    anthropic_key = _secret("ANTHROPIC_API_KEY")
    if anthropic_key:
        return extract_with_anthropic, anthropic_key, "Claude"
    gemini_key = _secret("GOOGLE_API_KEY")
    if gemini_key:
        return extract_with_gemini, gemini_key, "Gemini"
    return None, "", ""

st.title("🎓 Lithuania Course Tracker")
st.write(
    "Paste DreamApply course links (one per line). Each course becomes a row in the table, "
    "and you can download everything as an Excel file."
)

with st.expander("Continue an Excel file you downloaded before"):
    uploaded = st.file_uploader("Upload courses.xlsx", type=["xlsx"])
    if uploaded is not None and st.button("Load this file"):
        st.session_state.rows = from_excel_bytes(uploaded.getvalue())
        st.success(f"Loaded {len(st.session_state.rows)} courses.")

with st.expander("Find courses by country (uses web search)"):
    serper_key = _secret("SERPER_API_KEY")
    extract_fn, ai_key, ai_provider = _ai_extractor()

    if not serper_key:
        st.info(
            "This needs a free Serper.dev API key. Add it as a secret named "
            "`SERPER_API_KEY` in Streamlit Cloud (app settings -> Secrets), or in a "
            "local `.streamlit/secrets.toml` file, then reload the app."
        )
    else:
        if not ai_key:
            st.caption(
                "DreamApply course pages will be read automatically. For other "
                "universities, add an `ANTHROPIC_API_KEY` or `GOOGLE_API_KEY` secret "
                "to read those pages with AI too - without one they're skipped."
            )
        else:
            st.caption(f"Non-DreamApply pages will be read with {ai_provider}.")

        country = st.text_input("Country", placeholder="Lithuania")
        if st.button("Search") and country.strip():
            st.session_state.search_ran = True
            with st.spinner(f"Searching for {country.strip()} bachelor courses..."):
                try:
                    st.session_state.search_results = search_university_courses(country.strip(), serper_key)
                except Exception as error:
                    st.error(f"Search failed: {error}")
                    st.session_state.search_results = []

        results = st.session_state.search_results
        if results:
            st.caption(f"Found {len(results)} course page(s). Pick the ones to add:")
            selected = []
            for i, result in enumerate(results):
                label = result["title"] if result["is_dreamapply"] else f"{result['title']} (AI read)"
                if st.checkbox(label, key=f"search_pick_{i}"):
                    selected.append(result)
            if st.button("Add selected courses", type="primary") and selected:
                st.session_state.add_queue = list(selected)
                st.session_state.add_queue_total = len(selected)
                st.rerun()
        elif "search_ran" in st.session_state:
            st.caption("No course pages found for that country. Try a different spelling.")

        if st.session_state.add_queue:
            done = st.session_state.add_queue_total - len(st.session_state.add_queue)
            st.progress(
                done / st.session_state.add_queue_total,
                text=f"Adding course {done + 1} of {st.session_state.add_queue_total}...",
            )
            if st.button("Stop adding courses"):
                st.session_state.add_queue = []
                st.session_state.add_queue_total = 0
                st.rerun()
            else:
                # Process one item per rerun, so the Stop button above stays
                # clickable between items instead of the whole batch running
                # in one uninterruptible loop.
                result = st.session_state.add_queue.pop(0)
                url = result["link"]
                try:
                    if result["is_dreamapply"]:
                        with st.spinner(f"Reading {url}"):
                            row = scrape(url)
                    elif extract_fn:
                        with st.spinner(f"Reading {url} with {ai_provider}..."):
                            row = extract_fn(url, ai_key)
                    else:
                        st.warning(f"Skipped {url}: add an AI API key to read non-DreamApply pages.")
                        row = None
                    if row:
                        st.session_state.rows = upsert(st.session_state.rows, row)
                        st.success(f"Added: {row['Programme']} - {row['University']}")
                except Exception as error:
                    st.error(f"Couldn't read {url}: {error}")
                st.rerun()

urls_text = st.text_area(
    "Course links",
    placeholder="https://vytautasmagnus.dreamapply.com/courses/course/93-bachelor-degree-logistics-and-commerce\n"
    "https://apply.vilniustech.lt/courses/course/209-bachelor-logistics-and-transport-management",
    height=120,
)

if st.button("Add courses", type="primary"):
    urls = [u.strip() for u in urls_text.splitlines() if u.strip()]
    if not urls:
        st.warning("Paste at least one link first.")
    for url in urls:
        try:
            with st.spinner(f"Reading {url}"):
                row = scrape(url)
            st.session_state.rows = upsert(st.session_state.rows, row)
            st.success(f"Added: {row['Programme']} - {row['University']}")
        except Exception as error:  # show the problem, keep going with the other links
            st.error(f"Couldn't read {url}: {error}")

rows = st.session_state.rows
if rows:
    st.subheader(f"Your courses ({len(rows)})")
    st.caption("You can fix any cell by clicking it. Changes are included in the Excel download.")
    df = pd.DataFrame(rows, columns=COLUMNS)
    edited = st.data_editor(
        df,
        width="stretch",
        num_rows="dynamic",
        column_config={"URL": st.column_config.LinkColumn("URL")},
        key="editor",
    )
    clean_rows = edited.astype(object).where(pd.notna(edited), None).to_dict("records")

    col1, col2 = st.columns([1, 1])
    col1.download_button(
        "⬇️ Download Excel",
        data=to_excel_bytes(clean_rows),
        file_name="lithuania_courses.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
    )
    if col2.button("Clear table"):
        st.session_state.rows = []
        st.rerun()
else:
    st.info("No courses yet. Paste a link above and press **Add courses**.")

st.divider()
st.caption(
    "Data comes from each university's DreamApply page. Fees, deadlines and requirements change - "
    "always confirm on the official page before applying. Nothing you enter is stored on the server; "
    "download the Excel file to keep your list."
)
