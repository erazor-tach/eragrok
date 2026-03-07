# data/utils.py — ERAGROK
# Gestion utilisateurs (SQLite) + calculs nutrition/IMC
# API publique identique à l'ancienne version CSV pour zéro cassure dans l'app.

import os
import sys
import shutil
from pathlib import Path

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
    get_global_db().close()
    csv_path = Path(USERS_FILE)
    if csv_path.exists() and not Path(USERS_FILE + ".migrated").exists():
        try:
            from data.migrate import run_migration
            run_migration(USERS_DIR, verbose=False)
        except Exception as e:
            import logging; logging.warning(f"Migration auto: {e}")

def list_users() -> list:
    ensure_users_dir()
    from data.db import get_global_db
    con = get_global_db()
    rows = con.execute("SELECT name FROM users ORDER BY id ASC").fetchall()
    con.close()
    return [r["name"] for r in rows]

def get_user_info(display_name: str):
    ensure_users_dir()
    from data.db import get_global_db
    con = get_global_db()
    row = con.execute("SELECT * FROM users WHERE name=?", (display_name,)).fetchone()
    con.close()
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
    from data.db import get_global_db, get_user_db
    con = get_global_db()
    if con.execute("SELECT id FROM users WHERE name=?", (name,)).fetchone():
        con.close(); return False, "Un profil avec ce nom existe déjà."
    # date_naissance prioritaire ; sinon age_or_dob peut être un age brut
    dn = date_naissance or (age_or_dob if "/" in str(age_or_dob) else "")
    age_val = str(age_depuis_naissance(dn) or age_or_dob or "")
    con.execute(
        "INSERT INTO users (name,age,sexe,taille,poids,objectif,ajustement,date_naissance) VALUES (?,?,?,?,?,?,?,?)",
        (name, age_val, sexe, str(taille), str(poids), objectif, ajustement, dn))
    con.commit(); con.close()
    folder = to_folder_name(name)
    Path(USERS_DIR, folder).mkdir(parents=True, exist_ok=True)
    get_user_db(folder).close()
    return True, "Profil créé."

def update_user(old_name, new_name, age_or_dob, sexe, taille, poids, objectif, ajustement, date_naissance=""):
    ensure_users_dir()
    from data.db import get_global_db
    con = get_global_db()
    if not con.execute("SELECT id FROM users WHERE name=?", (old_name,)).fetchone():
        con.close(); return False
    dn = date_naissance or (age_or_dob if "/" in str(age_or_dob) else "")
    age_val = str(age_depuis_naissance(dn) or age_or_dob or "")
    con.execute(
        "UPDATE users SET name=?,age=?,sexe=?,taille=?,poids=?,objectif=?,ajustement=?,date_naissance=? WHERE name=?",
        (new_name, age_val, sexe, str(taille), str(poids), objectif, ajustement, dn, old_name))
    con.commit(); con.close()
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
        except Exception: pass
    return True

def delete_user(name):
    ensure_users_dir()
    from data.db import get_global_db
    con = get_global_db()
    if not con.execute("SELECT id FROM users WHERE name=?", (name,)).fetchone():
        con.close(); return False
    con.execute("DELETE FROM users WHERE name=?", (name,))
    con.commit(); con.close()
    user_dir = Path(USERS_DIR, to_folder_name(name))
    try:
        if user_dir.exists(): shutil.rmtree(str(user_dir))
    except Exception: pass
    return True

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
