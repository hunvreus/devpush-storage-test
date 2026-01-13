import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, redirect, render_template_string, request, send_from_directory
from werkzeug.utils import secure_filename

DB_PATH = os.getenv("DB_PATH", "./data/db.sqlite")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./data/uploads")

app = Flask(__name__)


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
    return render_template_string(
        """
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Storage Test</title>
  <style>
    body { font-family: sans-serif; max-width: 720px; margin: 40px auto; }
    form { border: 1px solid #ddd; padding: 16px; border-radius: 8px; }
    label { display: block; margin: 8px 0 4px; }
    input, textarea { width: 100%; padding: 8px; }
    button { margin-top: 12px; padding: 8px 12px; }
    .item { border-bottom: 1px solid #eee; padding: 12px 0; }
    img { max-width: 200px; display: block; margin-top: 8px; }
    .muted { color: #666; font-size: 12px; }
  </style>
</head>
<body>
  <h1>Storage Test</h1>
  <p class="muted">DB_PATH={{ db_path }} | UPLOAD_DIR={{ upload_dir }}</p>

  <form action="/items" method="post" enctype="multipart/form-data">
    <label for="title">Title</label>
    <input id="title" name="title" required />

    <label for="note">Note</label>
    <textarea id="note" name="note" rows="3"></textarea>

    <label for="image">Image</label>
    <input id="image" name="image" type="file" />

    <button type="submit">Save</button>
  </form>

  <h2>Items</h2>
  {% for row in rows %}
    <div class="item">
      <strong>#{{ row.id }} {{ row.title }}</strong>
      {% if row.note %}<div>{{ row.note }}</div>{% endif %}
      <div class="muted">{{ row.created_at }}</div>
      {% if row.image_path %}
        <img src="/uploads/{{ row.image_path | e }}" alt="{{ row.title | e }}" />
      {% endif %}
    </div>
  {% else %}
    <p>No items yet.</p>
  {% endfor %}
</body>
</html>
        """,
        rows=rows,
        db_path=DB_PATH,
        upload_dir=UPLOAD_DIR,
    )


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
        if filename:
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
    app.run(host="0.0.0.0", port=8000)
