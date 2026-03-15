# data/pdf_utils.py — THRESHOLD · Rapport PDF semaine par semaine
# ─────────────────────────────────────────────────────────────────────────────
# Copie quasi-verbatim de pdf_utils.py ERAGROK.
# Seuls changements :
#   - app (objet CTk) devient app_state (dict) partout
#   - tkinter / filedialog / messagebox supprimes
#   - chemins sauvegardes sur Bureau/Documents automatiquement
#   - snack-bar Flet pour feedback utilisateur (page= optionnel)
#   - PRODUCT_INFO importe depuis data.cycle ou data.widgets en fallback
#   - export_unified_pdf ajoute (rapport hebdo complet, absent de la version precedente)
# ─────────────────────────────────────────────────────────────────────────────
import os, datetime, subprocess, sys, re as _re
from pathlib import Path
from collections import defaultdict

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table,
        TableStyle, HRFlowable, PageBreak, KeepTogether,
    )
    RL_OK = True
except ImportError:
    RL_OK = False

_PW, _PH = A4 if RL_OK else (595, 842)
_ML = _MR = _MT = _MB = 12 * mm
_W  = _PW - _ML - _MR      # usable width ~171 mm

# Palette identique ERAGROK
if RL_OK:
    _ACC   = colors.HexColor("#f97316")
    _ACC2  = colors.HexColor("#fdba74")
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
        "cover_h1":  s("CH1", fontSize=36, textColor=_ACC,   leading=42, spaceAfter=4),
        "cover_sub": s("CS",  fontSize=13, textColor=_ACC2,  leading=16, spaceAfter=8),
        "cover_info":s("CI",  fontSize=10, textColor=_WHITE, leading=14, spaceAfter=3),
        "cover_disc":s("CD",  fontSize=7,  textColor=_MUTED, leading=10, spaceAfter=2),
        "week_main": s("WM",  fontSize=13, textColor=_ACC,   leading=16, spaceBefore=0, spaceAfter=2),
        "sec_hdr":   s("SH",  fontSize=9,  textColor=_ACC2,  leading=12, spaceBefore=4, spaceAfter=2),
        "h1":        s("H1",  fontSize=11, textColor=_ACC,   leading=14, spaceBefore=4, spaceAfter=2),
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
    if not RL_OK or not rows: return None
    tbl = Table(rows, colWidths=[c*mm for c in col_mm], rowHeights=None, repeatRows=1)
    base = [
        ("BACKGROUND",    (0,0), (-1,0),  _DARK4),
        ("TEXTCOLOR",     (0,0), (-1,0),  _ACC),
        ("FONTNAME",      (0,0), (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,-1), 7),
        ("FONTNAME",      (0,1), (-1,-1), "Helvetica"),
        ("TEXTCOLOR",     (0,1), (-1,-1), _WHITE),
        ("BACKGROUND",    (0,1), (-1,-1), _DARK2),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [_DARK2, _DARK3]),
        ("GRID",          (0,0), (-1,-1), 0.3, _BORD),
        ("ALIGN",         (0,0), (-1,-1), "LEFT"),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING",    (0,0), (-1,-1), 3),
        ("BOTTOMPADDING", (0,0), (-1,-1), 3),
        ("LEFTPADDING",   (0,0), (-1,-1), 4),
        ("RIGHTPADDING",  (0,0), (-1,-1), 4),
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
    iso    = d.isocalendar()
    monday = d - datetime.timedelta(days=d.weekday())
    return (iso[0], iso[1], monday)


def _weeks_range(start, n_weeks):
    monday = start - datetime.timedelta(days=start.weekday())
    return [monday + datetime.timedelta(weeks=i) for i in range(n_weeks)]


def _out_path(app_state, suffix):
    desktop = Path.home() / "Desktop"
    docs    = Path.home() / "Documents"
    base    = desktop if desktop.exists() else (docs if docs.exists() else Path.home())
    name    = app_state.get("current_user","threshold") or "threshold"
    return str(base / f"THRESHOLD_{name}_{suffix}_{datetime.date.today():%Y%m%d}.pdf")


def _mk_doc(path):
    return SimpleDocTemplate(
        path, pagesize=A4,
        leftMargin=_ML, rightMargin=_MR,
        topMargin=_MT,  bottomMargin=_MB,
        title="Rapport THRESHOLD",
    )


def _open_file(path):
    try:
        s = sys.platform
        if s == "win32" and hasattr(os,"startfile"): os.startfile(path)
        elif s == "darwin": subprocess.Popen(["open",     path])
        else:               subprocess.Popen(["xdg-open", path])
    except Exception:
        pass


def _snack(page, msg, color="#22c55e"):
    """Compatibilité — délègue vers ui.snackbar centralisé."""
    from ui.snackbar import snack, _LEVEL_COLORS
    _col_to_level = {v: k for k, v in _LEVEL_COLORS.items()}
    level = _col_to_level.get(color, "success")
    snack(page, msg, level)


def _ui(app_state):
    ui = app_state.get("user_info") or {}
    if not ui:
        try:
            from data import db as _db
            ui = _db.profil_get(app_state) or {}
        except Exception:
            pass
    return ui


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE DE GARDE  (identique ERAGROK)
# ══════════════════════════════════════════════════════════════════════════════
def _build_cover(app_state, story, st):
    ui  = _ui(app_state)
    try:
        from data import utils as _utils
        dn  = ui.get("date_naissance","")
        age = _utils.age_depuis_naissance(dn) or ui.get("age","—")
    except Exception:
        age = ui.get("age","—")

    story.append(Spacer(1, 30*mm))
    story.append(Paragraph("THRESHOLD", st["cover_h1"]))
    story.append(Paragraph(
        "Journal de suivi — Entrainement · Nutrition · Cycle hormonal",
        st["cover_sub"]))
    _hr(story, _ACC, 1.5)
    story.append(Spacer(1, 8*mm))

    rows = [
        [Paragraph("Athlete",  st["muted"]), Paragraph(str(ui.get("name","—")),      st["body"])],
        [Paragraph("Age",      st["muted"]), Paragraph(f"{age} ans",                 st["body"])],
        [Paragraph("Sexe",     st["muted"]), Paragraph(str(ui.get("sexe","—")),       st["body"])],
        [Paragraph("Taille",   st["muted"]), Paragraph(f"{ui.get('taille','—')} cm", st["body"])],
        [Paragraph("Objectif", st["muted"]), Paragraph(str(ui.get("objectif","—")),  st["body"])],
        [Paragraph("Genere",   st["muted"]), Paragraph(datetime.date.today().strftime("%d/%m/%Y"), st["body"])],
    ]
    t = _tbl(rows, [32,110])
    if t: story.append(t)

    story.append(Spacer(1, 12*mm))
    _hr(story, _BORD)
    story.append(Paragraph(
        "Ce document est genere automatiquement par THRESHOLD a des fins de suivi personnel. "
        "Les informations relatives aux substances sont fournies a titre educatif uniquement.",
        st["cover_disc"]))


# ══════════════════════════════════════════════════════════════════════════════
#  GÉNÉRATEUR DE PAGES SEMAINES  (coeur du rapport — copie verbatim ERAGROK)
#  Chaque page = 1 semaine ISO :  Entrainement | Nutrition | Cycle
# ══════════════════════════════════════════════════════════════════════════════
def _build_weekly_pages(app_state, story, st,
                        include_nut=True, include_train=True, include_cycle=True):
    try:
        from data import db as _db
    except Exception:
        return

    nut_rows  = _db.nutrition_get_all(app_state)  or []
    plan_rows = _db.planning_get_all(app_state)   or []
    hist_rows = _db.history_get_all(app_state)    or []
    cycle     = _db.cycle_get_active(app_state)

    cycle_debut   = _parse_date(cycle.get("debut",""))      if cycle else None
    cycle_len     = int(cycle.get("longueur_sem","12"))      if cycle else 12
    produits_s    = cycle.get("produits_doses","")           if cycle else ""
    washout_w     = 2
    cycle_pct_start = (cycle_debut + datetime.timedelta(weeks=cycle_len+washout_w)) if cycle_debut else None

    # PRODUCT_INFO — essaie cycle.py d'abord, fallback widgets
    PRODUCT_INFO = {}
    try:
        from data.cycle import PRODUCT_INFO as _PI
        PRODUCT_INFO = _PI
    except Exception:
        try:
            from data.widgets import HALF_LIVES
            PRODUCT_INFO = {k: {"demi_vie": f"{v}j","utilite":"—"} for k,v in HALF_LIVES.items()}
        except Exception:
            pass

    _PCT_NAMES = {"Clomiphene (Clomid)","Tamoxifen (Nolvadex)"}
    prod_doses = {}
    if produits_s:
        for e in produits_s.split("|"):
            e = e.strip()
            if e.startswith("[PCT]"): e = e[5:]
            if "_J+" in e: continue
            parts = e.split(":",1)
            prod_doses[parts[0].strip()] = parts[1].strip() if len(parts)>1 else ""

    def _group_by_week(rows, date_keys):
        bw = {}
        for r in rows:
            d = None
            for k in date_keys:
                d = _parse_date(r.get(k,""))
                if d: break
            if not d: continue
            wk = _iso_week(d)
            bw.setdefault(wk,[]).append((d,r))
        return bw

    nut_by_week  = _group_by_week(nut_rows,  ["date"])
    plan_by_week = _group_by_week(plan_rows, ["date"])
    hist_by_week = _group_by_week(hist_rows, ["planned_for","date"])

    all_weeks = sorted(set(list(nut_by_week)+list(plan_by_week)+list(hist_by_week)))
    if not all_weeks:
        story.append(Paragraph("Aucune donnee enregistree.", st["muted"]))
        return

    if cycle_debut:
        pct_weeks = 4
        total_w   = cycle_len + washout_w + pct_weeks
        for monday in _weeks_range(cycle_debut, total_w):
            wk = _iso_week(monday)
            if wk not in all_weeks:
                all_weeks.append(wk)
        all_weeks.sort()

    for wk in all_weeks[-52:]:
        year, wnum, monday = wk
        sunday = monday + datetime.timedelta(days=6)

        # Phase cycle
        phase_txt = ""
        if cycle_debut:
            days_in = (monday - cycle_debut).days
            week_n  = days_in // 7 + 1
            if 1 <= week_n <= cycle_len:
                phase_txt = f"  ·  CYCLE S{week_n}/{cycle_len}"
            elif week_n == cycle_len+1 or week_n == cycle_len+2:
                phase_txt = f"  ·  WASHOUT S{week_n-cycle_len}/{washout_w}"
            elif cycle_pct_start and monday >= cycle_pct_start:
                pct_w = ((monday-cycle_pct_start).days//7)+1
                phase_txt = f"  ·  PCT S{pct_w}"

        story.append(Paragraph(
            f"Sem. {wnum} / {year}   {monday:%d/%m} -> {sunday:%d/%m/%Y}{phase_txt}",
            st["week_main"]))
        story.append(HRFlowable(width="100%", thickness=1.5, color=_ACC,
                                spaceAfter=6, spaceBefore=0))

        # ① ENTRAINEMENT
        if include_train:
            story.append(Paragraph("  ENTRAINEMENT", st["sec_hdr"]))

        plan_days = sorted(plan_by_week.get(wk,[]), key=lambda x:x[0])
        hist_days = sorted(hist_by_week.get(wk,[]), key=lambda x:x[0])

        if plan_days:
            by_day = defaultdict(list)
            for d,r in plan_days: by_day[d].append(r)
            rows_t = [[Paragraph("Jour",st["muted"]),
                       Paragraph("Groupes",st["muted"]),
                       Paragraph("Exercices",st["muted"])]]
            for d in sorted(by_day):
                recs    = by_day[d]
                groupes = " / ".join(sorted({r.get("groupes","").strip() for r in recs if r.get("groupes","")}))
                lines   = [r.get("line","").strip() for r in recs if r.get("line","")]
                lines   = [_re.sub(r'\s*\([A-Z0-9_]+\)\s*$','',l).strip() for l in lines]
                ex_txt  = _clip(" · ".join(lines[:4]),70)
                rows_t.append([
                    Paragraph(f"{_DAY_FR[d.weekday()]} {d:%d/%m}",st["small"]),
                    Paragraph(_clip(groupes,22),st["small"]),
                    Paragraph(ex_txt,st["small"]),
                ])
            for wd in range(7):
                d = monday + datetime.timedelta(days=wd)
                if d not in by_day:
                    rows_t.append([
                        Paragraph(f"{_DAY_FR[wd]} {d:%d/%m}",st["muted"]),
                        Paragraph("—",st["muted"]),
                        Paragraph("Repos",st["muted"]),
                    ])
            t = _tbl(rows_t,[18,30,94])
            if t: story.append(t)
        elif hist_days:
            rows_t = [[Paragraph("Date",st["muted"]),
                       Paragraph("Type",st["muted"]),
                       Paragraph("Exercices",st["muted"])]]
            for d,r in hist_days:
                exs = r.get("exercises",[])
                rows_t.append([
                    Paragraph(str(r.get("date",""))[:10],st["small"]),
                    Paragraph(_clip(r.get("type",""),18),st["small"]),
                    Paragraph(_clip(" / ".join(str(e) for e in exs[:4]),60),st["small"]),
                ])
            t = _tbl(rows_t,[22,28,92])
            if t: story.append(t)
        else:
            story.append(Paragraph("  Aucune seance planifiee cette semaine.",st["muted"]))

        story.append(Spacer(1,5*mm))

        # ② NUTRITION
        if include_nut:
            story.append(Paragraph("  NUTRITION",st["sec_hdr"]))

        nut_days = sorted(nut_by_week.get(wk,[]),key=lambda x:x[0])
        if nut_days:
            rows_n = [[Paragraph(h,st["muted"]) for h in
                       ["Jour","Poids","Calories","Prot.","Gluc.","Lip.","Note"]]]
            cal_v=[]; prot_v=[]; gluc_v=[]; lip_v=[]; pds_v=[]
            for d,r in nut_days:
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
                    Paragraph(f"{_DAY_FR[d.weekday()]} {d:%d/%m}",st["small"]),
                    Paragraph(f"{pds:.1f}" if pds else "—",st["small"]),
                    Paragraph(f"{cal:.0f}" if cal else "—",st["small"]),
                    Paragraph(f"{prot:.0f}" if prot else "—",st["small"]),
                    Paragraph(f"{gluc:.0f}" if gluc else "—",st["small"]),
                    Paragraph(f"{lip:.0f}"  if lip  else "—",st["small"]),
                    Paragraph(_clip(str(r.get("note","")),24),st["muted"]),
                ])
            def _avg(lst): return f"{sum(lst)/len(lst):.1f}" if lst else "—"
            rows_n.append([
                Paragraph("MOY",       st["muted"]),
                Paragraph(_avg(pds_v), st["accent"]),
                Paragraph(_avg(cal_v), st["accent"]),
                Paragraph(_avg(prot_v),st["accent"]),
                Paragraph(_avg(gluc_v),st["accent"]),
                Paragraph(_avg(lip_v), st["accent"]),
                Paragraph("",          st["muted"]),
            ])
            moy_extras = [
                ("FONTNAME",   (0,-1),(-1,-1),"Helvetica-Bold"),
                ("BACKGROUND", (0,-1),(-1,-1),_DARK4),
                ("TEXTCOLOR",  (0,-1),(-1,-1),_ACC),
            ]
            t = _tbl(rows_n,[18,14,20,16,16,14,44],moy_extras)
            if t: story.append(t)
        else:
            story.append(Paragraph("  Aucune donnee nutrition cette semaine.",st["muted"]))

        story.append(Spacer(1,5*mm))

        # ③ CYCLE HORMONAL
        if include_cycle:
            story.append(Paragraph("  CYCLE HORMONAL",st["sec_hdr"]))
            if not cycle_debut:
                story.append(Paragraph("  Aucun cycle enregistre.",st["muted"]))
            else:
                days_in = (monday - cycle_debut).days
                week_n  = days_in // 7 + 1

                if 1 <= week_n <= cycle_len:
                    active = {p:d for p,d in prod_doses.items() if p not in _PCT_NAMES}
                    if active:
                        rows_c = [[Paragraph("Produit",st["muted"]),
                                   Paragraph("Dose",st["muted"]),
                                   Paragraph("Utilite",st["muted"]),
                                   Paragraph("Demi-vie",st["muted"])]]
                        for pname,dose in active.items():
                            info = PRODUCT_INFO.get(pname,{})
                            rows_c.append([
                                Paragraph(_clip(pname,28),st["small"]),
                                Paragraph(dose or "—",st["small"]),
                                Paragraph(_clip(info.get("utilite","—"),36),st["muted"]),
                                Paragraph(_clip(info.get("demi_vie","—"),20),st["muted"]),
                            ])
                        t = _tbl(rows_c,[40,20,60,22])
                        if t: story.append(t)
                    else:
                        story.append(Paragraph("  Produits actifs — voir configuration cycle.",st["muted"]))
                elif week_n == cycle_len+1 or week_n == cycle_len+2:
                    story.append(Paragraph("  WASHOUT — Arret de tous les produits du cycle.",st["warn"]))
                    story.append(Paragraph("  Surveiller : recuperation testiculaire, libido, energie.",st["muted"]))
                elif cycle_pct_start and monday >= cycle_pct_start:
                    pct_w = ((monday-cycle_pct_start).days//7)+1
                    story.append(Paragraph(f"  PCT — Semaine {pct_w}",st["ok"]))
                    pct_prods = {p:d for p,d in prod_doses.items() if p in _PCT_NAMES}
                    if pct_prods:
                        rows_pct = [[Paragraph("Produit",st["muted"]),
                                     Paragraph("Dose",st["muted"]),
                                     Paragraph("Role",st["muted"])]]
                        for pname,dose in pct_prods.items():
                            info = PRODUCT_INFO.get(pname,{})
                            rows_pct.append([
                                Paragraph(_clip(pname,30),st["small"]),
                                Paragraph(dose or "voir protocole",st["small"]),
                                Paragraph(_clip(info.get("utilite","Relance axe HPTA"),36),st["muted"]),
                            ])
                        t = _tbl(rows_pct,[50,40,52])
                        if t: story.append(t)
                    else:
                        story.append(Paragraph(
                            "  Clomid 50->25 mg/j + Nolvadex 20->10 mg/j (protocole standard 4 semaines)",
                            st["small"]))
                elif week_n < 1:
                    story.append(Paragraph("  Cycle pas encore demarre.",st["muted"]))
                else:
                    story.append(Paragraph("  Cycle termine.",st["muted"]))

        story.append(Spacer(1,4*mm))
        story.append(HRFlowable(width="100%",thickness=0.3,color=_BORD,
                                spaceAfter=2,spaceBefore=2))
        user_name = app_state.get("current_user","") or ""
        story.append(Paragraph(
            f"THRESHOLD  ·  {user_name}"
            f"  ·  Sem. {wnum}/{year}  ·  genere le {datetime.date.today():%d/%m/%Y}",
            st["muted"]))
        story.append(PageBreak())


# ══════════════════════════════════════════════════════════════════════════════
#  COMPARAISON 2 CYCLES
# ══════════════════════════════════════════════════════════════════════════════
def _build_compare_cycles(app_state, story, st):
    try:
        from data import db as _db
        rows = _db.cycle_get_all(app_state)
    except Exception:
        return
    if not rows or len(rows) < 2:
        story.append(Paragraph("Un seul cycle disponible — pas de comparaison possible.",st["muted"]))
        return
    c1, c2 = dict(rows[-2]), dict(rows[-1])
    story.append(Paragraph("COMPARAISON DES 2 DERNIERS CYCLES",st["h1"]))
    _hr(story, _ACC, 1)
    headers = ["","Cycle N-1","Cycle actuel"]
    data = [
        ["Debut",       c1.get("debut","—"),                    c2.get("debut","—")],
        ["Fin estimee", c1.get("fin_estimee","—"),              c2.get("fin_estimee","—")],
        ["Duree (sem)", c1.get("longueur_sem","—"),             c2.get("longueur_sem","—")],
        ["Produits",    _clip(c1.get("produits_doses","—"),40), _clip(c2.get("produits_doses","—"),40)],
        ["Note",        _clip(c1.get("note","—"),30),           _clip(c2.get("note","—"),30)],
    ]
    rows_t = [[Paragraph(str(c), st["muted"] if i==0 else st["body"])
               for i,c in enumerate(row)]
              for row in [headers]+data]
    t = _tbl(rows_t,[38,72,72])
    if t: story.append(t)
    story.append(PageBreak())


# ══════════════════════════════════════════════════════════════════════════════
#  EXPORT UNIFIE  (rapport hebdomadaire — fonctionnalite principale ERAGROK)
# ══════════════════════════════════════════════════════════════════════════════
def export_unified_pdf(app_state, path=None, page=None, sections=None):
    """
    Rapport PDF semaine par semaine.
    sections = dict {cover, nutrition, training, cycle, compare} — tout True par defaut.
    """
    if not RL_OK:
        _snack(page,"ReportLab non installe (pip install reportlab)","#ef4444")
        return None
    if sections is None:
        sections = {"cover":True,"nutrition":True,"training":True,
                    "cycle":True,"compare":False}

    path = path or _out_path(app_state,"rapport")
    Path(path).parent.mkdir(parents=True, exist_ok=True)

    st    = _styles()
    doc   = _mk_doc(path)
    story = []

    if sections.get("cover",True):
        _build_cover(app_state, story, st)
        story.append(PageBreak())

    if sections.get("compare") and sections.get("cycle",True):
        _build_compare_cycles(app_state, story, st)

    _build_weekly_pages(app_state, story, st,
                        include_nut=sections.get("nutrition",True),
                        include_train=sections.get("training",True),
                        include_cycle=sections.get("cycle",True))

    if story and isinstance(story[-1], PageBreak):
        story.pop()

    try:
        doc.build(story)
        _snack(page, f"Rapport PDF exporte : {Path(path).name}")
        _open_file(path)
        return path
    except Exception as e:
        _snack(page, f"Erreur PDF : {e}", "#ef4444")
        return None


# Aliases standalone (meme comportement qu'ERAGROK)
def export_cycle_pdf(app_state, path=None, page=None):
    return export_unified_pdf(app_state, path, page,
        sections={"cover":True,"nutrition":False,"training":False,
                  "cycle":True,"compare":False})

def export_nutrition_pdf(app_state, path=None, page=None):
    return export_unified_pdf(app_state, path, page,
        sections={"cover":True,"nutrition":True,"training":False,
                  "cycle":False,"compare":False})

def export_entrainement_pdf(app_state, path=None, page=None):
    return export_unified_pdf(app_state, path, page,
        sections={"cover":True,"nutrition":False,"training":True,
                  "cycle":False,"compare":False})


# ══════════════════════════════════════════════════════════════════════════════
#  EXPORT PDF NUTRITION COMPLET (historique + plan alimentaire)
# ══════════════════════════════════════════════════════════════════════════════
def export_nutrition_full_pdf(app_state, path=None, page=None):
    if not RL_OK:
        _snack(page,"ReportLab non installe (pip install reportlab)","#ef4444")
        return None

    path = path or _out_path(app_state,"NUTRITION")
    Path(path).parent.mkdir(parents=True, exist_ok=True)

    try:
        from data import db as _db, utils as _utils
    except Exception as ex:
        _snack(page, f"Import erreur : {ex}","#ef4444"); return None

    doc   = _mk_doc(path)
    st    = _styles()
    story = []

    ui     = _ui(app_state)
    name   = ui.get("name", app_state.get("current_user","—"))
    age    = ui.get("age","—")
    obj    = ui.get("objectif","—")
    poids  = ui.get("poids","—")
    taille = ui.get("taille","—")
    try:
        imc_val, imc_cat = _utils.calculer_imc(float(poids), float(taille))
        imc_str = f"{imc_val:.1f} — {imc_cat[0]}"
    except Exception:
        imc_str = "—"

    story.append(Paragraph("THRESHOLD",st["cover_h1"]))
    story.append(Paragraph("Bilan Nutrition",st["cover_sub"]))
    _hr(story,_ACC,1.5)
    story.append(Paragraph(f"Athlete : {name}   |   Age : {age} ans   |   Objectif : {obj}",st["cover_info"]))
    story.append(Paragraph(f"Poids : {poids} kg   |   Taille : {taille} cm   |   IMC : {imc_str}",st["cover_info"]))
    story.append(Paragraph(f"Exporte le : {datetime.date.today():%d/%m/%Y}",st["cover_info"]))
    _hr(story,_BORD)
    story.append(Spacer(1,8*mm))

    story.append(Paragraph("Historique Nutrition",st["sec_hdr"]))
    _hr(story)
    rows_data = []
    try: rows_data = _db.nutrition_get_all(app_state)
    except Exception: pass

    if rows_data:
        hdr = [Paragraph(h,st["muted"]) for h in
               ["Date","Poids (kg)","Calories","Proteines","Glucides","Lipides","Note"]]
        tbl_rows = [hdr]
        for r in rows_data:
            tbl_rows.append([
                Paragraph(r.get("date",""),      st["small"]),
                Paragraph(r.get("poids",""),     st["small"]),
                Paragraph(r.get("calories",""),  st["small"]),
                Paragraph(r.get("proteines",""), st["small"]),
                Paragraph(r.get("glucides",""),  st["small"]),
                Paragraph(r.get("lipides",""),   st["small"]),
                Paragraph(_clip(r.get("note",""),30),st["small"]),
            ])
        t = _tbl(tbl_rows,[28,20,22,22,22,22,34],rh=14)
        if t: story.append(t)
    else:
        story.append(Paragraph("Aucune donnee enregistree.",st["muted"]))

    story.append(Spacer(1,8*mm))

    last      = app_state.get("last_meal_plan")
    plan_days = None
    if last:
        if last.get("days"):   plan_days = last["days"]
        elif last.get("plan"): plan_days = [{"date":datetime.date.today(),"label":"Jour 1","plan":last["plan"]}]

    SLOT_ICONS = {"matin":"Matin","midi":"Midi","collation":"Collation","soir":"Soir","coucher":"Coucher"}

    if plan_days:
        story.append(PageBreak())
        story.append(Paragraph("Plan Alimentaire",st["sec_hdr"]))
        _hr(story,_ACC,1)
        for day_info in plan_days:
            plan = day_info.get("plan",[])
            story.append(Spacer(1,4*mm))
            story.append(Paragraph(f"{day_info.get('label','')}  {day_info.get('date','')}",st["week_main"]))
            _hr(story)
            tc=sum(m.get("tot_cal",0) for m in plan); tp=sum(m.get("tot_p",0) for m in plan)
            tg=sum(m.get("tot_g",0) for m in plan);  tl=sum(m.get("tot_l",0) for m in plan)
            story.append(Paragraph(f"{tc:.0f} kcal  |  {tp:.0f} g P  |  {tg:.0f} g G  |  {tl:.0f} g L",st["body"]))
            story.append(Spacer(1,3*mm))
            for meal in plan:
                lbl = SLOT_ICONS.get(meal.get("type",""),"")
                story.append(Paragraph(
                    f"{lbl}  {meal.get('name','')}  —  "
                    f"{meal.get('tot_cal',0):.0f} kcal | "
                    f"{meal.get('tot_p',0):.0f}g P · "
                    f"{meal.get('tot_g',0):.0f}g G · "
                    f"{meal.get('tot_l',0):.0f}g L",st["sec_hdr"]))
                items = meal.get("items",[])
                if items:
                    rows_m = [[Paragraph(h,st["muted"]) for h in ["Aliment","Qte","Kcal","P","G","L"]]]
                    for item in items:
                        rows_m.append([
                            Paragraph(item.get("food",""),st["small"]),
                            Paragraph(f"{item.get('g',0):.0f}g",st["small"]),
                            Paragraph(f"{item.get('kcal',0):.0f}",st["small"]),
                            Paragraph(f"{item.get('p',0):.1f}",st["small"]),
                            Paragraph(f"{item.get('g_',0):.1f}",st["small"]),
                            Paragraph(f"{item.get('l',0):.1f}",st["small"]),
                        ])
                    t = _tbl(rows_m,[55,18,18,18,18,18],rh=13)
                    if t: story.append(t)
                story.append(Spacer(1,2*mm))
    else:
        story.append(Paragraph("Aucun plan alimentaire genere.",st["muted"]))

    try:
        doc.build(story)
        _snack(page, f"PDF nutrition exporte : {Path(path).name}")
        _open_file(path)
        return path
    except Exception as e:
        _snack(page, f"Erreur PDF : {e}","#ef4444"); return None


# ══════════════════════════════════════════════════════════════════════════════
#  EXPORT — PLAN ALIMENTAIRE JOURNALIER
# ══════════════════════════════════════════════════════════════════════════════
def export_meal_plan_pdf(app_state, plan, path=None, page=None):
    if not RL_OK:
        _snack(page,"ReportLab non installe","#ef4444"); return None

    path = path or _out_path(app_state,"PLAN_ALIMENTAIRE")
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    doc=_mk_doc(path); st=_styles(); story=[]

    ui   = _ui(app_state)
    name = ui.get("name",app_state.get("current_user","—"))
    age  = ui.get("age","—"); obj=ui.get("objectif","—")

    story.append(Paragraph("THRESHOLD",st["cover_h1"]))
    story.append(Paragraph("Plan Alimentaire Journalier",st["cover_sub"]))
    _hr(story,_ACC,1.5)
    story.append(Paragraph(
        f"Athlete : {name}   |   Age : {age} ans   |   Objectif : {obj}   |   "
        f"Date : {datetime.date.today():%d/%m/%Y}",st["cover_info"]))
    _hr(story,_BORD)
    story.append(Spacer(1,6*mm))

    tot_cal=sum(m.get("tot_cal",0) for m in plan); tot_prot=sum(m.get("tot_p",0) for m in plan)
    tot_gluc=sum(m.get("tot_g",0) for m in plan); tot_lip=sum(m.get("tot_l",0) for m in plan)

    story.append(Paragraph("Recapitulatif macros",st["sec_hdr"]))
    mac_rows = [
        [Paragraph(h,st["muted"]) for h in ["Macro","Total","% kcal"]],
        [Paragraph("Calories",st["body"]),Paragraph(f"{tot_cal:.0f} kcal",st["body"]),Paragraph("100%",st["body"])],
        [Paragraph("Proteines",st["body"]),Paragraph(f"{tot_prot:.0f} g",st["body"]),
         Paragraph(f"{tot_prot*4/tot_cal*100:.0f}%" if tot_cal else "—",st["body"])],
        [Paragraph("Glucides",st["body"]),Paragraph(f"{tot_gluc:.0f} g",st["body"]),
         Paragraph(f"{tot_gluc*4/tot_cal*100:.0f}%" if tot_cal else "—",st["body"])],
        [Paragraph("Lipides",st["body"]),Paragraph(f"{tot_lip:.0f} g",st["body"]),
         Paragraph(f"{tot_lip*9/tot_cal*100:.0f}%" if tot_cal else "—",st["body"])],
    ]
    t=_tbl(mac_rows,[70,50,30])
    if t: story.append(t)
    story.append(Spacer(1,6*mm))

    SLOT_ICONS={"matin":"Matin","midi":"Midi","collation":"Collation","soir":"Soir","coucher":"Coucher"}
    for meal in plan:
        lbl=SLOT_ICONS.get(meal.get("type",""),"")
        story.append(Paragraph(
            f"{lbl}  {meal.get('name','')}  —  "
            f"{meal.get('tot_cal',0):.0f} kcal | "
            f"{meal.get('tot_p',0):.0f}g P · "
            f"{meal.get('tot_g',0):.0f}g G · "
            f"{meal.get('tot_l',0):.0f}g L",st["week_main"]))
        _hr(story)
        items=meal.get("items",[])
        if items:
            rows=[[Paragraph(h,st["muted"]) for h in ["Aliment","Quantite","Calories","Prot.","Glucides","Lipides"]]]
            for item in items:
                rows.append([
                    Paragraph(item.get("food",""),st["small"]),
                    Paragraph(f"{item.get('g',0):.0f} g",st["small"]),
                    Paragraph(f"{item.get('kcal',0):.0f}",st["small"]),
                    Paragraph(f"{item.get('p',0):.1f} g",st["small"]),
                    Paragraph(f"{item.get('g_',0):.1f} g",st["small"]),
                    Paragraph(f"{item.get('l',0):.1f} g",st["small"]),
                ])
            rows.append([
                Paragraph("TOTAL",st["accent"]),Paragraph("",st["small"]),
                Paragraph(f"{meal.get('tot_cal',0):.0f}",st["accent"]),
                Paragraph(f"{meal.get('tot_p',0):.1f} g",st["accent"]),
                Paragraph(f"{meal.get('tot_g',0):.1f} g",st["accent"]),
                Paragraph(f"{meal.get('tot_l',0):.1f} g",st["accent"]),
            ])
            t=_tbl(rows,[60,22,22,22,22,22])
            if t: story.append(t)
        else:
            story.append(Paragraph("Aucun aliment pour ce repas.",st["muted"]))
        story.append(Spacer(1,4*mm))

    story.append(Spacer(1,8*mm)); _hr(story,_BORD)
    story.append(Paragraph(
        "Ce plan a ete genere par THRESHOLD. Les quantites sont calculees pour correspondre "
        "a ton profil (TDEE + ajustement objectif). Adapte selon tes sensations.",st["muted"]))

    try:
        doc.build(story)
        _snack(page, f"Plan PDF exporte : {Path(path).name}")
        _open_file(path); return path
    except Exception as e:
        _snack(page, f"Erreur PDF : {e}","#ef4444"); return None


# ══════════════════════════════════════════════════════════════════════════════
#  EXPORT — LISTE DE COURSES  (identique ERAGROK)
# ══════════════════════════════════════════════════════════════════════════════
def export_shopping_pdf(app_state, shopping, period_lbl="",
                        path=None, page=None, print_after=False):
    if not RL_OK:
        _snack(page,"ReportLab requis (pip install reportlab)","#ef4444"); return None

    safe_lbl = period_lbl.replace(" ","_").replace("/","-").replace("\n","_")[:20] or "courses"
    path = path or _out_path(app_state,f"COURSES_{safe_lbl}")
    Path(path).parent.mkdir(parents=True, exist_ok=True)

    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib import colors as C

    ACC=C.HexColor("#f97316"); DARK=C.HexColor("#1e1030")
    GRAY2=C.HexColor("#f5f5fc"); WHITE=C.white; MUTED=C.HexColor("#666688"); BLACK=C.black

    PAGE_W,PAGE_H = A4
    MARGIN=14*mm; USABLE=PAGE_W-2*MARGIN

    sTitle  = ParagraphStyle("sT",fontSize=16,textColor=ACC, fontName="Helvetica-Bold",spaceAfter=2)
    sSub    = ParagraphStyle("sS",fontSize=9, textColor=MUTED,fontName="Helvetica",    spaceAfter=2)
    sDate   = ParagraphStyle("sDt",fontSize=8,textColor=MUTED,fontName="Helvetica-Oblique",spaceAfter=6)
    sCat    = ParagraphStyle("sCt",fontSize=9,textColor=C.white,fontName="Helvetica-Bold",leftIndent=4)
    sFoodN  = ParagraphStyle("sFN",fontSize=8,textColor=BLACK,fontName="Helvetica",    leftIndent=4)
    sFoodQ  = ParagraphStyle("sFQ",fontSize=8,textColor=ACC,  fontName="Helvetica-Bold",alignment=2)
    sFooter = ParagraphStyle("sF", fontSize=7,textColor=MUTED,fontName="Helvetica-Oblique",alignment=1)
    sTotLbl = ParagraphStyle("sTL",fontSize=10,textColor=MUTED,fontName="Helvetica-Bold")
    sTotVal = ParagraphStyle("sTV",fontSize=12,textColor=ACC,  fontName="Helvetica-Bold",alignment=2)

    all_rows=[]; row_styles=[]; row_idx=0; n_items=0

    for cat, items in shopping.items():
        if not items: continue
        all_rows.append([Paragraph(f"  {cat}",sCat),""])
        row_styles += [
            ("BACKGROUND",    (0,row_idx),(-1,row_idx),DARK),
            ("SPAN",          (0,row_idx),(-1,row_idx)),
            ("TOPPADDING",    (0,row_idx),(-1,row_idx),5),
            ("BOTTOMPADDING", (0,row_idx),(-1,row_idx),5),
        ]
        row_idx += 1
        for i,item in enumerate(items):
            food,_g_raw,label,note = (list(item)+["","","",""])[:4]
            bg = GRAY2 if i%2==0 else WHITE
            note_str = f'  <font size="7" color="#888899">{note}</font>' if note else ""
            all_rows.append([Paragraph(f"{food}{note_str}",sFoodN),Paragraph(f"<b>{label}</b>",sFoodQ)])
            row_styles += [
                ("BACKGROUND",    (0,row_idx),(-1,row_idx),bg),
                ("TOPPADDING",    (0,row_idx),(-1,row_idx),2),
                ("BOTTOMPADDING", (0,row_idx),(-1,row_idx),2),
            ]
            row_idx+=1; n_items+=1

    if not all_rows:
        _snack(page,"Aucun aliment dans ce plan.","#f59e0b"); return None

    main_tbl = Table(all_rows,colWidths=[USABLE*0.74,USABLE*0.26])
    main_tbl.setStyle(TableStyle([
        ("GRID",        (0,0),(-1,-1),0.25,C.HexColor("#ddddee")),
        ("LEFTPADDING", (0,0),(-1,-1),5),("RIGHTPADDING",(0,0),(-1,-1),5),
        ("VALIGN",      (0,0),(-1,-1),"MIDDLE"),
        ("FONTNAME",    (0,0),(-1,-1),"Helvetica"),("FONTSIZE",(0,0),(-1,-1),8),
    ]+row_styles))

    total_flowables=[]
    try:
        from data.prices_module import compute_shopping_cost
        costs=compute_shopping_cost(shopping,app_state)
        if costs.get("total",0)>0:
            nf,nt=costs.get("nb_prices_found",0),costs.get("nb_total",0)
            total_flowables+=[
                HRFlowable(width="100%",thickness=1,color=ACC,spaceAfter=4),
                Table([[Paragraph("TOTAL ESTIME",sTotLbl),
                        Paragraph(f"<b>approx. {costs['total']:.2f} EUR</b>  ({nf}/{nt} prix)",sTotVal)]],
                      colWidths=[USABLE*0.55,USABLE*0.45]),
                Paragraph("Estimation : prix moyens Open Food Facts + marche France 2025",
                          ParagraphStyle("ps",fontSize=7,textColor=MUTED,
                                         fontName="Helvetica-Oblique",spaceBefore=2)),
            ]
    except Exception:
        pass

    doc=SimpleDocTemplate(path,pagesize=A4,leftMargin=MARGIN,rightMargin=MARGIN,
                          topMargin=MARGIN,bottomMargin=MARGIN,
                          title=f"Liste de courses THRESHOLD — {period_lbl}",author="THRESHOLD")
    period_clean=period_lbl.replace("\n"," ")
    story=[Paragraph("LISTE DE COURSES — THRESHOLD",sTitle)]
    if period_clean: story.append(Paragraph(period_clean,sSub))
    story+=[
        Paragraph(f'Genere le {datetime.datetime.now().strftime("%d/%m/%Y a %H:%M")}'
                  f' · {n_items} aliments · Quantites brutes a acheter',sDate),
        HRFlowable(width="100%",thickness=1.5,color=ACC,spaceAfter=8),
        main_tbl,Spacer(1,8),
    ]+total_flowables+[
        Spacer(1,6),
        HRFlowable(width="100%",thickness=0.5,color=MUTED),
        Paragraph("THRESHOLD — Coach Bodybuilding · Liste generee automatiquement",sFooter),
    ]

    try:
        doc.build(story)
        _snack(page,f"Liste de courses exportee : {Path(path).name}")
        _open_file(path); return path
    except Exception as e:
        _snack(page,f"Erreur PDF : {e}","#ef4444"); return None


# ══════════════════════════════════════════════════════════════════════════════
#  EXPORT — PLAN MULTI-JOURS
# ══════════════════════════════════════════════════════════════════════════════
def export_multiday_plan_pdf(app_state, days, path=None, page=None):
    if not RL_OK:
        _snack(page,"ReportLab non installe","#ef4444"); return None

    n_days=len(days); mode_s="Semaine" if n_days==7 else f"{n_days}j"
    path=path or _out_path(app_state,f"PLAN_{mode_s.upper()}")
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    doc=_mk_doc(path); st=_styles(); story=[]

    ui=_ui(app_state); name=ui.get("name",app_state.get("current_user","—"))
    age=ui.get("age","—"); obj=ui.get("objectif","—")
    d0=days[0]["date"]; d1=days[-1]["date"]
    date_range=(f"{d0:%d/%m/%Y} -> {d1:%d/%m/%Y}" if hasattr(d0,"strftime") else f"{d0} -> {d1}")

    story.append(Paragraph("THRESHOLD",st["cover_h1"]))
    story.append(Paragraph(f"Plan Alimentaire — {mode_s} ({n_days} jours)",st["cover_sub"]))
    _hr(story,_ACC,1.5)
    story.append(Paragraph(
        f"Athlete : {name}   |   Age : {age} ans   |   Objectif : {obj}   |   "
        f"Periode : {date_range}",st["cover_info"]))
    _hr(story,_BORD); story.append(Spacer(1,6*mm))

    avg_cal =sum(sum(m.get("tot_cal",0) for m in d["plan"]) for d in days)/n_days
    avg_prot=sum(sum(m.get("tot_p",  0) for m in d["plan"]) for d in days)/n_days
    avg_gluc=sum(sum(m.get("tot_g",  0) for m in d["plan"]) for d in days)/n_days
    avg_lip =sum(sum(m.get("tot_l",  0) for m in d["plan"]) for d in days)/n_days

    story.append(Paragraph("Moyennes journalieres",st["sec_hdr"]))
    mac_rows=[
        [Paragraph(h,st["muted"]) for h in ["Macro","Moy. / jour","% kcal"]],
        [Paragraph("Calories",st["body"]),Paragraph(f"{avg_cal:.0f} kcal",st["body"]),Paragraph("100%",st["body"])],
        [Paragraph("Proteines",st["body"]),Paragraph(f"{avg_prot:.0f} g",st["body"]),
         Paragraph(f"{avg_prot*4/avg_cal*100:.0f}%" if avg_cal else "—",st["body"])],
        [Paragraph("Glucides",st["body"]),Paragraph(f"{avg_gluc:.0f} g",st["body"]),
         Paragraph(f"{avg_gluc*4/avg_cal*100:.0f}%" if avg_cal else "—",st["body"])],
        [Paragraph("Lipides",st["body"]),Paragraph(f"{avg_lip:.0f} g",st["body"]),
         Paragraph(f"{avg_lip*9/avg_cal*100:.0f}%" if avg_cal else "—",st["body"])],
    ]
    t=_tbl(mac_rows,[70,50,30]); story.append(t) if t else None
    story.append(Spacer(1,4*mm))

    story.append(Paragraph("Vue d'ensemble",st["sec_hdr"]))
    recap_rows=[[Paragraph(h,st["muted"]) for h in ["Jour","Date","Cal.","Prot.","Gluc.","Lip."]]]
    for d in days:
        tc=sum(m.get("tot_cal",0) for m in d["plan"]); tp=sum(m.get("tot_p",0) for m in d["plan"])
        tg=sum(m.get("tot_g",0) for m in d["plan"]);  tl=sum(m.get("tot_l",0) for m in d["plan"])
        ds=d["date"].strftime("%d/%m") if hasattr(d["date"],"strftime") else str(d["date"])
        recap_rows.append([
            Paragraph(str(d.get("label","")).split()[0],st["small"]),
            Paragraph(ds,st["small"]),Paragraph(f"{tc:.0f}",st["small"]),
            Paragraph(f"{tp:.0f}g",st["small"]),Paragraph(f"{tg:.0f}g",st["small"]),
            Paragraph(f"{tl:.0f}g",st["small"]),
        ])
    t=_tbl(recap_rows,[28,24,24,24,24,24]); story.append(t) if t else None
    story.append(PageBreak())

    SLOT_ICONS={"matin":"Matin","midi":"Midi","collation":"Collation","soir":"Soir","coucher":"Coucher"}
    for di,d in enumerate(days):
        plan=d["plan"]
        tc=sum(m.get("tot_cal",0) for m in plan); tp=sum(m.get("tot_p",0) for m in plan)
        tg=sum(m.get("tot_g",0) for m in plan);  tl=sum(m.get("tot_l",0) for m in plan)
        story.append(Paragraph(
            f"{d.get('label','')}  —  {tc:.0f} kcal | {tp:.0f}g P · {tg:.0f}g G · {tl:.0f}g L",
            st["week_main"]))
        _hr(story,_ACC,1.0); story.append(Spacer(1,3*mm))
        for meal in plan:
            lbl=SLOT_ICONS.get(meal.get("type",""),"")
            story.append(Paragraph(
                f"{lbl}  {meal.get('name','').strip()}  "
                f"— {meal.get('tot_cal',0):.0f} kcal | "
                f"{meal.get('tot_p',0):.0f}P · {meal.get('tot_g',0):.0f}G · {meal.get('tot_l',0):.0f}L",
                st["sec_hdr"]))
            items=meal.get("items",[])
            if items:
                rows=[[Paragraph(h,st["muted"]) for h in ["Aliment","Qte","kcal","P","G","L"]]]
                for item in items:
                    rows.append([
                        Paragraph(item.get("food",""),st["small"]),
                        Paragraph(f"{item.get('g',0):.0f}g",st["small"]),
                        Paragraph(f"{item.get('kcal',0):.0f}",st["small"]),
                        Paragraph(f"{item.get('p',0):.1f}",st["small"]),
                        Paragraph(f"{item.get('g_',0):.1f}",st["small"]),
                        Paragraph(f"{item.get('l',0):.1f}",st["small"]),
                    ])
                rows.append([
                    Paragraph("TOTAL",st["accent"]),Paragraph("",st["small"]),
                    Paragraph(f"{meal.get('tot_cal',0):.0f}",st["accent"]),
                    Paragraph(f"{meal.get('tot_p',0):.1f}",st["accent"]),
                    Paragraph(f"{meal.get('tot_g',0):.1f}",st["accent"]),
                    Paragraph(f"{meal.get('tot_l',0):.1f}",st["accent"]),
                ])
                t=_tbl(rows,[62,20,20,20,20,20])
                if t: story.append(t)
            story.append(Spacer(1,3*mm))
        if di<len(days)-1: story.append(PageBreak())

    story.append(Spacer(1,8*mm)); _hr(story,_BORD)
    story.append(Paragraph(
        "Plans generes par THRESHOLD. Macros calculees sur ton TDEE + objectif profil. "
        "Variation quotidienne garantie — aliments incompatibles automatiquement separes.",st["muted"]))

    try:
        doc.build(story)
        _snack(page,f"Plan {mode_s} PDF exporte : {Path(path).name}")
        _open_file(path); return path
    except Exception as e:
        _snack(page,f"Erreur PDF : {e}","#ef4444"); return None
