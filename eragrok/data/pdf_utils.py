# data/pdf_utils.py — ERAGROK · Rapport PDF semaine par semaine
# ─────────────────────────────────────────────────────────────────────────────
# 1 page = 1 semaine : Entraînement + Nutrition + Cycle côte à côte
# Design sombre, orange accent, tables claires
# ─────────────────────────────────────────────────────────────────────────────
import os, datetime
from pathlib import Path
from tkinter import messagebox, filedialog

def _root(app):
    return getattr(app, "root", None)

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table,
        TableStyle, HRFlowable, PageBreak, KeepTogether,
        Frame, PageTemplate,
    )
    from reportlab.platypus.flowables import BalancedColumns
    RL_OK = True
except ImportError:
    RL_OK = False

_PW, _PH = A4  if RL_OK else (595, 842)
_ML = _MR = _MT = _MB = 12 * mm
_W  = _PW - _ML - _MR      # usable width ≈ 171 mm

# ── Palette ──────────────────────────────────────────────────────────────────
if RL_OK:
    _ACC   = colors.HexColor("#f97316")   # orange accent
    _ACC2  = colors.HexColor("#fdba74")   # accent glow
    _DARK  = colors.HexColor("#080810")
    _DARK2 = colors.HexColor("#10101e")
    _DARK3 = colors.HexColor("#17172a")
    _DARK4 = colors.HexColor("#0c0c1a")
    _WHITE = colors.HexColor("#eef2ff")
    _MUTED = colors.HexColor("#818aaa")
    _BORD  = colors.HexColor("#1e1e38")
    _GRN   = colors.HexColor("#22c55e")
    _BLU   = colors.HexColor("#3b82f6")
    _WARN  = colors.HexColor("#f59e0b")
    _DNGR  = colors.HexColor("#ef4444")
    _PUR   = colors.HexColor("#a855f7")
else:
    _ACC=_ACC2=_DARK=_DARK2=_DARK3=_DARK4=_WHITE=_MUTED=_BORD=_GRN=_BLU=_WARN=_DNGR=_PUR=None

_DAY_FR = ["LUN","MAR","MER","JEU","VEN","SAM","DIM"]

# ── Styles ───────────────────────────────────────────────────────────────────
def _styles():
    if not RL_OK: return {}
    b = getSampleStyleSheet()
    def s(n, base="Normal", **kw):
        return ParagraphStyle(n, parent=b[base], **kw)
    return {
        # couverture
        "cover_h1":  s("CH1", fontSize=36, textColor=_ACC,   leading=42, spaceAfter=4),
        "cover_sub": s("CS",  fontSize=13, textColor=_ACC2,  leading=16, spaceAfter=8),
        "cover_info":s("CI",  fontSize=10, textColor=_WHITE, leading=14, spaceAfter=3),
        "cover_disc":s("CD",  fontSize=7,  textColor=_MUTED, leading=10, spaceAfter=2),
        # en-têtes section par semaine
        "week_main": s("WM",  fontSize=13, textColor=_ACC,   leading=16, spaceBefore=0, spaceAfter=2),
        "sec_hdr":   s("SH",  fontSize=9,  textColor=_ACC2,  leading=12, spaceBefore=4, spaceAfter=2),
        # corps
        "body":      s("B",   fontSize=8,  textColor=_WHITE, leading=11, spaceAfter=2),
        "small":     s("SM",  fontSize=7,  textColor=_WHITE, leading=10, spaceAfter=1),
        "muted":     s("MU",  fontSize=7,  textColor=_MUTED, leading=10, spaceAfter=1),
        "ok":        s("OK",  fontSize=8,  textColor=_GRN,   leading=11, spaceAfter=2),
        "warn":      s("W",   fontSize=8,  textColor=_WARN,  leading=11, spaceAfter=2),
        "danger":    s("D",   fontSize=8,  textColor=_DNGR,  leading=11, spaceAfter=2),
        "accent":    s("AC",  fontSize=8,  textColor=_ACC,   leading=11, spaceAfter=2),
    }


def _hr(story, c=None, thick=0.5):
    if RL_OK:
        story.append(HRFlowable(width="100%", thickness=thick,
                                color=c or _BORD, spaceAfter=3, spaceBefore=1))


def _tbl(rows, col_mm, extras=None, rh=16):
    """Crée une Table stylée dark."""
    if not RL_OK or not rows: return None
    tbl = Table(rows, colWidths=[c*mm for c in col_mm], rowHeights=None, repeatRows=1)
    base = [
        ("BACKGROUND",  (0,0), (-1,0),  _DARK4),
        ("TEXTCOLOR",   (0,0), (-1,0),  _ACC),
        ("FONTNAME",    (0,0), (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",    (0,0), (-1,-1), 7),
        ("FONTNAME",    (0,1), (-1,-1), "Helvetica"),
        ("TEXTCOLOR",   (0,1), (-1,-1), _WHITE),
        ("BACKGROUND",  (0,1), (-1,-1), _DARK2),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[_DARK2, _DARK3]),
        ("GRID",        (0,0), (-1,-1), 0.3, _BORD),
        ("ALIGN",       (0,0), (-1,-1), "LEFT"),
        ("VALIGN",      (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING",  (0,0), (-1,-1), 3),
        ("BOTTOMPADDING",(0,0),(-1,-1), 3),
        ("LEFTPADDING", (0,0), (-1,-1), 4),
        ("RIGHTPADDING",(0,0), (-1,-1), 4),
    ]
    if extras:
        base.extend(extras)
    tbl.setStyle(TableStyle(base))
    return tbl


def _clip(t, n=40):
    t = str(t or "—")
    return t if len(t) <= n else t[:n-1]+"…"


def _parse_date(s):
    for fmt in ("%d/%m/%Y","%Y-%m-%d","%d-%m-%Y"):
        try: return datetime.datetime.strptime(str(s or "").strip(), fmt).date()
        except: pass
    return None


def _iso_week(d):
    """Retourne (year, week_num, monday_date)."""
    iso = d.isocalendar()
    monday = d - datetime.timedelta(days=d.weekday())
    return (iso[0], iso[1], monday)


def _weeks_range(start, n_weeks):
    """Génère n_weeks lundis consécutifs à partir du lundi de start."""
    monday = start - datetime.timedelta(days=start.weekday())
    return [monday + datetime.timedelta(weeks=i) for i in range(n_weeks)]


def _out_path(app, suffix):
    base = Path.home() / "Desktop"
    base.mkdir(exist_ok=True)
    name = getattr(app, "selected_user_name", "eragrok") or "eragrok"
    return str(base / f"ERAGROK_{name}_{suffix}_{datetime.date.today():%Y%m%d}.pdf")


def _mk_doc(path):
    return SimpleDocTemplate(
        path, pagesize=A4,
        leftMargin=_ML, rightMargin=_MR,
        topMargin=_MT, bottomMargin=_MB,
        title="Rapport ERAGROK",
    )


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE DE GARDE
# ══════════════════════════════════════════════════════════════════════════════
def _build_cover(app, story, st):
    ui  = getattr(app, "user_info", {}) or {}
    from data import utils as _utils
    dn  = ui.get("date_naissance","")
    age = _utils.age_depuis_naissance(dn) or ui.get("age","—")

    story.append(Spacer(1, 30*mm))
    story.append(Paragraph("⚡ ERAGROK", st["cover_h1"]))
    story.append(Paragraph("Journal de suivi — Entraînement · Nutrition · Cycle hormonal", st["cover_sub"]))
    _hr(story, _ACC, 1.5)
    story.append(Spacer(1, 8*mm))

    # Infos profil dans une table 2 colonnes
    rows = [
        [Paragraph("Athlète", st["muted"]),      Paragraph(str(ui.get("name","—")), st["body"])],
        [Paragraph("Âge",     st["muted"]),      Paragraph(f"{age} ans", st["body"])],
        [Paragraph("Sexe",    st["muted"]),      Paragraph(str(ui.get("sexe","—")), st["body"])],
        [Paragraph("Taille",  st["muted"]),      Paragraph(f"{ui.get('taille','—')} cm", st["body"])],
        [Paragraph("Objectif",st["muted"]),      Paragraph(str(ui.get("objectif","—")), st["body"])],
        [Paragraph("Généré",  st["muted"]),      Paragraph(datetime.date.today().strftime("%d/%m/%Y"), st["body"])],
    ]
    t = _tbl(rows, [32, 110])
    if t:
        story.append(t)

    story.append(Spacer(1, 12*mm))
    _hr(story, _BORD)
    story.append(Paragraph(
        "Ce document est généré automatiquement par ERAGROK à des fins de suivi personnel. "
        "Les informations relatives aux substances sont fournies à titre éducatif uniquement.",
        st["cover_disc"]))


# ══════════════════════════════════════════════════════════════════════════════
#  GÉNÉRATEUR DE PAGES SEMAINES  (cœur du rapport)
# Chaque page = 1 semaine ISO avec 3 sections :
#   ① Entraînement   ② Nutrition   ③ Cycle
# ══════════════════════════════════════════════════════════════════════════════
def _build_weekly_pages(app, story, st, include_nut=True, include_train=True, include_cycle=True):
    try:
        from data import db as _db
    except Exception:
        return

    # ── Charger toutes les données ────────────────────────────────────────────
    nut_rows  = _db.nutrition_get_all(app)  or []
    plan_rows = _db.planning_get_all(app)   or []
    hist_rows = _db.history_get_all(app)    or []
    cycle     = _db.cycle_get_active(app)

    # Cycle params
    cycle_debut   = _parse_date(cycle.get("debut",""))    if cycle else None
    cycle_len     = int(cycle.get("longueur_sem","12"))   if cycle else 12
    produits_s    = cycle.get("produits_doses","")        if cycle else ""
    washout_w     = 2
    cycle_pct_start = (cycle_debut + datetime.timedelta(weeks=cycle_len + washout_w)) if cycle_debut else None

    try:
        from data.cycle_module import PRODUCT_INFO
    except Exception:
        PRODUCT_INFO = {}

    # Parse produits
    prod_doses = {}
    _PCT_NAMES = {"Clomiphene (Clomid)", "Tamoxifen (Nolvadex)"}
    if produits_s:
        for e in produits_s.split("|"):
            e = e.strip()
            if e.startswith("[PCT]"): e = e[5:]
            if "_J+" in e: continue
            parts = e.split(":",1)
            prod_doses[parts[0].strip()] = parts[1].strip() if len(parts)>1 else ""

    # Grouper nutrition par semaine ISO
    nut_by_week = {}
    for r in nut_rows:
        d = _parse_date(r.get("date",""))
        if not d: continue
        wk = _iso_week(d)
        nut_by_week.setdefault(wk,[]).append((d,r))

    # Grouper planning par semaine ISO
    plan_by_week = {}
    for r in plan_rows:
        d = _parse_date(r.get("date",""))
        if not d: continue
        wk = _iso_week(d)
        plan_by_week.setdefault(wk,[]).append((d,r))

    # Grouper historique par semaine
    hist_by_week = {}
    for r in hist_rows:
        d = _parse_date(r.get("planned_for","")) or _parse_date(str(r.get("date",""))[:10])
        if not d: continue
        wk = _iso_week(d)
        hist_by_week.setdefault(wk,[]).append((d,r))

    # Union de toutes les semaines avec données
    all_weeks = sorted(set(list(nut_by_week)+list(plan_by_week)+list(hist_by_week)))

    if not all_weeks:
        story.append(Paragraph("Aucune donnée enregistrée.", st["muted"]))
        return

    # Ajouter les semaines du cycle + washout + PCT (4 sem PCT standard)
    if cycle_debut:
        pct_weeks = 4
        total_w = cycle_len + washout_w + pct_weeks
        for monday in _weeks_range(cycle_debut, total_w):
            wk = _iso_week(monday)
            if wk not in all_weeks:
                all_weeks.append(wk)
        all_weeks.sort()

    for wk in all_weeks[-52:]:   # max 52 semaines
        year, wnum, monday = wk
        sunday = monday + datetime.timedelta(days=6)

        # ── En-tête de la page ────────────────────────────────────────────────
        # Déterminer phase cycle
        phase_txt = ""
        phase_col = _MUTED
        if cycle_debut:
            days_in = (monday - cycle_debut).days
            week_n  = days_in // 7 + 1
            if 1 <= week_n <= cycle_len:
                phase_txt = f"  ·  CYCLE S{week_n}/{cycle_len}"
                phase_col = _GRN
            elif week_n == cycle_len + 1 or week_n == cycle_len + 2:
                phase_txt = f"  ·  WASHOUT S{week_n - cycle_len}/{washout_w}"
                phase_col = _WARN
            elif cycle_pct_start and monday >= cycle_pct_start:
                pct_w = ((monday - cycle_pct_start).days // 7) + 1
                phase_txt = f"  ·  PCT S{pct_w}"
                phase_col = _BLU

        # Titre page
        story.append(Paragraph(
            f"Sem. {wnum} / {year}   {monday:%d/%m} → {sunday:%d/%m/%Y}{phase_txt}",
            st["week_main"]))

        # Barre orange épaisse
        story.append(HRFlowable(width="100%", thickness=1.5, color=_ACC,
                                spaceAfter=6, spaceBefore=0))

        # ── Section ① ENTRAÎNEMENT ────────────────────────────────────────────
        if include_train:
            story.append(Paragraph("  🏋  ENTRAÎNEMENT", st["sec_hdr"]))
        _show_train = include_train

        plan_days  = sorted(plan_by_week.get(wk,[]), key=lambda x:x[0])
        hist_days  = sorted(hist_by_week.get(wk,[]), key=lambda x:x[0])

        if plan_days:
            # 1 ligne par jour unique (grouper exercices par jour)
            from collections import defaultdict
            by_day = defaultdict(list)
            for d, r in plan_days:
                by_day[d].append(r)

            rows_t = [[
                Paragraph("Jour", st["muted"]),
                Paragraph("Groupes", st["muted"]),
                Paragraph("Exercices", st["muted"]),
            ]]
            for d in sorted(by_day):
                recs = by_day[d]
                groupes = " / ".join(sorted({r.get("groupes","").strip() for r in recs if r.get("groupes","")}))
                lines   = [r.get("line","").strip() for r in recs if r.get("line","")]
                # Nettoyer IDs entre parenthèses
                import re as _re
                lines = [_re.sub(r'\s*\([A-Z0-9_]+\)\s*$','',l).strip() for l in lines]
                ex_txt = _clip(" · ".join(lines[:4]), 70)
                rows_t.append([
                    Paragraph(f"{_DAY_FR[d.weekday()]} {d:%d/%m}", st["small"]),
                    Paragraph(_clip(groupes, 22), st["small"]),
                    Paragraph(ex_txt, st["small"]),
                ])
            # Jours sans séance
            for wd in range(7):
                d = monday + datetime.timedelta(days=wd)
                if d not in by_day:
                    rows_t.append([
                        Paragraph(f"{_DAY_FR[wd]} {d:%d/%m}", st["muted"]),
                        Paragraph("—", st["muted"]),
                        Paragraph("Repos", st["muted"]),
                    ])
            t = _tbl(rows_t, [18, 30, 94])  # 142mm
            if t: story.append(t)
        elif hist_days:
            rows_t = [[
                Paragraph("Date", st["muted"]),
                Paragraph("Type", st["muted"]),
                Paragraph("Exercices", st["muted"]),
            ]]
            for d, r in hist_days:
                exs = r.get("exercises",[])
                rows_t.append([
                    Paragraph(str(r.get("date",""))[:10], st["small"]),
                    Paragraph(_clip(r.get("type",""),18), st["small"]),
                    Paragraph(_clip(" / ".join(str(e) for e in exs[:4]),60), st["small"]),
                ])
            t = _tbl(rows_t, [22, 28, 92])
            if t: story.append(t)
        else:
            story.append(Paragraph("  Aucune séance planifiée cette semaine.", st["muted"]))

        story.append(Spacer(1, 5*mm))

        # ── Section ② NUTRITION ───────────────────────────────────────────────
        if include_nut:
            story.append(Paragraph("  🍎  NUTRITION", st["sec_hdr"]))
        _show_nut = include_nut

        nut_days = sorted(nut_by_week.get(wk,[]), key=lambda x:x[0])
        if nut_days:
            rows_n = [[
                Paragraph("Jour", st["muted"]),
                Paragraph("Poids", st["muted"]),
                Paragraph("Calories", st["muted"]),
                Paragraph("Prot.", st["muted"]),
                Paragraph("Gluc.", st["muted"]),
                Paragraph("Lip.", st["muted"]),
                Paragraph("Note", st["muted"]),
            ]]
            cal_v=[]; prot_v=[]; gluc_v=[]; lip_v=[]; pds_v=[]
            for d, r in nut_days:
                def _f(k):
                    v = str(r.get(k,"")).strip()
                    try: return float(v) if v else None
                    except: return None
                cal=_f("calories"); prot=_f("proteines")
                gluc=_f("glucides"); lip=_f("lipides"); pds=_f("poids")
                if cal:  cal_v.append(cal)
                if prot: prot_v.append(prot)
                if gluc: gluc_v.append(gluc)
                if lip:  lip_v.append(lip)
                if pds:  pds_v.append(pds)
                rows_n.append([
                    Paragraph(f"{_DAY_FR[d.weekday()]} {d:%d/%m}", st["small"]),
                    Paragraph(f"{pds:.1f}" if pds else "—", st["small"]),
                    Paragraph(f"{cal:.0f}" if cal else "—", st["small"]),
                    Paragraph(f"{prot:.0f}" if prot else "—", st["small"]),
                    Paragraph(f"{gluc:.0f}" if gluc else "—", st["small"]),
                    Paragraph(f"{lip:.0f}" if lip else "—", st["small"]),
                    Paragraph(_clip(str(r.get("note","")),24), st["muted"]),
                ])
            # Ligne moyennes
            def _avg(lst): return f"{sum(lst)/len(lst):.1f}" if lst else "—"
            rows_n.append([
                Paragraph("MOY", st["muted"]),
                Paragraph(_avg(pds_v), st["accent"]),
                Paragraph(_avg(cal_v), st["accent"]),
                Paragraph(_avg(prot_v), st["accent"]),
                Paragraph(_avg(gluc_v), st["accent"]),
                Paragraph(_avg(lip_v), st["accent"]),
                Paragraph("", st["muted"]),
            ])
            moy_extras = [
                ("FONTNAME",  (0,-1),(-1,-1), "Helvetica-Bold"),
                ("BACKGROUND",(0,-1),(-1,-1), _DARK4),
                ("TEXTCOLOR", (0,-1),(-1,-1), _ACC),
            ]
            t = _tbl(rows_n, [18, 14, 20, 16, 16, 14, 44], moy_extras)
            if t: story.append(t)
        else:
            story.append(Paragraph("  Aucune donnée nutrition cette semaine.", st["muted"]))

        story.append(Spacer(1, 5*mm))

        # ── Section ③ CYCLE ───────────────────────────────────────────────────
        if include_cycle:
            story.append(Paragraph("  💉  CYCLE HORMONAL", st["sec_hdr"]))

        if include_cycle and not cycle_debut:
            story.append(Paragraph("  Aucun cycle enregistré.", st["muted"]))
        else:
            days_in = (monday - cycle_debut).days
            week_n  = days_in // 7 + 1

            if 1 <= week_n <= cycle_len:
                # Afficher les produits actifs
                active = {p:d for p,d in prod_doses.items() if p not in _PCT_NAMES}
                if active:
                    rows_c = [[
                        Paragraph("Produit", st["muted"]),
                        Paragraph("Dose", st["muted"]),
                        Paragraph("Utilité", st["muted"]),
                        Paragraph("Demi-vie", st["muted"]),
                    ]]
                    for pname, dose in active.items():
                        info = PRODUCT_INFO.get(pname,{})
                        rows_c.append([
                            Paragraph(_clip(pname,28), st["small"]),
                            Paragraph(dose or "—", st["small"]),
                            Paragraph(_clip(info.get("utilite","—"),36), st["muted"]),
                            Paragraph(_clip(info.get("demi_vie","—"),20), st["muted"]),
                        ])
                    t = _tbl(rows_c, [40, 20, 60, 22])
                    if t: story.append(t)
                else:
                    story.append(Paragraph("  Produits actifs — voir configuration cycle.", st["muted"]))
            elif week_n == cycle_len + 1 or week_n == cycle_len + 2:
                story.append(Paragraph(
                    "  🚫  WASHOUT — Arrêt de tous les produits du cycle.", st["warn"]))
                story.append(Paragraph(
                    "  Surveiller : récupération testiculaire, libido, énergie.", st["muted"]))
            elif cycle_pct_start and monday >= cycle_pct_start:
                pct_w = ((monday - cycle_pct_start).days // 7) + 1
                story.append(Paragraph(f"  💊  PCT — Semaine {pct_w}", st["ok"]))
                # Afficher les produits PCT s'ils existent
                pct_prods = {p:d for p,d in prod_doses.items() if p in _PCT_NAMES}
                if pct_prods:
                    rows_pct = [[Paragraph("Produit",st["muted"]), Paragraph("Dose",st["muted"]), Paragraph("Rôle",st["muted"])]]
                    for pname, dose in pct_prods.items():
                        info = PRODUCT_INFO.get(pname,{})
                        rows_pct.append([
                            Paragraph(_clip(pname,30), st["small"]),
                            Paragraph(dose or "voir protocole", st["small"]),
                            Paragraph(_clip(info.get("utilite","Relance axe HPTA"),36), st["muted"]),
                        ])
                    t = _tbl(rows_pct, [50,40,52])
                    if t: story.append(t)
                else:
                    story.append(Paragraph(
                        "  Clomid 50→25 mg/j + Nolvadex 20→10 mg/j (protocole standard 4 semaines)",
                        st["small"]))
            elif week_n < 1:
                story.append(Paragraph("  Cycle pas encore démarré.", st["muted"]))
            else:
                story.append(Paragraph("  Cycle terminé.", st["muted"]))

        # ── Pied de page semaine ──────────────────────────────────────────────
        story.append(Spacer(1, 4*mm))
        story.append(HRFlowable(width="100%", thickness=0.3, color=_BORD,
                                spaceAfter=2, spaceBefore=2))
        story.append(Paragraph(
            f"ERAGROK  ·  {getattr(app,'selected_user_name','')}"
            f"  ·  Sem. {wnum}/{year}  ·  généré le {datetime.date.today():%d/%m/%Y}",
            st["muted"]))
        story.append(PageBreak())


# ══════════════════════════════════════════════════════════════════════════════
#  EXPORT UNIFIÉ
# ══════════════════════════════════════════════════════════════════════════════
def _show_export_dialog(app):
    """Boîte de dialogue pour choisir les sections du PDF."""
    import tkinter as tk
    import customtkinter as ctk
    from data.theme import TH, mk_card, mk_title, mk_sep, mk_label, mk_btn
    root = _root(app)
    dlg = ctk.CTkToplevel(root) if root else None
    if not dlg: return None, None, None
    dlg.title("Exporter le rapport PDF")
    dlg.geometry("440x320")
    dlg.configure(fg_color=TH.BG_CARD)
    dlg.grab_set(); dlg.focus_set()

    mk_title(dlg, "  📄  EXPORTER — Choisir les sections").pack(
        anchor="w", padx=20, pady=(16,4))
    mk_sep(dlg).pack(fill="x", padx=20, pady=(0,12))

    sections = {
        "cover":       ("📋  Page de garde",        tk.BooleanVar(value=True)),
        "nutrition":   ("🍎  Nutrition",             tk.BooleanVar(value=True)),
        "training":    ("🏋  Entraînement",          tk.BooleanVar(value=True)),
        "cycle":       ("💉  Cycle hormonal",        tk.BooleanVar(value=True)),
    }
    for key, (label, var) in sections.items():
        ctk.CTkCheckBox(dlg, text=label, variable=var,
                        font=("Inter",11), text_color=TH.TEXT,
                        fg_color=TH.ACCENT, hover_color=TH.ACCENT_HOVER,
                        checkmark_color="#000").pack(anchor="w", padx=28, pady=4)

    compare_var = tk.BooleanVar(value=False)
    ctk.CTkCheckBox(dlg, text="🔄  Rapport comparatif 2 cycles (si disponible)",
                    variable=compare_var,
                    font=("Inter",11), text_color=TH.TEXT_MUTED,
                    fg_color=TH.PURPLE, hover_color="#7e22ce",
                    checkmark_color="#fff").pack(anchor="w", padx=28, pady=4)

    result = [None]

    def _ok():
        result[0] = {k: v.get() for k,(_, v) in sections.items()}
        result[0]["compare"] = compare_var.get()
        dlg.destroy()

    def _cancel():
        dlg.destroy()

    btn_row = ctk.CTkFrame(dlg, fg_color="transparent")
    btn_row.pack(side="bottom", pady=16)
    mk_btn(btn_row, "✔  Exporter", _ok,
           color=TH.ACCENT, hover=TH.ACCENT_HOVER,
           width=140, height=38).pack(side="left", padx=8)
    mk_btn(btn_row, "Annuler", _cancel,
           color=TH.GRAY, hover=TH.GRAY_HVR,
           width=100, height=38).pack(side="left", padx=8)

    root.wait_window(dlg)
    return result[0]


def _build_compare_cycles(app, story, st):
    """Tableau comparatif des 2 derniers cycles."""
    try:
        from data import db as _db
        rows = _db.cycle_get_all(app)
    except Exception:
        return
    if len(rows) < 2:
        story.append(Paragraph("Un seul cycle disponible — pas de comparaison possible.", st["muted"]))
        return
    c1, c2 = dict(rows[-2]), dict(rows[-1])
    story.append(Paragraph("🔄  COMPARAISON DES 2 DERNIERS CYCLES", st["h1"]))
    _hr(story, _ACC, 1)

    headers = ["", "Cycle N-1", "Cycle actuel"]
    data = [
        ["Début",       c1.get("debut","—"),        c2.get("debut","—")],
        ["Fin estimée", c1.get("fin_estimee","—"),   c2.get("fin_estimee","—")],
        ["Durée (sem)", c1.get("longueur_sem","—"),  c2.get("longueur_sem","—")],
        ["Produits",    _clip(c1.get("produits_doses","—"),40), _clip(c2.get("produits_doses","—"),40)],
        ["Note",        _clip(c1.get("note","—"),30), _clip(c2.get("note","—"),30)],
    ]
    rows_t = [[Paragraph(str(c), st["muted"] if i==0 else st["body"])
               for i, c in enumerate(row)] for row in [headers]+data]
    t = _tbl(rows_t, [38, 72, 72])
    if t: story.append(t)
    story.append(PageBreak())



# ══════════════════════════════════════════════════════════════════════════════
#  EXPORT PDF NUTRITION COMPLET (historique + plan alimentaire)
# ══════════════════════════════════════════════════════════════════════════════
def export_nutrition_full_pdf(app, ask_path=True):
    """
    PDF nutrition unique qui contient :
      1. Page de garde (athlète, macros cibles, IMC)
      2. Historique nutrition (tableau complet)
      3. Plan alimentaire actuel (si généré)
    """
    if not RL_OK:
        messagebox.showerror("ERAGROK", "ReportLab requis : pip install reportlab")
        return

    default = _out_path(app, "NUTRITION")
    if ask_path:
        path = filedialog.asksaveasfilename(
            title="Exporter PDF Nutrition",
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialfile=os.path.basename(default),
        )
        if not path: return
    else:
        path = default

    from data import db as _db2, utils as _utils2
    doc  = _mk_doc(path)
    st   = _styles()
    story = []

    ui   = getattr(app, "user_info", {}) or {}
    dn   = ui.get("date_naissance", "")
    age  = _utils2.age_depuis_naissance(dn) or ui.get("age", "—")
    name = ui.get("name", getattr(app, "selected_user_name", "—"))
    obj  = ui.get("objectif", "—")
    poids = ui.get("poids", "—")
    taille = ui.get("taille", "—")
    try:
        imc_val, imc_cat = _utils2.calculer_imc(float(poids), float(taille))
        imc_str = f"{imc_val:.1f} — {imc_cat[0]}"
    except Exception:
        imc_str = "—"

    # ── Page de garde ─────────────────────────────────────────────────────────
    story.append(Paragraph("ERAGROK", st["cover_h1"]))
    story.append(Paragraph("Bilan Nutrition", st["cover_sub"]))
    _hr(story, _ACC, 1.5)
    story.append(Paragraph(
        f"Athlète : {name}   |   Âge : {age} ans   |   Objectif : {obj}",
        st["cover_info"]))
    story.append(Paragraph(
        f"Poids : {poids} kg   |   Taille : {taille} cm   |   IMC : {imc_str}",
        st["cover_info"]))
    story.append(Paragraph(
        f"Exporté le : {datetime.date.today():%d/%m/%Y}",
        st["cover_info"]))
    _hr(story, _BORD)
    story.append(Spacer(1, 8*mm))

    # ── Historique nutrition ──────────────────────────────────────────────────
    story.append(Paragraph("Historique Nutrition", st["sec_hdr"]))
    _hr(story)
    rows_data = []
    try: rows_data = _db2.nutrition_get_all(app)
    except Exception: pass

    if rows_data:
        hdr = [Paragraph(h, st["muted"]) for h in
               ["Date", "Poids (kg)", "Calories", "Protéines", "Glucides", "Lipides", "Note"]]
        tbl_rows = [hdr]
        for r in rows_data:
            tbl_rows.append([
                Paragraph(r.get("date",   ""), st["small"]),
                Paragraph(r.get("poids",  ""), st["small"]),
                Paragraph(r.get("calories",""), st["small"]),
                Paragraph(r.get("proteines",""), st["small"]),
                Paragraph(r.get("glucides",""), st["small"]),
                Paragraph(r.get("lipides", ""), st["small"]),
                Paragraph(_clip(r.get("note",""), 30), st["small"]),
            ])
        t = _tbl(tbl_rows, [28, 20, 22, 22, 22, 22, 34], rh=14)
        if t: story.append(t)
    else:
        story.append(Paragraph("Aucune donnée enregistrée.", st["muted"]))

    story.append(Spacer(1, 8*mm))

    # ── Plan alimentaire actuel (si présent) ──────────────────────────────────
    last = getattr(app, "_last_meal_plan", None)
    plan_days = None
    if last:
        if last.get("days"):
            plan_days = last["days"]
        elif last.get("plan"):
            plan_days = [{"date": str(datetime.date.today()), "label": "Jour 1",
                          "plan": last["plan"]}]

    if plan_days:
        story.append(PageBreak())
        story.append(Paragraph("Plan Alimentaire", st["sec_hdr"]))
        _hr(story, _ACC, 1)
        SLOT_ICONS = {"matin":"🌅","midi":"☀","collation":"🍎","soir":"🌙","coucher":"🌛"}
        for day_info in plan_days:
            day_lbl = day_info.get("label", "")
            day_date = day_info.get("date", "")
            plan = day_info.get("plan", [])
            story.append(Spacer(1, 4*mm))
            story.append(Paragraph(
                f"{day_lbl}  {day_date}",
                st["week_main"]))
            _hr(story)
            # Macros du jour
            tot_cal  = sum(m.get("tot_cal",0) for m in plan)
            tot_prot = sum(m.get("tot_p",0)   for m in plan)
            tot_gluc = sum(m.get("tot_g",0)   for m in plan)
            tot_lip  = sum(m.get("tot_l",0)   for m in plan)
            story.append(Paragraph(
                f"🔥 {tot_cal:.0f} kcal  |  🥩 {tot_prot:.0f} g P  |  "
                f"🍚 {tot_gluc:.0f} g G  |  🥑 {tot_lip:.0f} g L",
                st["body"]))
            story.append(Spacer(1, 3*mm))
            for meal in plan:
                story.append(Paragraph(
                    f"{SLOT_ICONS.get(meal.get('type',''),'')}  {meal.get('name','')}  —  "
                    f"{meal.get('tot_cal',0):.0f} kcal | "
                    f"{meal.get('tot_p',0):.0f}g P · "
                    f"{meal.get('tot_g',0):.0f}g G · "
                    f"{meal.get('tot_l',0):.0f}g L",
                    st["week_sub"]))
                if meal.get("items"):
                    rows_m = [[Paragraph(h, st["muted"]) for h in
                               ["Aliment","Qté","Kcal","P","G","L"]]]
                    for item in meal["items"]:
                        rows_m.append([
                            Paragraph(item.get("food",""), st["small"]),
                            Paragraph(f"{item.get('g',0):.0f}g", st["small"]),
                            Paragraph(f"{item.get('kcal',0):.0f}", st["small"]),
                            Paragraph(f"{item.get('p',0):.1f}", st["small"]),
                            Paragraph(f"{item.get('g_',0):.1f}", st["small"]),
                            Paragraph(f"{item.get('l',0):.1f}", st["small"]),
                        ])
                    t = _tbl(rows_m, [55, 18, 18, 18, 18, 18], rh=13)
                    if t: story.append(t)
                story.append(Spacer(1, 2*mm))
    else:
        story.append(Paragraph("Aucun plan alimentaire généré.", st["muted"]))

    # Build
    try:
        doc.build(story)
        messagebox.showinfo("ERAGROK", f"✅ PDF exporté :\n{path}")
    except Exception as e:
        messagebox.showerror("ERAGROK", f"Erreur PDF : {e}")

def export_unified_pdf(app, ask_path=True):
    if not RL_OK:
        messagebox.showerror("ERAGROK","reportlab manquant.\npip install reportlab")
        return

    # Boîte de dialogue de sélection des sections
    sections = _show_export_dialog(app)
    if not sections:  # annulé
        return

    path = _out_path(app, "rapport")
    if ask_path:
        path = filedialog.asksaveasfilename(
            parent=_root(app),
            title="Enregistrer le Rapport ERAGROK",
            defaultextension=".pdf",
            filetypes=[("PDF","*.pdf")],
            initialfile=os.path.basename(path),
        ) or path
    if not path: return

    st  = _styles()
    doc = _mk_doc(path)
    story = []

    if sections.get("cover", True):
        _build_cover(app, story, st)
        story.append(PageBreak())

    if sections.get("compare") and sections.get("cycle", True):
        _build_compare_cycles(app, story, st)

    _build_weekly_pages(app, story, st,
                        include_nut=sections.get("nutrition", True),
                        include_train=sections.get("training", True),
                        include_cycle=sections.get("cycle", True))

    # Retirer le dernier PageBreak superflu
    if story and isinstance(story[-1], PageBreak):
        story.pop()

    try:
        doc.build(story)
        messagebox.showinfo("ERAGROK", f"✅ Rapport exporté :\n{path}")
    except Exception as e:
        messagebox.showerror("ERAGROK", f"Erreur PDF :\n{e}")


# Aliases standalone (compatibilité sidebar)
def export_cycle_pdf(app, ask_path=True):
    export_unified_pdf(app, ask_path)

def export_nutrition_pdf(app, ask_path=True):
    export_unified_pdf(app, ask_path)

def export_entrainement_pdf(app, ask_path=True):
    export_unified_pdf(app, ask_path)


# ══════════════════════════════════════════════════════════════════════════════
#  EXPORT PDF — PLAN ALIMENTAIRE
# ══════════════════════════════════════════════════════════════════════════════
def export_meal_plan_pdf(app, plan, ask_path=True):
    """Génère un PDF propre du plan alimentaire journalier."""
    if not RL_OK:
        messagebox.showerror("ERAGROK", "ReportLab n'est pas installé (pip install reportlab).")
        return

    # Chemin de sauvegarde
    default = _out_path(app, "PLAN_ALIMENTAIRE")
    if ask_path:
        path = filedialog.asksaveasfilename(
            title="Enregistrer le plan alimentaire",
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialfile=os.path.basename(default),
        )
        if not path:
            return
    else:
        path = default

    doc = _mk_doc(path)
    st  = _styles()
    story = []

    ui  = getattr(app, "user_info", {}) or {}
    from data import utils as _utils
    dn  = ui.get("date_naissance", "")
    age = _utils.age_depuis_naissance(dn) or ui.get("age", "—")
    name = ui.get("name", getattr(app, "selected_user_name", "—"))
    obj  = ui.get("objectif", "—")

    # ── En-tête ───────────────────────────────────────────────────────────────
    story.append(Paragraph("ERAGROK", st["cover_h1"]))
    story.append(Paragraph("Plan Alimentaire Journalier", st["cover_sub"]))
    _hr(story, _ACC, 1.5)
    story.append(Paragraph(
        f"Athlète : {name}   |   Âge : {age} ans   |   Objectif : {obj}   |   "
        f"Date : {datetime.date.today():%d/%m/%Y}",
        st["cover_info"]))
    _hr(story, _BORD)
    story.append(Spacer(1, 6*mm))

    # ── Totaux journée ────────────────────────────────────────────────────────
    tot_cal  = sum(m["tot_cal"] for m in plan)
    tot_prot = sum(m["tot_p"]   for m in plan)
    tot_gluc = sum(m["tot_g"]   for m in plan)
    tot_lip  = sum(m["tot_l"]   for m in plan)

    story.append(Paragraph("Récapitulatif macros", st["sec_hdr"]))
    mac_rows = [
        [Paragraph("Macro", st["muted"]),
         Paragraph("Total", st["muted"]),
         Paragraph("% kcal", st["muted"])],
        [Paragraph("🔥 Calories", st["body"]),
         Paragraph(f"{tot_cal:.0f} kcal", st["body"]), Paragraph("100%", st["body"])],
        [Paragraph("🥩 Protéines", st["body"]),
         Paragraph(f"{tot_prot:.0f} g", st["body"]),
         Paragraph(f"{tot_prot*4/tot_cal*100:.0f}%" if tot_cal else "—", st["body"])],
        [Paragraph("🍚 Glucides", st["body"]),
         Paragraph(f"{tot_gluc:.0f} g", st["body"]),
         Paragraph(f"{tot_gluc*4/tot_cal*100:.0f}%" if tot_cal else "—", st["body"])],
        [Paragraph("🥑 Lipides", st["body"]),
         Paragraph(f"{tot_lip:.0f} g", st["body"]),
         Paragraph(f"{tot_lip*9/tot_cal*100:.0f}%" if tot_cal else "—", st["body"])],
    ]
    t = _tbl(mac_rows, [70, 50, 30])
    if t:
        story.append(t)
    story.append(Spacer(1, 6*mm))

    # ── Détail par repas ──────────────────────────────────────────────────────
    SLOT_ICONS = {"matin":"🌅","midi":"☀","collation":"🍎","soir":"🌙","coucher":"🌛"}
    for meal in plan:
        story.append(Paragraph(
            f"{SLOT_ICONS.get(meal['type'],'')}  {meal['name']}  —  "
            f"{meal['tot_cal']:.0f} kcal | {meal['tot_p']:.0f}g P · "
            f"{meal['tot_g']:.0f}g G · {meal['tot_l']:.0f}g L",
            st["week_main"]))
        _hr(story)

        if meal["items"]:
            rows = [
                [Paragraph(h, st["muted"]) for h in
                 ["Aliment", "Quantité", "Calories", "Prot.", "Glucides", "Lipides"]]
            ]
            for item in meal["items"]:
                rows.append([
                    Paragraph(item["food"], st["small"]),
                    Paragraph(f"{item['g']:.0f} g", st["small"]),
                    Paragraph(f"{item['kcal']:.0f}", st["small"]),
                    Paragraph(f"{item['p']:.1f} g", st["small"]),
                    Paragraph(f"{item['g_']:.1f} g", st["small"]),
                    Paragraph(f"{item['l']:.1f} g", st["small"]),
                ])
            # Total ligne
            rows.append([
                Paragraph("TOTAL", st["accent"]),
                Paragraph("", st["small"]),
                Paragraph(f"{meal['tot_cal']:.0f}", st["accent"]),
                Paragraph(f"{meal['tot_p']:.1f} g", st["accent"]),
                Paragraph(f"{meal['tot_g']:.1f} g", st["accent"]),
                Paragraph(f"{meal['tot_l']:.1f} g", st["accent"]),
            ])
            t = _tbl(rows, [60, 22, 22, 22, 22, 22])
            if t: story.append(t)
        else:
            story.append(Paragraph("Aucun aliment pour ce repas.", st["muted"]))
        story.append(Spacer(1, 4*mm))

    # ── Note bas de page ──────────────────────────────────────────────────────
    story.append(Spacer(1, 8*mm))
    _hr(story, _BORD)
    story.append(Paragraph(
        "Ce plan a été généré par ERAGROK. Les quantités sont calculées pour correspondre "
        "à ton profil (TDEE + ajustement objectif). Adapte selon tes sensations.",
        st["muted"]))

    try:
        doc.build(story)
        messagebox.showinfo("ERAGROK", f"✅ Plan exporté :\n{path}")
        try:
            import subprocess, sys
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception:
            pass
    except Exception as e:
        messagebox.showerror("ERAGROK", f"Erreur génération PDF : {e}")


# ══════════════════════════════════════════════════════════════════════════════
#  EXPORT PDF — PLAN MULTI-JOURS (semaine / mois)
# ══════════════════════════════════════════════════════════════════════════════
def export_shopping_pdf(app, shopping, period_lbl="", ask_path=True, print_after=False):
    """
    Génère un PDF liste de courses A4 — table unique avec headers catégorie intercalés.
    Architecture robuste : une seule Table ReportLab, pas de colonnes imbriquées.
    """
    if not RL_OK:
        messagebox.showerror("ERAGROK", "ReportLab requis (pip install reportlab).")
        return

    safe_lbl = period_lbl.replace(" ","_").replace("/","-").replace("\n","_")[:20] or "courses"
    default  = _out_path(app, f"COURSES_{safe_lbl}")

    if ask_path and not print_after:
        path = filedialog.asksaveasfilename(
            title="Enregistrer liste de courses",
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialfile=os.path.basename(default),
        )
        if not path: return
    else:
        import tempfile as _tmp
        if print_after:
            _tf = _tmp.NamedTemporaryFile(suffix=".pdf", delete=False)
            path = _tf.name
            _tf.close()
        else:
            path = default

    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units  import mm
    from reportlab.platypus   import (SimpleDocTemplate, Paragraph, Spacer,
                                       Table, TableStyle, HRFlowable)
    from reportlab.lib        import colors

    ACC   = colors.HexColor("#f97316")
    DARK  = colors.HexColor("#1e1030")
    GRAY2 = colors.HexColor("#f5f5fc")
    GRAY  = colors.HexColor("#ebebf5")
    MUTED = colors.HexColor("#666688")
    BLACK = colors.black
    WHITE = colors.white

    PAGE_W, PAGE_H = A4
    MARGIN = 14 * mm
    USABLE = PAGE_W - 2 * MARGIN

    sTitle  = ParagraphStyle("sT",  fontSize=16, textColor=ACC,  fontName="Helvetica-Bold", spaceAfter=2)
    sSub    = ParagraphStyle("sS",  fontSize=9,  textColor=MUTED, fontName="Helvetica",      spaceAfter=2)
    sDate   = ParagraphStyle("sDt", fontSize=8,  textColor=MUTED, fontName="Helvetica-Oblique", spaceAfter=6)
    sCat    = ParagraphStyle("sCat",fontSize=9,  textColor=WHITE, fontName="Helvetica-Bold",  leftIndent=4)
    sFoodN  = ParagraphStyle("sFN", fontSize=8.5,textColor=BLACK, fontName="Helvetica",       leftIndent=4)
    sFoodQ  = ParagraphStyle("sFQ", fontSize=8.5,textColor=ACC,   fontName="Helvetica-Bold",  alignment=2)
    sFooter = ParagraphStyle("sF",  fontSize=7,  textColor=MUTED, fontName="Helvetica-Oblique", alignment=1)
    sTotLbl = ParagraphStyle("sTL", fontSize=10, textColor=MUTED, fontName="Helvetica-Bold")
    sTotVal = ParagraphStyle("sTV", fontSize=12, textColor=ACC,   fontName="Helvetica-Bold",  alignment=2)

    # ── Construire toutes les lignes en une seule Table ───────────────────────
    all_rows   = []
    row_styles = []
    row_idx    = 0
    n_items    = 0

    for cat, items in shopping.items():
        if not items: continue

        # Ligne header catégorie (couvre les 2 colonnes)
        all_rows.append([Paragraph(f"  {cat}", sCat), ""])
        row_styles += [
            ("BACKGROUND",    (0, row_idx), (-1, row_idx), DARK),
            ("SPAN",          (0, row_idx), (-1, row_idx)),
            ("TOPPADDING",    (0, row_idx), (-1, row_idx), 5),
            ("BOTTOMPADDING", (0, row_idx), (-1, row_idx), 5),
        ]
        row_idx += 1

        for i, (food, g_raw, label, note) in enumerate(items):
            bg = GRAY2 if i % 2 == 0 else WHITE
            note_str = f'  <font size="7" color="#888899">{note}</font>' if note else ""
            all_rows.append([
                Paragraph(f"{food}{note_str}", sFoodN),
                Paragraph(f"<b>{label}</b>", sFoodQ),
            ])
            row_styles += [
                ("BACKGROUND",    (0, row_idx), (-1, row_idx), bg),
                ("TOPPADDING",    (0, row_idx), (-1, row_idx), 2),
                ("BOTTOMPADDING", (0, row_idx), (-1, row_idx), 2),
            ]
            row_idx += 1
            n_items  += 1

    if not all_rows:
        messagebox.showinfo("ERAGROK", "Aucun aliment dans ce plan.")
        return

    main_tbl = Table(all_rows, colWidths=[USABLE * 0.74, USABLE * 0.26])
    main_tbl.setStyle(TableStyle([
        ("GRID",         (0, 0), (-1, -1), 0.25, colors.HexColor("#ddddee")),
        ("LEFTPADDING",  (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("FONTNAME",     (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE",     (0, 0), (-1, -1), 8.5),
    ] + row_styles))

    # ── Total estimé ──────────────────────────────────────────────────────────
    total_flowables = []
    if hasattr(app, "current_user") and shopping:
        try:
            from data.prices_module import compute_shopping_cost
            costs = compute_shopping_cost(shopping, app)
            if costs["total"] > 0:
                n_f, n_t = costs["nb_prices_found"], costs["nb_total"]
                total_flowables.append(HRFlowable(width="100%", thickness=1, color=ACC, spaceAfter=4))
                total_flowables.append(Table(
                    [[Paragraph("TOTAL ESTIMÉ", sTotLbl),
                      Paragraph(f"<b>≈ {costs['total']:.2f} €</b>  ({n_f}/{n_t} prix)", sTotVal)]],
                    colWidths=[USABLE * 0.55, USABLE * 0.45],
                ))
                total_flowables.append(Paragraph(
                    "Estimation : prix moyens Open Food Facts + marché France 2025",
                    ParagraphStyle("ps", fontSize=7, textColor=MUTED,
                                   fontName="Helvetica-Oblique", spaceBefore=2)
                ))
        except Exception:
            pass

    # ── Assembler le document ─────────────────────────────────────────────────
    doc = SimpleDocTemplate(
        path, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN,  bottomMargin=MARGIN,
        title=f"Liste de courses ERAGROK — {period_lbl}",
        author="ERAGROK",
    )

    period_clean = period_lbl.replace("\n", " ")
    story = [
        Paragraph("LISTE DE COURSES — ERAGROK", sTitle),
    ]
    if period_clean:
        story.append(Paragraph(period_clean, sSub))
    story += [
        Paragraph(
            f'Généré le {datetime.datetime.now().strftime("%d/%m/%Y à %H:%M")}'
            f' · {n_items} aliments · Quantités brutes à acheter',
            sDate
        ),
        HRFlowable(width="100%", thickness=1.5, color=ACC, spaceAfter=8),
        main_tbl,
        Spacer(1, 8),
    ] + total_flowables + [
        Spacer(1, 6),
        HRFlowable(width="100%", thickness=0.5, color=MUTED),
        Paragraph("ERAGROK — Coach Bodybuilding · Liste générée automatiquement", sFooter),
    ]

    doc.build(story)

    # ── Impression / ouverture cross-platform ─────────────────────────────────
    import subprocess as _sp, platform as _pl

    def _open_file(p):
        try:
            s = _pl.system()
            if s == "Windows" and hasattr(os, "startfile"): os.startfile(p)
            elif s == "Darwin":  _sp.Popen(["open",     p])
            else:                _sp.Popen(["xdg-open", p])
        except Exception: pass

    def _print_file(p):
        try:
            s = _pl.system()
            if s == "Windows" and hasattr(os, "startfile"):
                os.startfile(p, "print"); return True
            elif s == "Darwin":
                _sp.call(["lpr", p]); return True
            else:
                return _sp.call(["lpr", p], stdout=_sp.DEVNULL, stderr=_sp.DEVNULL) == 0
        except Exception:
            return False

    if print_after:
        if not _print_file(path):
            _open_file(path)
            messagebox.showinfo(
                "ERAGROK",
                "Impression automatique non disponible sur ce système.\n"
                "Le PDF s'ouvre — utilisez Fichier → Imprimer dans votre lecteur PDF."
            )
    else:
        if ask_path:
            messagebox.showinfo("ERAGROK", f"✅ Liste de courses exportée :\n{path}")
        else:
            _open_file(path)



def export_multiday_plan_pdf(app, days, ask_path=True):
    """
    Génère un PDF complet semaine/mois :
    - Page de garde avec résumé macro moyen
    - 1 section par jour avec tous les repas et aliments
    """
    if not RL_OK:
        messagebox.showerror("ERAGROK",
            "ReportLab n'est pas installé (pip install reportlab).")
        return

    n_days = len(days)
    mode_s = "Semaine" if n_days == 7 else f"{n_days}j"
    default = _out_path(app, f"PLAN_{mode_s.upper()}")

    if ask_path:
        path = filedialog.asksaveasfilename(
            title=f"Enregistrer le plan {mode_s}",
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialfile=os.path.basename(default),
        )
        if not path: return
    else:
        path = default

    doc = _mk_doc(path)
    st  = _styles()
    story = []

    ui   = getattr(app, "user_info", {}) or {}
    from data import utils as _utils
    dn   = ui.get("date_naissance", "")
    age  = _utils.age_depuis_naissance(dn) or ui.get("age", "—")
    name = ui.get("name", getattr(app, "selected_user_name", "—"))
    obj  = ui.get("objectif", "—")

    date_range = f"{days[0]['date']:%d/%m/%Y} → {days[-1]['date']:%d/%m/%Y}"

    # ── PAGE DE GARDE ─────────────────────────────────────────────────────────
    story.append(Paragraph("ERAGROK", st["cover_h1"]))
    story.append(Paragraph(
        f"Plan Alimentaire — {mode_s} ({n_days} jours)", st["cover_sub"]))
    _hr(story, _ACC, 1.5)
    story.append(Paragraph(
        f"Athlète : {name}   |   Âge : {age} ans   |   Objectif : {obj}   |   "
        f"Période : {date_range}",
        st["cover_info"]))
    _hr(story, _BORD)
    story.append(Spacer(1, 6*mm))

    # Moyennes macro
    avg_cal  = sum(sum(m["tot_cal"] for m in d["plan"]) for d in days)/n_days
    avg_prot = sum(sum(m["tot_p"]   for m in d["plan"]) for d in days)/n_days
    avg_gluc = sum(sum(m["tot_g"]   for m in d["plan"]) for d in days)/n_days
    avg_lip  = sum(sum(m["tot_l"]   for m in d["plan"]) for d in days)/n_days

    story.append(Paragraph("Moyennes journalières", st["sec_hdr"]))
    mac_rows = [
        [Paragraph(h, st["muted"]) for h in ["Macro","Moy. / jour","% kcal"]],
        [Paragraph("🔥 Calories",  st["body"]),
         Paragraph(f"{avg_cal:.0f} kcal", st["body"]),
         Paragraph("100%", st["body"])],
        [Paragraph("🥩 Protéines", st["body"]),
         Paragraph(f"{avg_prot:.0f} g", st["body"]),
         Paragraph(f"{avg_prot*4/avg_cal*100:.0f}%" if avg_cal else "—", st["body"])],
        [Paragraph("🍚 Glucides",  st["body"]),
         Paragraph(f"{avg_gluc:.0f} g", st["body"]),
         Paragraph(f"{avg_gluc*4/avg_cal*100:.0f}%" if avg_cal else "—", st["body"])],
        [Paragraph("🥑 Lipides",   st["body"]),
         Paragraph(f"{avg_lip:.0f} g", st["body"]),
         Paragraph(f"{avg_lip*9/avg_cal*100:.0f}%" if avg_cal else "—", st["body"])],
    ]
    t = _tbl(mac_rows, [70, 50, 30])
    if t: story.append(t)
    story.append(Spacer(1, 6*mm))

    # ── Tableau récap semaine (1 ligne / jour) ────────────────────────────────
    story.append(Paragraph("Vue d'ensemble", st["sec_hdr"]))
    recap_rows = [[Paragraph(h, st["muted"]) for h in
                   ["Jour","Date","Cal.","Prot.","Gluc.","Lip."]]]
    for d in days:
        tc = sum(m["tot_cal"] for m in d["plan"])
        tp = sum(m["tot_p"]   for m in d["plan"])
        tg = sum(m["tot_g"]   for m in d["plan"])
        tl = sum(m["tot_l"]   for m in d["plan"])
        recap_rows.append([
            Paragraph(d["label"].split()[0], st["small"]),
            Paragraph(d["date"].strftime("%d/%m"), st["small"]),
            Paragraph(f"{tc:.0f}", st["small"]),
            Paragraph(f"{tp:.0f}g", st["small"]),
            Paragraph(f"{tg:.0f}g", st["small"]),
            Paragraph(f"{tl:.0f}g", st["small"]),
        ])
    t = _tbl(recap_rows, [28, 24, 24, 24, 24, 24])
    if t: story.append(t)

    story.append(PageBreak())

    # ── 1 page par jour ───────────────────────────────────────────────────────
    SLOT_ICONS = {"matin":"Matin","midi":"Midi","collation":"Collation",
                  "soir":"Soir","coucher":"Coucher"}

    for di, d in enumerate(days):
        plan = d["plan"]
        tc   = sum(m["tot_cal"] for m in plan)
        tp   = sum(m["tot_p"]   for m in plan)
        tg   = sum(m["tot_g"]   for m in plan)
        tl   = sum(m["tot_l"]   for m in plan)

        # En-tête journée
        story.append(Paragraph(
            f"{d['label']}  —  {tc:.0f} kcal | {tp:.0f}g P · {tg:.0f}g G · {tl:.0f}g L",
            st["week_main"]))
        _hr(story, _ACC, 1.0)
        story.append(Spacer(1, 3*mm))

        for meal in plan:
            story.append(Paragraph(
                f"{SLOT_ICONS.get(meal['type'],'')}  {meal['name'].strip()}  "
                f"— {meal['tot_cal']:.0f} kcal | "
                f"{meal['tot_p']:.0f}P · {meal['tot_g']:.0f}G · {meal['tot_l']:.0f}L",
                st["sec_hdr"]))

            if meal["items"]:
                rows = [[Paragraph(h, st["muted"]) for h in
                         ["Aliment","Qté","kcal","P","G","L"]]]
                for item in meal["items"]:
                    rows.append([
                        Paragraph(item["food"], st["small"]),
                        Paragraph(f"{item['g']:.0f}g", st["small"]),
                        Paragraph(f"{item['kcal']:.0f}", st["small"]),
                        Paragraph(f"{item['p']:.1f}", st["small"]),
                        Paragraph(f"{item['g_']:.1f}", st["small"]),
                        Paragraph(f"{item['l']:.1f}", st["small"]),
                    ])
                rows.append([
                    Paragraph("TOTAL", st["accent"]),
                    Paragraph("", st["small"]),
                    Paragraph(f"{meal['tot_cal']:.0f}", st["accent"]),
                    Paragraph(f"{meal['tot_p']:.1f}", st["accent"]),
                    Paragraph(f"{meal['tot_g']:.1f}", st["accent"]),
                    Paragraph(f"{meal['tot_l']:.1f}", st["accent"]),
                ])
                t = _tbl(rows, [62, 20, 20, 20, 20, 20])
                if t: story.append(t)
            story.append(Spacer(1, 3*mm))

        # Saut de page sauf dernier jour
        if di < len(days)-1:
            story.append(PageBreak())

    # ── Pied de page ──────────────────────────────────────────────────────────
    story.append(Spacer(1, 8*mm))
    _hr(story, _BORD)
    story.append(Paragraph(
        "Plans générés par ERAGROK. Macros calculées sur ton TDEE + objectif profil. "
        "Variation quotidienne garantie — aliments incompatibles automatiquement séparés.",
        st["muted"]))

    try:
        doc.build(story)
        messagebox.showinfo("ERAGROK", f"✅ Plan {mode_s} exporté :\n{path}")
        try:
            import subprocess, sys
            if sys.platform == "win32":   os.startfile(path)
            elif sys.platform == "darwin": subprocess.Popen(["open", path])
            else:                          subprocess.Popen(["xdg-open", path])
        except Exception:
            pass
    except Exception as e:
        messagebox.showerror("ERAGROK", f"Erreur génération PDF : {e}")
