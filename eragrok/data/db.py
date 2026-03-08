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
            date_naissance TEXT   DEFAULT '',
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
            date_naissance TEXT DEFAULT '',
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
        CREATE TABLE IF NOT EXISTS food_prices (
            food        TEXT PRIMARY KEY,
            prix_kg     REAL  DEFAULT 0,   -- prix moyen €/kg (ou €/L, €/unité)
            unite       TEXT  DEFAULT 'kg', -- kg | L | unite
            source      TEXT  DEFAULT 'default',  -- default | openfoodfacts | manual
            last_update TEXT  DEFAULT ''   -- ISO date YYYY-MM-DD
        );
        CREATE TABLE IF NOT EXISTS meal_plans (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            date        TEXT    NOT NULL,       -- date de création YYYY-MM-DD
            mode        TEXT    DEFAULT 'jour', -- jour | semaine | mois
            n_meals     INTEGER DEFAULT 4,
            cal_target  REAL    DEFAULT 0,
            prot_target REAL    DEFAULT 0,
            gluc_target REAL    DEFAULT 0,
            lip_target  REAL    DEFAULT 0,
            adj_label   TEXT    DEFAULT '',
            plan_json   TEXT    DEFAULT '[]',   -- JSON complet du plan (meals ou days)
            accepted    INTEGER DEFAULT 0,      -- 0=draft, 1=accepté
            budget_w    REAL    DEFAULT 0       -- budget semaine € (0=pas de budget)
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

def nutrition_delete_all(app):
    """Supprime toutes les entrées nutrition de l'utilisateur courant."""
    con = get_user_db_from_app(app)
    con.execute("DELETE FROM nutrition")
    con.commit()
    con.close()


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

def cycle_get_active(app):
    """Retourne le cycle le plus pertinent :
    1. Cycle en cours (aujourd'hui entre debut et fin_estimee)
    2. Sinon le cycle dont le debut est le plus proche d'aujourd'hui.
    """
    import datetime as _dt
    rows = cycle_get_all(app)
    if not rows:
        return None

    def _parse(s):
        for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
            try:
                return _dt.datetime.strptime(str(s or "").strip(), fmt).date()
            except Exception:
                pass
        return None

    today = _dt.date.today()
    best = None
    best_delta = None

    for r in rows:
        d_debut = _parse(r.get("debut", ""))
        if not d_debut:
            continue
        try:
            n_weeks = int(r.get("longueur_sem", 12))
        except Exception:
            n_weeks = 12
        d_fin = _parse(r.get("fin_estimee", "")) or (
            d_debut + _dt.timedelta(weeks=n_weeks + 6))

        # Priorité absolue : cycle en cours
        if d_debut <= today <= d_fin:
            return r

        # Sinon : distance minimale à aujourd'hui (abs sur debut)
        delta = abs((d_debut - today).days)
        if best_delta is None or delta < best_delta:
            best_delta = delta
            best = r

    return best

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


# ── food_prices ───────────────────────────────────────────────────────────────

def prices_get_all(app) -> dict:
    """Retourne {food: {prix_kg, unite, source, last_update}}."""
    try:
        con = get_user_db_from_app(app)
        rows = con.execute("SELECT food, prix_kg, unite, source, last_update FROM food_prices").fetchall()
        return {r["food"]: dict(r) for r in rows}
    except Exception:
        return {}

def prices_upsert(app, food: str, prix_kg: float, unite: str = "kg",
                  source: str = "default", last_update: str = "") -> None:
    """Insère ou met à jour le prix d'un aliment."""
    import datetime as _dt
    if not last_update:
        last_update = _dt.date.today().isoformat()
    try:
        con = get_user_db_from_app(app)
        con.execute("""
            INSERT INTO food_prices (food, prix_kg, unite, source, last_update)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(food) DO UPDATE SET
                prix_kg=excluded.prix_kg,
                unite=excluded.unite,
                source=excluded.source,
                last_update=excluded.last_update
        """, (food, prix_kg, unite, source, last_update))
        con.commit()
    except Exception:
        pass

def prices_last_update(app) -> str:
    """Retourne la date de dernière mise à jour (max) ou '' si table vide."""
    try:
        con  = get_user_db_from_app(app)
        row  = con.execute("SELECT MAX(last_update) as lu FROM food_prices").fetchone()
        return row["lu"] or ""
    except Exception:
        return ""

def prices_count(app) -> int:
    """Nombre d'entrées dans food_prices."""
    try:
        con = get_user_db_from_app(app)
        r   = con.execute("SELECT COUNT(*) as n FROM food_prices").fetchone()
        return r["n"]
    except Exception:
        return 0


# ════════════════════════════════════════════════════════════════════════════
#  MEAL PLANS  (historique des plans alimentaires générés)
# ════════════════════════════════════════════════════════════════════════════

def meal_plan_insert(app, date: str, mode: str, n_meals: int,
                     cal: float, prot: float, gluc: float, lip: float,
                     adj_label: str, plan_json: str,
                     accepted: bool = False, budget_w: float = 0) -> int | None:
    """Insère un plan et retourne son id."""
    try:
        con = get_user_db_from_app(app)
        cur = con.execute("""
            INSERT INTO meal_plans
                (date, mode, n_meals, cal_target, prot_target, gluc_target,
                 lip_target, adj_label, plan_json, accepted, budget_w)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, (date, mode, n_meals, cal, prot, gluc, lip,
              adj_label, plan_json, 1 if accepted else 0, budget_w))
        con.commit()
        row_id = cur.lastrowid
        con.close()
        return row_id
    except Exception:
        return None

def meal_plan_accept(app, plan_id: int):
    """Marque un plan comme accepté."""
    try:
        con = get_user_db_from_app(app)
        con.execute("UPDATE meal_plans SET accepted=1 WHERE id=?", (plan_id,))
        con.commit(); con.close()
    except Exception:
        pass

def meal_plan_get_last(app, accepted_only: bool = False) -> dict | None:
    """Retourne le dernier plan (ou le dernier accepté)."""
    try:
        con = get_user_db_from_app(app)
        clause = "WHERE accepted=1" if accepted_only else ""
        row = con.execute(
            f"SELECT * FROM meal_plans {clause} ORDER BY id DESC LIMIT 1"
        ).fetchone()
        con.close()
        if not row: return None
        d = dict(row)
        d["plan_json"] = json.loads(d["plan_json"])
        d["accepted"]  = bool(d["accepted"])
        return d
    except Exception:
        return None

def meal_plan_get_all(app, limit: int = 30) -> list:
    """Retourne les N derniers plans (les plus récents en premier)."""
    try:
        con = get_user_db_from_app(app)
        rows = con.execute(
            "SELECT * FROM meal_plans ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        con.close()
        result = []
        for r in rows:
            d = dict(r)
            try: d["plan_json"] = json.loads(d["plan_json"])
            except: d["plan_json"] = []
            d["accepted"] = bool(d["accepted"])
            result.append(d)
        return result
    except Exception:
        return []

def meal_plan_delete(app, plan_id: int):
    """Supprime un plan par id."""
    try:
        con = get_user_db_from_app(app)
        con.execute("DELETE FROM meal_plans WHERE id=?", (plan_id,))
        con.commit(); con.close()
    except Exception:
        pass
