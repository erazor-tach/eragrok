# data/pdf_utils.py — ERAGROK · Rapport PDF complet
# ─────────────────────────────────────────────────────────────────────────────
# Architecture :
#   • Lecture 100 % depuis SQLite (db.py) — aucune dépendance aux widgets UI
#   • export_unified_pdf(app) → rapport complet, 1 semaine par page
#   • export_cycle_pdf / export_nutrition_pdf / export_entrainement_pdf
#     → exports standalone (appellent le même moteur)
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
    )
    RL_OK = True
except ImportError:
    RL_OK = False

_MARGIN = 14
_W = 210 - 2 * _MARGIN   # 182 mm utilisables

# ── Palette ──────────────────────────────────────────────────────────────────
class _C:
    if RL_OK:
        ACCENT   = colors.HexColor("#f97316")
        ACCENT2  = colors.HexColor("#ea580c")
        SUCCESS  = colors.HexColor("#22c55e")
        WARN     = colors.HexColor("#f59e0b")
        DANGER   = colors.HexColor("#ef4444")
        INFO     = colors.HexColor("#3b82f6")
        PURPLE   = colors.HexColor("#a855f7")
        WHITE    = colors.HexColor("#eef2ff")
        MUTED    = colors.HexColor("#818aaa")
        DARK     = colors.HexColor("#10101e")
        DARK2    = colors.HexColor("#17172a")
        BORDER   = colors.HexColor("#1e1e38")
        HDR      = colors.HexColor("#0c0c1a")
        PHASE = {
            "CYCLE":       colors.HexColor("#0d2b0d"),
            "WASHOUT":     colors.HexColor("#2a2010"),
            "PCT":         colors.HexColor("#1a1a2e"),
            "AVANT CYCLE": colors.HexColor("#1a1a28"),
            "TERMINÉ":     colors.HexColor("#111111"),
        }
        DIFF = {1:colors.HexColor("#1a3a1a"), 2:colors.HexColor("#1a2a0a"),
                3:colors.HexColor("#2a2000"), 4:colors.HexColor("#2a0a00"),
                5:colors.HexColor("#1a0000")}
    else:
        ACCENT=ACCENT2=SUCCESS=WARN=DANGER=INFO=PURPLE=WHITE=MUTED=DARK=DARK2=BORDER=HDR=None
        PHASE={}; DIFF={}


def _styles():
    if not RL_OK: return {}
    b = getSampleStyleSheet()
    def s(n, base="Normal", **kw):
        return ParagraphStyle(n, parent=b[base], **kw)
    return {
        "cover_title": s("CT","Title",  fontSize=30, textColor=_C.ACCENT, spaceAfter=4, leading=36),
        "cover_sub":   s("CS","Normal", fontSize=12, textColor=_C.MUTED,  spaceAfter=6),
        "cover_disc":  s("CD","Normal", fontSize=8,  textColor=_C.MUTED,  spaceAfter=2, leading=11),
        "title":  s("TT","Title",   fontSize=18, textColor=_C.ACCENT, spaceAfter=4),
        "h1":     s("H1","Heading1",fontSize=13, textColor=_C.ACCENT,  spaceBefore=10, spaceAfter=4),
        "h2":     s("H2","Heading2",fontSize=10, textColor=_C.ACCENT,  spaceBefore=6,  spaceAfter=3),
        "h3":     s("H3","Heading3",fontSize=9,  textColor=_C.ACCENT2, spaceBefore=4,  spaceAfter=2),
        "body":   s("B","Normal",   fontSize=9,  textColor=_C.WHITE,  spaceAfter=3,  leading=13),
        "small":  s("SM","Normal",  fontSize=8,  textColor=_C.WHITE,  spaceAfter=2,  leading=11),
        "muted":  s("M","Normal",   fontSize=8,  textColor=_C.MUTED,  spaceAfter=2,  leading=11),
        "warn":   s("W","Normal",   fontSize=9,  textColor=_C.WARN,   spaceAfter=3,  leading=13),
        "danger": s("D","Normal",   fontSize=9,  textColor=_C.DANGER, spaceAfter=3,  leading=13),
        "ok":     s("OK","Normal",  fontSize=9,  textColor=_C.SUCCESS,spaceAfter=3,  leading=13),
        "week_hdr":s("WH","Heading1",fontSize=11,textColor=_C.ACCENT, spaceBefore=0, spaceAfter=3),
    }


def _clip(text, n=50):
    t = str(text or "—")
    return t if len(t) <= n else t[:n-1]+"…"


def _hr(story, color=None):
    if RL_OK:
        story.append(HRFlowable(width="100%", thickness=0.8,
                                color=color or _C.BORDER,
                                spaceAfter=4, spaceBefore=2))


def _mk_table(rows, col_mm, extras=None):
    if not RL_OK or not rows: return None
    tbl = Table(rows, colWidths=[c*mm for c in col_mm], repeatRows=1)
    base = [
        ("BACKGROUND",     (0,0),(-1,0),   _C.HDR),
        ("TEXTCOLOR",      (0,0),(-1,0),   _C.ACCENT),
        ("FONTNAME",       (0,0),(-1,0),   "Helvetica-Bold"),
        ("FONTSIZE",       (0,0),(-1,-1),  7.5),
        ("ROWBACKGROUNDS", (0,1),(-1,-1),  [_C.DARK, _C.DARK2]),
        ("TEXTCOLOR",      (0,1),(-1,-1),  _C.WHITE),
        ("GRID",           (0,0),(-1,-1),  0.3, _C.BORDER),
        ("PADDING",        (0,0),(-1,-1),  4),
        ("VALIGN",         (0,0),(-1,-1),  "MIDDLE"),
        ("WORDWRAP",       (0,0),(-1,-1),  True),
    ]
    if extras: base.extend(extras)
    tbl.setStyle(TableStyle(base))
    return tbl


def _mk_doc(path):
    return SimpleDocTemplate(
        path, pagesize=A4,
        rightMargin=_MARGIN*mm, leftMargin=_MARGIN*mm,
        topMargin=_MARGIN*mm,   bottomMargin=_MARGIN*mm,
    )


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


def _parse_date(s):
    if not s: return None
    s = str(s).strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try: return datetime.datetime.strptime(s, fmt).date()
        except: pass
    return None


def _week_key(d):
    """Retourne (année_iso, semaine_iso, lundi) pour trier."""
    iso = d.isocalendar()
    monday = d - datetime.timedelta(days=d.weekday())
    return (iso[0], iso[1], monday)


def _weeks_range(start_date, n_weeks):
    """Génère n_weeks lundis à partir de start_date."""
    monday = start_date - datetime.timedelta(days=start_date.weekday())
    for i in range(n_weeks):
        yield monday + datetime.timedelta(weeks=i)


DAY_FR = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE DE GARDE
# ══════════════════════════════════════════════════════════════════════════════
def _build_cover(app, story, st):
    try: from data import utils
    except: import utils

    info   = getattr(app, "user_info", {}) or {}
    user   = getattr(app, "current_user", "utilisateur")
    name   = getattr(app, "selected_user_name", user)
    poids  = str(info.get("poids", "—"))
    taille = str(info.get("taille", "—"))
    sexe   = info.get("sexe", "—")
    age    = str(info.get("age", "—"))
    ajust  = info.get("ajustement", "Maintien (0%)")

    imc_str = "—"
    try:
        imc_val, imc_cat = utils.calculer_imc(float(poids), float(taille))
        if imc_val: imc_str = f"{imc_val:.1f} — {imc_cat[0]}"
    except: pass

    story.append(Spacer(1, 16*mm))
    story.append(Paragraph("⚡  ERAGROK", st["cover_title"]))
    story.append(Paragraph("Coach Bodybuilding — Rapport Hebdomadaire Complet", st["cover_sub"]))
    _hr(story, _C.ACCENT)
    story.append(Spacer(1, 6*mm))

    rows = [
        ["Nom",       name],
        ["Poids",     f"{poids} kg"],
        ["Taille",    f"{taille} cm"],
        ["Sexe",      sexe],
        ["Âge",       f"{age} ans"],
        ["IMC",       imc_str],
        ["Objectif",  ajust],
        ["Généré le", datetime.datetime.now().strftime("%d/%m/%Y à %H:%M")],
    ]
    tbl = Table(rows, colWidths=[45*mm, 129*mm])
    tbl.setStyle(TableStyle([
        ("FONTNAME",       (0,0),(0,-1), "Helvetica-Bold"),
        ("FONTSIZE",       (0,0),(-1,-1), 10),
        ("TEXTCOLOR",      (0,0),(0,-1),  _C.ACCENT),
        ("TEXTCOLOR",      (1,0),(1,-1),  _C.WHITE),
        ("ROWBACKGROUNDS", (0,0),(-1,-1), [_C.DARK, _C.DARK2]),
        ("GRID",           (0,0),(-1,-1), 0.3, _C.BORDER),
        ("PADDING",        (0,0),(-1,-1), 6),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 8*mm))
    story.append(Paragraph(
        "Ce rapport regroupe nutrition, entraînement et cycle hormonal. "
        "1 semaine par page. Données issues de votre base ERAGROK.",
        st["cover_disc"]))


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION CYCLE  (1 page : résumé produits + alertes)
# ══════════════════════════════════════════════════════════════════════════════
def _build_cycle_section(app, story, st):
    try: from data import db as _db
    except: return

    # Lecture depuis DB — pas de dépendance aux widgets
    cycle = _db.cycle_get_last(app)
    if not cycle:
        story.append(Paragraph("Aucun cycle enregistré.", st["muted"]))
        return

    debut_s     = cycle.get("debut", "—")
    fin_s       = cycle.get("fin_estimee", "—")
    longueur_s  = cycle.get("longueur_sem", "12")
    produits_s  = cycle.get("produits_doses", "")
    note_s      = cycle.get("note", "")

    story.append(Paragraph("💉  Cycle Hormonal — Résumé", st["h1"]))
    _hr(story)
    story.append(Paragraph(
        f"Début : {debut_s}  ·  Fin estimée : {fin_s}  ·  Durée : {longueur_s} sem.",
        st["muted"]))
    story.append(Spacer(1, 4))

    # Alertes si données cycle_module disponibles
    try:
        from data import cycle_module as cm
        prods_list = [e.split(":")[0].strip()
                      for e in produits_s.split("|") if e.strip()] if produits_s else []
        has_testo = any(p in getattr(cm, "_AROMATIZING_TEST", set()) for p in prods_list)
        for cond, msg in [
            (has_testo and not any(p in getattr(cm,"_AI_PRODUCTS",set()) for p in prods_list),
             "Testostérone SANS anti-aromatase — risque gynécomastie"),
            (has_testo and not any(p in getattr(cm,"_HCG_PRODUCTS_SET",set()) for p in prods_list),
             "Testostérone SANS hCG — risque atrophie testiculaire"),
        ]:
            if cond:
                story.append(Paragraph(f"⚠  {msg}", st["danger"]))
    except: pass

    story.append(Spacer(1, 4))

    # Tableau produits
    if produits_s:
        entries = [e.strip() for e in produits_s.split("|") if e.strip()]
        rows = [["Produit", "Dose/sem", "Plage réf.", "Forme", "Utilité"]]
        try: from data.cycle_module import PRODUCT_INFO
        except: PRODUCT_INFO = {}
        for entry in entries:
            parts = entry.split(":", 1)
            pname = parts[0].strip()
            dose  = parts[1].strip() if len(parts) > 1 else "—"
            info  = PRODUCT_INFO.get(pname, {})
            d_min = info.get("dose_min", "—")
            d_max = info.get("dose_max", "")
            ref   = f"{d_min}–{d_max}" if d_max else d_min
            try:
                from data.cycle_module import _ORAL_PRODUCTS
                forme = "Oral" if pname in _ORAL_PRODUCTS else "Inject."
            except: forme = "—"
            utilite = _clip(info.get("utilite", "—"), 40)
            rows.append([_clip(pname,36), dose, ref, forme, utilite])
        t = _mk_table(rows, [54, 22, 26, 18, 62])
        if t: story.append(t)
        story.append(Spacer(1, 6))

    if note_s:
        story.append(Paragraph(f"📝  Notes : {_clip(note_s, 200)}", st["body"]))


# ══════════════════════════════════════════════════════════════════════════════
#  NUTRITION — 1 semaine par page
# ══════════════════════════════════════════════════════════════════════════════
def _build_nutrition_weekly(app, story, st, weeks_limit=26):
    try: from data import db as _db
    except: return

    all_rows = _db.nutrition_get_all(app)
    if not all_rows:
        story.append(Paragraph("Aucune donnée nutrition.", st["muted"]))
        return

    # Grouper par semaine ISO
    weeks = {}
    for r in all_rows:
        d = _parse_date(r.get("date", ""))
        if not d: continue
        wk = _week_key(d)
        weeks.setdefault(wk, []).append((d, r))

    sorted_weeks = sorted(weeks.keys())

    for wk in sorted_weeks[-weeks_limit:]:
        monday = wk[2]
        sunday = monday + datetime.timedelta(days=6)
        days_data = sorted(weeks[wk], key=lambda x: x[0])

        # En-tête semaine
        story.append(Paragraph(
            f"🍎  Nutrition — Sem. {wk[1]}/{wk[0]}  "
            f"({monday:%d/%m} → {sunday:%d/%m/%Y})",
            st["h1"]))
        _hr(story)

        # Tableau journalier
        rows = [["Jour", "Date", "Poids (kg)", "Calories", "Prot. (g)",
                 "Gluc. (g)", "Lip. (g)", "Note"]]
        cal_vals = []; prot_vals = []; gluc_vals = []; lip_vals = []; poids_vals = []

        for d, r in days_data:
            def _f(k):
                v = r.get(k,"").strip()
                try: return float(v) if v else None
                except: return None

            cal  = _f("calories");  prot = _f("proteines")
            gluc = _f("glucides");  lip  = _f("lipides")
            poids= _f("poids")

            if cal:   cal_vals.append(cal)
            if prot:  prot_vals.append(prot)
            if gluc:  gluc_vals.append(gluc)
            if lip:   lip_vals.append(lip)
            if poids: poids_vals.append(poids)

            rows.append([
                DAY_FR[d.weekday()],
                d.strftime("%d/%m"),
                f"{poids:.1f}" if poids else "—",
                f"{cal:.0f}" if cal else "—",
                f"{prot:.0f}" if prot else "—",
                f"{gluc:.0f}" if gluc else "—",
                f"{lip:.0f}" if lip else "—",
                _clip(r.get("note",""), 24),
            ])

        # Ligne moyennes
        def _avg(lst): return f"{sum(lst)/len(lst):.1f}" if lst else "—"
        rows.append([
            "Moy.", "",
            _avg(poids_vals), _avg(cal_vals),
            _avg(prot_vals),  _avg(gluc_vals), _avg(lip_vals), "",
        ])

        # Colonne widths : [14,16,22,22,22,22,22,42] = 182mm
        t = _mk_table(rows, [14,16,22,22,22,22,22,42],
                      [("FONTNAME",(0,-1),(-1,-1),"Helvetica-Bold"),
                       ("BACKGROUND",(0,-1),(-1,-1),_C.HDR),
                       ("TEXTCOLOR",(0,-1),(-1,-1),_C.ACCENT)])
        if t: story.append(t)
        story.append(PageBreak())


# ══════════════════════════════════════════════════════════════════════════════
#  ENTRAÎNEMENT — 1 semaine par page
# ══════════════════════════════════════════════════════════════════════════════
def _build_entrainement_weekly(app, story, st, weeks_limit=26):
    try: from data import db as _db
    except: return

    plan_rows = _db.planning_get_all(app)
    hist_rows = _db.history_get_all(app)

    if not plan_rows and not hist_rows:
        story.append(Paragraph("Aucune donnée entraînement.", st["muted"]))
        return

    # Grouper planning par semaine
    plan_weeks = {}
    for r in plan_rows:
        d = _parse_date(r.get("date",""))
        if not d: continue
        wk = _week_key(d)
        plan_weeks.setdefault(wk, []).append((d, r))

    # Grouper historique par semaine (planned_for)
    hist_weeks = {}
    for r in hist_rows:
        d = _parse_date(r.get("planned_for","")) or _parse_date(r.get("date","")[:10])
        if not d: continue
        wk = _week_key(d)
        hist_weeks.setdefault(wk, []).append((d, r))

    all_wks = sorted(set(list(plan_weeks.keys()) + list(hist_weeks.keys())))

    for wk in all_wks[-weeks_limit:]:
        monday = wk[2]
        sunday = monday + datetime.timedelta(days=6)

        story.append(Paragraph(
            f"🏋  Entraînement — Sem. {wk[1]}/{wk[0]}  "
            f"({monday:%d/%m} → {sunday:%d/%m/%Y})",
            st["h1"]))
        _hr(story)

        # Planning de la semaine (technique par technique)
        plan_days = plan_weeks.get(wk, [])
        if plan_days:
            story.append(Paragraph("Planning", st["h2"]))
            p_rows = [["Jour", "Date", "Catégorie", "Programme", "Technique"]]
            for d, r in sorted(plan_days, key=lambda x: x[0]):
                p_rows.append([
                    DAY_FR[d.weekday()],
                    d.strftime("%d/%m"),
                    _clip(r.get("groupes",""), 18),
                    _clip(r.get("programme",""), 14),
                    _clip(r.get("line",""), 80),
                ])
            # [14,16,28,20,104] = 182mm
            t = _mk_table(p_rows, [14,16,28,20,104])
            if t: story.append(t)
            story.append(Spacer(1, 4))

        # Séances réalisées (historique)
        hist_days = hist_weeks.get(wk, [])
        if hist_days:
            story.append(Paragraph("Séances réalisées", st["h2"]))
            h_rows = [["Enregistré", "Type", "Durée", "Exercices"]]
            for d, r in sorted(hist_days, key=lambda x: x[0]):
                exs = r.get("exercises", [])
                exs_txt = _clip(" / ".join(str(e) for e in exs[:5]), 90)
                h_rows.append([
                    _clip(r.get("date","")[:16], 16),
                    _clip(r.get("type",""), 18),
                    _clip(r.get("duration",""), 10),
                    exs_txt,
                ])
            # [28,20,16,118] = 182mm
            t = _mk_table(h_rows, [28,20,16,118])
            if t: story.append(t)
            story.append(Spacer(1, 4))

        story.append(PageBreak())

    # Programme sauvegardé le plus récent
    progs = _db.programmes_get_all(app)
    if progs:
        last_prog = progs[-1]
        lines = last_prog.get("lines", [])
        if lines:
            story.append(Paragraph(
                f"📋  Dernier programme sauvegardé : {last_prog.get('title','')}",
                st["h1"]))
            _hr(story)
            story.append(Paragraph(
                f"Créé le {last_prog.get('created','')[:16]}  ·  {len(lines)} lignes",
                st["muted"]))
            story.append(Spacer(1, 4))
            for ln in lines[:60]:
                story.append(Paragraph(_clip(str(ln), 100), st["small"]))
            story.append(PageBreak())


# ══════════════════════════════════════════════════════════════════════════════
#  CYCLE HEBDOMADAIRE  (1 page par semaine de cycle)
# ══════════════════════════════════════════════════════════════════════════════
def _build_cycle_weekly(app, story, st):
    try: from data import db as _db
    except: return

    cycle = _db.cycle_get_last(app)
    if not cycle: return

    debut_s    = cycle.get("debut","")
    longueur_s = cycle.get("longueur_sem","12")
    produits_s = cycle.get("produits_doses","")
    note_s     = cycle.get("note","")

    debut_date = _parse_date(debut_s)
    try: n_weeks = int(longueur_s.strip())
    except: n_weeks = 12

    if not debut_date or not produits_s: return

    entries = [e.strip() for e in produits_s.split("|") if e.strip()]
    prod_doses = {}
    for entry in entries:
        parts = entry.split(":", 1)
        prod_doses[parts[0].strip()] = parts[1].strip() if len(parts) > 1 else ""

    try: from data.cycle_module import PRODUCT_INFO
    except: PRODUCT_INFO = {}

    washout_w = 2
    total_weeks = n_weeks + washout_w

    for wi, monday in enumerate(_weeks_range(debut_date, total_weeks)):
        sunday = monday + datetime.timedelta(days=6)
        week_n = wi + 1

        if wi < n_weeks:
            phase = "CYCLE"; phase_col = _C.SUCCESS
        else:
            phase = "WASHOUT"; phase_col = _C.WARN

        story.append(Paragraph(
            f"💉  Cycle — S{week_n}/{n_weeks}  [{phase}]  "
            f"({monday:%d/%m} → {sunday:%d/%m/%Y})",
            st["h1"]))
        _hr(story)

        if phase == "CYCLE":
            rows = [["Produit", "Dose/sem", "Jours d'injection", "Utilité", "Risque"]]
            for pname, dose in prod_doses.items():
                info    = PRODUCT_INFO.get(pname, {})
                timing  = _clip(info.get("timing","—"), 30)
                utilite = _clip(info.get("utilite","—"), 34)
                dang    = info.get("dangerosite","—")
                rows.append([_clip(pname,34), dose or "—", timing, utilite, dang])
            t = _mk_table(rows, [54,20,40,46,22])
            if t: story.append(t)
        else:
            story.append(Paragraph("🚫  Arrêt de tous les produits du cycle.", st["warn"]))
            story.append(Paragraph(
                "Surveiller : récupération testiculaire, taux hormonaux, sommeil, libido.",
                st["body"]))
            if wi == n_weeks:
                story.append(Paragraph(
                    "Début PCT recommandé (si non Cruise/TRT) : Clomid 50mg + Nolvadex 20mg",
                    st["ok"]))

        if note_s and wi == 0:
            story.append(Spacer(1, 4))
            story.append(Paragraph(f"📝  {_clip(note_s, 200)}", st["muted"]))

        story.append(PageBreak())


# ══════════════════════════════════════════════════════════════════════════════
#  EXPORT UNIFIÉ  (objectif final : rapport complet semaine par semaine)
# ══════════════════════════════════════════════════════════════════════════════
def export_unified_pdf(app, ask_path=True):
    if not RL_OK:
        messagebox.showerror("ERAGROK", "reportlab manquant.\npip install reportlab")
        return

    path = _out_path(app, "eragrok_complet")
    if ask_path:
        path = filedialog.asksaveasfilename(
            parent=_root(app),
            title="Enregistrer le Rapport Complet ERAGROK",
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialfile=os.path.basename(path),
        ) or path
    if not path: return

    st  = _styles()
    doc = _mk_doc(path)
    story = []

    # Page de garde
    _build_cover(app, story, st)
    story.append(PageBreak())

    # Résumé cycle (1 page)
    _build_cycle_section(app, story, st)
    story.append(PageBreak())

    # Nutrition hebdomadaire
    story.append(Paragraph("🍎  NUTRITION — Historique hebdomadaire", st["title"]))
    story.append(Spacer(1, 4))
    _build_nutrition_weekly(app, story, st)

    # Entraînement hebdomadaire
    story.append(Paragraph("🏋  ENTRAÎNEMENT — Historique hebdomadaire", st["title"]))
    story.append(Spacer(1, 4))
    _build_entrainement_weekly(app, story, st)

    # Cycle semaine par semaine
    story.append(Paragraph("💉  CYCLE HORMONAL — Semaine par semaine", st["title"]))
    story.append(Spacer(1, 4))
    _build_cycle_weekly(app, story, st)

    _footer(story, st)

    try:
        doc.build(story)
        messagebox.showinfo("ERAGROK", f"✅ Rapport complet exporté :\n{path}")
    except Exception as e:
        messagebox.showerror("ERAGROK", f"Erreur export PDF :\n{e}")


# ══════════════════════════════════════════════════════════════════════════════
#  EXPORTS STANDALONE
# ══════════════════════════════════════════════════════════════════════════════
def export_cycle_pdf(app, ask_path=True):
    if not RL_OK:
        messagebox.showerror("ERAGROK","reportlab manquant.\npip install reportlab"); return
    path = _out_path(app, "cycle")
    if ask_path:
        path = filedialog.asksaveasfilename(
            parent=_root(app), title="Exporter cycle PDF",
            defaultextension=".pdf", filetypes=[("PDF","*.pdf")],
            initialfile=os.path.basename(path)) or path
    if not path: return
    st = _styles(); doc = _mk_doc(path); story = []
    _build_cover(app, story, st)
    story.append(PageBreak())
    _build_cycle_section(app, story, st)
    story.append(PageBreak())
    _build_cycle_weekly(app, story, st)
    _footer(story, st)
    try:
        doc.build(story)
        messagebox.showinfo("ERAGROK", f"✅ PDF cycle exporté :\n{path}")
    except Exception as e:
        messagebox.showerror("ERAGROK", f"Erreur PDF :\n{e}")


def export_nutrition_pdf(app, ask_path=True):
    if not RL_OK:
        messagebox.showerror("ERAGROK","reportlab manquant.\npip install reportlab"); return
    path = _out_path(app, "nutrition")
    if ask_path:
        path = filedialog.asksaveasfilename(
            parent=_root(app), title="Exporter nutrition PDF",
            defaultextension=".pdf", filetypes=[("PDF","*.pdf")],
            initialfile=os.path.basename(path)) or path
    if not path: return
    st = _styles(); doc = _mk_doc(path); story = []
    _build_cover(app, story, st)
    story.append(PageBreak())
    _build_nutrition_weekly(app, story, st)
    _footer(story, st)
    try:
        doc.build(story)
        messagebox.showinfo("ERAGROK", f"✅ PDF nutrition exporté :\n{path}")
    except Exception as e:
        messagebox.showerror("ERAGROK", f"Erreur PDF :\n{e}")


def export_entrainement_pdf(app, ask_path=True):
    if not RL_OK:
        messagebox.showerror("ERAGROK","reportlab manquant.\npip install reportlab"); return
    path = _out_path(app, "entrainement")
    if ask_path:
        path = filedialog.asksaveasfilename(
            parent=_root(app), title="Exporter entraînement PDF",
            defaultextension=".pdf", filetypes=[("PDF","*.pdf")],
            initialfile=os.path.basename(path)) or path
    if not path: return
    st = _styles(); doc = _mk_doc(path); story = []
    _build_cover(app, story, st)
    story.append(PageBreak())
    _build_entrainement_weekly(app, story, st)
    _footer(story, st)
    try:
        doc.build(story)
        messagebox.showinfo("ERAGROK", f"✅ PDF entraînement exporté :\n{path}")
    except Exception as e:
        messagebox.showerror("ERAGROK", f"Erreur PDF :\n{e}")
