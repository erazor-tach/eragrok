# data/db.py — THRESHOLD · Couche SQLite avec pool de connexions
# ─────────────────────────────────────────────────────────────────────────────
# AMÉLIORATION #1 : Pool de connexions par thread + contextmanager
#
# Avant : chaque fonction faisait sqlite3.connect() / con.close() → ~25 opens/s
# Après : une connexion réutilisée par (thread × base), fermée en fin de bloc
#
# API publique inchangée — aucune modification requise dans les autres modules.
#
# Architecture :
#   _ConnectionPool          → dict {db_path: connexion} par threading.local()
#   db_connection(path)      → contextmanager — ouvre ou réutilise, commit auto
#   get_global_db()          → garde sa signature (compatibilité profil.py etc.)
#   get_user_db(folder)      → garde sa signature
#   get_user_db_from_app(app)→ garde sa signature
#   Toutes les fonctions CRUD utilisent db_connection() en interne
# ─────────────────────────────────────────────────────────────────────────────
from __future__ import annotations

import json
import os
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from data.logger import log_exc

# ════════════════════════════════════════════════════════════════════════════
#  POOL DE CONNEXIONS  (une connexion par thread × chemin de base)
# ════════════════════════════════════════════════════════════════════════════

_local = threading.local()   # stockage thread-local


def _get_pool() -> dict[str, sqlite3.Connection]:
    """Retourne (ou crée) le pool de connexions du thread courant."""
    if not hasattr(_local, "pool"):
        _local.pool = {}
    return _local.pool


def _get_migrations_done() -> dict[str, set]:
    """Retourne le dict {db_path: set(versions_appliquées)} du thread courant.

    Stocké dans threading.local pour éviter les attributs dynamiques sur
    sqlite3.Connection (interdits en Python 3.14+).
    """
    if not hasattr(_local, "migrations_done"):
        _local.migrations_done = {}
    return _local.migrations_done


def _open_connection(db_path: str) -> sqlite3.Connection:
    """Ouvre une nouvelle connexion avec les réglages standard."""
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db_path, check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA foreign_keys=ON")
    return con


@contextmanager
def db_connection(db_path: str) -> Generator[sqlite3.Connection, None, None]:
    """Context-manager qui fournit une connexion réutilisée par thread.

    Usage :
        with db_connection(path) as con:
            con.execute(...)
            # commit automatique en sortie de bloc si pas d'exception
            # rollback automatique en cas d'exception

    La connexion N'EST PAS fermée — elle reste dans le pool du thread
    pour la prochaine utilisation. Appeler close_all_connections() en fin
    de session si nécessaire (ex : tests).
    """
    pool = _get_pool()
    con = pool.get(db_path)
    if con is None:
        con = _open_connection(db_path)
        pool[db_path] = con

    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise


def close_all_connections() -> None:
    """Ferme toutes les connexions du thread courant (utile pour les tests)."""
    pool = _get_pool()
    for con in pool.values():
        try:
            con.close()
        except Exception:
            pass
    pool.clear()


# ════════════════════════════════════════════════════════════════════════════
#  RÉSOLUTION DU DOSSIER USERS
# ════════════════════════════════════════════════════════════════════════════

def _users_dir() -> str:
    from data.utils import USERS_DIR
    return USERS_DIR


# ════════════════════════════════════════════════════════════════════════════
#  CHEMINS DES BASES
# ════════════════════════════════════════════════════════════════════════════

def global_db_path() -> str:
    return os.path.join(_users_dir(), "eragrok.db")

def user_db_path(folder: str) -> str:
    return os.path.join(_users_dir(), folder, f"{folder}.db")


# ════════════════════════════════════════════════════════════════════════════
#  INITIALISATION DES SCHÉMAS
#  Les schémas sont désormais gérés par data/migrate_schema.py +
#  data/migrations/global_NNN_*.sql et user_NNN_*.sql.
#  Ces fonctions sont conservées uniquement pour compatibilité éventuelle.
# ════════════════════════════════════════════════════════════════════════════

def _init_global_schema(con: sqlite3.Connection) -> None:
    """Conservé pour compatibilité — les migrations prennent le relai."""
    from data.migrate_schema import apply_migrations
    apply_migrations(con, "global")


def _init_user_schema(con: sqlite3.Connection) -> None:
    """Conservé pour compatibilité — les migrations prennent le relai."""
    from data.migrate_schema import apply_migrations
    apply_migrations(con, "user")


# ════════════════════════════════════════════════════════════════════════════
#  ACCESSEURS PUBLICS (API compatible avec l'existant)
# ════════════════════════════════════════════════════════════════════════════

def get_global_db() -> sqlite3.Connection:
    """Retourne la connexion poolée à la base globale (migrations appliquées)."""
    path = global_db_path()
    pool = _get_pool()
    if path not in pool:
        pool[path] = _open_connection(path)
    con = pool[path]
    from data.migrate_schema import apply_migrations, _load_migration_files
    done = _get_migrations_done()
    known = done.get(path, set())
    available = {v for v, _, _ in _load_migration_files("global")}
    if not available.issubset(known):
        apply_migrations(con, "global")
        done[path] = available
    return con


def get_user_db(folder: str) -> sqlite3.Connection:
    """Retourne la connexion poolée à la base utilisateur (migrations appliquées)."""
    path = user_db_path(folder)
    pool = _get_pool()
    if path not in pool:
        pool[path] = _open_connection(path)
    con = pool[path]
    from data.migrate_schema import apply_migrations, _load_migration_files
    done = _get_migrations_done()
    known = done.get(path, set())
    available = {v for v, _, _ in _load_migration_files("user")}
    if not available.issubset(known):
        apply_migrations(con, "user")
        done[path] = available
    return con


def get_user_db_from_app(app) -> sqlite3.Connection:
    """Résout le folder depuis AppState, dict ou objet, et retourne la connexion poolée."""
    if isinstance(app, dict):
        folder = app.get("current_user") or "default"
    else:
        # AppState expose .folder ; objets legacy exposent .current_user
        folder = getattr(app, "folder", None) or getattr(app, "current_user", None) or "default"
    return get_user_db(folder)


def _user_path_from_app(app) -> str:
    """Retourne le chemin de la base utilisateur sans ouvrir de connexion."""
    if isinstance(app, dict):
        folder = app.get("current_user") or "default"
    else:
        folder = getattr(app, "folder", None) or getattr(app, "current_user", None) or "default"
    return user_db_path(folder)


# ════════════════════════════════════════════════════════════════════════════
#  NUTRITION
# ════════════════════════════════════════════════════════════════════════════

def nutrition_insert(app, date, poids, age, calories, proteines, glucides, lipides, note=""):
    with db_connection(_user_path_from_app(app)) as con:
        con.execute(
            "INSERT INTO nutrition (date,poids,age,calories,proteines,glucides,lipides,note) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (date, poids, age, str(calories), str(proteines), str(glucides), str(lipides), note),
        )


def nutrition_get_all(app) -> list[dict]:
    with db_connection(_user_path_from_app(app)) as con:
        rows = con.execute("SELECT * FROM nutrition ORDER BY date ASC").fetchall()
    return [dict(r) for r in rows]


def nutrition_get_last_n(app, n: int = 1) -> list[dict]:
    with db_connection(_user_path_from_app(app)) as con:
        rows = con.execute(
            "SELECT * FROM nutrition ORDER BY date DESC LIMIT ?", (n,)
        ).fetchall()
    return [dict(r) for r in rows]


def nutrition_update(app, row_id, date, poids, age, calories, proteines, glucides, lipides, note):
    with db_connection(_user_path_from_app(app)) as con:
        con.execute(
            "UPDATE nutrition SET date=?,poids=?,age=?,calories=?,proteines=?,"
            "glucides=?,lipides=?,note=? WHERE id=?",
            (date, poids, age, str(calories), str(proteines), str(glucides), str(lipides), note, row_id),
        )


def nutrition_delete_by_date(app, date_str: str):
    with db_connection(_user_path_from_app(app)) as con:
        con.execute("DELETE FROM nutrition WHERE date=?", (date_str,))


def nutrition_delete_all(app):
    with db_connection(_user_path_from_app(app)) as con:
        con.execute("DELETE FROM nutrition")


def nutrition_delete_by_id(app, row_id):
    with db_connection(_user_path_from_app(app)) as con:
        con.execute("DELETE FROM nutrition WHERE id=?", (row_id,))


# ════════════════════════════════════════════════════════════════════════════
#  PLANNING
# ════════════════════════════════════════════════════════════════════════════

def planning_insert(app, date, groupes="", programme="", types="", note="", line=""):
    with db_connection(_user_path_from_app(app)) as con:
        con.execute(
            "INSERT INTO planning (date,groupes,programme,types,note,line) VALUES (?,?,?,?,?,?)",
            (date, groupes, programme, types, note, line),
        )


def planning_get_all(app) -> list[dict]:
    with db_connection(_user_path_from_app(app)) as con:
        rows = con.execute(
            "SELECT * FROM planning ORDER BY date ASC, id ASC"
        ).fetchall()
    return [dict(r) for r in rows]


def planning_delete(app, date_str: str, line_text: str):
    with db_connection(_user_path_from_app(app)) as con:
        con.execute("DELETE FROM planning WHERE date=? AND line=?", (date_str, line_text))


# ════════════════════════════════════════════════════════════════════════════
#  CYCLE
# ════════════════════════════════════════════════════════════════════════════

def cycle_get_all(app) -> list[dict]:
    with db_connection(_user_path_from_app(app)) as con:
        rows = con.execute("SELECT * FROM cycle ORDER BY id ASC").fetchall()
    return [dict(r) for r in rows]


def cycle_get_last(app) -> dict | None:
    with db_connection(_user_path_from_app(app)) as con:
        row = con.execute("SELECT * FROM cycle ORDER BY id DESC LIMIT 1").fetchone()
    return dict(row) if row else None


def cycle_get_active(app) -> dict | None:
    """Retourne le cycle actif ou le plus proche d'aujourd'hui."""
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
    best, best_delta = None, None

    for r in rows:
        d_debut = _parse(r.get("debut", ""))
        if not d_debut:
            continue
        try:
            n_weeks = int(r.get("longueur_sem", 12))
        except Exception:
            n_weeks = 12
        d_fin_cycle = _parse(r.get("fin_estimee", "")) or (
            d_debut + _dt.timedelta(weeks=n_weeks)
        )
        end_mode = r.get("end_mode", "PCT")
        d_fin_active = (
            d_fin_cycle
            if end_mode in ("TRT", "Cruise")
            else d_fin_cycle + _dt.timedelta(weeks=6)
        )
        if d_debut <= today <= d_fin_active:
            return r
        delta = abs((d_debut - today).days)
        if best_delta is None or delta < best_delta:
            best_delta = delta
            best = r

    return best


def cycle_insert(app, debut, fin_estimee, longueur_sem, produits_doses, note="", end_mode="PCT"):
    with db_connection(_user_path_from_app(app)) as con:
        con.execute(
            "INSERT INTO cycle (debut,fin_estimee,longueur_sem,produits_doses,note,end_mode,days_2x_config) "
            "VALUES (?,?,?,?,?,?,?)",
            (debut, fin_estimee, str(longueur_sem), produits_doses, note, end_mode, "{}"),
        )

# ════════════════════════════════════════════════════════════════════════════
#  TRAINING HISTORY
# ════════════════════════════════════════════════════════════════════════════

def _decode_history_row(d: dict) -> dict:
    try:
        d["exercises"] = json.loads(d["exercises"])
    except Exception:
        d["exercises"] = []
    return d


def history_get_all(app) -> list[dict]:
    with db_connection(_user_path_from_app(app)) as con:
        rows = con.execute("SELECT * FROM training_history ORDER BY id ASC").fetchall()
    return [_decode_history_row(dict(r)) for r in rows]


def history_insert(app, entry: dict):
    with db_connection(_user_path_from_app(app)) as con:
        con.execute(
            "INSERT INTO training_history (date,type,duration,notes,exercises,planned_for) "
            "VALUES (?,?,?,?,?,?)",
            (
                entry.get("date", ""),
                entry.get("type", ""),
                entry.get("duration", ""),
                entry.get("notes", ""),
                json.dumps(entry.get("exercises", []), ensure_ascii=False),
                entry.get("planned_for", ""),
            ),
        )


def history_save_all(app, entries: list):
    """Remplace toute la table training_history (compatibilité avec l'ancien _save_hist)."""
    with db_connection(_user_path_from_app(app)) as con:
        con.execute("DELETE FROM training_history")
        for entry in entries:
            con.execute(
                "INSERT INTO training_history (date,type,duration,notes,exercises,planned_for) "
                "VALUES (?,?,?,?,?,?)",
                (
                    entry.get("date", ""),
                    entry.get("type", ""),
                    entry.get("duration", ""),
                    entry.get("notes", ""),
                    json.dumps(entry.get("exercises", []), ensure_ascii=False),
                    entry.get("planned_for", ""),
                ),
            )


# ════════════════════════════════════════════════════════════════════════════
#  PROGRAMMES
# ════════════════════════════════════════════════════════════════════════════

def programmes_get_all(app) -> list[dict]:
    with db_connection(_user_path_from_app(app)) as con:
        rows = con.execute("SELECT * FROM programmes ORDER BY id ASC").fetchall()
    result = []
    for r in rows:
        d = dict(r)
        try:
            d["lines"] = json.loads(d["lines"])
        except Exception:
            d["lines"] = []
        result.append(d)
    return result


def programmes_insert(app, title: str, created: str, lines: list):
    with db_connection(_user_path_from_app(app)) as con:
        con.execute(
            "INSERT INTO programmes (title,created,lines) VALUES (?,?,?)",
            (title, created, json.dumps(lines, ensure_ascii=False)),
        )


# ════════════════════════════════════════════════════════════════════════════
#  SETTINGS
# ════════════════════════════════════════════════════════════════════════════

def settings_get(app, key: str, default: str = "") -> str:
    try:
        with db_connection(_user_path_from_app(app)) as con:
            row = con.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row["value"] if row else default
    except Exception:
        log_exc(f"settings_get({key})")
        return default


def settings_set(app, key: str, value):
    with db_connection(_user_path_from_app(app)) as con:
        con.execute(
            "INSERT OR REPLACE INTO settings (key,value) VALUES (?,?)", (key, str(value))
        )


def is_cycle_qualified(app) -> bool:
    return settings_get(app, "cycle_qualified", "") != ""


def set_cycle_qualified(app):
    import datetime
    settings_set(app, "cycle_qualified", datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))


# ════════════════════════════════════════════════════════════════════════════
#  FOOD PRICES
# ════════════════════════════════════════════════════════════════════════════

def prices_get_all(app) -> dict:
    try:
        with db_connection(_user_path_from_app(app)) as con:
            rows = con.execute(
                "SELECT food,prix_kg,unite,source,last_update FROM food_prices"
            ).fetchall()
        return {r["food"]: dict(r) for r in rows}
    except Exception:
        log_exc("prices_get_all")
        return {}


def prices_upsert(app, food: str, prix_kg: float, unite: str = "kg",
                  source: str = "default", last_update: str = "") -> None:
    import datetime as _dt
    if not last_update:
        last_update = _dt.date.today().isoformat()
    try:
        with db_connection(_user_path_from_app(app)) as con:
            con.execute(
                "INSERT INTO food_prices (food,prix_kg,unite,source,last_update) "
                "VALUES (?,?,?,?,?) "
                "ON CONFLICT(food) DO UPDATE SET "
                "prix_kg=excluded.prix_kg, unite=excluded.unite, "
                "source=excluded.source, last_update=excluded.last_update",
                (food, prix_kg, unite, source, last_update),
            )
    except Exception:
        log_exc(f"prices_upsert({food})")


def prices_last_update(app) -> str:
    try:
        with db_connection(_user_path_from_app(app)) as con:
            row = con.execute("SELECT MAX(last_update) AS lu FROM food_prices").fetchone()
        return row["lu"] or ""
    except Exception:
        return ""


def prices_count(app) -> int:
    try:
        with db_connection(_user_path_from_app(app)) as con:
            r = con.execute("SELECT COUNT(*) AS n FROM food_prices").fetchone()
        return r["n"]
    except Exception:
        return 0


# ════════════════════════════════════════════════════════════════════════════
#  MEAL PLANS
# ════════════════════════════════════════════════════════════════════════════

def meal_plan_insert(app, date: str, mode: str, n_meals: int,
                     cal: float, prot: float, gluc: float, lip: float,
                     adj_label: str, plan_json: str,
                     accepted: bool = False, budget_w: float = 0) -> int | None:
    try:
        with db_connection(_user_path_from_app(app)) as con:
            cur = con.execute(
                "INSERT INTO meal_plans "
                "(date,mode,n_meals,cal_target,prot_target,gluc_target,"
                "lip_target,adj_label,plan_json,accepted,budget_w) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (date, mode, n_meals, cal, prot, gluc, lip,
                 adj_label, plan_json, 1 if accepted else 0, budget_w),
            )
        return cur.lastrowid
    except Exception:
        log_exc("meal_plan_insert")
        return None


def meal_plan_accept(app, plan_id: int):
    try:
        with db_connection(_user_path_from_app(app)) as con:
            con.execute("UPDATE meal_plans SET accepted=1 WHERE id=?", (plan_id,))
    except Exception:
        log_exc("meal_plan_accept")


def meal_plan_get_last(app, accepted_only: bool = False) -> dict | None:
    try:
        clause = "WHERE accepted=1" if accepted_only else ""
        with db_connection(_user_path_from_app(app)) as con:
            row = con.execute(
                f"SELECT * FROM meal_plans {clause} ORDER BY id DESC LIMIT 1"
            ).fetchone()
        if not row:
            return None
        d = dict(row)
        d["plan_json"] = json.loads(d["plan_json"])
        d["accepted"] = bool(d["accepted"])
        return d
    except Exception:
        log_exc("meal_plan_get_last")
        return None


def meal_plan_to_dashboard(db_plan: dict) -> dict | None:
    """Normalise un enregistrement DB en dict compatible dashboard/app_state.

    plan_json peut contenir :
    - Mode jour  : [{nom, items, tot_cal, ...}, ...]  → liste de repas directe
    - Mode multi : [{date, plan:[repas...]}, ...]      → liste de jours

    _build_plan_view (dashboard) attend toujours une liste de repas.
    Pour le mode multi on prend les repas du premier jour.
    """
    if not db_plan:
        return None
    raw = db_plan.get("plan_json", [])
    if not raw:
        return None
    if isinstance(raw, list) and raw and isinstance(raw[0], dict) and "plan" in raw[0]:
        meals = raw[0].get("plan", [])
    else:
        meals = raw
    if not meals:
        return None
    return {
        "plan":  meals,
        "cal":   db_plan.get("cal_target", 0),
        "prot":  db_plan.get("prot_target", 0),
        "gluc":  db_plan.get("gluc_target", 0),
        "lip":   db_plan.get("lip_target", 0),
    }


def meal_plan_get_all(app, limit: int = 30) -> list:
    try:
        with db_connection(_user_path_from_app(app)) as con:
            rows = con.execute(
                "SELECT * FROM meal_plans ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            try:
                d["plan_json"] = json.loads(d["plan_json"])
            except Exception:
                d["plan_json"] = []
            d["accepted"] = bool(d["accepted"])
            result.append(d)
        return result
    except Exception:
        return []


def meal_plan_delete(app, plan_id: int):
    try:
        with db_connection(_user_path_from_app(app)) as con:
            con.execute("DELETE FROM meal_plans WHERE id=?", (plan_id,))
    except Exception:
        pass


# ════════════════════════════════════════════════════════════════════════════
#  CUSTOM PRODUCTS  (produits personnalisés — anciennement custom_products.json)
# ════════════════════════════════════════════════════════════════════════════

def custom_products_get_all(app) -> list[dict]:
    """Retourne tous les produits personnalisés de l'utilisateur."""
    try:
        # get_user_db garantit que la migration 003 est appliquée
        if isinstance(app, dict):
            folder = app.get("current_user") or "default"
        else:
            folder = getattr(app, "folder", None) or getattr(app, "current_user", None) or "default"
        con = get_user_db(folder)
        rows = con.execute(
            "SELECT * FROM custom_products ORDER BY categorie_id ASC, nom ASC"
        ).fetchall()
        con.commit()
        return [dict(r) for r in rows]
    except Exception:
        log_exc("custom_products_get_all")
        return []


def custom_products_upsert(app, nom: str, categorie_id: int,
                           dose: str = "", halflife: str = "",
                           usage: str = "", notes: str = "") -> bool:
    """Insère ou met à jour un produit personnalisé. Retourne True si succès."""
    try:
        if isinstance(app, dict):
            folder = app.get("current_user") or "default"
        else:
            folder = getattr(app, "folder", None) or getattr(app, "current_user", None) or "default"
        con = get_user_db(folder)
        con.execute("""
            INSERT INTO custom_products (nom, categorie_id, dose, halflife, usage, notes)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(nom) DO UPDATE SET
                categorie_id = excluded.categorie_id,
                dose         = excluded.dose,
                halflife     = excluded.halflife,
                usage        = excluded.usage,
                notes        = excluded.notes
        """, (nom, categorie_id, dose, halflife, usage, notes))
        con.commit()
        return True
    except Exception:
        log_exc(f"custom_products_upsert({nom})")
        return False


def custom_products_delete(app, nom: str) -> bool:
    """Supprime un produit personnalisé par nom. Retourne True si succès."""
    try:
        if isinstance(app, dict):
            folder = app.get("current_user") or "default"
        else:
            folder = getattr(app, "folder", None) or getattr(app, "current_user", None) or "default"
        con = get_user_db(folder)
        con.execute("DELETE FROM custom_products WHERE nom=?", (nom,))
        con.commit()
        return True
    except Exception:
        log_exc(f"custom_products_delete({nom})")
        return False


def custom_products_get_one(app, nom: str) -> dict | None:
    """Retourne un produit personnalisé par nom, ou None."""
    try:
        if isinstance(app, dict):
            folder = app.get("current_user") or "default"
        else:
            folder = getattr(app, "folder", None) or getattr(app, "current_user", None) or "default"
        con = get_user_db(folder)
        row = con.execute(
            "SELECT * FROM custom_products WHERE nom=?", (nom,)
        ).fetchone()
        con.commit()
        return dict(row) if row else None
    except Exception:
        log_exc(f"custom_products_get_one({nom})")
        return None


def custom_products_migrate_from_json(app, json_path: str) -> int:
    """Migre un fichier custom_products.json existant vers la DB.

    Retourne le nombre de produits migrés.
    Supprime le fichier JSON après migration réussie.
    """
    import json as _json
    from pathlib import Path
    path = Path(json_path)
    if not path.exists():
        return 0
    try:
        prods = _json.loads(path.read_text(encoding="utf-8"))
        count = 0
        for p in prods:
            nom = p.get("nom", "").strip()
            if not nom:
                continue
            ok = custom_products_upsert(
                app,
                nom          = nom,
                categorie_id = int(p.get("categorie_id", 0)),
                dose         = p.get("dose", ""),
                halflife     = p.get("halflife", ""),
                usage        = p.get("usage", ""),
                notes        = p.get("notes", ""),
            )
            if ok:
                count += 1
        if count > 0:
            path.rename(str(path) + ".migrated")
            log_exc  # ne pas utiliser ici — pas d'exception
            from data.logger import log
            log.info("custom_products : %d produits migrés depuis %s", count, json_path)
        return count
    except Exception:
        log_exc(f"custom_products_migrate_from_json({json_path})")
        return 0


# ════════════════════════════════════════════════════════════════════════════
#  CUSTOM FOOD  (aliments personnalisés — catalogue nutrition)
# ════════════════════════════════════════════════════════════════════════════

def custom_food_get_all(app) -> list[dict]:
    """Retourne tous les aliments personnalisés triés par catégorie puis nom."""
    try:
        with db_connection(_user_path_from_app(app)) as con:
            rows = con.execute(
                "SELECT * FROM custom_food ORDER BY categorie ASC, nom ASC"
            ).fetchall()
        return [dict(r) for r in rows]
    except Exception:
        log_exc("custom_food_get_all")
        return []

def custom_food_upsert(app, nom: str, categorie: str = "Divers",
                       kcal: float = 0, proteines: float = 0,
                       glucides: float = 0, lipides: float = 0,
                       fibres: float = 0, unite: str = "g",
                       portion_ref: float = 100, notes: str = "") -> bool:
    try:
        with db_connection(_user_path_from_app(app)) as con:
            con.execute("""
                INSERT INTO custom_food
                    (nom, categorie, kcal, proteines, glucides, lipides,
                     fibres, unite, portion_ref, notes)
                VALUES (?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(nom) DO UPDATE SET
                    categorie=excluded.categorie, kcal=excluded.kcal,
                    proteines=excluded.proteines, glucides=excluded.glucides,
                    lipides=excluded.lipides, fibres=excluded.fibres,
                    unite=excluded.unite, portion_ref=excluded.portion_ref,
                    notes=excluded.notes
            """, (nom, categorie, kcal, proteines, glucides, lipides,
                  fibres, unite, portion_ref, notes))
        return True
    except Exception:
        log_exc(f"custom_food_upsert({nom})")
        return False

def custom_food_delete(app, nom: str) -> bool:
    try:
        with db_connection(_user_path_from_app(app)) as con:
            con.execute("DELETE FROM custom_food WHERE nom=?", (nom,))
        return True
    except Exception:
        log_exc(f"custom_food_delete({nom})")
        return False

def custom_food_get_one(app, nom: str) -> dict | None:
    try:
        with db_connection(_user_path_from_app(app)) as con:
            row = con.execute(
                "SELECT * FROM custom_food WHERE nom=?", (nom,)
            ).fetchone()
        return dict(row) if row else None
    except Exception:
        log_exc(f"custom_food_get_one({nom})")
        return None
