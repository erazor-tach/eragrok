# data/entrainement_schedule.py
# -*- coding: utf-8 -*-
"""
Gestion persistence du planning d'entraînement (CSV).
Toutes les lectures/écritures/suppressions du fichier entrainement.csv
sont centralisées ici — l'UI n'y touche plus directement.
"""

import os
import csv
import datetime
from pathlib import Path

from data import utils

DATE_FORMAT = "%d/%m/%Y"


# ── Helpers internes ──────────────────────────────────────────────────────────

def _schedule_file(app) -> str:
    user_dir = utils.get_user_dir(app)
    if not user_dir:
        raise ValueError("Aucun utilisateur sélectionné.")
    Path(user_dir).mkdir(parents=True, exist_ok=True)
    return os.path.join(user_dir, "entrainement.csv")


def parse_date(s) -> str | None:
    """Normalise n'importe quelle chaîne date en 'dd/mm/YYYY', ou None."""
    if isinstance(s, datetime.date):
        return s.strftime(DATE_FORMAT)
    if not s:
        return None
    s = str(s).strip()
    fmts = ("%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d")
    for fmt in fmts:
        try:
            return datetime.datetime.strptime(s, fmt).date().strftime(DATE_FORMAT)
        except Exception:
            pass
    # tentative numérique
    parts = [p for p in s.replace("-", "/").split("/") if p.strip().isdigit()]
    try:
        if len(parts) == 3:
            d, m, y = map(int, parts)
            if y < 100:
                y = y + 2000 if y < 70 else 1900 + y
            return datetime.date(y, m, d).strftime(DATE_FORMAT)
    except Exception:
        pass
    return None


# ── API publique ──────────────────────────────────────────────────────────────

def read_schedule(app) -> list[dict]:
    """
    Lit le fichier entrainement.csv et retourne une liste de dicts :
    {date, groupes, program, types, note, line}
    """
    fichier = _schedule_file(app)
    entries = []
    if not os.path.exists(fichier):
        return entries
    try:
        with open(fichier, "r", newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader, None)  # skip header
            for row in reader:
                if not row:
                    continue
                raw_date = row[0] if len(row) > 0 else ""
                entries.append({
                    "date":    parse_date(raw_date),
                    "groupes": row[1] if len(row) > 1 else "",
                    "program": row[2] if len(row) > 2 else "",
                    "types":   row[3] if len(row) > 3 else "",
                    "note":    row[4] if len(row) > 4 else "",
                    "line":    row[5] if len(row) > 5 else "",
                })
    except Exception:
        pass
    return entries


def write_entry(app, date_str, line, groupes="", program="", types="", note=""):
    """Ajoute une ligne dans entrainement.csv."""
    date_str = parse_date(date_str)
    fichier = _schedule_file(app)
    new_file = not os.path.exists(fichier)
    with open(fichier, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if new_file:
            writer.writerow(["Date", "Groupes", "Programme", "Types", "Note", "Line"])
        writer.writerow([date_str or "", groupes, program, types, note, line])


def delete_entry(app, date_str, line_text):
    """Supprime la première ligne correspondant à (date_str, line_text)."""
    date_str = parse_date(date_str) if date_str else ""
    fichier = _schedule_file(app)
    if not os.path.exists(fichier):
        return
    try:
        with open(fichier, "r", newline="", encoding="utf-8") as f:
            rows = list(csv.reader(f))
        header = rows[0] if rows else []
        data   = rows[1:] if len(rows) > 1 else []
        new_data = [
            r for r in data
            if not (
                len(r) > 0
                and (r[0].strip() == (date_str or "").strip())
                and (len(r) <= 5 or r[5] == line_text)
            )
        ]
        with open(fichier, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if header:
                writer.writerow(header)
            for r in new_data:
                writer.writerow(r)
    except Exception:
        pass


def assign_date_to_undated(app, line_text: str, new_date_str: str) -> bool:
    """Assigne new_date_str à la première entrée sans date dont line == line_text."""
    new_date_str = parse_date(new_date_str) or ""
    fichier = _schedule_file(app)
    if not os.path.exists(fichier):
        return False
    try:
        with open(fichier, "r", newline="", encoding="utf-8") as f:
            rows = list(csv.reader(f))
        header = rows[0] if rows else []
        data   = rows[1:] if len(rows) > 1 else []
        updated = False
        for i, r in enumerate(data):
            date_field = r[0] if len(r) > 0 else ""
            line_field = r[5] if len(r) > 5 else ""
            if (not date_field or not date_field.strip()) and line_field.strip() == line_text:
                while len(r) < 6:
                    r.append("")
                r[0] = new_date_str
                data[i] = r
                updated = True
                break
        if updated:
            with open(fichier, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                if header:
                    writer.writerow(header)
                for r in data:
                    writer.writerow(r)
        return updated
    except Exception:
        return False
