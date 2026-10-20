"""DELULU HQ — a tiny, beginner-friendly Flask app."""
import os
import random
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

from flask import Flask, flash, g, jsonify, redirect, render_template, request, url_for

BASE_DIR = Path(__file__).resolve().parent
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-change-me")
app.config["DATABASE"] = os.environ.get("DATABASE_PATH", str(BASE_DIR / "delulu.db"))

MOODS = ["Dreamy", "Unbothered", "Romantic", "Chaotic", "Soft", "Powerful", "Melancholy"]
HABIT_STARTERS = ["Drink water", "Move my body", "Read 10 pages", "Do my skincare"]
QUOTES = [
    "You are allowed to be a work in progress and a masterpiece at once.",
    "Romanticize the little things. They are the big things.",
    "Your life is happening now, angel. Make it a scene.",
    "Softness is a strength with excellent taste.",
    "Be the plot twist you needed.",
]
MOVIES = {
    "Dreamy": ("The Moon Sent Me a Playlist", "One seaside summer, a mysterious mixtape, and a girl learning to listen to her own heart.", ["Space Song — Beach House", "Moon Song — Phoebe Bridgers", "Dreams — The Cranberries"]),
    "Unbothered": ("No Notes, Just Nerve", "A city girl deletes the group chat and discovers the radical joy of minding her own gorgeous business.", ["Good as Hell — Lizzo", "Boss Bitch — Doja Cat", "Flowers — Miley Cyrus"]),
    "Romantic": ("Meet Me Under the Marquee", "Two almost-strangers keep missing the same train until the universe, and a very nosy florist, intervenes.", ["Lover — Taylor Swift", "Kiss Me — Sixpence None the Richer", "Glue Song — beabadoobee"]),
    "Chaotic": ("Oops! All Plot Twists", "A perfectly planned week becomes a glittery disaster tour with one surprisingly excellent ending.", ["360 — Charli xcx", "Von dutch — Charli xcx", "HOT TO GO! — Chappell Roan"]),
    "Soft": ("A Little Room to Bloom", "In a sunlit apartment, a burnt-out overachiever learns to make tea, take naps, and begin again.", ["Sweet — Cigarettes After Sex", "Garden Song — Phoebe Bridgers", "Bloom — The Paper Kites"]),
    "Powerful": ("Her Name in Neon", "After a career detour, a designer builds a tiny empire with big ideas, brave friends, and immaculate eyeliner.", ["Confident — Demi Lovato", "Run the World (Girls) — Beyoncé", "Free Woman — Lady Gaga"]),
    "Melancholy": ("The Beautiful Almost", "A tender story about letting a chapter end without pretending it meant nothing.", ["Liability — Lorde", "The Night We Met — Lord Huron", "Bags — Clairo"]),
}

def db():
    if "db" not in g:
        g.db = sqlite3.connect(app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db

@app.teardown_appcontext
def close_db(_error=None):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()

def init_db():
    conn = sqlite3.connect(app.config["DATABASE"])
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS diary (id INTEGER PRIMARY KEY, title TEXT NOT NULL, body TEXT NOT NULL, mood TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS habits (id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE, created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS habit_logs (id INTEGER PRIMARY KEY, habit_id INTEGER NOT NULL REFERENCES habits(id) ON DELETE CASCADE, day TEXT NOT NULL, UNIQUE(habit_id, day));
    CREATE TABLE IF NOT EXISTS checkins (day TEXT PRIMARY KEY, mood TEXT NOT NULL, note TEXT DEFAULT '');
    """)
    if conn.execute("SELECT COUNT(*) FROM habits").fetchone()[0] == 0:
        conn.executemany("INSERT INTO habits(name, created_at) VALUES (?, ?)", [(x, date.today().isoformat()) for x in HABIT_STARTERS])
    conn.commit()
    conn.close()

def home_data():
    today = date.today().isoformat()
    habits = db().execute("SELECT h.*, EXISTS(SELECT 1 FROM habit_logs l WHERE l.habit_id=h.id AND l.day=?) done FROM habits h ORDER BY h.id", (today,)).fetchall()
    logs = db().execute("SELECT day, COUNT(*) count FROM habit_logs WHERE day >= ? GROUP BY day ORDER BY day", ((date.today()-timedelta(days=6)).isoformat(),)).fetchall()
    log_map = {r["day"]: r["count"] for r in logs}
    chart = [{"day": (date.today()-timedelta(days=i)).strftime("%a"), "count": log_map.get((date.today()-timedelta(days=i)).isoformat(), 0)} for i in reversed(range(7))]
    entries = db().execute("SELECT * FROM diary ORDER BY updated_at DESC LIMIT 4").fetchall()
    checkin = db().execute("SELECT mood FROM checkins WHERE day=?", (today,)).fetchone()
    return habits, chart, entries, checkin["mood"] if checkin else None

@app.get("/")
def index():
    habits, chart, entries, today_mood = home_data()
    completed = sum(h["done"] for h in habits)
    return render_template("index.html", habits=habits, chart=chart, entries=entries, today_mood=today_mood,
                           quote=random.choice(QUOTES), moods=MOODS, completed=completed,
                           streak=streak_count(), pet="✨" if completed else "🐰")

def streak_count():
    days = {r[0] for r in db().execute("SELECT DISTINCT day FROM habit_logs")}
    count = 0
    cursor = date.today()
    while cursor.isoformat() in days:
        count += 1
        cursor -= timedelta(days=1)
    if count == 0 and (date.today()-timedelta(days=1)).isoformat() in days:
        cursor = date.today()-timedelta(days=1)
        while cursor.isoformat() in days:
            count += 1
            cursor -= timedelta(days=1)
    return count

@app.post("/api/detective")
def detective():
    situation = request.form.get("situation", "").strip()
    if len(situation) < 8 or len(situation) > 1200:
        return jsonify(error="Give us at least 8 characters, and keep it under 1,200."), 400
    # Balanced, intentionally non-diagnostic fallback. AI_API_KEY is optional for future integrations.
    return jsonify(title="The evidence, your honor", situation=situation, explanations=[
        {"label":"The hopeful read 💌", "text":"There may be interest or good intentions here. Look for consistent actions, not one dazzling clue."},
        {"label":"The ordinary read ☁️", "text":"They could simply be busy, distracted, or communicating in their usual way. One moment rarely tells the whole story."},
        {"label":"The you-first read 👑", "text":"Whatever they meant, notice how this lands for you. You can ask directly, set a boundary, or give it a little space."},
    ], note="A playful perspective check—not mind-reading. Clear communication beats decoding clues.")

@app.post("/api/movie")
def movie():
    mood = request.form.get("mood", "").strip()
    if mood not in MOVIES:
        return jsonify(error="Pick a mood from the list."), 400
    title, synopsis, soundtrack = MOVIES[mood]
    return jsonify(title=title, synopsis=synopsis, soundtrack=soundtrack, score=random.randint(82, 100), mood=mood)

@app.post("/api/checkin")
def checkin():
    mood = request.form.get("mood", "").strip()
    if mood not in MOODS:
        return jsonify(error="Please choose one of the listed moods."), 400
    db().execute("INSERT INTO checkins(day,mood) VALUES(?,?) ON CONFLICT(day) DO UPDATE SET mood=excluded.mood", (date.today().isoformat(), mood))
    db().commit()
    return jsonify(ok=True, mood=mood)

@app.post("/api/habits")
def add_habit():
    name = request.form.get("name", "").strip()
    if not 2 <= len(name) <= 60:
        return jsonify(error="Habit names need 2–60 characters."), 400
    try:
        db().execute("INSERT INTO habits(name,created_at) VALUES(?,?)", (name, date.today().isoformat()))
        db().commit()
    except sqlite3.IntegrityError:
        return jsonify(error="That habit is already on your list."), 400
    return jsonify(ok=True)

@app.post("/api/habits/<int:habit_id>/toggle")
def toggle_habit(habit_id):
    conn = db()
    if not conn.execute("SELECT id FROM habits WHERE id=?", (habit_id,)).fetchone():
        return jsonify(error="Habit not found."), 404
    today = date.today().isoformat()
    exists = conn.execute("SELECT id FROM habit_logs WHERE habit_id=? AND day=?", (habit_id,today)).fetchone()
    if exists: conn.execute("DELETE FROM habit_logs WHERE id=?", (exists["id"],))
    else: conn.execute("INSERT INTO habit_logs(habit_id,day) VALUES(?,?)", (habit_id,today))
    conn.commit()
    return jsonify(ok=True, done=not bool(exists))

@app.post("/api/diary")
def create_entry():
    title, body, mood = (request.form.get(k, "").strip() for k in ("title","body","mood"))
    if not title or len(title)>100 or not body or len(body)>5000 or mood not in MOODS:
        return jsonify(error="Add a title (1–100 chars), an entry (1–5,000 chars), and choose a mood."), 400
    now = datetime.now().isoformat(timespec="minutes")
    cur = db().execute("INSERT INTO diary(title,body,mood,created_at,updated_at) VALUES(?,?,?,?,?)", (title,body,mood,now,now))
    db().commit()
    return jsonify(ok=True, id=cur.lastrowid)

@app.route("/api/diary/<int:entry_id>", methods=["GET","PUT","DELETE"])
def diary_entry(entry_id):
    conn = db()
    entry = conn.execute("SELECT * FROM diary WHERE id=?", (entry_id,)).fetchone()
    if not entry: return jsonify(error="Entry not found."), 404
    if request.method == "GET": return jsonify(dict(entry))
    if request.method == "DELETE":
        conn.execute("DELETE FROM diary WHERE id=?", (entry_id,)); conn.commit(); return jsonify(ok=True)
    title, body, mood = (request.form.get(k, "").strip() for k in ("title","body","mood"))
    if not title or len(title)>100 or not body or len(body)>5000 or mood not in MOODS:
        return jsonify(error="Add a title (1–100 chars), an entry (1–5,000 chars), and choose a mood."), 400
    conn.execute("UPDATE diary SET title=?,body=?,mood=?,updated_at=? WHERE id=?", (title,body,mood,datetime.now().isoformat(timespec="minutes"),entry_id))
    conn.commit(); return jsonify(ok=True)

@app.errorhandler(404)
def not_found(_error):
    if request.path.startswith("/api/"): return jsonify(error="That little corner doesn't exist."), 404
    return "Page not found", 404

if __name__ == "__main__":
    init_db()
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
