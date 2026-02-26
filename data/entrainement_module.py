# data/entrainement_module.py
# -*- coding: utf-8 -*-
"""
Écran d'entraînement : calendrier + groupes + catalogue + programmation jour/semaine/mois
Générateur mensuel et génération intégrale (rotation sans répétition).
Export et visualisation PDF de la liste "Programme (séances)" (utilise reportlab).
PDF : une semaine par page, coloration selon difficulty_level (1-5), légende, notes techniques.
"""

import os
import csv
import json
from pathlib import Path
import datetime
import random
import calendar
import tempfile
import webbrowser
import textwrap
import re

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog

from tkcalendar import Calendar

from data import utils
from data import training_techniques as tt

# Optional import for PDF generation; handled at runtime with friendly message if absent
try:
    from reportlab.pdfgen import canvas as pdf_canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except Exception:
    REPORTLAB_AVAILABLE = False

DATE_FORMAT = "%d/%m/%Y"
HISTORY_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M"


# ----------------- Helpers for user dir / current user -----------------


def _ensure_user_dir(app):
    user_name = _get_current_user(app)
    user_dir = os.path.join(utils.USERS_DIR, user_name) if user_name else os.path.join(utils.USERS_DIR, "default")
    Path(user_dir).mkdir(parents=True, exist_ok=True)
    return user_dir


def _get_current_user(app):
    return getattr(app, "current_user", None) or getattr(app, "selected_user_name", None)


# ----------------- Beginner descriptions / tech label -----------------


def _format_tech_label(t):
    return f"{t['nom']} — {t.get('reps','—')} — {t.get('charge','—')} ({t['id']})"


_BEGINNER_DESCRIPTIONS = {
    "series_10_12_standard": {
        "title": "Séries 10–12 (standard)",
        "what": "Bloc de 3–4 séries de 10–12 répétitions pour développer le volume musculaire.",
        "how": "Charge modérée (60–75% 1RM), cadence contrôlée, repos 60–90 s.",
        "tips": "Priorise la technique; commence par exercices composés puis blocs 10–12.",
        "warnings": "Évite d'aller systématiquement à l'échec sur les mouvements lourds.",
    },
    "bfr": {
        "title": "Blood Flow Restriction (BFR)",
        "what": "Travail à faible charge avec occlusion partielle pour augmenter le pump.",
        "how": "Charges légères, répétitions élevées; utiliser bandes adaptées.",
        "tips": "Utilise en complément, pas sur exercices très lourds.",
        "warnings": "Consulter si antécédents vasculaires; ne pas serrer excessivement.",
    },
}


def _get_beginner_text(tid, tech):
    b = _BEGINNER_DESCRIPTIONS.get(tid)
    if b:
        return (
            f"{b['title']}\n\nQu'est-ce que c'est ?\n{b['what']}\n\nComment faire (simple) :\n{b['how']}\n\nConseils :\n{b['tips']}\n\nPrécautions :\n{b['warnings']}"
        )
    if not tech:
        return "Sélectionne une technique pour voir les explications simples."
    title = tech.get("nom", "Technique")
    what = tech.get("objectif", "Objectif non spécifié.")
    how = f"Répétitions : {tech.get('reps','—')} ; Charge : {tech.get('charge','—')} ; Repos : {tech.get('repos','—')}"
    tips = "Commence léger, priorise la technique, augmente progressivement la charge ou le volume."
    warnings = "Évite les techniques avancées sans supervision; respecte la récupération."
    return f"{title}\n\nQu'est-ce que c'est ?\n{what}\n\nComment faire (simple) :\n{how}\n\nConseils :\n{tips}\n\nPrécautions :\n{warnings}"


# ----------------- Schedule storage helpers -----------------


def _schedule_file_for_user(app):
    user_dir = _ensure_user_dir(app)
    return os.path.join(user_dir, "entrainement.csv")


def _parse_date_flexible_to_display(s):
    if not s:
        return None
    s = s.strip()
    fmts = ("%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d")
    for fmt in fmts:
        try:
            d = datetime.datetime.strptime(s, fmt).date()
            return d.strftime(DATE_FORMAT)
        except Exception:
            pass
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


def _read_schedule(app):
    fichier = _schedule_file_for_user(app)
    entries = []
    if not os.path.exists(fichier):
        return entries
    try:
        with open(fichier, "r", newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            for row in reader:
                if not row:
                    continue
                raw_date = row[0] if len(row) > 0 else ""
                date_norm = _parse_date_flexible_to_display(raw_date)
                date_field = date_norm if date_norm else None
                groupes = row[1] if len(row) > 1 else ""
                program = row[2] if len(row) > 2 else ""
                types = row[3] if len(row) > 3 else ""
                note = row[4] if len(row) > 4 else ""
                line = row[5] if len(row) > 5 else ""
                entries.append(
                    {"date": date_field, "groupes": groupes, "program": program, "types": types, "note": note, "line": line}
                )
    except Exception:
        return entries
    return entries


def _write_schedule_entry(app, date_str, line, groupes="", program="", types="", note=""):
    if isinstance(date_str, datetime.date):
        date_str = date_str.strftime(DATE_FORMAT)
    elif date_str:
        date_str = _parse_date_flexible_to_display(str(date_str))

    fichier = _schedule_file_for_user(app)
    new_file = not os.path.exists(fichier)
    try:
        with open(fichier, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if new_file:
                writer.writerow(["Date", "Groupes", "Programme", "Types", "Note", "Line"])
            writer.writerow([date_str or "", groupes, program, types, note, line])
    except Exception:
        pass

    if date_str:
        hist_date_field = date_str
    else:
        hist_date_field = datetime.datetime.now().strftime(HISTORY_TIMESTAMP_FORMAT)

    try:
        entry = {
            "date": hist_date_field,
            "type": program or "séance",
            "duration": "",
            "notes": note or (f"Ajoutée depuis le planning pour le {date_str}" if date_str else "Ajoutée depuis le planning"),
            "exercises": [line],
            "planned_for": date_str,
        }
        _add_training_entry(app, entry)
    except Exception:
        pass


def _delete_schedule_entry(app, date_str, line_text):
    if isinstance(date_str, datetime.date):
        date_str = date_str.strftime(DATE_FORMAT)
    elif date_str:
        date_str = _parse_date_flexible_to_display(str(date_str))

    fichier = _schedule_file_for_user(app)
    if not os.path.exists(fichier):
        return
    try:
        with open(fichier, "r", newline="", encoding="utf-8") as f:
            rows = list(csv.reader(f))
            header = rows[0] if rows else []
            data = rows[1:] if len(rows) > 1 else []
        new_data = [
            r
            for r in data
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

    try:
        _delete_history_entries_matching(app, date_str, line_text)
    except Exception:
        pass


# ----------------- Training history (JSON) helpers -----------------


def _history_file_for_user(app):
    user_dir = _ensure_user_dir(app)
    return os.path.join(user_dir, "training_history.json")


def _load_training_history(app):
    user = _get_current_user(app)
    if not user:
        return []
    fichier = _history_file_for_user(app)
    if not os.path.exists(fichier):
        return []
    try:
        with open(fichier, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
    except Exception:
        pass
    return []


def _save_training_history(app, history_list):
    fichier = _history_file_for_user(app)
    try:
        with open(fichier, "w", encoding="utf-8") as f:
            json.dump(history_list, f, ensure_ascii=False, indent=2)
    except Exception:
        raise


def _add_training_entry(app, entry):
    pf = entry.get("planned_for")
    if isinstance(pf, datetime.date):
        entry["planned_for"] = pf.strftime(DATE_FORMAT)
    elif pf:
        entry["planned_for"] = _parse_date_flexible_to_display(str(pf))
    history = _load_training_history(app)
    history.insert(0, entry)
    _save_training_history(app, history)


def _delete_training_entry(app, index):
    history = _load_training_history(app)
    if 0 <= index < len(history):
        history.pop(index)
        _save_training_history(app, history)
        return True
    return False


def _delete_history_entries_matching(app, planned_for, line_text):
    if isinstance(planned_for, datetime.date):
        planned_for = planned_for.strftime(DATE_FORMAT)
    elif planned_for:
        planned_for = _parse_date_flexible_to_display(str(planned_for))

    if not planned_for and not line_text:
        return 0
    history = _load_training_history(app)
    if not history:
        return 0
    new_hist = []
    removed = 0
    for e in history:
        matched = False
        if planned_for and e.get("planned_for") == planned_for:
            if not line_text:
                matched = True
            else:
                exs = e.get("exercises", [])
                for ex in exs:
                    if isinstance(ex, str) and line_text.strip() in ex:
                        matched = True
                        break
                    if isinstance(ex, dict) and line_text.strip() in (ex.get("name", "") or ""):
                        matched = True
                        break
                if not matched:
                    notes = (e.get("notes") or "")
                    if line_text.strip() and line_text.strip() in notes:
                        matched = True
        else:
            exs = e.get("exercises", [])
            for ex in exs:
                if isinstance(ex, str) and line_text.strip() in ex:
                    matched = True
                    break
                if isinstance(ex, dict) and line_text.strip() in (ex.get("name", "") or ""):
                    matched = True
                    break
            if not matched:
                notes = (e.get("notes") or "")
                if line_text.strip() and line_text.strip() in notes:
                    matched = True
        if matched:
            removed += 1
        else:
            new_hist.append(e)
    if removed:
        _save_training_history(app, new_hist)
    return removed


def _update_history_planned_for(app, old_line_text, new_planned_for):
    if isinstance(new_planned_for, datetime.date):
        new_planned_for = new_planned_for.strftime(DATE_FORMAT)
    elif new_planned_for:
        new_planned_for = _parse_date_flexible_to_display(str(new_planned_for))

    if not old_line_text or not new_planned_for:
        return 0
    history = _load_training_history(app)
    changed = 0
    for e in history:
        if e.get("planned_for"):
            continue
        matched = False
        exs = e.get("exercises", [])
        for ex in exs:
            if isinstance(ex, str) and old_line_text.strip() in ex:
                matched = True
                break
            if isinstance(ex, dict) and old_line_text.strip() in (ex.get("name", "") or ""):
                matched = True
                break
        if not matched:
            notes = (e.get("notes") or "")
            if old_line_text.strip() and old_line_text.strip() in notes:
                matched = True
        if matched:
            e["planned_for"] = new_planned_for
            changed += 1
    if changed:
        _save_training_history(app, history)
    return changed


# ----------------- Rotation helper (no repetition until pool exhausted) -----------------


def _build_rotation_from_pool(pool):
    ids = []
    seen = set()
    for t in pool:
        tid = t.get("id")
        if not tid:
            continue
        if tid in seen:
            continue
        seen.add(tid)
        ids.append(tid)
    if not ids:
        return []
    random.shuffle(ids)
    return ids


class _RotationIterator:
    def __init__(self, pool):
        self.pool = pool or []
        self._base_rotation = _build_rotation_from_pool(self.pool)
        self.rotation = list(self._base_rotation)
        self.index = 0

    def next(self):
        if not self.rotation:
            self._base_rotation = _build_rotation_from_pool(self.pool)
            self.rotation = list(self._base_rotation)
            self.index = 0
            if not self.rotation:
                return None
        if self.index >= len(self.rotation):
            self._base_rotation = _build_rotation_from_pool(self.pool)
            self.rotation = list(self._base_rotation)
            self.index = 0
            if not self.rotation:
                return None
        val = self.rotation[self.index]
        self.index += 1
        return val

    def all_ids(self):
        return list(self._base_rotation)


# ----------------- PDF export / preview helpers -----------------


def _program_list_to_lines(app):
    """Récupère les lignes visibles dans app.program_listbox sous forme de liste de chaînes."""
    if not hasattr(app, "program_listbox"):
        return []
    return [app.program_listbox.get(i) for i in range(app.program_listbox.size())]


def _wrap_text_for_width(text, max_chars):
    """Simple wrapper using textwrap to split text into lines of max_chars."""
    wrapper = textwrap.TextWrapper(width=max_chars, break_long_words=True, replace_whitespace=False)
    lines = []
    for paragraph in str(text).split("\n"):
        lines.extend(wrapper.wrap(paragraph) or [""])
    return lines


def _extract_id_from_line(line):
    """Extrait un id entre parenthèses à la fin d'une ligne, sinon None."""
    if not line:
        return None
    m = re.search(r"\(([A-Za-z0-9_\-]+)\)\s*$", line)
    if m:
        return m.group(1)
    return None


def _normalize_difficulty_text(s):
    if not s:
        return None
    t = str(s).lower()
    t = t.replace("é", "e").replace("è", "e").replace("ê", "e").replace("à", "a").replace("ù", "u")
    # search keywords
    if re.search(r"tres[-\s]?legere|tres[-\s]?l[eé]gere|tres legere", t):
        return "legere"
    if re.search(r"\blegere\b|legere\b", t):
        return "legere"
    if re.search(r"\bmod[eè]r[eé]e\b|moderee|modere", t):
        return "moderee"
    if re.search(r"\blourde\b|lourde\b", t):
        return "lourde"
    if re.search(r"tres[-\s]?lourde|tres[-\s]?lourde|tres lourde", t):
        return "lourde"
    return None


# mapping difficulty level (1-5) -> background color hex
DIFFICULTY_LEVEL_COLORS = {
    1: colors.HexColor("#e6fff2"),
    2: colors.HexColor("#d1fae5"),
    3: colors.HexColor("#fef3c7"),
    4: colors.HexColor("#fcd5c5"),
    5: colors.HexColor("#fee2e2"),
}

# fallback mapping from normalized text categories to level
_TEXT_TO_LEVEL = {
    "legere": 2,
    "moderee": 3,
    "lourde": 5,
}


def _detect_difficulty_from_tech(tech):
    """
    Détermine la difficulté normalisée en priorité :
    1) difficulty_level (int 1-5)
    2) difficulte (champ existant)
    3) keys 'difficulty'/'niveau'/'intensity' (texte)
    4) charge (pourcentage moyen)
    5) notes (analyse mots-clés)
    Retourne un int 1..5 ou None.
    """
    if not tech:
        return None
    # 1) difficulty_level explicit
    lvl = tech.get("difficulty_level")
    if isinstance(lvl, int) and 1 <= lvl <= 5:
        return lvl
    # 2) ancien champ 'difficulte'
    old = tech.get("difficulte")
    if isinstance(old, int) and 1 <= old <= 5:
        return old
    # 3) textual keys
    for key in ("difficulty", "niveau", "intensity"):
        v = tech.get(key)
        if v and isinstance(v, str):
            norm = _normalize_difficulty_text(v)
            if norm:
                return _TEXT_TO_LEVEL.get(norm, None)
    # 4) infer from 'charge' if percentage present
    charge = tech.get("charge") or ""
    if isinstance(charge, str) and "%" in charge:
        nums = [int(n) for n in re.findall(r"(\d{1,3})", charge)]
        if nums:
            avg = sum(nums) / len(nums)
            # thresholds: <55 -> 2, 55-75 -> 3, 75-85 -> 4, >85 -> 5
            if avg < 55:
                return 2
            if 55 <= avg <= 75:
                return 3
            if 75 < avg <= 85:
                return 4
            return 5
    # 5) analyze notes
    notes = tech.get("notes") or ""
    norm = _normalize_difficulty_text(notes)
    if norm:
        return _TEXT_TO_LEVEL.get(norm, None)
    return None


def _get_color_for_tech(tech):
    """
    Retourne un objet reportlab color (colors.HexColor) pour la technique.
    Priorité : difficulty_level -> difficulte -> détection automatique.
    """
    if not REPORTLAB_AVAILABLE:
        return None
    if not tech:
        return colors.white
    lvl = _detect_difficulty_from_tech(tech)
    if isinstance(lvl, int) and lvl in DIFFICULTY_LEVEL_COLORS:
        return DIFFICULTY_LEVEL_COLORS[lvl]
    return colors.white


def _draw_legend(c, x, y, usable_width):
    """
    Dessine la légende des couleurs en haut de la première page.
    Retourne la nouvelle coordonnée y après la légende.
    """
    start_x = x
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(colors.black)
    c.drawString(start_x, y, "Légende difficulté (1→5) :")
    y -= 5 * mm
    c.setFont("Helvetica", 8)
    items = [
        ("1 — Très facile / Endurance", DIFFICULTY_LEVEL_COLORS.get(1)),
        ("2 — Légère", DIFFICULTY_LEVEL_COLORS.get(2)),
        ("3 — Modérée", DIFFICULTY_LEVEL_COLORS.get(3)),
        ("4 — Élevée", DIFFICULTY_LEVEL_COLORS.get(4)),
        ("5 — Très exigeant", DIFFICULTY_LEVEL_COLORS.get(5)),
    ]
    for label, col in items:
        c.setFillColor(col or colors.white)
        c.rect(start_x, y - 4 * mm, 6 * mm, 4 * mm, fill=1, stroke=0)
        c.setFillColor(colors.black)
        c.drawString(start_x + 8 * mm, y - 3.5 * mm, label)
        y -= 6 * mm
    y -= 2 * mm
    return y


def export_program_to_pdf(app, path=None, full_notes=False):
    """
    Exporte la liste Programme (séances) en PDF.
    - Une semaine par page (séparateurs '--- Semaine ... ---' déterminent les blocs).
    - Coloration des lignes selon difficulty_level (1-5) appliquée à la technique.
    - Légende sur la première page.
    - full_notes=False (par défaut) tronque les notes à 300 caractères; si True, inclut notes complètes.
    Retourne le chemin du fichier PDF créé ou None en cas d'erreur.
    """
    if not REPORTLAB_AVAILABLE:
        messagebox.showerror("reportlab manquant", "La bibliothèque reportlab n'est pas installée.\nInstalle-la avec : pip install reportlab")
        return None

    raw_lines = _program_list_to_lines(app)
    if not raw_lines:
        messagebox.showinfo("Vide", "La liste Programme (séances) est vide.")
        return None

    # découper en blocs semaine
    weeks = []
    current_week = {"title": None, "lines": []}
    for ln in raw_lines:
        if isinstance(ln, str) and ln.strip().startswith("---"):
            if current_week["title"] or current_week["lines"]:
                weeks.append(current_week)
            current_week = {"title": ln.strip().strip("- ").strip(), "lines": []}
        else:
            if isinstance(ln, str) and ln.strip() == "":
                continue
            current_week["lines"].append(ln)
    if current_week["title"] or current_week["lines"]:
        weeks.append(current_week)
    if not weeks:
        weeks = [{"title": "Semaine", "lines": raw_lines}]

    if not path:
        default_name = f"programme_{getattr(app, 'selected_user_name', 'user')}_{datetime.date.today().isoformat()}.pdf"
        path = filedialog.asksaveasfilename(title="Exporter Programme en PDF", defaultextension=".pdf", initialfile=default_name, filetypes=[("PDF", "*.pdf")])
        if not path:
            return None

    try:
        c = pdf_canvas.Canvas(path, pagesize=A4)
        width, height = A4
        # marges réduites pour plus de contenu
        margin_left = 14 * mm
        margin_right = 14 * mm
        margin_top = 14 * mm
        margin_bottom = 14 * mm
        usable_width = width - margin_left - margin_right

        # fonts and sizes (reduced)
        title_font_name = "Helvetica-Bold"
        title_font_size = 12
        normal_font_name = "Helvetica"
        normal_font_size = 8.5
        small_font_name = "Helvetica-Oblique"
        small_font_size = 7.5

        # approximate char width for wrapping
        avg_char_width_mm = 2.6 * mm
        max_chars = max(40, int(usable_width / avg_char_width_mm))

        for page_idx, wk in enumerate(weeks):
            c.setFillColor(colors.black)
            y = height - margin_top

            # Page header: title + page number
            c.setFont(title_font_name, title_font_size)
            page_title = f"{wk.get('title') or 'Semaine'} — {getattr(app, 'selected_user_name', '—')}"
            c.drawString(margin_left, y, page_title)
            # page number on right
            c.setFont(normal_font_name, 8)
            c.drawRightString(width - margin_right, y, f"Page {page_idx + 1} / {len(weeks)}")
            y -= 7 * mm

            # On dessine la légende uniquement sur la première page
            if page_idx == 0:
                y = _draw_legend(c, margin_left, y, usable_width)

            # thin separator
            c.setStrokeColor(colors.HexColor("#e5e7eb"))
            c.setLineWidth(0.5)
            c.line(margin_left, y, width - margin_right, y)
            y -= 6 * mm

            # Render each line (jours lun-dim) for this week
            for ln in wk.get("lines", []):
                if y < margin_bottom + 12 * mm:
                    c.showPage()
                    y = height - margin_top
                    c.setFont(title_font_name, title_font_size)
                    c.drawString(margin_left, y, page_title + " (suite)")
                    c.setFont(normal_font_name, 8)
                    c.drawRightString(width - margin_right, y, f"Page {page_idx + 1} / {len(weeks)}")
                    y -= 8 * mm
                    c.setStrokeColor(colors.HexColor("#e5e7eb"))
                    c.setLineWidth(0.5)
                    c.line(margin_left, y, width - margin_right, y)
                    y -= 6 * mm

                text = str(ln).rstrip()

                # determine technique id and fetch technique
                tid = _extract_id_from_line(text)
                tech = tt.find_technique_by_id(tid) if tid else None

                # determine background color based on technique difficulty level
                bg_color = _get_color_for_tech(tech) if tech else colors.white

                # wrap main line
                main_wrapped = _wrap_text_for_width(text, max_chars)
                # build details lines
                details_lines = []
                if tech:
                    cat = tech.get("categorie", "")
                    reps = tech.get("reps", "")
                    charge = tech.get("charge", "")
                    repos = tech.get("repos", "")
                    details_lines.append(f"Catégorie: {cat}  •  Reps: {reps}  •  Charge: {charge}  •  Repos: {repos}")
                    notes = tech.get("notes", "") or ""
                    if notes:
                        if not full_notes:
                            short_notes = notes.strip()
                            if len(short_notes) > 300:
                                short_notes = short_notes[:297].rstrip() + "..."
                            notes = short_notes
                        details_lines.append(f"Notes: {notes}")
                details_wrapped = []
                for d in details_lines:
                    details_wrapped.extend(_wrap_text_for_width(d, max_chars - 6))
                # compute rectangle height for the main line + details
                line_height_mm = normal_font_size * 0.35 * mm * 2.2
                small_line_height_mm = small_font_size * 0.35 * mm * 2.0
                main_height = max(1, len(main_wrapped)) * line_height_mm
                details_height = max(0, len(details_wrapped)) * small_line_height_mm
                rect_padding = 3 * mm
                rect_height = main_height + details_height + rect_padding
                if rect_height < 10 * mm:
                    rect_height = 10 * mm

                # draw background rectangle BEFORE text
                c.setFillColor(bg_color)
                rect_x = margin_left - 2 * mm
                rect_y = y - rect_height + 2 * mm
                rect_w = usable_width + 4 * mm
                c.rect(rect_x, rect_y, rect_w, rect_height, fill=1, stroke=0)

                # draw main text
                tx = margin_left + 1 * mm
                ty = y - 4 * mm
                c.setFillColor(colors.black)
                c.setFont(normal_font_name, normal_font_size)
                for mw in main_wrapped:
                    c.drawString(tx, ty, mw)
                    ty -= line_height_mm
                # draw details in smaller grey font
                if details_wrapped:
                    c.setFont(small_font_name, small_font_size)
                    c.setFillColor(colors.HexColor("#374151"))
                    for dw in details_wrapped:
                        c.drawString(tx + 4 * mm, ty, dw)
                        ty -= small_line_height_mm

                # move y down
                y = rect_y - (2 * mm)

            # finish page
            c.showPage()

        c.save()
        messagebox.showinfo("Exporté", f"Programme exporté en PDF :\n{path}")
        return path
    except Exception as e:
        messagebox.showerror("Erreur PDF", f"Impossible de générer le PDF : {e}")
        return None


def preview_program_pdf(app, full_notes=False):
    """
    Génère un PDF temporaire et l'ouvre avec l'application par défaut.
    """
    if not REPORTLAB_AVAILABLE:
        messagebox.showerror("reportlab manquant", "La bibliothèque reportlab n'est pas installée.\nInstalle-la avec : pip install reportlab")
        return None

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    tmp_path = tmp.name
    tmp.close()
    created = export_program_to_pdf(app, path=tmp_path, full_notes=full_notes)
    if created:
        try:
            webbrowser.open_new(created)
        except Exception:
            messagebox.showinfo("Ouverture", f"PDF créé : {created}")
    else:
        pass


# ----------------- UI principal -----------------


def show_entrainement_screen(app, program=None):
    """
    Fonction exposée pour l'interface principale : construit l'écran complet.
    Doit être appelée depuis l'application principale (ex: entrainement_module.show_entrainement_screen(app)).
    """
    for w in app.content.winfo_children():
        w.destroy()

    tk.Label(
        app.content,
        text=f"ENTRAÎNEMENT - Élève : {getattr(app, 'selected_user_name', '—')}",
        font=("Helvetica", 20, "bold"),
        bg="#f3f4f6",
        fg="#0f172a",
    ).pack(pady=12)

    top = tk.Frame(app.content, bg="#f3f4f6")
    top.pack(fill="x", padx=20)

    tk.Label(top, text="Programme :", bg="#f3f4f6").pack(side="left")
    app.program_selected_var = tk.StringVar(value=program if program else "Standard")
    prog_combo = ttk.Combobox(
        top,
        values=["Standard", "Sarco", "Myofi"],
        textvariable=app.program_selected_var,
        state="readonly",
        width=18,
    )
    prog_combo.pack(side="left", padx=8)
    ttk.Button(top, text="Charger", command=lambda: _load_program(app, app.program_selected_var.get())).pack(
        side="left", padx=6
    )
    ttk.Button(top, text="Retour Dashboard", command=getattr(app, "show_dashboard", lambda: None)).pack(
        side="right"
    )

    view_frame = tk.Frame(app.content, bg="#f3f4f6")
    view_frame.pack(fill="x", padx=20, pady=(6, 0))
    tk.Label(view_frame, text="Vue :", bg="#f3f4f6").pack(side="left")
    app.view_mode_var = tk.StringVar(value="Jour")
    for m in ["Jour", "Semaine", "Mois"]:
        ttk.Radiobutton(view_frame, text=m, value=m, variable=app.view_mode_var, command=lambda: _refresh_schedule_view(app)).pack(
            side="left", padx=6
        )
    app.beginner_mode_var = tk.BooleanVar(value=True)
    cb = tk.Checkbutton(view_frame, text="Mode Débutant", variable=app.beginner_mode_var, bg="#f3f4f6")
    cb.pack(side="right")

    main = tk.Frame(app.content, bg="#f3f4f6")
    main.pack(fill="both", expand=True, padx=20, pady=10)
    main.columnconfigure(0, weight=0)
    main.columnconfigure(1, weight=1)
    main.columnconfigure(2, weight=1)

    # Left: calendar + groupes
    left_zone = tk.Frame(main, bg="#f3f4f6")
    left_zone.grid(row=0, column=0, sticky="ns", padx=(0, 12))
    cal_frame = tk.Frame(left_zone, bg="#f3f4f6")
    cal_frame.pack(pady=8)
    app.calendar = Calendar(cal_frame, selectmode="day")
    app.calendar.pack()
    app.calendar.bind("<<CalendarSelected>>", lambda ev: _on_calendar_select(app))

    groupes_frame = tk.Frame(left_zone, bg="#f3f4f6")
    groupes_frame.pack(anchor="w", pady=(10, 6))
    tk.Label(groupes_frame, text="Groupes musculaires :", font=("Helvetica", 12, "bold"), bg="#f3f4f6").pack(anchor="w")
    app.groupes_vars = {}
    groupes = ["Pecs", "Dos", "Cuisses", "Épaules", "Bras", "Full body", "Alpha body"]
    chk_frame = tk.Frame(groupes_frame, bg="#f3f4f6")
    chk_frame.pack(anchor="w", pady=6)
    for i, g in enumerate(groupes):
        var = tk.BooleanVar()
        cbg = tk.Checkbutton(chk_frame, text=g, variable=var, bg="#f3f4f6", anchor="w")
        cbg.grid(row=i // 2, column=i % 2, sticky="w", padx=8, pady=4)
        app.groupes_vars[g] = var

    # Center: catalogue
    center = tk.Frame(main, bg="#ffffff", bd=1, relief="solid")
    center.grid(row=0, column=1, sticky="nsew", padx=(0, 12), pady=4)
    tk.Label(center, text="Catalogue des techniques", font=("Helvetica", 12, "bold"), bg="#ffffff").pack(anchor="w", padx=8, pady=(8, 4))
    search_frame = tk.Frame(center, bg="#ffffff")
    search_frame.pack(fill="x", padx=8)
    tk.Label(search_frame, text="Rechercher :", bg="#ffffff").pack(side="left")
    app.tech_search_var = tk.StringVar()
    search_entry = ttk.Entry(search_frame, textvariable=app.tech_search_var, width=28)
    search_entry.pack(side="left", padx=6)
    ttk.Button(search_frame, text="Effacer", command=lambda: app.tech_search_var.set("")).pack(side="left", padx=4)
    tree_frame = tk.Frame(center, bg="#ffffff")
    tree_frame.pack(fill="both", expand=True, padx=8, pady=8)
    app.tech_tree = ttk.Treeview(tree_frame, show="tree")
    vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=app.tech_tree.yview)
    app.tech_tree.configure(yscrollcommand=vsb.set)
    app.tech_tree.pack(side="left", fill="both", expand=True)
    vsb.pack(side="right", fill="y")
    app.tech_tree.bind("<<TreeviewSelect>>", lambda ev: _on_tech_select(app))
    app.tech_search_var.trace_add("write", lambda *a: _refresh_tech_tree(app))

    # Right: schedule + detail + programme + history
    right = tk.Frame(main, bg="#ffffff", bd=1, relief="solid")
    right.grid(row=0, column=2, sticky="nsew", pady=4)
    tk.Label(right, text="Planning", font=("Helvetica", 12, "bold"), bg="#ffffff").pack(anchor="w", padx=8, pady=(8, 4))
    app.schedule_listbox = tk.Listbox(right, height=12)
    app.schedule_listbox.pack(fill="both", expand=False, padx=8, pady=(0, 8))
    app.schedule_listbox.bind("<Double-1>", lambda ev: _on_schedule_double_click(app))

    schedule_btn_frame = tk.Frame(right, bg="#ffffff")
    schedule_btn_frame.pack(fill="x", padx=8, pady=(0, 8))
    ttk.Button(schedule_btn_frame, text="Ajouter à la date sélectionnée", command=lambda: _add_selected_to_selected_date(app)).pack(side="left", padx=6)
    ttk.Button(schedule_btn_frame, text="Assigner la date sélectionnée", command=lambda: _assign_date_to_entry(app)).pack(side="left", padx=6)
    ttk.Button(schedule_btn_frame, text="Supprimer sélection", command=lambda: _delete_selected_schedule_item(app)).pack(side="left", padx=6)
    ttk.Button(schedule_btn_frame, text="Charger template Sarco", command=lambda: _load_program(app, "Sarco")).pack(side="left", padx=6)

    tk.Label(right, text="Détail (Mode Débutant si activé)", font=("Helvetica", 12, "bold"), bg="#ffffff").pack(anchor="w", padx=8, pady=(4, 4))
    app.detail_text = tk.Text(right, height=10, wrap="word")
    app.detail_text.pack(fill="both", expand=True, padx=8, pady=(0, 8))
    app.detail_text.config(state="disabled")

    tk.Label(right, text="Programme (séances)", font=("Helvetica", 12, "bold"), bg="#ffffff").pack(anchor="w", padx=8, pady=(4, 4))
    app.program_listbox = tk.Listbox(right, height=8)
    app.program_listbox.pack(fill="both", expand=True, padx=8, pady=(0, 8))
    app.program_listbox.bind("<Double-1>", lambda ev: _on_program_list_double_click(app))

    prog_btn_frame = tk.Frame(right, bg="#ffffff")
    prog_btn_frame.pack(anchor="w", pady=8, padx=8)
    ttk.Button(prog_btn_frame, text="Ajouter technique sélectionnée", command=lambda: _add_selected_tech_to_program(app)).pack(side="left", padx=6)
    ttk.Button(prog_btn_frame, text="Supprimer", command=lambda: _remove_selected_program_item(app)).pack(side="left", padx=6)
    ttk.Button(prog_btn_frame, text="Charger template", command=lambda: _load_program(app, app.program_selected_var.get())).pack(side="left", padx=6)

    # --- Générateur de programme mensuel (UI) ---
    gen_frame = tk.Frame(right, bg="#ffffff")
    gen_frame.pack(fill="x", padx=8, pady=(4, 8))
    tk.Label(gen_frame, text="Générer programme mensuel :", bg="#ffffff").pack(anchor="w")

    # Cases à cocher catégories
    app.gen_cat_sarco = tk.BooleanVar(value=True)
    app.gen_cat_mixte = tk.BooleanVar(value=True)
    app.gen_cat_myofi = tk.BooleanVar(value=True)
    chk_frame = tk.Frame(gen_frame, bg="#ffffff")
    chk_frame.pack(anchor="w", pady=4)
    tk.Checkbutton(chk_frame, text="Sarcoplasmique", variable=app.gen_cat_sarco, bg="#ffffff").grid(row=0, column=0, sticky="w", padx=4)
    tk.Checkbutton(chk_frame, text="Mixte", variable=app.gen_cat_mixte, bg="#ffffff").grid(row=0, column=1, sticky="w", padx=4)
    tk.Checkbutton(chk_frame, text="Myofibrillaire", variable=app.gen_cat_myofi, bg="#ffffff").grid(row=0, column=2, sticky="w", padx=4)

    # Week-end option
    app.gen_weekend_mode = tk.StringVar(value="Off")
    wk_frame = tk.Frame(gen_frame, bg="#ffffff")
    wk_frame.pack(anchor="w", pady=2)
    ttk.Radiobutton(wk_frame, text="Off", value="Off", variable=app.gen_weekend_mode).pack(side="left", padx=6)
    ttk.Radiobutton(wk_frame, text="Entraînement", value="Train", variable=app.gen_weekend_mode).pack(side="left", padx=6)

    # Boutons générer + PDF
    btns_frame = tk.Frame(gen_frame, bg="#ffffff")
    btns_frame.pack(anchor="w", pady=6)
    ttk.Button(btns_frame, text="Générer pour le mois sélectionné", command=lambda: generate_month_program(app)).pack(side="left", padx=6)
    ttk.Button(btns_frame, text="Générer l'intégralité (rotation)", command=lambda: generate_full_rotation_program(app)).pack(side="left", padx=6)
    ttk.Button(btns_frame, text="Tout effacer", command=lambda: _clear_program_list(app)).pack(side="left", padx=6)
    ttk.Button(btns_frame, text="Visualiser PDF", command=lambda: preview_program_pdf(app)).pack(side="left", padx=6)
    ttk.Button(btns_frame, text="Exporter en PDF", command=lambda: export_program_to_pdf(app)).pack(side="left", padx=6)
    # --- fin générateur ---

    # Notes and save
    app.note_text = tk.Text(app.content, height=4, width=120)
    app.note_text.pack(padx=20, pady=(6, 12))
    ttk.Button(app.content, text="SAUVEGARDER ENTRAÎNEMENT", command=lambda: _sauvegarder_entrainement(app)).pack(pady=8)

    # ----------------- Integrated History Panel (visible in the screen) -----------------
    hist_frame = ttk.Frame(right)
    hist_frame.pack(fill="both", expand=True, padx=8, pady=(8, 12))
    ttk.Label(hist_frame, text="Historique des séances", font=("Helvetica", 12, "bold")).pack(anchor="w", pady=(0, 6))

    hist_inner = ttk.Frame(hist_frame)
    hist_inner.pack(fill="both", expand=True)

    left_hist = ttk.Frame(hist_inner, width=260)
    left_hist.pack(side="left", fill="y", padx=(0, 8), pady=4)
    app.history_listbox = tk.Listbox(left_hist, height=12)
    app.history_listbox.pack(fill="both", expand=True)
    hist_btns = ttk.Frame(left_hist)
    hist_btns.pack(fill="x", pady=6)
    ttk.Button(hist_btns, text="Voir", command=lambda: _history_view_selected_inline(app)).pack(side="left", padx=4)
    ttk.Button(hist_btns, text="Supprimer", command=lambda: _history_delete_selected_inline(app)).pack(side="left", padx=4)
    ttk.Button(hist_btns, text="Actualiser", command=lambda: _history_refresh(app.history_listbox, app)).pack(side="left", padx=4)

    right_hist = ttk.Frame(hist_inner)
    right_hist.pack(side="left", fill="both", expand=True)
    ttk.Label(right_hist, text="Détail séance", font=("Helvetica", 12, "bold")).pack(anchor="w", pady=(0, 6))
    app.history_detail = tk.Text(right_hist, wrap="word", state="disabled", height=10)
    app.history_detail.pack(fill="both", expand=True)

    hist_top_btns = tk.Frame(hist_frame)
    hist_top_btns.pack(fill="x", pady=(6, 0))
    ttk.Button(hist_top_btns, text="Importer", command=lambda: _history_import(app.content, app)).pack(side="left", padx=6)
    ttk.Button(hist_top_btns, text="Exporter", command=lambda: _history_export(app.content, app)).pack(side="left", padx=6)

    app.history_listbox.bind("<<ListboxSelect>>", lambda ev: _history_on_select_inline(app))

    app._schedule_entries = _read_schedule(app)
    try:
        today = datetime.date.today()
        app.calendar.selection_set(today)
    except Exception:
        pass
    _refresh_tech_tree(app)
    _refresh_schedule_view(app)
    _load_program(app, app.program_selected_var.get())
    _history_refresh(app.history_listbox, app)


# ----------------- catalogue and other UI helpers -----------------


def _refresh_tech_tree(app):
    tree = app.tech_tree
    for iid in tree.get_children():
        tree.delete(iid)
    query = app.tech_search_var.get().lower().strip()
    all_tech = tt.get_all_techniques()
    cats = {"SARCOPLASMIQUE": [], "MIXTE": [], "MYOFIBRILLAIRE": []}
    for t in all_tech:
        cats.setdefault((t.get("categorie") or "").upper(), []).append(t)
    for cat in ["SARCOPLASMIQUE", "MIXTE", "MYOFIBRILLAIRE"]:
        items = cats.get(cat, [])
        if not items:
            continue
        parent = tree.insert("", "end", text=f"{cat} ({len(items)})", open=True)
        for t in items:
            label = _format_tech_label(t)
            if query:
                hay = " ".join([t.get("nom", ""), t.get("id", ""), t.get("reps", ""), t.get("notes", "")]).lower()
                if query not in hay:
                    continue
            tree.insert(parent, "end", text=label, values=(t["id"],), tags=(t["id"],))


def _on_tech_select(app):
    sel = app.tech_tree.selection()
    if not sel:
        return
    text = app.tech_tree.item(sel[0], "text")
    tid = None
    if "(" in text and ")" in text:
        tid = text.split("(")[-1].split(")")[0].strip()
    if not tid:
        tags = app.tech_tree.item(sel[0], "tags") or []
        if tags:
            tid = tags[0]
    tech = tt.find_technique_by_id(tid) if tid else None
    app._last_selected_tech_id = tech["id"] if tech else None
    if getattr(app, "beginner_mode_var", tk.BooleanVar(value=False)).get():
        text_block = _get_beginner_text(tid, tech) if tech else "Sélectionne une technique pour voir les explications simples."
    else:
        if tech:
            text_block = (
                f"{tech.get('nom','—')}\n\nReps: {tech.get('reps','—')}\nCharge: {tech.get('charge','—')}\nRepos: {tech.get('repos','—')}\nObjectif: {tech.get('objectif','—')}\n\nNotes:\n{tech.get('notes','')}"
            )
        else:
            text_block = "Sélectionne une technique pour voir le détail."
    app.detail_text.config(state="normal")
    app.detail_text.delete("1.0", tk.END)
    app.detail_text.insert("1.0", text_block)
    app.detail_text.config(state="disabled")


# ----------------- schedule view and actions (add/assign/delete) -----------------


def _on_calendar_select(app):
    _refresh_schedule_view(app)


def _refresh_schedule_view(app):
    app._schedule_entries = _read_schedule(app)
    mode = app.view_mode_var.get() if hasattr(app, "view_mode_var") else "Jour"
    try:
        sel_date = app.calendar.selection_get()
        if not isinstance(sel_date, datetime.date):
            sel_date = datetime.datetime.strptime(app.calendar.get_date(), DATE_FORMAT).date()
    except Exception:
        sel_date = datetime.date.today()
    app._selected_date = sel_date
    app.schedule_listbox.delete(0, tk.END)

    def _insert_line(text):
        app.schedule_listbox.insert(tk.END, text)

    if mode == "Jour":
        date_str = sel_date.strftime(DATE_FORMAT)
        entries = [e for e in app._schedule_entries if e.get("date") == date_str]
        undated = [e for e in app._schedule_entries if e.get("date") is None]
        if not entries:
            _insert_line(f"Aucune séance programmée pour {date_str}")
        else:
            for e in entries:
                display = f"{date_str} — {e.get('line') or e.get('program') or e.get('types')}"
                _insert_line(display)
        if undated:
            _insert_line("")
            _insert_line("Entrées sans date (sélectionne et clique 'Assigner la date sélectionnée') :")
            for e in undated:
                _insert_line("[Sans date] " + (e.get('line') or e.get('program') or "—"))
    elif mode == "Semaine":
        start = sel_date - datetime.timedelta(days=sel_date.weekday())
        days = [start + datetime.timedelta(days=i) for i in range(7)]
        for d in days:
            ds = d.strftime(DATE_FORMAT)
            day_entries = [e for e in app._schedule_entries if e.get("date") == ds]
            _insert_line(f"--- {ds} ({d.strftime('%a')}) ---")
            if not day_entries:
                _insert_line(" (aucune)")
            else:
                for e in day_entries:
                    display = f"{ds} — {e.get('line') or e.get('program') or e.get('types')}"
                    _insert_line(" " + display)
        undated = [e for e in app._schedule_entries if e.get("date") is None]
        if undated:
            _insert_line("")
            _insert_line("Entrées sans date :")
            for e in undated:
                _insert_line(" [Sans date] " + (e.get("line") or ""))
    else:  # Mois
        first = sel_date.replace(day=1)
        next_month = first.replace(day=28) + datetime.timedelta(days=4)
        last = next_month - datetime.timedelta(days=next_month.day)
        for day in range(1, last.day + 1):
            d = first.replace(day=day)
            ds = d.strftime(DATE_FORMAT)
            day_entries = [e for e in app._schedule_entries if e.get("date") == ds]
            if day_entries:
                _insert_line(f"--- {ds} ---")
                for e in day_entries:
                    display = f"{ds} — {e.get('line') or e.get('program') or e.get('types')}"
                    _insert_line(" " + display)
        undated = [e for e in app._schedule_entries if e.get("date") is None]
        if undated:
            _insert_line("")
            _insert_line("Entrées sans date :")
            for e in undated:
                _insert_line(" [Sans date] " + (e.get("line") or ""))


def _add_selected_to_selected_date(app):
    tid = getattr(app, "_last_selected_tech_id", None)
    if not tid:
        messagebox.showinfo("Info", "Sélectionne une technique dans le catalogue.")
        return
    tech = tt.find_technique_by_id(tid)
    if not tech:
        messagebox.showerror("Erreur", "Technique introuvable.")
        return
    try:
        sel_date = app.calendar.selection_get()
        if not isinstance(sel_date, datetime.date):
            sel_date = datetime.datetime.strptime(app.calendar.get_date(), DATE_FORMAT).date()
    except Exception:
        sel_date = datetime.date.today()
    date_str = sel_date.strftime(DATE_FORMAT)
    groupes = ", ".join([g for g, v in app.groupes_vars.items() if v.get()]) if getattr(app, "groupes_vars", None) else ""
    program = app.program_selected_var.get() if hasattr(app, "program_selected_var") else ""
    types = f"{tech.get('categorie','')}"
    line = f"{tech['nom']} [{tech.get('reps','—')}] | {tech.get('charge','—')} ({tech['id']})"
    _write_schedule_entry(app, date_str, line, groupes=groupes, program=program, types=types, note="")
    app._schedule_entries = _read_schedule(app)
    _refresh_schedule_view(app)
    messagebox.showinfo("Ajouté", f"Technique ajoutée pour le {date_str}.")


def _assign_date_to_entry(app):
    sel = app.schedule_listbox.curselection()
    if not sel:
        messagebox.showinfo("Info", "Sélectionne d'abord une ligne sans date.")
        return
    idx = sel[0]
    text = app.schedule_listbox.get(idx)
    if not text or "[Sans date]" not in text:
        messagebox.showinfo("Info", "Sélectionne une entrée marquée [Sans date].")
        return
    line_text = text.split("[Sans date]")[-1].strip()
    try:
        sel_date = app.calendar.selection_get()
        if not isinstance(sel_date, datetime.date):
            sel_date = datetime.datetime.strptime(app.calendar.get_date(), DATE_FORMAT).date()
    except Exception:
        sel_date = datetime.date.today()
    date_str = sel_date.strftime(DATE_FORMAT)
    fichier = _schedule_file_for_user(app)
    if not os.path.exists(fichier):
        messagebox.showerror("Erreur", "Fichier introuvable.")
        return
    try:
        with open(fichier, "r", newline="", encoding="utf-8") as f:
            rows = list(csv.reader(f))
            header = rows[0] if rows else []
            data = rows[1:] if len(rows) > 1 else []
        updated = False
        for i, r in enumerate(data):
            line_field = r[5] if len(r) > 5 else ""
            date_field = r[0] if len(r) > 0 else ""
            if (not date_field or date_field.strip() == "") and line_field.strip() == line_text:
                while len(r) < 6:
                    r.append("")
                r[0] = date_str
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
            app._schedule_entries = _read_schedule(app)
            _refresh_schedule_view(app)
            try:
                _update_history_planned_for(app, line_text, date_str)
            except Exception:
                pass
            messagebox.showinfo("Succès", f"Date assignée : {date_str}")
        else:
            messagebox.showerror("Erreur", "Impossible de trouver l'entrée correspondante dans le fichier.")
    except Exception as e:
        messagebox.showerror("Erreur", f"Impossible d'assigner la date : {e}")


def _delete_selected_schedule_item(app):
    sel = app.schedule_listbox.curselection()
    if not sel:
        messagebox.showinfo("Info", "Sélectionne une ligne du planning à supprimer.")
        return
    idx = sel[0]
    text = app.schedule_listbox.get(idx)
    mode = app.view_mode_var.get() if hasattr(app, "view_mode_var") else "Jour"
    if mode == "Jour":
        try:
            sel_date = app.calendar.selection_get()
            if not isinstance(sel_date, datetime.date):
                sel_date = datetime.datetime.strptime(app.calendar.get_date(), DATE_FORMAT).date()
        except Exception:
            sel_date = datetime.date.today()
        date_str = sel_date.strftime(DATE_FORMAT)
        if text.startswith("Aucune séance"):
            return
        if "[Sans date]" in text:
            line_text = text.split("[Sans date]")[-1].strip()
            _delete_schedule_entry(app, "", line_text)
        else:
            if "—" in text:
                parts = text.split("—", 1)
                line_text = parts[1].strip() if len(parts) > 1 else text.strip()
            else:
                line_text = text.strip()
            _delete_schedule_entry(app, date_str, line_text)
        app._schedule_entries = _read_schedule(app)
        _refresh_schedule_view(app)
        messagebox.showinfo("Supprimé", "La séance a été supprimée.")
    else:
        list_items = app.schedule_listbox.get(0, tk.END)
        date_str = None
        for i in range(idx, -1, -1):
            it = list_items[i]
            if it.startswith("--- ") and it.endswith(" ---"):
                date_str = it.strip().strip("- ").strip()
                break
        if not date_str:
            messagebox.showerror("Erreur", "Impossible d'identifier la date de la ligne sélectionnée.")
            return
        line_text = text.strip()
        if line_text == "(aucune)":
            return
        if line_text.startswith("[Sans date]"):
            line_text = line_text.split("[Sans date]")[-1].strip()
            _delete_schedule_entry(app, "", line_text)
        else:
            if "—" in line_text:
                parts = line_text.split("—", 1)
                line_text = parts[1].strip() if len(parts) > 1 else line_text
            _delete_schedule_entry(app, date_str, line_text)
        app._schedule_entries = _read_schedule(app)
        _refresh_schedule_view(app)
        messagebox.showinfo("Supprimé", f"Entrée supprimée pour {date_str}.")


def _on_schedule_double_click(app):
    sel = app.schedule_listbox.curselection()
    if not sel:
        return
    text = app.schedule_listbox.get(sel[0])
    if text.startswith("---") or text.strip().startswith("(aucune)") or text.startswith("Aucune séance"):
        return
    tid = None
    if "(" in text and ")" in text:
        try:
            tid = text.split("(")[-1].split(")")[0].strip()
        except Exception:
            tid = None
    tech = tt.find_technique_by_id(tid) if tid else None
    if tech:
        _open_tech_detail_dialog(app, tech)
    else:
        dlg = tk.Toplevel()
        dlg.title("Détail")
        dlg.transient(app.root if hasattr(app, "root") else app.content)
        tk.Label(dlg, text=text, wraplength=600, justify="left").pack(padx=12, pady=12)
        ttk.Button(dlg, text="Fermer", command=dlg.destroy).pack(pady=(0, 12))


# ----------------- program templates and other helpers -----------------


def _on_program_change(app):
    if not hasattr(app, "program_listbox"):
        return
    _load_program(app, app.program_selected_var.get())


def _load_program(app, name):
    if not hasattr(app, "program_listbox"):
        return
    app.program_listbox.delete(0, tk.END)
    if name in ["Sarco", "Myofi"]:
        template = tt.build_program_template(name, weeks=4)
        for w in template["weeks"]:
            app.program_listbox.insert(tk.END, f"--- Semaine {w['week']} ---")
            for s in w["sessions"]:
                app.program_listbox.insert(tk.END, f" Séance {s['session']}")
                for ex in s["exercises"]:
                    tech = tt.find_technique_by_id(ex["id"])
                    if tech:
                        line = f" {tech['nom']} [{tech['reps']}] | {tech['charge']} ({tech['id']})"
                    else:
                        line = f" {ex.get('nom','—')} [{ex.get('reps','—')}]"
                    app.program_listbox.insert(tk.END, line)
    else:
        app.program_listbox.insert(tk.END, "Standard - Jour A : Pecs/Dos 4x8-10")
        app.program_listbox.insert(tk.END, "Standard - Jour B : Jambes 4x8-10")
        app.program_listbox.insert(tk.END, "Standard - Jour C : Épaules/Arms 4x8-10")


def _collect_tech_pool(categories):
    all_tech = tt.get_all_techniques()
    wanted = set([c.upper() for c in categories])
    pool = []
    seen = set()
    for t in all_tech:
        cat = (t.get("categorie") or "").upper()
        tid = t.get("id")
        if not tid:
            continue
        if cat in wanted and tid not in seen:
            pool.append(t)
            seen.add(tid)
    return pool


def generate_month_program(app):
    try:
        sel_date = app.calendar.selection_get()
        if not isinstance(sel_date, datetime.date):
            sel_date = datetime.datetime.strptime(app.calendar.get_date(), DATE_FORMAT).date()
    except Exception:
        sel_date = datetime.date.today()
    year = sel_date.year
    month = sel_date.month

    cats = []
    if getattr(app, "gen_cat_sarco", tk.BooleanVar()).get():
        cats.append("SARCOPLASMIQUE")
    if getattr(app, "gen_cat_mixte", tk.BooleanVar()).get():
        cats.append("MIXTE")
    if getattr(app, "gen_cat_myofi", tk.BooleanVar()).get():
        cats.append("MYOFIBRILLAIRE")
    if not cats:
        messagebox.showwarning("Catégories", "Sélectionne au moins une catégorie.")
        return

    pool = _collect_tech_pool(cats)
    if not pool:
        messagebox.showwarning("Pool vide", "Aucune technique trouvée pour les catégories sélectionnées.")
        return

    day_to_group = {0: "Pectoraux", 1: "Cuisses", 2: "Épaules", 3: "Dos", 4: "Bras"}

    app.program_listbox.delete(0, tk.END)

    rotation_iter = _RotationIterator(pool)

    cal = calendar.Calendar(firstweekday=0)
    month_weeks = cal.monthdatescalendar(year, month)

    for week_idx, week in enumerate(month_weeks, start=1):
        weekly_id = rotation_iter.next()
        weekly_tech = tt.find_technique_by_id(weekly_id) if weekly_id else None

        app.program_listbox.insert(tk.END, f"--- Semaine {week_idx} ---")
        for d in week:
            if d.month != month:
                continue
            weekday = d.weekday()
            if weekday in day_to_group:
                group = day_to_group[weekday]
                if weekly_tech:
                    line = f"{d.strftime(DATE_FORMAT)} - {group} : {weekly_tech['nom']} [{weekly_tech.get('reps','—')}] | {weekly_tech.get('charge','—')} ({weekly_tech['id']})"
                else:
                    line = f"{d.strftime(DATE_FORMAT)} - {group} : (technique manquante)"
                app.program_listbox.insert(tk.END, line)
            else:
                if app.gen_weekend_mode.get() == "Train":
                    if weekly_tech:
                        line = f"{d.strftime(DATE_FORMAT)} - Week-end : {weekly_tech['nom']} [{weekly_tech.get('reps','—')}] | {weekly_tech.get('charge','—')} ({weekly_tech['id']})"
                    else:
                        line = f"{d.strftime(DATE_FORMAT)} - Week-end : (technique manquante)"
                    app.program_listbox.insert(tk.END, line)
                else:
                    app.program_listbox.insert(tk.END, f"{d.strftime(DATE_FORMAT)} - Week-end : Off")
    messagebox.showinfo("Génération terminée", "Programme mensuel généré dans la liste Programme (séances).")


def generate_full_rotation_program(app):
    try:
        sel_date = app.calendar.selection_get()
        if not isinstance(sel_date, datetime.date):
            sel_date = datetime.datetime.strptime(app.calendar.get_date(), DATE_FORMAT).date()
    except Exception:
        sel_date = datetime.date.today()

    cats = []
    if getattr(app, "gen_cat_sarco", tk.BooleanVar()).get():
        cats.append("SARCOPLASMIQUE")
    if getattr(app, "gen_cat_mixte", tk.BooleanVar()).get():
        cats.append("MIXTE")
    if getattr(app, "gen_cat_myofi", tk.BooleanVar()).get():
        cats.append("MYOFIBRILLAIRE")
    if not cats:
        messagebox.showwarning("Catégories", "Sélectionne au moins une catégorie.")
        return

    pool = _collect_tech_pool(cats)
    if not pool:
        messagebox.showwarning("Pool vide", "Aucune technique trouvée pour les catégories sélectionnées.")
        return

    rotation_ids = _build_rotation_from_pool(pool)
    if not rotation_ids:
        messagebox.showwarning("Rotation", "Impossible de construire la rotation.")
        return

    sel_monday = sel_date - datetime.timedelta(days=sel_date.weekday())

    day_to_group = {0: "Pectoraux", 1: "Cuisses", 2: "Épaules", 3: "Dos", 4: "Bras"}

    app.program_listbox.delete(0, tk.END)

    for week_offset, tech_id in enumerate(rotation_ids, start=0):
        week_start = sel_monday + datetime.timedelta(weeks=week_offset)
        week_num_label = f"Semaine {week_start.isocalendar()[1]} (+{week_offset})"
        app.program_listbox.insert(tk.END, f"--- {week_num_label} ---")
        tech = tt.find_technique_by_id(tech_id) if tech_id else None
        for weekday in range(0, 7):
            d = week_start + datetime.timedelta(days=weekday)
            if weekday in day_to_group:
                group = day_to_group[weekday]
                if tech:
                    line = f"{d.strftime(DATE_FORMAT)} - {group} : {tech['nom']} [{tech.get('reps','—')}] | {tech.get('charge','—')} ({tech['id']})"
                else:
                    line = f"{d.strftime(DATE_FORMAT)} - {group} : (technique manquante)"
                app.program_listbox.insert(tk.END, line)
            else:
                if app.gen_weekend_mode.get() == "Train":
                    if tech:
                        line = f"{d.strftime(DATE_FORMAT)} - Week-end : {tech['nom']} [{tech.get('reps','—')}] | {tech.get('charge','—')} ({tech['id']})"
                    else:
                        line = f"{d.strftime(DATE_FORMAT)} - Week-end : (technique manquante)"
                    app.program_listbox.insert(tk.END, line)
                else:
                    app.program_listbox.insert(tk.END, f"{d.strftime(DATE_FORMAT)} - Week-end : Off")

    messagebox.showinfo("Génération intégrale", f"Génération complète terminée : {len(rotation_ids)} semaine(s) ajoutée(s).")


def _clear_program_list(app):
    if not messagebox.askyesno("Confirmer", "Effacer toute la liste Programme (séances) ?"):
        return
    app.program_listbox.delete(0, tk.END)
    messagebox.showinfo("Effacé", "La liste Programme (séances) a été effacée.")


def _add_selected_tech_to_program(app):
    tid = getattr(app, "_last_selected_tech_id", None)
    if not tid:
        messagebox.showinfo("Info", "Sélectionne une technique dans le catalogue.")
        return
    tech = tt.find_technique_by_id(tid)
    line = f"{tech['nom']} [{tech.get('reps','—')}] | {tech.get('charge','—')} ({tech['id']})"
    app.program_listbox.insert(tk.END, line)


def _remove_selected_program_item(app):
    sel = app.program_listbox.curselection()
    if not sel:
        return
    for i in reversed(sel):
        app.program_listbox.delete(i)


def _on_program_list_double_click(app):
    sel = app.program_listbox.curselection()
    if not sel:
        return
    line = app.program_listbox.get(sel[0])
    tid = None
    if "(" in line and ")" in line:
        tid = line.split("(")[-1].split(")")[0].strip()
    tech = tt.find_technique_by_id(tid) if tid else None
    if tech:
        _open_tech_detail_dialog(app, tech)
    else:
        dlg = tk.Toplevel()
        dlg.title("Détail")
        dlg.transient(app.root if hasattr(app, "root") else app.content)
        tk.Label(dlg, text=line, wraplength=600, justify="left").pack(padx=12, pady=12)
        ttk.Button(dlg, text="Fermer", command=dlg.destroy).pack(pady=(0, 12))


def _open_tech_detail_dialog(app, tech):
    dlg = tk.Toplevel()
    dlg.title(tech["nom"])
    dlg.geometry("520x520")
    tk.Label(dlg, text=tech["nom"], font=("Helvetica", 14, "bold")).pack(pady=8)
    tk.Label(dlg, text=f"ID : {tech['id']}").pack()
    tk.Label(dlg, text=f"Catégorie : {tech['categorie']}").pack()
    tk.Label(dlg, text=f"Reps : {tech['reps']}").pack()
    tk.Label(dlg, text=f"Charge : {tech['charge']}").pack()
    tk.Label(dlg, text=f"Repos : {tech['repos']}").pack()
    tk.Label(dlg, text=f"Objectif : {tech['objectif']}").pack()
    tk.Label(dlg, text="Notes :", font=("Helvetica", 12, "bold")).pack(pady=(10, 0))
    txt = tk.Text(dlg, height=10, width=64, wrap="word")
    txt.pack(padx=8, pady=(4, 8))
    if getattr(app, "beginner_mode_var", tk.BooleanVar(value=False)).get():
        txt.insert("1.0", _get_beginner_text(tech.get("id"), tech) + "\n\n---\n\nDétails techniques complets :\n" + tech.get("notes", ""))
    else:
        txt.insert("1.0", tech.get("notes", ""))
    txt.config(state="disabled")
    ttk.Button(dlg, text="Fermer", command=dlg.destroy).pack(pady=8)


# ----------------- save whole training -----------------


def _sauvegarder_entrainement(app):
    if not getattr(app, "current_user", None) and not getattr(app, "selected_user_name", None):
        messagebox.showerror("Erreur", "Sélectionne un élève d'abord")
        return
    try:
        sel_date = app.calendar.selection_get()
        if not isinstance(sel_date, datetime.date):
            sel_date = datetime.datetime.strptime(app.calendar.get_date(), DATE_FORMAT).date()
    except Exception:
        sel_date = datetime.date.today()
    date_str = sel_date.strftime(DATE_FORMAT)
    groupes = ", ".join([g for g, v in app.groupes_vars.items() if v.get()]) if getattr(app, "groupes_vars", None) else ""
    program = app.program_selected_var.get() if hasattr(app, "program_selected_var") else ""
    note = app.note_text.get("1.0", tk.END).strip()
    raw_lines = [app.program_listbox.get(i) for i in range(app.program_listbox.size())] if hasattr(app, "program_listbox") else []
    lines = []
    for ln in raw_lines:
        s = ln.strip()
        if not s:
            continue
        if s.startswith("---") or s.lower().startswith("standard -") or s.strip().startswith("Séance"):
            continue
        lines.append(s)
    for line in lines:
        _write_schedule_entry(app, date_str, line, groupes=groupes, program=program, types="", note=note)

    app._schedule_entries = _read_schedule(app)
    _refresh_schedule_view(app)
    messagebox.showinfo("Succès", f"{len(lines)} ligne(s) sauvegardées pour {date_str}.")


# ----------------- History inline handlers -----------------


def _history_refresh(listbox, app):
    listbox.delete(0, tk.END)
    user = _get_current_user(app)
    if not user:
        listbox.insert(tk.END, "(Aucun profil sélectionné)")
        return
    history = _load_training_history(app)
    if not history:
        listbox.insert(tk.END, "(Aucun historique)")
        return
    for entry in history:
        date = entry.get("date", "inconnue")
        typ = entry.get("type", "général")
        dur = entry.get("duration", "")
        label = f"{date} — {typ}"
        if dur:
            label += f" — {dur}"
        listbox.insert(tk.END, label)


def _history_show_detail(detail_widget, entry):
    detail_widget.configure(state="normal")
    detail_widget.delete("1.0", tk.END)
    lines = []
    lines.append(f"Date : {entry.get('date','-')}")
    lines.append(f"Type : {entry.get('type','-')}")
    if "duration" in entry:
        lines.append(f"Durée : {entry.get('duration')}")
    if "notes" in entry and entry.get("notes"):
        lines.append("")
        lines.append("Notes :")
        lines.append(entry.get("notes", ""))
    if "exercises" in entry and isinstance(entry["exercises"], list):
        lines.append("")
        lines.append("Exercices :")
        for ex in entry["exercises"]:
            if isinstance(ex, dict):
                name = ex.get("name", "?")
                sets = ex.get("sets", "")
                reps = ex.get("reps", "")
                lines.append(f"- {name} — sets: {sets} reps: {reps}")
            else:
                lines.append(f"- {ex}")
    if entry.get("planned_for"):
        lines.append("")
        lines.append(f"Planifiée pour : {entry.get('planned_for')}")
    detail_widget.insert(tk.END, "\n".join(lines))
    detail_widget.configure(state="disabled")


def _history_on_select_inline(app):
    sel = app.history_listbox.curselection()
    if not sel:
        return
    idx = sel[0]
    history = _load_training_history(app)
    if idx >= len(history):
        return
    entry = history[idx]
    _history_show_detail(app.history_detail, entry)


def _history_view_selected_inline(app):
    sel = app.history_listbox.curselection()
    if not sel:
        messagebox.showinfo("Sélection", "Sélectionnez une séance dans l'historique.")
        return
    idx = sel[0]
    history = _load_training_history(app)
    if idx >= len(history):
        messagebox.showerror("Erreur", "Sélection invalide.")
        return
    entry = history[idx]
    _history_show_detail(app.history_detail, entry)


def _history_delete_selected_inline(app):
    sel = app.history_listbox.curselection()
    if not sel:
        messagebox.showinfo("Sélection", "Sélectionnez une séance à supprimer.")
        return
    idx = sel[0]
    if not messagebox.askyesno("Confirmer", "Supprimer la séance sélectionnée ?"):
        return
    ok = _delete_training_entry(app, idx)
    if ok:
        messagebox.showinfo("Supprimé", "Séance supprimée.")
        _history_refresh(app.history_listbox, app)
        app.history_detail.configure(state="normal")
        app.history_detail.delete("1.0", tk.END)
        app.history_detail.configure(state="disabled")
    else:
        messagebox.showerror("Erreur", "Impossible de supprimer la séance.")


def _history_import(parent, app):
    user = _get_current_user(app)
    if not user:
        messagebox.showwarning("Profil requis", "Sélectionnez ou créez un profil avant d'importer.")
        return
    path = filedialog.askopenfilename(title="Importer séance (JSON)", filetypes=[("JSON", "*.json"), ("All", "*.*")])
    if not path:
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            data.setdefault("date", datetime.datetime.now().strftime(HISTORY_TIMESTAMP_FORMAT))
            if data.get("planned_for"):
                data["planned_for"] = _parse_date_flexible_to_display(str(data["planned_for"]))
            _add_training_entry(app, data)
            messagebox.showinfo("Importé", "Séance importée.")
        elif isinstance(data, list):
            for e in data:
                if isinstance(e, dict):
                    e.setdefault("date", datetime.datetime.now().strftime(HISTORY_TIMESTAMP_FORMAT))
                    if e.get("planned_for"):
                        e["planned_for"] = _parse_date_flexible_to_display(str(e["planned_for"]))
                    _add_training_entry(app, e)
            messagebox.showinfo("Importé", "Historique importé.")
        else:
            messagebox.showerror("Format", "Fichier JSON non reconnu.")
    except Exception as e:
        messagebox.showerror("Erreur", f"Impossible d'importer: {e}")
    if hasattr(app, "history_listbox"):
        _history_refresh(app.history_listbox, app)


def _history_export(parent, app):
    user = _get_current_user(app)
    if not user:
        messagebox.showwarning("Profil requis", "Sélectionnez ou créez un profil avant d'exporter.")
        return
    history = _load_training_history(app)
    if not history:
        messagebox.showinfo("Vide", "Aucun historique à exporter.")
        return
    path = filedialog.asksaveasfilename(title="Exporter historique", defaultextension=".json", filetypes=[("JSON", "*.json")])
    if not path:
        return
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        messagebox.showinfo("Exporté", f"Historique exporté vers {path}")
    except Exception as e:
        messagebox.showerror("Erreur", f"Impossible d'exporter: {e}")


# End of module

