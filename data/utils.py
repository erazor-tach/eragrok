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

USERS_DIR = "users"
USERS_FILE = os.path.join(USERS_DIR, "eragrok_users.csv")

ADJUSTMENTS = {
    "Déficit léger (-10 à -15%)": -0.125,
    "Déficit modéré (-15 à -25%)": -0.20,
    "Maintien (0%)": 0.0,
    "Surplus léger (lean) (+5 à +10%)": 0.075,
    "Surplus standard (+10 à +15%)": 0.125,
    "Surplus agressif (+15 à +20%)": 0.175
}

IMC_TABLE_5 = [
    (0.0, 18.5, "Maigreur"),
    (18.5, 25.0, "Normal"),
    (25.0, 30.0, "Surpoids"),
    (30.0, 40.0, "Obésité modérée"),
    (40.0, 999.0, "Obésité sévère")
]

# ----------------- Gestion fichiers / profils -----------------
def ensure_users_dir():
    Path(USERS_DIR).mkdir(exist_ok=True)
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

def get_user_info(name):
    ensure_users_dir()
    with open(USERS_FILE, 'r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if not header:
            return None
        idx = {h: i for i, h in enumerate(header)}
        for row in reader:
            if len(row) > idx.get("Name", 1) and row[idx["Name"]] == name:
                info = {}
                info["name"] = row[idx["Name"]]
                info["age"] = int(row[idx["Age"]]) if row[idx["Age"]].strip() else None
                info["sexe"] = row[idx["Sexe"]] if "Sexe" in idx else None
                info["taille"] = int(row[idx["Taille (cm)"]]) if row[idx["Taille (cm)"]].strip() else None
                info["poids"] = float(row[idx["Poids (kg)"]]) if row[idx["Poids (kg)"]].strip() else None
                info["objectif"] = row[idx["Objectif"]] if "Objectif" in idx else None
                info["ajustement"] = row[idx["Ajustement"]] if "Ajustement" in idx else "Maintien (0%)"
                return info
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
    # create user folder and files
    prefix = name.lower().replace(" ", "_")
    user_dir = os.path.join(USERS_DIR, prefix)
    os.makedirs(user_dir, exist_ok=True)
    files = {
        "entrainement.csv": ["Date", "Groupes musculaires", "Programme", "Note"],
        "nutrition.csv": ["Date", "Poids (kg)", "Age", "Calories", "Protéines (g)", "Glucides (g)", "Lipides (g)", "Note"],
        "cycle.csv": ["Date", "Dose testo (mg/sem)", "hCG (UI/sem)", "Phase (blast/cruise)", "Note"]
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
    # rename folder if exists
    old_dir = os.path.join(USERS_DIR, old_name.lower().replace(" ", "_"))
    new_dir = os.path.join(USERS_DIR, new_name.lower().replace(" ", "_"))
    try:
        if os.path.exists(old_dir):
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
    # remove folder
    user_dir = os.path.join(USERS_DIR, name.lower().replace(" ", "_"))
    try:
        if os.path.exists(user_dir):
            shutil.rmtree(user_dir)
    except Exception:
        pass
    return True

# ----------------- Calculs -----------------
def calculer_imc(poids, taille_cm):
    """
    Retourne (imc, (categorie, imc_min, imc_max)) ou (None, None) si invalide.
    """
    try:
        poids = float(poids)
        taille_cm = float(taille_cm)
    except Exception:
        return None, None
    if poids <= 0 or taille_cm <= 0:
        return None, None
    taille_m = taille_cm / 100.0
    imc = poids / (taille_m ** 2)
    cat = None
    for low, high, label in IMC_TABLE_5:
        if imc >= low and imc < high:
            cat = (label, low, high)
            break
    return imc, cat

def calculs_nutrition(poids, age, sexe, objectif, taille_cm):
    """
    Calcule BMR, TDEE, calories et macronutriments (mêmes formules que dans le code d'origine).
    Retourne dict ou None si données invalides.
    """
    try:
        poids = float(poids)
        age = int(age)
        taille = float(taille_cm)
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
    if objectif == "Gain de masse":
        calories = tdee * 1.10
    elif objectif == "Perte de poids":
        calories = tdee * 0.90
    else:
        calories = tdee
    proteines = poids * 2.3
    if objectif == "Gain de masse":
        glucides = (calories * 0.47) / 4
        lipides = (calories * 0.23) / 9
    elif objectif == "Perte de poids":
        glucides = (calories * 0.37) / 4
        lipides = (calories * 0.23) / 9
    else:
        glucides = (calories * 0.45) / 4
        lipides = (calories * 0.25) / 9
    return {
        "bmr": bmr,
        "tdee": tdee,
        "calories": calories,
        "proteines": proteines,
        "glucides": glucides,
        "lipides": lipides
    }

# ----------------- Conversion Ajustement -> Objectif -----------------
def ajustement_to_objectif(ajustement_label):
    """
    Convertit un label d'ajustement calorique en objectif logique.
    Exemples :
      - 'Déficit léger (-10 à -15%)' -> 'Perte de poids'
      - 'Maintien (0%)' -> 'Maintien'
      - 'Surplus standard (+10 à +15%)' -> 'Gain de masse'
    """
    if not ajustement_label:
        return "Maintien"
    label = ajustement_label.lower()
    if "déficit" in label:
        return "Perte de poids"
    if "surplus" in label:
        return "Gain de masse"
    if "maintien" in label:
        return "Maintien"
    return "Maintien"