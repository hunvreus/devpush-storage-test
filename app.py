import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, redirect, render_template, request, send_from_directory
from werkzeug.utils import secure_filename

DB_PATH = os.getenv("DB_PATH", "./data/db.sqlite")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./data/uploads")
ALLOWED_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}

app = Flask(__name__)


@app.template_filter("datefmt")
def datefmt(val):
    dt = datetime.fromisoformat(val)
    now = datetime.now(timezone.utc)
    diff = now - dt
    s = int(diff.total_seconds())
    if s < 60:
        return "just now"
    if s < 3600:
        m = s // 60
        return f"{m}m ago"
    if s < 86400:
        h = s // 3600
        return f"{h}h ago"
    d = s // 86400
    if d == 1:
        return "yesterday"
    if d < 30:
        return f"{d}d ago"
    return dt.strftime("%b %d, %Y")


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _init_db():
    Path(os.path.dirname(DB_PATH) or ".").mkdir(parents=True, exist_ok=True)
    Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                note TEXT,
                image_path TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


_db_ready = False


@app.before_request
def startup():
    global _db_ready
    if _db_ready:
        return
    _init_db()
    _db_ready = True


@app.get("/")
def index():
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, title, note, image_path, created_at FROM items ORDER BY id DESC"
        ).fetchall()
    return render_template("index.html", rows=rows, db_path=DB_PATH, upload_dir=UPLOAD_DIR)


@app.post("/items")
def create_item():
    title = (request.form.get("title") or "").strip()
    note = (request.form.get("note") or "").strip() or None
    if not title:
        return redirect("/")

    image = request.files.get("image")
    image_path = None
    if image and image.filename:
        filename = secure_filename(image.filename)
        ext = os.path.splitext(filename)[1].lower()
        if filename and ext in ALLOWED_EXT:
            stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
            stored_name = f"{stamp}-{filename}"
            dest_path = os.path.join(UPLOAD_DIR, stored_name)
            image.save(dest_path)
            image_path = stored_name

    now = datetime.now(timezone.utc).isoformat()
    with _connect() as conn:
        conn.execute(
            "INSERT INTO items (title, note, image_path, created_at) VALUES (?, ?, ?, ?)",
            (title, note, image_path, now),
        )
        conn.commit()

    return redirect("/")


@app.get("/uploads/<path:filename>")
def uploads(filename):
    return send_from_directory(UPLOAD_DIR, filename)


if __name__ == "__main__":
    _init_db()
    app.run(host="0.0.0.0", port=8000, debug=True)
