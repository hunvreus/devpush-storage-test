# devpush-storage-test

Minimal Flask app to test database + volume storage.

## Env vars

- `DB_PATH` (SQLite path)
- `UPLOAD_DIR` (directory for uploaded files)

Example values for devpush storage:

```
DB_PATH=/data/database/<storage-name>/db.sqlite
UPLOAD_DIR=/data/volume/<storage-name>
```

## Run locally

```
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
export DB_PATH=/data/database/<storage-name>/db.sqlite
export UPLOAD_DIR=/data/volume/<storage-name>
python app.py
```

## Endpoints

- `GET /` form + list
- `POST /items` create item
- `GET /uploads/<filename>` serve uploads
