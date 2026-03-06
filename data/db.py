# data/db.py — ERAGROK · Couche SQLite
# Remplace tout accès CSV/JSON. Un seul fichier .db par utilisateur.
#
# Schéma :
#   users/eragrok.db           → table users  (registre global)
#   users/{folder}/{folder}.db → tables nutrition, planning, cycle,
#                                 training_history, programmes, settings
# ─────────────────────────────────────────────────────────────────────────────
import os, json, sqlite3
from pathlib import Path

# Résolu dynamiquement depuis utils pour éviter l'import circulaire
def _users_dir():
    from data.utils import USERS_DIR
    return USERS_DIR

# ════════════════════════════════════════════════════════════════════════════
#  BASE GLOBALE  (registre des utilisateurs)
# ════════════════════════════════════════════════════════════════════════════

def global_db_path():
    return os.path.join(_users_dir(), "eragrok.db")

def get_global_db():
    p = global_db_path()
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(p)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL UNIQUE,
            age         TEXT    DEFAULT '',
            sexe        TEXT    DEFAULT 'Homme',
            taille      TEXT    DEFAULT '',
            poids       TEXT    DEFAULT '',
            objectif    TEXT    DEFAULT '',
            ajustement  TEXT    DEFAULT 'Maintien (0%)'
        )
    """)
    con.commit()
    return con


# ════════════════════════════════════════════════════════════════════════════
#  BASE UTILISATEUR
# ════════════════════════════════════════════════════════════════════════════

def user_db_path(folder: str) -> str:
    return os.path.join(_users_dir(), folder, f"{folder}.db")

def get_user_db(folder: str) -> sqlite3.Connection:
    """Retourne une connexion à la base de l'utilisateur, crée les tables si besoin."""
    p = user_db_path(folder)
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(p)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.executescript("""
        CREATE TABLE IF NOT EXISTS nutrition (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            date        TEXT NOT NULL,
            poids       TEXT DEFAULT '',
            age         TEXT DEFAULT '',
            calories    TEXT DEFAULT '',
            proteines   TEXT DEFAULT '',
            glucides    TEXT DEFAULT '',
            lipides     TEXT DEFAULT '',
            note        TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS planning (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            date        TEXT NOT NULL,
            groupes     TEXT DEFAULT '',
            programme   TEXT DEFAULT '',
            types       TEXT DEFAULT '',
            note        TEXT DEFAULT '',
            line        TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS cycle (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            debut           TEXT DEFAULT '',
            fin_estimee     TEXT DEFAULT '',
            longueur_sem    TEXT DEFAULT '',
            produits_doses  TEXT DEFAULT '',
            note            TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS training_history (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            date        TEXT DEFAULT '',
            type        TEXT DEFAULT '',
            duration    TEXT DEFAULT '',
            notes       TEXT DEFAULT '',
            exercises   TEXT DEFAULT '[]',
            planned_for TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS programmes (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            title   TEXT DEFAULT '',
            created TEXT DEFAULT '',
            lines   TEXT DEFAULT '[]'
        );
        CREATE TABLE IF NOT EXISTS settings (
            key     TEXT PRIMARY KEY,
            value   TEXT DEFAULT ''
        );
    """)
    con.commit()
    return con

def get_user_db_from_app(app) -> sqlite3.Connection:
    folder = getattr(app, "current_user", None) or "default"
    return get_user_db(folder)


# ════════════════════════════════════════════════════════════════════════════
#  NUTRITION
# ════════════════════════════════════════════════════════════════════════════

def nutrition_insert(app, date, poids, age, calories, proteines, glucides, lipides, note=""):
    con = get_user_db_from_app(app)
    con.execute("""
        INSERT INTO nutrition (date, poids, age, calories, proteines, glucides, lipides, note)
        VALUES (?,?,?,?,?,?,?,?)
    """, (date, poids, age, str(calories), str(proteines), str(glucides), str(lipides), note))
    con.commit(); con.close()

def nutrition_get_all(app):
    """Retourne toutes les lignes comme liste de dicts, ordre chronologique."""
    con = get_user_db_from_app(app)
    rows = con.execute("SELECT * FROM nutrition ORDER BY date ASC").fetchall()
    con.close()
    return [dict(r) for r in rows]

def nutrition_get_last_n(app, n=1):
    con = get_user_db_from_app(app)
    rows = con.execute("SELECT * FROM nutrition ORDER BY date DESC LIMIT ?", (n,)).fetchall()
    con.close()
    return [dict(r) for r in rows]

def nutrition_update(app, row_id, date, poids, age, calories, proteines, glucides, lipides, note):
    con = get_user_db_from_app(app)
    con.execute("""
        UPDATE nutrition SET date=?, poids=?, age=?, calories=?, proteines=?,
                             glucides=?, lipides=?, note=?
        WHERE id=?
    """, (date, poids, age, str(calories), str(proteines), str(glucides), str(lipides), note, row_id))
    con.commit(); con.close()

def nutrition_delete_by_date(app, date_str):
    con = get_user_db_from_app(app)
    con.execute("DELETE FROM nutrition WHERE date=?", (date_str,))
    con.commit(); con.close()

def nutrition_delete_by_id(app, row_id):
    con = get_user_db_from_app(app)
    con.execute("DELETE FROM nutrition WHERE id=?", (row_id,))
    con.commit(); con.close()


# ════════════════════════════════════════════════════════════════════════════
#  PLANNING
# ════════════════════════════════════════════════════════════════════════════

def planning_insert(app, date, groupes="", programme="", types="", note="", line=""):
    con = get_user_db_from_app(app)
    con.execute("""
        INSERT INTO planning (date, groupes, programme, types, note, line)
        VALUES (?,?,?,?,?,?)
    """, (date, groupes, programme, types, note, line))
    con.commit(); con.close()

def planning_get_all(app):
    con = get_user_db_from_app(app)
    rows = con.execute("SELECT * FROM planning ORDER BY date ASC, id ASC").fetchall()
    con.close()
    return [dict(r) for r in rows]

def planning_delete(app, date_str, line_text):
    con = get_user_db_from_app(app)
    con.execute("DELETE FROM planning WHERE date=? AND line=?", (date_str, line_text))
    con.commit(); con.close()


# ════════════════════════════════════════════════════════════════════════════
#  CYCLE
# ════════════════════════════════════════════════════════════════════════════

def cycle_get_all(app):
    con = get_user_db_from_app(app)
    rows = con.execute("SELECT * FROM cycle ORDER BY id ASC").fetchall()
    con.close()
    return [dict(r) for r in rows]

def cycle_get_last(app):
    con = get_user_db_from_app(app)
    row = con.execute("SELECT * FROM cycle ORDER BY id DESC LIMIT 1").fetchone()
    con.close()
    return dict(row) if row else None

def cycle_insert(app, debut, fin_estimee, longueur_sem, produits_doses, note=""):
    con = get_user_db_from_app(app)
    con.execute("""
        INSERT INTO cycle (debut, fin_estimee, longueur_sem, produits_doses, note)
        VALUES (?,?,?,?,?)
    """, (debut, fin_estimee, str(longueur_sem), produits_doses, note))
    con.commit(); con.close()


# ════════════════════════════════════════════════════════════════════════════
#  TRAINING HISTORY
# ════════════════════════════════════════════════════════════════════════════

def history_get_all(app):
    con = get_user_db_from_app(app)
    rows = con.execute("SELECT * FROM training_history ORDER BY id ASC").fetchall()
    con.close()
    result = []
    for r in rows:
        d = dict(r)
        try: d["exercises"] = json.loads(d["exercises"])
        except Exception: d["exercises"] = []
        result.append(d)
    return result

def history_insert(app, entry: dict):
    con = get_user_db_from_app(app)
    con.execute("""
        INSERT INTO training_history (date, type, duration, notes, exercises, planned_for)
        VALUES (?,?,?,?,?,?)
    """, (
        entry.get("date",""),
        entry.get("type",""),
        entry.get("duration",""),
        entry.get("notes",""),
        json.dumps(entry.get("exercises",[]), ensure_ascii=False),
        entry.get("planned_for",""),
    ))
    con.commit(); con.close()

def history_save_all(app, entries: list):
    """Remplace toute la table training_history (compatibilité avec l'ancien _save_hist)."""
    con = get_user_db_from_app(app)
    con.execute("DELETE FROM training_history")
    for entry in entries:
        con.execute("""
            INSERT INTO training_history (date, type, duration, notes, exercises, planned_for)
            VALUES (?,?,?,?,?,?)
        """, (
            entry.get("date",""),
            entry.get("type",""),
            entry.get("duration",""),
            entry.get("notes",""),
            json.dumps(entry.get("exercises",[]), ensure_ascii=False),
            entry.get("planned_for",""),
        ))
    con.commit(); con.close()


# ════════════════════════════════════════════════════════════════════════════
#  PROGRAMMES
# ════════════════════════════════════════════════════════════════════════════

def programmes_get_all(app):
    con = get_user_db_from_app(app)
    rows = con.execute("SELECT * FROM programmes ORDER BY id ASC").fetchall()
    con.close()
    result = []
    for r in rows:
        d = dict(r)
        try: d["lines"] = json.loads(d["lines"])
        except Exception: d["lines"] = []
        result.append(d)
    return result

def programmes_insert(app, title, created, lines):
    con = get_user_db_from_app(app)
    con.execute("""
        INSERT INTO programmes (title, created, lines) VALUES (?,?,?)
    """, (title, created, json.dumps(lines, ensure_ascii=False)))
    con.commit(); con.close()


# ════════════════════════════════════════════════════════════════════════════
#  SETTINGS  (clé/valeur — ex : cycle_qualified)
# ════════════════════════════════════════════════════════════════════════════

def settings_get(app, key, default=""):
    try:
        con = get_user_db_from_app(app)
        row = con.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        con.close()
        return row["value"] if row else default
    except Exception:
        return default

def settings_set(app, key, value):
    con = get_user_db_from_app(app)
    con.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?,?)", (key, str(value)))
    con.commit(); con.close()

def is_cycle_qualified(app):
    return settings_get(app, "cycle_qualified", "") != ""

def set_cycle_qualified(app):
    import datetime
    settings_set(app, "cycle_qualified", datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
