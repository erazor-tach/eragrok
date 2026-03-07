# data/entrainement_history.py
# -*- coding: utf-8 -*-
"""
Gestion de l'historique des séances (training_history.json).
Toute la logique JSON est ici — séparée de l'UI et du planning CSV.
"""

import os
import json
import datetime
from pathlib import Path

from data import utils
from data.entrainement_schedule import parse_date

HISTORY_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M"


# ── Helpers internes ──────────────────────────────────────────────────────────

def _history_file(app) -> str:
    user_dir = utils.get_user_dir(app)
    if not user_dir:
        raise ValueError("Aucun utilisateur sélectionné.")
    Path(user_dir).mkdir(parents=True, exist_ok=True)
    return os.path.join(user_dir, "training_history.json")


# ── API publique ──────────────────────────────────────────────────────────────

def load(app) -> list[dict]:
    """Charge et retourne l'historique complet (liste de dicts)."""
    if not utils.get_current_user_folder(app):
        return []
    fichier = _history_file(app)
    if not os.path.exists(fichier):
        return []
    try:
        with open(fichier, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception:
        return []


def save(app, history: list[dict]):
    """Sauvegarde la liste complète."""
    fichier = _history_file(app)
    with open(fichier, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def add_entry(app, entry: dict):
    """Insère une entrée en tête de l'historique."""
    pf = entry.get("planned_for")
    if isinstance(pf, datetime.date):
        entry["planned_for"] = pf.strftime("%d/%m/%Y")
    elif pf:
        entry["planned_for"] = parse_date(str(pf))
    history = load(app)
    history.insert(0, entry)
    save(app, history)


def delete_at(app, index: int) -> bool:
    """Supprime l'entrée à l'index donné. Retourne True si succès."""
    history = load(app)
    if 0 <= index < len(history):
        history.pop(index)
        save(app, history)
        return True
    return False


def delete_matching(app, planned_for: str, line_text: str) -> int:
    """
    Supprime toutes les entrées dont planned_for correspond ET dont
    l'un des exercices / les notes contiennent line_text.
    Retourne le nombre d'entrées supprimées.
    """
    planned_for = parse_date(planned_for) if planned_for else ""
    if not planned_for and not line_text:
        return 0

    history = load(app)
    new_hist = []
    removed = 0

    for e in history:
        matched = _entry_matches(e, planned_for, line_text)
        if matched:
            removed += 1
        else:
            new_hist.append(e)

    if removed:
        save(app, new_hist)
    return removed


def update_planned_for(app, old_line_text: str, new_planned_for: str) -> int:
    """
    Met à jour le champ planned_for des entrées sans date dont les
    exercices / notes contiennent old_line_text.
    Retourne le nombre de mises à jour.
    """
    new_planned_for = parse_date(new_planned_for) if new_planned_for else ""
    if not old_line_text or not new_planned_for:
        return 0
    history = load(app)
    changed = 0
    for e in history:
        if e.get("planned_for"):
            continue
        if _entry_matches(e, "", old_line_text):
            e["planned_for"] = new_planned_for
            changed += 1
    if changed:
        save(app, history)
    return changed


# ── Helpers privés ────────────────────────────────────────────────────────────

def _entry_matches(entry: dict, planned_for: str, line_text: str) -> bool:
    """Vérifie si une entrée correspond aux critères planned_for + line_text."""
    pf_match = (not planned_for) or (entry.get("planned_for") == planned_for)
    if not pf_match:
        return False
    if not line_text:
        return True
    # cherche line_text dans les exercices
    for ex in entry.get("exercises", []):
        if isinstance(ex, str) and line_text.strip() in ex:
            return True
        if isinstance(ex, dict) and line_text.strip() in (ex.get("name", "") or ""):
            return True
    # cherche dans les notes
    return line_text.strip() in (entry.get("notes") or "")
