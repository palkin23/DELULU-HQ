DELULU HQ — The Main Character Operating System

A playful, private-by-default personal dashboard built with Python, Flask, SQLite, HTML, CSS, and vanilla JavaScript. It works without an AI key: Detective gives a balanced perspective check and Mood-to-Movie uses a built-in collection of fictional movie concepts.

## Run it locally

You need Python 3.9 or newer. From this folder:

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux instead: source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5001. The app uses port 5001 by default so it can run alongside other local Flask projects. Set the `PORT` environment variable to use a different port. The first run creates `delulu.db` and seeds four starter rituals. Your journal, mood check-ins, and completed rituals remain in that local SQLite database. The database file is ignored by Git.

For a custom secret key, set `SECRET_KEY` in your environment before starting the server. The development fallback key is not suitable for a public deployment. Set `DATABASE_PATH` to change the database location. `AI_API_KEY` is intentionally optional; the current app has useful offline generators and does not send personal writing to an external service.

## First files to read

1. **`app.py`** — routes, validation, SQLite queries, and the offline feature data. Start with `index()`, then look at the `/api/...` routes.
2. **`templates/index.html`** — the page structure and the spots where Flask inserts saved data.
3. **`static/app.js`** — modal forms and the browser requests to Flask.
4. **`static/style.css`** — colors, layout, responsive rules, and animations.
5. **`tests/test_app.py`** — examples of calling routes and checking the saved data.

## Features

- **Delulu Detective:** enter a situation for three plausible, balanced readings and a gentle reminder that this is not mind-reading.
- **Mood-to-Movie:** select one of seven moods for a fictional title, synopsis, soundtrack suggestions, and a playful score.
- **Glow-Up Lab:** add rituals, check them off, see a seven-day activity chart, and build a streak. Your tiny companion celebrates completed rituals.
- **3 AM Confessional:** create, edit, and delete mood-tagged diary pages. Entries are stored locally in SQLite.
- **The HQ:** rotating daily quote, persistent daily mood check-in, recent pages, and progress widgets.

## Data and privacy

This starter app has no login or user separation. Run it on your own computer and do not expose the development server to the internet. Diary contents are stored as plain text in the local `delulu.db`; back up or delete that file to manage your data. There is no external AI integration in this version.

## Run the tests

```bash
python -m unittest discover -s tests -v