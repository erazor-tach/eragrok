# data/pdf_utils.py — ERAGROK · Module PDF Centralisé
# ──────────────────────────────────────────────────────────────────────────────
# ARCHITECTURE :
#   Ce module est l'unique point d'entrée pour tout ce qui touche au PDF.
#   Chaque autre module (cycle, nutrition, entrainement) l'importe.
#
# EXPORTS :
#   export_cycle_pdf(app)        → PDF cycle standalone
#   export_nutrition_pdf(app)    → PDF nutrition standalone
#   export_entrainement_pdf(app) → PDF entrainement standalone
#   export_unified_pdf(app)      → PDF complet OBJECTIF FINAL
#
# COLONNES A4 (174mm utiles = 210 - 2×14mm) :
#   Tableau produits  [50,20,28,28,20,18]     = 164mm ✓
#   Tableau planning  [16,18,14,60,34,32]     = 174mm ✓
#   Tableau profil    [60,114]                 = 174mm ✓
# ──────────────────────────────────────────────────────────────────────────────

import os
import csv
import datetime
from pathlib import Path
from tkinter import messagebox, filedialog
import tkinter as _tk

def _root(app):
    """Retourne la fenêtre root pour les dialogs modaux."""
    return getattr(app, "root", None)

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        HRFlowable, PageBreak,
    )
    RL_OK = True
except ImportError:
    RL_OK = False

_MARGIN = 14          # mm
_USABLE = 210 - 2 * _MARGIN   # 182 mm utilisables


# ── Palette ───────────────────────────────────────────────────────────────────
class _C:
    if RL_OK:
        ACCENT  = colors.HexColor("#4aaa4a")
        ACCENT2 = colors.HexColor("#2d7a2d")
        WARN    = colors.HexColor("#cc8800")
        DANGER  = colors.HexColor("#cc3333")
        INFO    = colors.HexColor("#4488cc")
        WHITE   = colors.HexColor("#dddddd")
        MUTED   = colors.HexColor("#999999")
        DARK    = colors.HexColor("#111811")
        DARK2   = colors.HexColor("#151f15")
        BORDER  = colors.HexColor("#2a4a2a")
        HDR     = colors.HexColor("#1a3a1a")
        PHASE = {
            "CYCLE":   colors.HexColor("#182218"),
            "WASHOUT": colors.HexColor("#2a2010"),
            "PCT":     colors.HexColor("#1a1a2e"),
            "CRUISE":  colors.HexColor("#182030"),
            "TRT":     colors.HexColor("#201828"),
        }
    else:
        ACCENT=ACCENT2=WARN=DANGER=INFO=WHITE=MUTED=DARK=DARK2=BORDER=HDR=None
        PHASE={}


def _styles():
    if not RL_OK:
        return {}
    b = getSampleStyleSheet()
    def s(n, base="Normal", **kw):
        return ParagraphStyle(n, parent=b[base], **kw)
    return {
        "cover_title": s("CT","Title",  fontSize=28, textColor=_C.ACCENT, spaceAfter=4, leading=34),
        "cover_sub":   s("CS","Normal", fontSize=13, textColor=_C.MUTED,  spaceAfter=6),
        "cover_disc":  s("CD","Normal", fontSize=8,  textColor=_C.MUTED,  spaceAfter=2, leading=11),
        "title":  s("T", "Title",   fontSize=16, textColor=_C.ACCENT, spaceAfter=4),
        "h1":     s("H1","Heading1",fontSize=13, textColor=_C.ACCENT, spaceBefore=10, spaceAfter=4),
        "h2":     s("H2","Heading2",fontSize=10, textColor=_C.ACCENT, spaceBefore=7,  spaceAfter=3),
        "h3":     s("H3","Heading3",fontSize=9,  textColor=_C.ACCENT2,spaceBefore=4,  spaceAfter=2),
        "body":   s("B", "Normal",  fontSize=9,  textColor=_C.WHITE,  spaceAfter=3,  leading=13),
        "small":  s("SM","Normal",  fontSize=8,  textColor=_C.WHITE,  spaceAfter=2,  leading=11),
        "muted":  s("M", "Normal",  fontSize=8,  textColor=_C.MUTED,  spaceAfter=2,  leading=11),
        "warn":   s("W", "Normal",  fontSize=9,  textColor=_C.WARN,   spaceAfter=3,  leading=13),
        "danger": s("D", "Normal",  fontSize=9,  textColor=_C.DANGER, spaceAfter=3,  leading=13),
    }


# ── Helpers ───────────────────────────────────────────────────────────────────
def _clip(text, n=50):
    t = str(text or "—")
    return t if len(t) <= n else t[:n-1]+"…"


def _hr(story, color=None):
    if not RL_OK:
        return
    story.append(HRFlowable(width="100%", thickness=0.8,
                             color=color or _C.BORDER, spaceAfter=5, spaceBefore=2))


def _section_title(story, text, st):
    story.append(Paragraph(text, st["h1"]))
    _hr(story)


def _mk_table(rows, col_mm, extras=None):
    if not RL_OK or not rows:
        return None
    tbl = Table(rows, colWidths=[c*mm for c in col_mm], repeatRows=1)
    base = [
        ("BACKGROUND",     (0,0),(-1,0),   _C.HDR),
        ("TEXTCOLOR",      (0,0),(-1,0),   _C.ACCENT),
        ("FONTNAME",       (0,0),(-1,0),   "Helvetica-Bold"),
        ("FONTSIZE",       (0,0),(-1,-1),  8),
        ("ROWBACKGROUNDS", (0,1),(-1,-1),  [_C.DARK, _C.DARK2]),
        ("TEXTCOLOR",      (0,1),(-1,-1),  _C.WHITE),
        ("GRID",           (0,0),(-1,-1),  0.3, _C.BORDER),
        ("PADDING",        (0,0),(-1,-1),  4),
        ("VALIGN",         (0,0),(-1,-1),  "MIDDLE"),
        ("WORDWRAP",       (0,0),(-1,-1),  True),
    ]
    if extras:
        base.extend(extras)
    tbl.setStyle(TableStyle(base))
    return tbl


def _mk_doc(path):
    return SimpleDocTemplate(path, pagesize=A4,
                              rightMargin=_MARGIN*mm, leftMargin=_MARGIN*mm,
                              topMargin=_MARGIN*mm,   bottomMargin=_MARGIN*mm)


def _out_path(app, prefix):
    try:
        from data import utils as _u
        user = getattr(app, "current_user", "utilisateur")
        d = os.path.join(_u.USERS_DIR, user)
    except Exception:
        d = str(Path.home())
    Path(d).mkdir(parents=True, exist_ok=True)
    return os.path.join(d, f"{prefix}_{datetime.datetime.now():%Y%m%d_%H%M}.pdf")


def _footer(story, st):
    story.append(Spacer(1, 8))
    _hr(story, _C.MUTED)
    story.append(Paragraph(
        "Ce document est un outil de suivi personnel. "
        "Il ne constitue pas un avis médical. "
        "Consultez un professionnel de santé avant tout protocole.",
        st["muted"]))


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION CYCLE
# ══════════════════════════════════════════════════════════════════════════════
def _build_cycle_section(app, story, st):
    try:
        from data import cycle_module as cm
    except ImportError:
        try:
            import cycle_module as cm
        except ImportError:
            story.append(Paragraph("Module cycle non disponible.", st["warn"]))
            return

    selected = cm._gather_selected_products(app)
    if not selected:
        story.append(Paragraph("Aucun produit sélectionné dans le module cycle.", st["muted"]))
        return

    _section_title(story, "💉  Cycle Hormonal", st)

    try:    n_weeks = int(app.cycle_length_var.get().strip())
    except: n_weeks = 12
    end_v   = getattr(app,"cycle_end_var",     None)
    pct_v   = getattr(app,"cycle_pct_mode_var",None)
    start_v = getattr(app,"cycle_start_var",   None)
    end_s   = end_v.get()   if end_v   else "PCT"
    pct_s   = pct_v.get()   if pct_v   else "Normal"
    start_s = start_v.get() if start_v else "—"

    story.append(Paragraph(
        f"Début : {start_s}  ·  Durée : {n_weeks} semaines  ·  "
        f"Fin : {end_s} ({pct_s})  ·  {datetime.datetime.now():%d/%m/%Y %H:%M}",
        st["muted"]))
    story.append(Spacer(1, 4))

    # Alertes
    has_testo = any(p in cm._AROMATIZING_TEST for p in selected)
    for cond, msg in [
        (has_testo and not any(p in cm._AI_PRODUCTS for p in selected),
         "Testostérone SANS anti-aromatase — risque gynécomastie / hypertension"),
        (has_testo and not any(p in cm._HCG_PRODUCTS_SET for p in selected),
         "Testostérone SANS hCG — risque atrophie testiculaire"),
        (any("Trenbolone" in p or "Nandrolone" in p for p in selected)
         and not any("Cabergoline" in p for p in selected),
         "Tren/Deca SANS Cabergoline — risque prolactine élevée"),
    ]:
        if cond:
            story.append(Paragraph(f"⚠  {msg}", st["danger"]))

    story.append(Spacer(1, 4))

    # Tableau produits — [50,20,28,28,20,18] = 164mm ✓
    story.append(Paragraph("Produits & Doses", st["h2"]))
    rows = [["Produit","Dose/sem","Plage min","Plage max","Conseillé","Forme"]]
    for prod in selected:
        info  = cm.PRODUCT_INFO.get(prod, {})
        d_min = info.get("dose_min","—")
        d_max = info.get("dose_max","—")
        rec   = cm._recommended_dose(d_min)
        entry = getattr(app,"cycle_product_doses",{}).get(prod)
        dose  = ""
        if entry:
            try: dose = entry.get().strip()
            except: pass
        forme = "Oral" if prod in cm._ORAL_PRODUCTS else "Inject."
        rows.append([_clip(prod,36), dose or "—",
                     _clip(d_min,20), _clip(d_max,20),
                     _clip(rec,14), forme])
    t = _mk_table(rows, [50,20,28,28,20,18])
    if t:
        story.append(t)
    story.append(Spacer(1, 6))

    # Tableau planning — [16,18,14,60,34,32] = 174mm ✓
    try:
        plan = cm._build_cycle_plan(app, end_s, pct_s)
    except Exception:
        plan = []

    if plan:
        story.append(Paragraph("Planning semaine par semaine", st["h2"]))
        p_rows = [["Sem.","Date","Phase","Produits & IA","hCG / Timing","PCT"]]
        for e in plan:
            p_rows.append([
                _clip(e["label"],      8),
                _clip(e["date_start"],10),
                _clip(e["phase"],      8),
                _clip(e["produits"],  44),
                _clip(e["hcg"],       24),
                _clip(e["pct_info"],  24),
            ])
        extras = []
        for i, e in enumerate(plan, 1):
            bg = _C.PHASE.get(e["phase"], _C.DARK)
            extras.append(("BACKGROUND",(0,i),(-1,i), bg))
        t2 = _mk_table(p_rows, [16,18,14,60,34,32], extras)
        if t2:
            story.append(t2)
        story.append(Spacer(1, 6))

    # Notes produit — [46,46,82] = 174mm ✓
    notes_rows = [["Produit","Timing","Notes"]]
    for prod in selected:
        info = cm.PRODUCT_INFO.get(prod, {})
        t_   = info.get("timing","")
        n_   = info.get("notes", "")
        if t_ or n_:
            notes_rows.append([_clip(prod,30), _clip(t_,30), _clip(n_,50)])
    if len(notes_rows) > 1:
        story.append(Paragraph("Notes & timing", st["h2"]))
        t3 = _mk_table(notes_rows, [46,46,82])
        if t3:
            story.append(t3)
        story.append(Spacer(1, 4))

    # Notes utilisateur
    nw = getattr(app,"cycle_note_text",None)
    if nw:
        try:
            import tkinter as tk
            un = nw.get("1.0", tk.END).strip()
            if un:
                story.append(Paragraph("Notes personnelles", st["h2"]))
                story.append(Paragraph(_clip(un,500), st["body"]))
        except Exception:
            pass


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION NUTRITION
# ══════════════════════════════════════════════════════════════════════════════
def _build_nutrition_section(app, story, st):
    _section_title(story, "🍎  Nutrition & Composition Corporelle", st)

    try:
        from data import utils
    except ImportError:
        try: import utils
        except: story.append(Paragraph("Module utils non disponible.", st["warn"])); return

    info   = getattr(app,"user_info",{}) or {}
    poids  = info.get("poids","—")
    taille = info.get("taille","—")
    sexe   = info.get("sexe","—")
    age    = info.get("age","—")
    ajust  = info.get("ajustement","Maintien (0%)")
    try:
        pv = getattr(app,"poids_var",None)
        if pv: poids = pv.get().strip() or poids
    except Exception: pass

    imc_str = poids_cibles = macros_str = "—"
    try:
        imc_val, imc_cat = utils.calculer_imc(float(poids), float(taille))
        if imc_val:
            tm = float(taille)/100
            p_lo = round(18.5*tm**2,1); p_hi = round(25.0*tm**2,1)
            p_id = round(22.0*tm**2,1)
            imc_str      = f"{imc_val:.1f} — {imc_cat[0]}"
            poids_cibles = f"Normal : {p_lo}–{p_hi} kg  |  Idéal : {p_id} kg"
    except Exception: pass
    try:
        age_v = int(getattr(app,"age_var",None).get() or age)
        nut = utils.calculs_nutrition(float(poids), age_v, sexe, ajust, float(taille))
        if nut:
            adj = utils.ADJUSTMENTS.get(ajust, 0.0)
            cal = nut["tdee"] * (1+adj)
            cp,fp = (0.47,0.23) if "masse" in ajust.lower() else \
                    (0.37,0.23) if "déficit" in ajust.lower() else (0.45,0.25)
            g = (cal*cp)/4; l = (cal*fp)/9
            macros_str = (f"{cal:.0f} kcal  |  Prot. {nut['proteines']:.0f} g"
                          f"  |  Gluc. {g:.0f} g  |  Lip. {l:.0f} g")
    except Exception: pass

    # Tableau profil — [60,114] = 174mm ✓
    profile_rows = [
        ["Poids actuel",   f"{poids} kg"],
        ["Taille",         f"{taille} cm"],
        ["Sexe",           sexe],
        ["Âge",            f"{age} ans"],
        ["Objectif",       ajust],
        ["IMC",            imc_str],
        ["Poids cibles",   poids_cibles],
        ["Macros estimés", macros_str],
    ]
    tbl = Table(profile_rows, colWidths=[60*mm, 114*mm])
    tbl.setStyle(TableStyle([
        ("FONTNAME",       (0,0),(0,-1), "Helvetica-Bold"),
        ("FONTSIZE",       (0,0),(-1,-1), 9),
        ("TEXTCOLOR",      (0,0),(0,-1),  _C.ACCENT),
        ("TEXTCOLOR",      (1,0),(1,-1),  _C.WHITE),
        ("ROWBACKGROUNDS", (0,0),(-1,-1), [_C.DARK, _C.DARK2]),
        ("GRID",           (0,0),(-1,-1), 0.3, _C.BORDER),
        ("PADDING",        (0,0),(-1,-1), 5),
        ("VALIGN",         (0,0),(-1,-1), "MIDDLE"),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 6))

    # Historique nutrition
    try:
        user_dir = os.path.join(utils.USERS_DIR, getattr(app,"current_user",""))
        nut_file = os.path.join(user_dir,"nutrition.csv")
        if os.path.exists(nut_file):
            with open(nut_file,"r",newline="",encoding="utf-8") as f:
                rows = list(csv.reader(f))
            if len(rows) > 1:
                headers = rows[0][:5]
                data    = rows[1:][-15:]
                story.append(Paragraph(f"Historique nutrition ({len(data)} entrées)", st["h2"]))
                n_rows = [headers] + [[_clip(c,22) for c in r[:5]] for r in data]
                # [28,22,30,30,30] = 140mm ✓
                t = _mk_table(n_rows, [28,22,30,30,30])
                if t: story.append(t)
                story.append(Spacer(1, 4))
    except Exception: pass


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION ENTRAÎNEMENT
# ══════════════════════════════════════════════════════════════════════════════
def _build_entrainement_section(app, story, st):
    _section_title(story, "🏋  Entraînement", st)

    try:
        from data import utils
        user_dir = os.path.join(utils.USERS_DIR, getattr(app,"current_user",""))

        for fname in ("planning.csv","entrainement.csv"):
            pf = os.path.join(user_dir, fname)
            if os.path.exists(pf):
                with open(pf,"r",newline="",encoding="utf-8") as f:
                    rows = list(csv.reader(f))
                if len(rows) > 1:
                    headers = rows[0]
                    data    = rows[1:][-20:]
                    story.append(Paragraph(
                        f"Dernières {len(data)} séances ({fname})", st["muted"]))
                    nc  = min(len(headers), 5)
                    cw  = [round(_USABLE/nc, 1)] * nc
                    t   = _mk_table(
                        [headers[:nc]] + [[_clip(c,28) for c in r[:nc]] for r in data],
                        cw)
                    if t: story.append(t)
                    story.append(Spacer(1, 4))
                break

        if hasattr(app,"program_listbox"):
            lines = [app.program_listbox.get(i)
                     for i in range(app.program_listbox.size())]
            if lines:
                story.append(Paragraph("Programme actif", st["h2"]))
                for ln in lines[:40]:
                    story.append(Paragraph(_clip(str(ln),90), st["small"]))
                story.append(Spacer(1,4))
    except Exception as e:
        story.append(Paragraph(f"Erreur entraînement : {e}", st["warn"]))

    gv = getattr(app,"groupes_vars",{})
    actifs = [g for g, v in gv.items() if v.get()]
    if actifs:
        story.append(Paragraph(f"Groupes ciblés : {', '.join(actifs)}", st["body"]))


# ══════════════════════════════════════════════════════════════════════════════
#  EXPORTS STANDALONE
# ══════════════════════════════════════════════════════════════════════════════
def export_cycle_pdf(app, ask_path=False):
    if not RL_OK:
        messagebox.showerror("ERAGROK","reportlab manquant.\npip install reportlab"); return
    path = _out_path(app,"cycle")
    if ask_path:
        path = filedialog.asksaveasfilename(
            parent=_root(app), title="Exporter cycle PDF", defaultextension=".pdf",
            filetypes=[("PDF","*.pdf")], initialfile=os.path.basename(path)) or path
    if not path: return
    st = _styles(); doc = _mk_doc(path); story = []
    user = getattr(app,"current_user","utilisateur")
    story.append(Paragraph("ERAGROK — Cycle Hormonal", st["title"]))
    story.append(Paragraph(
        f"Utilisateur : {user}  ·  {datetime.datetime.now():%d/%m/%Y %H:%M}", st["muted"]))
    _hr(story)
    story.append(Paragraph("Outil de suivi personnel — pas un avis médical.", st["warn"]))
    story.append(Spacer(1,6))
    _build_cycle_section(app, story, st)
    _footer(story, st)
    try:
        doc.build(story)
        messagebox.showinfo("ERAGROK", f"✅ PDF cycle exporté :\n{path}")
    except Exception as e:
        messagebox.showerror("ERAGROK", f"Erreur PDF :\n{e}")


def export_nutrition_pdf(app, ask_path=False):
    if not RL_OK:
        messagebox.showerror("ERAGROK","reportlab manquant.\npip install reportlab"); return
    path = _out_path(app,"nutrition")
    if ask_path:
        path = filedialog.asksaveasfilename(
            parent=_root(app), title="Exporter nutrition PDF", defaultextension=".pdf",
            filetypes=[("PDF","*.pdf")], initialfile=os.path.basename(path)) or path
    if not path: return
    st = _styles(); doc = _mk_doc(path); story = []
    user = getattr(app,"current_user","utilisateur")
    story.append(Paragraph("ERAGROK — Rapport Nutrition", st["title"]))
    story.append(Paragraph(
        f"Utilisateur : {user}  ·  {datetime.datetime.now():%d/%m/%Y %H:%M}", st["muted"]))
    _hr(story); story.append(Spacer(1,6))
    _build_nutrition_section(app, story, st)
    _footer(story, st)
    try:
        doc.build(story)
        messagebox.showinfo("ERAGROK", f"✅ PDF nutrition exporté :\n{path}")
    except Exception as e:
        messagebox.showerror("ERAGROK", f"Erreur PDF :\n{e}")


def export_entrainement_pdf(app, ask_path=False):
    if not RL_OK:
        messagebox.showerror("ERAGROK","reportlab manquant.\npip install reportlab"); return
    path = _out_path(app,"entrainement")
    if ask_path:
        path = filedialog.asksaveasfilename(
            parent=_root(app), title="Exporter entraînement PDF", defaultextension=".pdf",
            filetypes=[("PDF","*.pdf")], initialfile=os.path.basename(path)) or path
    if not path: return
    st = _styles(); doc = _mk_doc(path); story = []
    user = getattr(app,"current_user","utilisateur")
    story.append(Paragraph("ERAGROK — Rapport Entraînement", st["title"]))
    story.append(Paragraph(
        f"Utilisateur : {user}  ·  {datetime.datetime.now():%d/%m/%Y %H:%M}", st["muted"]))
    _hr(story); story.append(Spacer(1,6))
    _build_entrainement_section(app, story, st)
    _footer(story, st)
    try:
        doc.build(story)
        messagebox.showinfo("ERAGROK", f"✅ PDF entraînement exporté :\n{path}")
    except Exception as e:
        messagebox.showerror("ERAGROK", f"Erreur PDF :\n{e}")


# ══════════════════════════════════════════════════════════════════════════════
#  EXPORT UNIFIÉ — RAPPORT COMPLET (OBJECTIF FINAL)
# ══════════════════════════════════════════════════════════════════════════════
def export_unified_pdf(app, sections=None, ask_path=True):
    """
    PDF complet ERAGROK :
    page de garde + profil + nutrition + entraînement + cycle
    """
    if not RL_OK:
        messagebox.showerror("ERAGROK","reportlab manquant.\npip install reportlab"); return

    if sections is None:
        sections = ["nutrition","entrainement","cycle"]

    path = _out_path(app,"eragrok_complet")
    if ask_path:
        path = filedialog.asksaveasfilename(
            parent=_root(app), title="Enregistrer le Rapport Complet ERAGROK",
            defaultextension=".pdf", filetypes=[("PDF","*.pdf")],
            initialfile=os.path.basename(path)) or path
    if not path:
        return

    try:
        from data import utils
    except ImportError:
        import utils

    st  = _styles()
    doc = _mk_doc(path)
    story = []

    info   = getattr(app,"user_info",{}) or {}
    user   = getattr(app,"current_user","utilisateur")
    name   = getattr(app,"selected_user_name", user)
    poids  = info.get("poids","—")
    taille = info.get("taille","—")
    try:
        pv = getattr(app,"poids_var",None)
        if pv: poids = pv.get().strip() or poids
    except Exception: pass

    imc_str = "—"
    try:
        imc_val, imc_cat = utils.calculer_imc(float(poids), float(taille))
        if imc_val: imc_str = f"{imc_val:.1f} — {imc_cat[0]}"
    except Exception: pass

    # ── Page de garde ─────────────────────────────────────────────────────────
    story.append(Spacer(1, 18*mm))
    story.append(Paragraph("⚡  ERAGROK", st["cover_title"]))
    story.append(Paragraph("Coach Bodybuilding — Rapport Personnel Complet", st["cover_sub"]))
    _hr(story, _C.ACCENT)
    story.append(Spacer(1, 6*mm))

    cover_rows = [
        ["Nom",       name],
        ["Poids",     f"{poids} kg"],
        ["Taille",    f"{taille} cm"],
        ["Sexe",      info.get("sexe","—")],
        ["Âge",       f"{info.get('age','—')} ans"],
        ["IMC",       imc_str],
        ["Objectif",  info.get("ajustement","—")],
        ["Généré le", datetime.datetime.now().strftime("%d/%m/%Y à %H:%M")],
    ]
    cover_tbl = Table(cover_rows, colWidths=[45*mm, 129*mm])
    cover_tbl.setStyle(TableStyle([
        ("FONTNAME",       (0,0),(0,-1), "Helvetica-Bold"),
        ("FONTSIZE",       (0,0),(-1,-1), 10),
        ("TEXTCOLOR",      (0,0),(0,-1),  _C.ACCENT),
        ("TEXTCOLOR",      (1,0),(1,-1),  _C.WHITE),
        ("ROWBACKGROUNDS", (0,0),(-1,-1), [_C.DARK, _C.DARK2]),
        ("GRID",           (0,0),(-1,-1), 0.3, _C.BORDER),
        ("PADDING",        (0,0),(-1,-1), 6),
    ]))
    story.append(cover_tbl)
    story.append(Spacer(1, 8*mm))
    story.append(Paragraph(
        "Ce document regroupe l'ensemble de vos données personnelles ERAGROK : "
        "nutrition, entraînement et cycle hormonal. "
        "Il ne constitue pas un avis médical — "
        "consultez un professionnel avant tout protocole hormonal.",
        st["cover_disc"]))

    # Sections
    builders = {
        "nutrition":    _build_nutrition_section,
        "entrainement": _build_entrainement_section,
        "cycle":        _build_cycle_section,
    }
    for sec in sections:
        if sec in builders:
            story.append(PageBreak())
            builders[sec](app, story, st)

    _footer(story, st)

    try:
        doc.build(story)
        messagebox.showinfo("ERAGROK", f"✅ Rapport complet exporté :\n{path}")
    except Exception as e:
        messagebox.showerror("ERAGROK", f"Erreur export PDF :\n{e}")
