# 🎓 Lithuania Course Tracker

Paste a university course link, get a tidy Excel row.

Many Lithuanian universities publish their programmes on **DreamApply**, and every DreamApply course page uses the same layout (Tuition fee, Application fee, Entry qualification, Language requirements, Application deadline…). This app reads those pages and fills one row per course, so a student can compare programmes side by side and download the table as Excel.

Built as the first step of a larger project: an AI assistant that helps international students check their eligibility and prepare applications for Lithuanian bachelor's programmes.

## What it does

- Paste one or more DreamApply course links → each becomes a row
- Or type a country, search the web for bachelor-course pages at *any* university or college there, and pick which ones to add (needs a Serper.dev API key; DreamApply pages are read automatically, other universities' pages are read with an AI model if you add a Claude or Gemini key - see below)
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
search.py            Finds bachelor-course pages for a country (Serper.dev search)
ai_extract.py         Reads a non-DreamApply course page with Claude or Gemini
excel_export.py      Builds the formatted Excel file (and reads it back)
tests/               Parser, Excel, search and AI-extraction tests (pytest)
sample/              Example Excel with two courses
railway.json         Start command if you deploy on Railway
```

## Country search (optional)

The "Find courses by country" box searches the web for bachelor-course pages at any
university or college in that country, instead of you pasting links one by one.

1. **Web search** - needs a free [Serper.dev](https://serper.dev) API key (2,500 free
   searches). Without this key the box just shows setup instructions; everything else
   in the app still works.
2. **Reading the pages it finds** - DreamApply pages are parsed automatically, for
   free, the same way pasted links are. Any other university's page needs an AI model
   to read it (there's no single layout to parse), so add **one** of:
   - `ANTHROPIC_API_KEY` (Claude, console.anthropic.com) - used first if both are set
   - `GOOGLE_API_KEY` (Gemini, aistudio.google.com)

   Without either key, non-DreamApply results still show up in the list but are
   skipped when you click "Add selected courses" (a warning says why). AI reads are
   not free - each page read costs a small amount on your API account.

Add secrets:
- **Locally**: create `.streamlit/secrets.toml`:
  ```toml
  SERPER_API_KEY = "your-serper-key"
  ANTHROPIC_API_KEY = "your-anthropic-key"      # optional
  GOOGLE_API_KEY = "your-google-key"            # optional
  ```
- **On Streamlit Cloud**: app page -> Settings -> Secrets -> paste the same lines.

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
