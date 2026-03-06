# data/entrainement_pdf.py
# -*- coding: utf-8 -*-
"""
Export et prévisualisation PDF du programme d'entraînement.
Utilise reportlab (optionnel).
"""

import re
import textwrap
import tempfile
import webbrowser
import datetime

try:
    from reportlab.pdfgen import canvas as pdf_canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except Exception:
    REPORTLAB_AVAILABLE = False

# Import léger — on évite d'importer training_techniques ici pour garder ce module indépendant
try:
    from data import training_techniques as tt
    _TT_AVAILABLE = True
except Exception:
    _TT_AVAILABLE = False


# ── Couleurs par niveau de difficulté (1→5) ───────────────────────────────────
if REPORTLAB_AVAILABLE:
    DIFFICULTY_COLORS = {
        1: colors.HexColor("#e6fff2"),
        2: colors.HexColor("#d1fae5"),
        3: colors.HexColor("#fef3c7"),
        4: colors.HexColor("#fcd5c5"),
        5: colors.HexColor("#fee2e2"),
    }
else:
    DIFFICULTY_COLORS = {}


# ── Helpers internes ──────────────────────────────────────────────────────────

def _extract_id(line: str) -> str | None:
    if not line:
        return None
    m = re.search(r"\(([A-Za-z0-9_\-]+)\)\s*$", line)
    return m.group(1) if m else None


def _wrap(text: str, max_chars: int) -> list[str]:
    wrapper = textwrap.TextWrapper(width=max_chars, break_long_words=True, replace_whitespace=False)
    lines = []
    for para in str(text).split("\n"):
        lines.extend(wrapper.wrap(para) or [""])
    return lines


def _detect_difficulty(tech: dict) -> int | None:
    if not tech:
        return None
    lvl = tech.get("difficulty_level")
    if isinstance(lvl, int) and 1 <= lvl <= 5:
        return lvl
    old = tech.get("difficulte")
    if isinstance(old, int) and 1 <= old <= 5:
        return old
    return None


def _bg_color(tech: dict):
    if not REPORTLAB_AVAILABLE:
        return None
    lvl = _detect_difficulty(tech)
    return DIFFICULTY_COLORS.get(lvl, colors.white) if lvl else colors.white


def _draw_legend(c, x: float, y: float, usable_width: float) -> float:
    labels = [
        ("1 — Très facile / Endurance", 1),
        ("2 — Légère",                  2),
        ("3 — Modérée",                 3),
        ("4 — Élevée",                  4),
        ("5 — Très exigeant",           5),
    ]
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(colors.black)
    c.drawString(x, y, "Légende difficulté (1→5) :")
    y -= 5 * mm
    c.setFont("Helvetica", 8)
    for label, lvl in labels:
        col = DIFFICULTY_COLORS.get(lvl, colors.white)
        c.setFillColor(col)
        c.rect(x, y - 4 * mm, 6 * mm, 4 * mm, fill=1, stroke=0)
        c.setFillColor(colors.black)
        c.drawString(x + 8 * mm, y - 3.5 * mm, label)
        y -= 6 * mm
    return y - 2 * mm


def _split_weeks(lines: list[str]) -> list[dict]:
    """Découpe la liste programme en blocs semaine."""
    weeks, current = [], {"title": None, "lines": []}
    for ln in lines:
        if isinstance(ln, str) and ln.strip().startswith("---"):
            if current["title"] or current["lines"]:
                weeks.append(current)
            current = {"title": ln.strip().strip("- ").strip(), "lines": []}
        else:
            if isinstance(ln, str) and ln.strip():
                current["lines"].append(ln)
    if current["title"] or current["lines"]:
        weeks.append(current)
    return weeks or [{"title": "Programme", "lines": lines}]


# ── API publique ──────────────────────────────────────────────────────────────

def export_to_pdf(app, path: str | None = None, full_notes: bool = False) -> str | None:
    """
    Génère le PDF du programme (liste program_listbox).
    Retourne le chemin du fichier créé, ou None en cas d'échec/annulation.
    """
    from tkinter import messagebox, filedialog

    if not REPORTLAB_AVAILABLE:
        messagebox.showerror("reportlab manquant",
            "Installe reportlab : pip install reportlab")
        return None

    if not hasattr(app, "program_listbox"):
        messagebox.showinfo("Erreur", "Aucune liste de programme accessible.")
        return None

    raw_lines = [app.program_listbox.get(i) for i in range(app.program_listbox.size())]
    if not raw_lines:
        messagebox.showinfo("Vide", "La liste Programme (séances) est vide.")
        return None

    weeks = _split_weeks(raw_lines)

    if not path:
        default_name = (
            f"programme_{getattr(app, 'selected_user_name', 'user')}"
            f"_{datetime.date.today().isoformat()}.pdf"
        )
        path = filedialog.asksaveasfilename(
            title="Exporter Programme en PDF",
            defaultextension=".pdf",
            initialfile=default_name,
            filetypes=[("PDF", "*.pdf")],
        )
        if not path:
            return None

    try:
        c = pdf_canvas.Canvas(path, pagesize=A4)
        width, height = A4
        ml = mr = mt = mb = 14 * mm
        usable_w = width - ml - mr
        avg_cw = 2.6 * mm
        max_chars = max(40, int(usable_w / avg_cw))

        for page_idx, wk in enumerate(weeks):
            y = height - mt
            c.setFillColor(colors.black)

            # En-tête de page
            c.setFont("Helvetica-Bold", 12)
            title = f"{wk.get('title') or 'Semaine'} — {getattr(app, 'selected_user_name', '—')}"
            c.drawString(ml, y, title)
            c.setFont("Helvetica", 8)
            c.drawRightString(width - mr, y, f"Page {page_idx + 1} / {len(weeks)}")
            y -= 7 * mm

            if page_idx == 0:
                y = _draw_legend(c, ml, y, usable_w)

            c.setStrokeColor(colors.HexColor("#e5e7eb"))
            c.setLineWidth(0.5)
            c.line(ml, y, width - mr, y)
            y -= 6 * mm

            for ln in wk.get("lines", []):
                # Nouvelle page si nécessaire
                if y < mb + 12 * mm:
                    c.showPage()
                    y = height - mt
                    c.setFont("Helvetica-Bold", 12)
                    c.drawString(ml, y, title + " (suite)")
                    c.setFont("Helvetica", 8)
                    c.drawRightString(width - mr, y, f"Page {page_idx + 1} / {len(weeks)}")
                    y -= 8 * mm
                    c.setStrokeColor(colors.HexColor("#e5e7eb"))
                    c.setLineWidth(0.5)
                    c.line(ml, y, width - mr, y)
                    y -= 6 * mm

                text = str(ln).rstrip()
                tid  = _extract_id(text)
                tech = (tt.find_technique_by_id(tid) if tid and _TT_AVAILABLE else None)
                bg   = _bg_color(tech)

                # Lignes wrappées + détails
                main_w = _wrap(text, max_chars)
                details_w = []
                if tech:
                    details_w.append(
                        f"Catégorie: {tech.get('categorie','')}  •  "
                        f"Reps: {tech.get('reps','')}  •  "
                        f"Charge: {tech.get('charge','')}  •  "
                        f"Repos: {tech.get('repos','')}"
                    )
                    notes = (tech.get("notes") or "").strip()
                    if notes:
                        if not full_notes and len(notes) > 300:
                            notes = notes[:297].rstrip() + "..."
                        details_w.append(f"Notes: {notes}")
                details_flat = []
                for d in details_w:
                    details_flat.extend(_wrap(d, max_chars - 6))

                lh  = 8.5 * 0.35 * mm * 2.2
                slh = 7.5 * 0.35 * mm * 2.0
                rect_h = max(10 * mm,
                             len(main_w) * lh + len(details_flat) * slh + 3 * mm)

                # Rectangle coloré
                c.setFillColor(bg)
                c.rect(ml - 2*mm, y - rect_h + 2*mm,
                       usable_w + 4*mm, rect_h, fill=1, stroke=0)

                # Texte principal
                tx, ty = ml + mm, y - 4*mm
                c.setFillColor(colors.black)
                c.setFont("Helvetica", 8.5)
                for mw in main_w:
                    c.drawString(tx, ty, mw)
                    ty -= lh
                if details_flat:
                    c.setFont("Helvetica-Oblique", 7.5)
                    c.setFillColor(colors.HexColor("#374151"))
                    for dw in details_flat:
                        c.drawString(tx + 4*mm, ty, dw)
                        ty -= slh

                y = (y - rect_h + 2*mm) - 2*mm

            c.showPage()

        c.save()
        messagebox.showinfo("Exporté", f"Programme exporté :\n{path}")
        return path

    except Exception as e:
        from tkinter import messagebox as mb
        mb.showerror("Erreur PDF", f"Impossible de générer le PDF : {e}")
        return None


def preview_pdf(app, full_notes: bool = False):
    """Génère un PDF temporaire et l'ouvre dans le viewer par défaut."""
    if not REPORTLAB_AVAILABLE:
        from tkinter import messagebox
        messagebox.showerror("reportlab manquant",
            "Installe reportlab : pip install reportlab")
        return
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    tmp.close()
    created = export_to_pdf(app, path=tmp.name, full_notes=full_notes)
    if created:
        try:
            webbrowser.open_new(created)
        except Exception:
            from tkinter import messagebox
            messagebox.showinfo("PDF créé", created)
