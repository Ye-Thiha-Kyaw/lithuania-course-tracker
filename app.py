"""Lithuania Course Tracker - paste DreamApply course links, get an Excel sheet.

Run locally:  streamlit run app.py
"""

import pandas as pd
import streamlit as st

from dreamapply import COLUMNS, scrape
from excel_export import from_excel_bytes, to_excel_bytes, upsert

st.set_page_config(page_title="Lithuania Course Tracker", page_icon="🎓", layout="wide")

if "rows" not in st.session_state:
    st.session_state.rows = []

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
