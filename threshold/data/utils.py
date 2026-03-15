# data/utils.py — ERAGROK
# Gestion utilisateurs (SQLite) + calculs nutrition/IMC
# API publique identique à l'ancienne version CSV pour zéro cassure dans l'app.

import os
import sys
import shutil
from functools import lru_cache
from pathlib import Path

from data.logger import log_exc

# ── Résolution du dossier racine ──────────────────────────────────────────────
# En mode .exe PyInstaller :  sys.frozen=True, sys.executable = chemin du .exe
#   → on écrit TOUJOURS à côté du .exe (lecture/écriture garanti)
#   → sys._MEIPASS = dossier temporaire extrait (lecture seule, supprimé à la fin)
# En mode script normal :     on remonte 2 niveaux depuis utils.py
if getattr(sys, "frozen", False):
    # Dossier contenant le .exe → données persistantes ici
    _DATA_ROOT = Path(sys.executable).resolve().parent
else:
    # Développement : racine du projet (eragrok/)
    _DATA_ROOT = Path(__file__).resolve().parent.parent

_ROOT     = _DATA_ROOT
USERS_DIR = str(_DATA_ROOT / "users")
USERS_FILE = str(_DATA_ROOT / "users" / "eragrok_users.csv")  # conservé pour compat

ADJUSTMENTS = {
    "Déficit léger (-10 à -15%)":      -0.125,
    "Déficit modéré (-15 à -25%)":     -0.20,
    "Maintien (0%)":                    0.0,
    "Surplus léger (lean) (+5 à +10%)": 0.075,
    "Surplus standard (+10 à +15%)":    0.125,
    "Surplus agressif (+15 à +20%)":    0.175,
}

IMC_TABLE_5 = [
    (0.0,  18.5, "Maigreur"),
    (18.5, 25.0, "Normal"),
    (25.0, 30.0, "Surpoids"),
    (30.0, 40.0, "Obésité modérée"),
    (40.0, 999., "Obésité sévère"),
]

def to_folder_name(display_name: str) -> str:
    return (display_name or "").strip().lower().replace(" ", "_")

def get_current_user_folder(app) -> str:
    return getattr(app, "current_user", "") or ""

def get_user_dir(app) -> str:
    folder = get_current_user_folder(app)
    return os.path.join(USERS_DIR, folder) if folder else ""

def ensure_users_dir():
    Path(USERS_DIR).mkdir(parents=True, exist_ok=True)
    from data.db import get_global_db
    get_global_db()   # initialise le schéma si besoin — NE PAS fermer la connexion poolée
    csv_path = Path(USERS_FILE)
    if csv_path.exists() and not Path(USERS_FILE + ".migrated").exists():
        try:
            from data.migrate import run_migration
            run_migration(USERS_DIR, verbose=False)
        except Exception as e:
            pass  # migration warning suppressed

def list_users() -> list:
    ensure_users_dir()
    from data.db import db_connection, global_db_path
    with db_connection(global_db_path()) as con:
        rows = con.execute("SELECT name FROM users ORDER BY id ASC").fetchall()
    return [r["name"] for r in rows]

def get_user_info(display_name: str):
    ensure_users_dir()
    from data.db import db_connection, global_db_path
    with db_connection(global_db_path()) as con:
        row = con.execute("SELECT * FROM users WHERE name=?", (display_name,)).fetchone()
    if not row: return None
    def _int(v):
        try: return int(v) if str(v).strip() else None
        except: return None
    def _float(v):
        try: return float(v) if str(v).strip() else None
        except: return None
    raw_dn = ""
    try: raw_dn = row["date_naissance"] or ""
    except Exception: pass
    # Calculer l'âge dynamiquement depuis date_naissance, sinon fallback colonne age
    computed_age = age_depuis_naissance(raw_dn) or _int(row["age"])
    return {
        "name": row["name"], "age": computed_age, "sexe": row["sexe"],
        "taille": _int(row["taille"]), "poids": _float(row["poids"]),
        "objectif": row["objectif"],
        "ajustement": row["ajustement"] or "Maintien (0%)",
        "folder": to_folder_name(row["name"]),
        "date_naissance": raw_dn,
    }


def age_depuis_naissance(date_naissance: str) -> int | None:
    """Calcule l'âge en années depuis une date 'JJ/MM/AAAA'. Retourne None si invalide."""
    if not date_naissance:
        return None
    try:
        import datetime
        d = datetime.datetime.strptime(str(date_naissance).strip(), "%d/%m/%Y").date()
        today = datetime.date.today()
        age = today.year - d.year - ((today.month, today.day) < (d.month, d.day))
        return age if age >= 0 else None
    except Exception:
        return None

def add_user(name, age_or_dob, sexe, taille, poids="", objectif="", ajustement="Maintien (0%)", date_naissance=""):
    ensure_users_dir()
    from data.db import db_connection, global_db_path, get_user_db
    with db_connection(global_db_path()) as con:
        if con.execute("SELECT id FROM users WHERE name=?", (name,)).fetchone():
            return False, "Un profil avec ce nom existe déjà."
        # date_naissance prioritaire ; sinon age_or_dob peut être un age brut
        dn = date_naissance or (age_or_dob if "/" in str(age_or_dob) else "")
        age_val = str(age_depuis_naissance(dn) or age_or_dob or "")
        con.execute(
            "INSERT INTO users (name,age,sexe,taille,poids,objectif,ajustement,date_naissance) VALUES (?,?,?,?,?,?,?,?)",
            (name, age_val, sexe, str(taille), str(poids), objectif, ajustement, dn))
    folder = to_folder_name(name)
    Path(USERS_DIR, folder).mkdir(parents=True, exist_ok=True)
    get_user_db(folder)   # initialise le schéma utilisateur — NE PAS fermer
    return True, "Profil créé."

def update_user(old_name, new_name, age_or_dob, sexe, taille, poids, objectif, ajustement, date_naissance=""):
    ensure_users_dir()
    from data.db import db_connection, global_db_path
    with db_connection(global_db_path()) as con:
        if not con.execute("SELECT id FROM users WHERE name=?", (old_name,)).fetchone():
            return False
        dn = date_naissance or (age_or_dob if "/" in str(age_or_dob) else "")
        age_val = str(age_depuis_naissance(dn) or age_or_dob or "")
        con.execute(
            "UPDATE users SET name=?,age=?,sexe=?,taille=?,poids=?,objectif=?,ajustement=?,date_naissance=? WHERE name=?",
            (new_name, age_val, sexe, str(taille), str(poids), objectif, ajustement, dn, old_name))
    old_f, new_f = to_folder_name(old_name), to_folder_name(new_name)
    old_dir, new_dir = Path(USERS_DIR, old_f), Path(USERS_DIR, new_f)
    if old_dir.exists() and old_f != new_f:
        try:
            if new_dir.exists():
                for f in old_dir.iterdir():
                    dst = new_dir / f.name
                    if not dst.exists(): shutil.move(str(f), str(dst))
                shutil.rmtree(str(old_dir))
            else:
                old_dir.rename(new_dir)
            old_db = new_dir / f"{old_f}.db"
            new_db = new_dir / f"{new_f}.db"
            if old_db.exists() and not new_db.exists(): old_db.rename(new_db)
        except Exception:
            log_exc(f"update_user — renommage dossier {old_f} → {new_f}")
    return True

def delete_user(name):
    ensure_users_dir()
    from data.db import db_connection, global_db_path
    with db_connection(global_db_path()) as con:
        if not con.execute("SELECT id FROM users WHERE name=?", (name,)).fetchone():
            return False
        con.execute("DELETE FROM users WHERE name=?", (name,))
    user_dir = Path(USERS_DIR, to_folder_name(name))
    try:
        if user_dir.exists(): shutil.rmtree(str(user_dir))
    except Exception:
        log_exc(f"delete_user — suppression dossier {user_dir}")
    return True

@lru_cache(maxsize=256)
def calculer_imc(poids, taille_cm):
    try: poids = float(poids); taille_cm = float(taille_cm)
    except: return None, None
    if poids <= 0 or taille_cm <= 0: return None, None
    taille_m = taille_cm / 100.0
    imc = poids / (taille_m ** 2)
    cat = None
    for low, high, label in IMC_TABLE_5:
        if low <= imc < high: cat = (label, low, high); break
    return imc, cat

@lru_cache(maxsize=256)
def calculs_nutrition(poids, age, sexe, objectif, taille_cm):
    try: poids = float(poids); age = int(age); taille = float(taille_cm)
    except: return None
    if poids <= 0 or age <= 0 or taille <= 0: return None
    if sexe == "Homme":
        bmr = 88.362 + (13.397*poids) + (4.799*taille) - (5.677*age)
    else:
        bmr = 447.593 + (9.247*poids) + (3.098*taille) - (4.330*age)
    tdee = bmr * 1.55
    if objectif == "Gain de masse":   calories = tdee*1.10; cp,fp = 0.47, 0.23
    elif objectif == "Perte de poids": calories = tdee*0.90; cp,fp = 0.37, 0.23
    else:                              calories = tdee;       cp,fp = 0.45, 0.25
    return {"bmr":bmr,"tdee":tdee,"calories":calories,
            "proteines":poids*2.3,"glucides":(calories*cp)/4,"lipides":(calories*fp)/9,
            "carb_pct":cp,"fat_pct":fp}

def ajustement_to_objectif(ajustement_label: str) -> str:
    if not ajustement_label: return "Maintien"
    label = ajustement_label.lower()
    if "déficit" in label: return "Perte de poids"
    if "surplus" in label: return "Gain de masse"
    return "Maintien"


def clear_nutrition_cache() -> None:
    """Vide le cache LRU des calculs nutritionnels.

    À appeler lors d'un changement de profil (poids, taille, âge, objectif)
    pour forcer le recalcul complet au prochain accès.
    Appelé automatiquement depuis AppState.reset_user() si branché.
    """
    calculs_nutrition.cache_clear()
    calculer_imc.cache_clear()
    if "surplus" in label: return "Gain de masse"
    return "Maintien"


# ══════════════════════════════════════════════════════════════════════════════
#  VALIDATION CHAMPS NUMÉRIQUES
# ══════════════════════════════════════════════════════════════════════════════

def parse_num(value, cast=float, default=None, min_val=None, max_val=None):
    """Parse sécurisé d'une valeur numérique depuis un champ texte.

    Accepte virgule ou point comme séparateur décimal.
    Retourne `default` si la valeur est vide, invalide ou hors bornes.

    Exemples :
        parse_num("85.5")          → 85.5
        parse_num("85,5")          → 85.5
        parse_num("abc")           → None
        parse_num("", default=0)   → 0
        parse_num("300", max_val=250) → None  (hors borne)
    """
    if value is None:
        return default
    s = str(value).strip().replace(",", ".")
    if not s:
        return default
    try:
        v = cast(s)
    except (ValueError, TypeError):
        return default
    if min_val is not None and v < min_val:
        return default
    if max_val is not None and v > max_val:
        return default
    return v


def validate_taille(value) -> tuple[float | None, str]:
    """Valide une taille en cm. Retourne (valeur, message_erreur)."""
    v = parse_num(value, float, None, min_val=100, max_val=250)
    if v is None:
        s = str(value or "").strip()
        if not s:
            return None, "La taille est obligatoire."
        return None, f"Taille invalide « {s} » — entre 100 et 250 cm."
    return v, ""


def validate_poids(value) -> tuple[float | None, str]:
    """Valide un poids en kg. Retourne (valeur, message_erreur)."""
    v = parse_num(value, float, None, min_val=30, max_val=400)
    if v is None:
        s = str(value or "").strip()
        if not s:
            return None, "Le poids est obligatoire."
        return None, f"Poids invalide « {s} » — entre 30 et 400 kg."
    return v, ""
