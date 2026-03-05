# data/utils.py
# Utilitaires partagés pour ERAGROK
# - gestion fichiers utilisateurs
# - constantes (ADJUSTMENTS)
# - fonctions de calcul (nutrition, IMC)
# - conversion ajustement -> objectif

import os
import csv
import shutil
from pathlib import Path

# ── FIX CHEMIN ABSOLU ──────────────────────────────────────────────────────────
# Peu importe d'où l'app est lancée, on pointe toujours vers le bon dossier.
_ROOT = Path(__file__).resolve().parent.parent   # data/ -> racine du projet
USERS_DIR  = str(_ROOT / "users")
USERS_FILE = str(_ROOT / "users" / "eragrok_users.csv")
# ───────────────────────────────────────────────────────────────────────────────

ADJUSTMENTS = {
    "Déficit léger (-10 à -15%)":    -0.125,
    "Déficit modéré (-15 à -25%)":   -0.20,
    "Maintien (0%)":                   0.0,
    "Surplus léger (lean) (+5 à +10%)": 0.075,
    "Surplus standard (+10 à +15%)":   0.125,
    "Surplus agressif (+15 à +20%)":   0.175,
}

IMC_TABLE_5 = [
    (0.0,  18.5, "Maigreur"),
    (18.5, 25.0, "Normal"),
    (25.0, 30.0, "Surpoids"),
    (30.0, 40.0, "Obésité modérée"),
    (40.0, 999., "Obésité sévère"),
]


# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS UTILISATEURS UNIFIÉS
#  Convention stricte :
#    • folder_name  = nom en minuscules, espaces → underscores  (ex: "rudy")
#    • display_name = nom tel que saisi dans le formulaire      (ex: "Rudy")
# ══════════════════════════════════════════════════════════════════════════════

def to_folder_name(display_name: str) -> str:
    """Convertit un nom d'affichage en nom de dossier (lowercase + underscores)."""
    return (display_name or "").strip().lower().replace(" ", "_")


def get_current_user_folder(app) -> str:
    """
    Retourne le folder_name de l'utilisateur courant.
    Source unique : app.current_user (toujours un folder_name).
    Lève une valeur vide si aucun utilisateur n'est sélectionné.
    """
    return getattr(app, "current_user", "") or ""


def get_user_dir(app) -> str:
    """Retourne le chemin absolu du dossier de l'utilisateur courant."""
    folder = get_current_user_folder(app)
    if not folder:
        return ""
    return os.path.join(USERS_DIR, folder)


# ══════════════════════════════════════════════════════════════════════════════
#  GESTION FICHIERS / PROFILS
# ══════════════════════════════════════════════════════════════════════════════

def ensure_users_dir():
    Path(USERS_DIR).mkdir(parents=True, exist_ok=True)
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Name", "Age", "Sexe", "Taille (cm)", "Poids (kg)", "Objectif", "Ajustement"])


def list_users():
    ensure_users_dir()
    users = []
    with open(USERS_FILE, 'r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            if len(row) > 1:
                users.append(row[1])
    return users


def get_user_info(display_name: str):
    ensure_users_dir()
    with open(USERS_FILE, 'r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if not header:
            return None
        idx = {h: i for i, h in enumerate(header)}
        for row in reader:
            if len(row) > idx.get("Name", 1) and row[idx["Name"]] == display_name:
                def _int(v):
                    try: return int(v) if str(v).strip() else None
                    except Exception: return None
                def _float(v):
                    try: return float(v) if str(v).strip() else None
                    except Exception: return None
                return {
                    "name":       row[idx["Name"]],
                    "age":        _int(row[idx["Age"]]),
                    "sexe":       row[idx.get("Sexe", 3)] if "Sexe" in idx else None,
                    "taille":     _int(row[idx["Taille (cm)"]]),
                    "poids":      _float(row[idx["Poids (kg)"]]),
                    "objectif":   row[idx["Objectif"]] if "Objectif" in idx else None,
                    "ajustement": row[idx["Ajustement"]] if "Ajustement" in idx else "Maintien (0%)",
                    # Champ calculé pratique
                    "folder":     to_folder_name(row[idx["Name"]]),
                }
    return None


def add_user(name, age, sexe, taille, poids="", objectif="", ajustement="Maintien (0%)"):
    ensure_users_dir()
    users = list_users()
    if name in users:
        return False, "Un profil avec ce nom existe déjà."
    new_id = len(users) + 1
    with open(USERS_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([new_id, name, age, sexe, taille, poids, objectif, ajustement])
    # créer dossier + fichiers CSV vides
    folder = to_folder_name(name)
    user_dir = os.path.join(USERS_DIR, folder)
    os.makedirs(user_dir, exist_ok=True)
    files = {
        "entrainement.csv": ["Date", "Groupes musculaires", "Programme", "Note"],
        "nutrition.csv":    ["Date", "Poids (kg)", "Age", "Calories",
                             "Protéines (g)", "Glucides (g)", "Lipides (g)", "Note"],
        "cycle.csv":        ["Date", "Dose testo (mg/sem)", "hCG (UI/sem)",
                             "Phase (blast/cruise)", "Note"],
    }
    for fname, headers in files.items():
        path = os.path.join(user_dir, fname)
        if not os.path.exists(path):
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
    return True, "Profil créé."


def update_user(old_name, new_name, age, sexe, taille, poids, objectif, ajustement):
    ensure_users_dir()
    rows = []
    updated = False
    with open(USERS_FILE, 'r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader, None)
        for row in reader:
            if len(row) > 1 and row[1] == old_name:
                row = [row[0], new_name, age, sexe, taille, poids, objectif, ajustement]
                updated = True
            rows.append(row)
    if not updated:
        return False
    with open(USERS_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Name", "Age", "Sexe", "Taille (cm)", "Poids (kg)", "Objectif", "Ajustement"])
        for r in rows:
            writer.writerow(r)
    # renommer le dossier si besoin
    old_dir = os.path.join(USERS_DIR, to_folder_name(old_name))
    new_dir = os.path.join(USERS_DIR, to_folder_name(new_name))
    try:
        if os.path.exists(old_dir) and old_dir != new_dir:
            if os.path.exists(new_dir):
                for fname in os.listdir(old_dir):
                    src = os.path.join(old_dir, fname)
                    dst = os.path.join(new_dir, fname)
                    if not os.path.exists(dst):
                        shutil.move(src, dst)
                shutil.rmtree(old_dir)
            else:
                os.rename(old_dir, new_dir)
    except Exception:
        pass
    return True


def delete_user(name):
    ensure_users_dir()
    rows = []
    deleted = False
    with open(USERS_FILE, 'r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader, None)
        for row in reader:
            if len(row) > 1 and row[1] == name:
                deleted = True
                continue
            rows.append(row)
    if not deleted:
        return False
    with open(USERS_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Name", "Age", "Sexe", "Taille (cm)", "Poids (kg)", "Objectif", "Ajustement"])
        for i, r in enumerate(rows, start=1):
            writer.writerow([i] + r[1:])
    user_dir = os.path.join(USERS_DIR, to_folder_name(name))
    try:
        if os.path.exists(user_dir):
            shutil.rmtree(user_dir)
    except Exception:
        pass
    return True


# ══════════════════════════════════════════════════════════════════════════════
#  CALCULS
# ══════════════════════════════════════════════════════════════════════════════

def calculer_imc(poids, taille_cm):
    """Retourne (imc, (categorie, imc_min, imc_max)) ou (None, None)."""
    try:
        poids    = float(poids)
        taille_cm = float(taille_cm)
    except Exception:
        return None, None
    if poids <= 0 or taille_cm <= 0:
        return None, None
    taille_m = taille_cm / 100.0
    imc = poids / (taille_m ** 2)
    cat = None
    for low, high, label in IMC_TABLE_5:
        if low <= imc < high:
            cat = (label, low, high)
            break
    return imc, cat


def calculs_nutrition(poids, age, sexe, objectif, taille_cm):
    """
    Calcule BMR, TDEE et macronutriments.
    Retourne un dict ou None si les données sont invalides.
    """
    try:
        poids    = float(poids)
        age      = int(age)
        taille   = float(taille_cm)
    except Exception:
        return None
    if poids <= 0 or age <= 0 or taille <= 0:
        return None

    if sexe == "Homme":
        bmr = 88.362 + (13.397 * poids) + (4.799 * taille) - (5.677 * age)
    else:
        bmr = 447.593 + (9.247 * poids) + (3.098 * taille) - (4.330 * age)

    activity_factor = 1.55
    tdee = bmr * activity_factor

    # Calories selon objectif (sans ajustement — l'ajustement est appliqué côté UI)
    if objectif == "Gain de masse":
        calories = tdee * 1.10
        carb_pct, fat_pct = 0.47, 0.23
    elif objectif == "Perte de poids":
        calories = tdee * 0.90
        carb_pct, fat_pct = 0.37, 0.23
    else:
        calories = tdee
        carb_pct, fat_pct = 0.45, 0.25

    proteines = poids * 2.3
    glucides  = (calories * carb_pct) / 4
    lipides   = (calories * fat_pct)  / 9

    return {
        "bmr":       bmr,
        "tdee":      tdee,
        "calories":  calories,
        "proteines": proteines,
        "glucides":  glucides,
        "lipides":   lipides,
        # On expose aussi les pourcentages pour éviter de les recalculer partout
        "carb_pct":  carb_pct,
        "fat_pct":   fat_pct,
    }


def ajustement_to_objectif(ajustement_label: str) -> str:
    """
    Convertit un label d'ajustement calorique en objectif logique.
    Ex : 'Déficit léger (-10 à -15%)' -> 'Perte de poids'
    """
    if not ajustement_label:
        return "Maintien"
    label = ajustement_label.lower()
    if "déficit" in label:
        return "Perte de poids"
    if "surplus" in label:
        return "Gain de masse"
    return "Maintien"
