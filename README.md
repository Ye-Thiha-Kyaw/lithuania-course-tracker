# 🎓 Lithuania Course Tracker

Paste a university course link, get a tidy Excel row.

Many Lithuanian universities publish their programmes on **DreamApply**, and every DreamApply course page uses the same layout (Tuition fee, Application fee, Entry qualification, Language requirements, Application deadline…). This app reads those pages and fills one row per course, so a student can compare programmes side by side and download the table as Excel.

Built as the first step of a larger project: an AI assistant that helps international students check their eligibility and prepare applications for Lithuanian bachelor's programmes.

## What it does

- Paste one or more DreamApply course links → each becomes a row
- Or type a country, search the web for matching DreamApply course pages, and pick which ones to add (needs a Serper.dev API key, see below)
- Pulls out key numbers: tuition, application fee, minimum grade %, IELTS minimum, references needed, blocked citizenships, deadline, start date
- Keeps the full requirement text too, because the details matter
- Edit any cell in the browser, then **Download Excel**
- Upload a previously downloaded file to keep adding to it
- Pasting the same link again updates that row instead of duplicating it

Works with links like:
```
https://vytautasmagnus.dreamapply.com/courses/course/93-bachelor-degree-logistics-and-commerce
https://apply.vilniustech.lt/courses/course/209-bachelor-logistics-and-transport-management
```

## Project structure

```
app.py               Streamlit web page
dreamapply.py        Downloads and parses a DreamApply course page
search.py            Finds DreamApply course pages for a country (Serper.dev search)
excel_export.py      Builds the formatted Excel file (and reads it back)
tests/               Parser, Excel and search tests (pytest)
sample/              Example Excel with two courses
railway.json         Start command if you deploy on Railway
```

## Country search (optional)

The "Find courses by country" box searches the web for DreamApply course pages instead of
you pasting links one by one. It needs a free [Serper.dev](https://serper.dev) API key
(2,500 free searches):

1. Sign up at serper.dev and copy your API key.
2. **Locally**: create `.streamlit/secrets.toml` with:
   ```toml
   SERPER_API_KEY = "your-key-here"
   ```
3. **On Streamlit Cloud**: app page -> Settings -> Secrets -> paste the same line.

Without a key, the rest of the app (pasting links directly) works exactly as before.

## Run it on your computer

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Run the tests with `pip install pytest && pytest`.

## Put it online (a link that opens in any browser)

### 1. Push to GitHub
```bash
git init
git add .
git commit -m "Lithuania course tracker"
git branch -M main
git remote add origin https://github.com/<your-username>/lithuania-course-tracker.git
git push -u origin main
```

### 2a. Streamlit Community Cloud (free, easiest)
1. Go to share.streamlit.io and sign in with GitHub.
2. **Create app** → pick this repo, branch `main`, main file `app.py`.
3. Deploy. You get a link like `https://<name>.streamlit.app`.
Every `git push` redeploys automatically. The app sleeps when nobody uses it and wakes up in a few seconds.

### 2b. Railway (~$5/month, always on)
1. railway.com → **New Project** → **Deploy from GitHub repo** → pick this repo.
2. Railway reads `railway.json` for the start command.
3. Settings → Networking → **Generate Domain** to get a public link.

## Limitations

- Fees, deadlines and requirements change every year. Always confirm on the official page before applying. The `Date checked` column shows when each page was read.
- DreamApply can show different requirements depending on citizenship. The app reads the default view.
- Values like "Min. grade (%)" are pulled out of free text with patterns. If a cell is empty, check the full-text columns.
- Only DreamApply course pages are supported for now.
- No data is stored on the server. Download the Excel file to keep your list.

## Roadmap

- [x] DreamApply course pages → Excel
- [ ] List all English-taught bachelor courses from a university's DreamApply catalogue automatically
- [ ] Eligibility check from a student's grades and English certificate
- [ ] Motivation letter feedback (coaching, not ghost-writing)
- [ ] Personal application timeline from deadlines
