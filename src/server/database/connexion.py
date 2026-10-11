import sqlite3
from pathlib import Path

from flask import current_app, g


SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schema" / "database.sql"


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def migrer_db(db):
    colonnes_emetteur = {
        ligne["name"] if isinstance(ligne, sqlite3.Row) else ligne[1]
        for ligne in db.execute("PRAGMA table_info(emetteur)")
    }
    if "prenom" not in colonnes_emetteur:
        db.execute(
            "ALTER TABLE emetteur ADD COLUMN prenom TEXT NOT NULL DEFAULT ''"
        )


def init_db():
    db = get_db()
    db.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    migrer_db(db)
    db.commit()


def init_app(app):
    app.teardown_appcontext(close_db)
