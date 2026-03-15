# data/nutrition.py — THRESHOLD · Module Nutrition (Flet)
# ─────────────────────────────────────────────────────────────────────────────
# Port COMPLET de nutrition_module.py ERAGROK (1845 lignes) vers Flet.
# Logique métier 100% conservée.  Toutes les sections portées :
#   • Calculs nutritionnels (TDEE, macros, ajustement)
#   • Jauge IMC (7 zones, curseur, diff poids cible)  → Canvas Flet SVG-like
#   • Alerte PCT (depuis features / cycle DB)
#   • Graphique évolution poids (ascii sparkline faute de matplotlib)
#   • Carte cycle hormonal inline (produits, doses, dangérosité, risque stack)
#   • Plan alimentaire (dernier plan accepté depuis DB)
#   • Historique nutrition (tableau triable, modifier, supprimer, tout supprimer)
#   • Semaines en cours / suivante (nutrition réelle + cibles + entraînement + cycle)
#   • Sauvegarde nutrition, export PDF (stub), calculateur repas (stub ouverture)
#   • Détection de modifications non sauvegardées (snack warning)
# ─────────────────────────────────────────────────────────────────────────────
from __future__ import annotations
import calendar as pycal
import datetime
import re
from collections import defaultdict
from typing import Optional

import flet as ft

from ui.theme import (
    ACCENT, ACCENT_DIM, ACCENT_GLOW, ACCENT_HOVER,
    BG_CARD, BG_CARD2, BG_INPUT, BG_ROOT,
    BORDER, BLUE, BLUE_HVR, DANGER, DANGER_HVR,
    GRAY, GRAY_HVR, PURPLE, SUCCESS, SUCCESS_HVR,
    TEXT, TEXT_ACCENT, TEXT_MUTED, TEXT_SUB, WARNING,
    R_CARD, R_INPUT,
    mk_btn, mk_card, mk_card2, mk_dropdown, mk_entry,
    mk_label, mk_sep, mk_title, mk_badge,
)
from data import db as _db
from data import utils
from data import food_catalogue as _fc

# ── Logique métier extraite (proposition #9) ──────────────────────────────────
# Les fonctions pures vivent maintenant dans data/logic/nutrition_logic.py.
# Ce réexport garantit la compatibilité totale — aucun autre module à modifier.
from data.logic.nutrition_logic import (
    _d2s, _parse_date_flex, _week_dates,
    _calculs, _imc_zone, _imc_diff_text,
    _avg, _sparkline,
    IMC_ZONES, IMC_MIN, IMC_MAX,
)

DATE_FMT = "%d/%m/%Y"
TS_FMT   = "%Y-%m-%d %H:%M"
DAY_FR   = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]

# IMC_ZONES / IMC_MIN / IMC_MAX importés depuis data.logic.nutrition_logic

DANG_COL = {
    0: "#555555", 1: "#22c55e", 2: "#84cc16",
    3: "#f59e0b", 4: "#ef4444", 5: "#7f1d1d",
}
RISK_TXT = {
    0: "—", 1: "✅ Faible", 2: "✅ Modéré",
    3: "⚠️  Élevé", 4: "🔴 Très élevé", 5: "🔴 Extrême",
}

PCT_NAMES = {"Clomiphene (Clomid)", "Tamoxifen (Nolvadex)"}


# ══════════════════════════════════════════════════════════════════════════════
#  SOUS-COMPOSANTS UI
# ══════════════════════════════════════════════════════════════════════════════

def _build_imc_gauge(imc, poids, taille):
    """Jauge IMC style Threshold — slider visuel avec 4 zones."""
    ZONES = [
        (16.0, 18.5, "#60a5fa", "Maigreur"),
        (18.5, 25.0, "#22c55e", "Optimal"),
        (25.0, 30.0, "#f97316", "Surpoids"),
        (30.0, 40.0, "#ef4444", "Obésité"),
    ]

    if imc is not None:
        zone_col  = next((c for lo,hi,c,_ in ZONES if lo<=imc<hi), DANGER)
        zone_lbl  = next((l for lo,hi,_,l in ZONES if lo<=imc<hi), "Obésité")
    else:
        zone_col, zone_lbl = TEXT_MUTED, "—"

    # ── En-tête ────────────────────────────────────────────────────────────────
    if imc is not None:
        header = ft.Row([
            ft.Text(f"{imc:.1f}", size=36, color=zone_col,
                    weight=ft.FontWeight.BOLD),
            ft.Column([
                ft.Text("IMC", size=10, color=TEXT_SUB),
                ft.Text(zone_lbl, size=13, color=zone_col,
                        weight=ft.FontWeight.BOLD),
            ], spacing=0),
        ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER)
    else:
        header = ft.Row([
            ft.Text("IMC  —", size=18, color=TEXT_MUTED),
            ft.Text("Renseigne poids et taille", size=10, color=TEXT_MUTED),
        ], spacing=8)

    # ── Barre slider ───────────────────────────────────────────────────────────
    total = IMC_MAX - IMC_MIN  # 24

    # Segments colorés — proportionnels à la largeur réelle de chaque zone
    segments = []
    for i, (lo, hi, col, lbl) in enumerate(ZONES):
        expand_val = int((hi - lo) / total * 1000)
        is_first = (i == 0)
        is_last  = (i == len(ZONES) - 1)
        segments.append(ft.Container(
            expand=expand_val,
            height=10,
            bgcolor=col,
            opacity=0.65,
            border_radius=ft.BorderRadius.only(
                top_left=5 if is_first else 0,
                bottom_left=5 if is_first else 0,
                top_right=5 if is_last else 0,
                bottom_right=5 if is_last else 0,
            ),
        ))

    bar_row = ft.Row(segments, spacing=0, expand=True)

    # Barre de progression jusqu'à la position IMC
    cursor_stack = ft.Container()
    if imc is not None:
        pct = max(0.0, min(1.0, (imc - IMC_MIN) / total))
        cursor_stack = ft.ProgressBar(
            value=pct,
            bgcolor=ft.Colors.TRANSPARENT,
            color=zone_col,
            height=4,
        )

    label_row = ft.Row(
        [ft.Container(
            content=ft.Text(lbl, size=9, color=col, text_align=ft.TextAlign.CENTER),
            expand=int((hi-lo)/total*1000),
        ) for lo, hi, col, lbl in ZONES],
        spacing=0,
    )

    tick_row = ft.Row(
        [ft.Container(
            content=ft.Text(str(int(lo)), size=8, color=TEXT_MUTED, text_align=ft.TextAlign.LEFT),
            expand=int((hi-lo)/total*1000),
        ) for lo, hi, col, lbl in ZONES] + [ft.Text("40", size=8, color=TEXT_MUTED)],
        spacing=0,
    )

    # ── Message différentiel ───────────────────────────────────────────────────
    diff_controls = []
    if imc is not None and poids and taille:
        diff_txt, diff_col = _imc_diff_text(imc, poids, taille)
        try:
            tm   = float(taille) / 100
            p_lo = round(18.5 * tm**2, 1)
            p_hi = round(25.0 * tm**2, 1)
            p_id = round(22.0 * tm**2, 1)
            diff_controls = [
                ft.Container(height=4),
                ft.Text(diff_txt, size=10, color=diff_col,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER),
                ft.Text(f"Normal : {p_lo} – {p_hi} kg     Idéal : {p_id} kg",
                        size=9, color=TEXT_SUB,
                        text_align=ft.TextAlign.CENTER),
            ]
        except Exception:
            pass

    return ft.Container(
        content=ft.Column([
            header,
            ft.Container(height=8),
            bar_row,
            ft.Container(height=2),
            cursor_stack,
            label_row,
            tick_row,
            *diff_controls,
        ], spacing=2),
        bgcolor=BG_CARD2,
        border_radius=10,
        padding=ft.Padding.all(14),
    )


def _build_metrics_col(poids_val: Optional[float], taille_val: Optional[float],
                        imc_val: Optional[float], imc_cat,
                        user_info: dict) -> ft.Column:
    """Métriques en ligne compacte + message différentiel IMC."""
    imc_str   = "—"
    imc_color = TEXT_MUTED
    if imc_val is not None:
        cat_lbl   = imc_cat[0] if imc_cat else "—"
        imc_str   = f"{imc_val:.1f} — {cat_lbl}"
        imc_color, _ = _imc_zone(imc_val)

    age_str = ""
    dn = user_info.get("date_naissance", "")
    age = utils.age_depuis_naissance(dn) or user_info.get("age")
    if age:
        age_str = f"{age} ans"

    # Ligne métriques horizontale
    chips = []
    if poids_val:
        chips.append(ft.Text(f"⚖ {poids_val:.1f} kg", size=12, color=TEXT))
    if imc_val is not None:
        chips.append(ft.Text(f"  IMC {imc_str}", size=12, color=imc_color,
                             weight=ft.FontWeight.BOLD))
    if taille_val:
        chips.append(ft.Text(f"  📐 {taille_val:.0f} cm", size=12, color=TEXT_SUB))
    if age_str:
        chips.append(ft.Text(f"  🎂 {age_str}", size=12, color=TEXT_SUB))

    metrics_row = ft.Row(chips, spacing=0, wrap=True)

    # Message différentiel poids-cible IMC
    diff_controls = []
    if imc_val is not None and poids_val and taille_val:
        diff_txt, diff_col = _imc_diff_text(imc_val, poids_val, taille_val)
        if diff_txt:
            diff_controls.append(
                ft.Text(diff_txt, size=12, color=diff_col, weight=ft.FontWeight.BOLD)
            )
        try:
            tm = float(taille_val) / 100
            p_lo = round(18.5 * tm ** 2, 1)
            p_hi = round(25.0 * tm ** 2, 1)
            p_id = round(22.0 * tm ** 2, 1)
            diff_controls.append(
                ft.Text(
                    f"Normal : {p_lo} – {p_hi} kg    Idéal : {p_id} kg",
                    size=11, color=TEXT_MUTED,
                )
            )
        except Exception:
            pass

    return ft.Column(
        [metrics_row] + diff_controls,
        spacing=4,
    )


def _build_macro_display(nut: Optional[dict]) -> ft.Row:
    """Ligne 4 colonnes macros (calories, protéines, glucides, lipides)."""
    def col(emoji, label, val, color):
        return ft.Column([
            ft.Text(f"{emoji}  {label}", size=11, color=TEXT_MUTED),
            ft.Text(val, size=20, color=color, weight=ft.FontWeight.BOLD),
        ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    if nut:
        c_cal  = col("🔥", "Calories",  f"{nut['cal']:.0f} kcal",  ACCENT_GLOW)
        c_prot = col("🥩", "Protéines", f"{nut['proteines']:.0f} g", "#4aaa4a")
        c_gluc = col("🍚", "Glucides",  f"{nut['glucides']:.0f} g",  "#3b82f6")
        c_lip  = col("🥑", "Lipides",   f"{nut['lipides']:.0f} g",   "#a855f7")
        tdee_txt = ft.Text(
            f"TDEE {nut['tdee']:.0f} kcal  |  ajust. {nut['adj']*100:+.0f}%",
            size=10, color=TEXT_MUTED, text_align=ft.TextAlign.CENTER,
        )
    else:
        c_cal  = col("🔥", "Calories",  "— kcal",  TEXT_MUTED)
        c_prot = col("🥩", "Protéines", "— g",      TEXT_MUTED)
        c_gluc = col("🍚", "Glucides",  "— g",      TEXT_MUTED)
        c_lip  = col("🥑", "Lipides",   "— g",      TEXT_MUTED)
        tdee_txt = ft.Text("", size=10, color=TEXT_MUTED)

    return ft.Column([
        ft.Row([c_cal, c_prot, c_gluc, c_lip],
               spacing=28, wrap=True,
               alignment=ft.MainAxisAlignment.CENTER),
        tdee_txt,
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6)


def _build_cycle_inline(app_state: dict) -> ft.Column:
    """
    Carte cycle hormonal inline — port de _draw_cycle_body + _render_cycle_card_inline.
    Affiche : dates, produits avec dose/utilité/demi-vie/dangérosité, risque stack, note.
    """
    controls = []

    try:
        fake = _FakeApp(app_state.get("current_user", ""))
        cycle = _db.cycle_get_active(fake)
    except Exception:
        cycle = None

    try:
        from data.cycle import PRODUCT_INFO
    except Exception:
        PRODUCT_INFO = {}

    if not cycle:
        controls.append(ft.Text("  Aucun cycle enregistré.", size=12, color=TEXT_MUTED))
        return ft.Column(controls, spacing=4)

    # ── Ligne dates ─────────────────────────────────────────────────────────
    controls.append(
        ft.Container(
            content=ft.Row([
                _info_cell("📅 Début",    cycle.get("debut", "—"),               TEXT),
                _info_cell("🏁 Fin est.", cycle.get("fin_estimee", "—"),         ACCENT_GLOW),
                _info_cell("⏱ Durée",    f"{cycle.get('longueur_sem','—')} sem.", TEXT_SUB),
            ], spacing=16, wrap=True),
            bgcolor=BG_CARD2, border_radius=8,
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            margin=ft.margin.only(bottom=4),
        )
    )

    # ── Produits ─────────────────────────────────────────────────────────────
    produits_s = cycle.get("produits_doses", "")
    if produits_s:
        controls.append(ft.Text("  Produits du stack :", size=11, color=TEXT_ACCENT,
                                 weight=ft.FontWeight.BOLD))
        entries    = [p.strip() for p in produits_s.split("|") if p.strip()]
        dang_scores = []

        for entry in entries:
            parts     = entry.split(":", 1)
            prod_name = parts[0].strip()
            prod_dose = parts[1].strip() if len(parts) > 1 else ""
            info      = PRODUCT_INFO.get(prod_name, {})
            dang_str  = info.get("dangerosite", "")
            stars     = dang_str.count("★")
            dang_scores.append(stars)
            dang_col  = DANG_COL.get(stars, TEXT_SUB)

            row_items = [
                ft.Text(f"• {prod_name}", size=12, color=TEXT, expand=True),
            ]
            if prod_dose:
                row_items.append(mk_badge(prod_dose, color=ACCENT_DIM, text_color=ACCENT_GLOW))
            if dang_str:
                row_items.append(ft.Text(dang_str, size=11, color=dang_col))

            sub_items = []
            if info:
                utilite  = info.get("utilite", "")
                demi_vie = info.get("demi_vie", "")
                notes_p  = info.get("notes", "")
                dose_ref = info.get("dose_min", "")

                if utilite or demi_vie:
                    line2 = []
                    if utilite:  line2.append(ft.Text(f"🎯 {utilite}", size=11, color=TEXT_SUB))
                    if demi_vie: line2.append(ft.Text(f"⏲ {demi_vie}", size=11, color=TEXT_MUTED))
                    sub_items.append(ft.Row(line2, spacing=12))

                if dose_ref:
                    sub_items.append(ft.Text(f"💊 Réf: {dose_ref}", size=10, color=TEXT_MUTED))
                if notes_p:
                    sub_items.append(ft.Text(f"⚡ {notes_p}", size=10, color="#cc8800"))

            controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Row(row_items, wrap=True, spacing=6),
                        *sub_items,
                    ], spacing=3),
                    bgcolor=BG_CARD2, border_radius=6,
                    padding=ft.padding.symmetric(horizontal=10, vertical=6),
                    margin=ft.margin.only(bottom=3),
                )
            )

        # Risque global
        if dang_scores:
            max_dang  = max(dang_scores)
            risk_txt  = RISK_TXT.get(max_dang, "—")
            risk_col  = DANG_COL.get(max_dang, TEXT_SUB)
            controls.append(
                ft.Row([
                    ft.Text("Risque stack :", size=11, color=TEXT_MUTED, width=110),
                    ft.Text(risk_txt, size=12, color=risk_col, weight=ft.FontWeight.BOLD),
                ], spacing=4)
            )

    # ── Note utilisateur ─────────────────────────────────────────────────────
    note = cycle.get("note", "")
    if note:
        controls.append(
            ft.Container(
                content=ft.Text(
                    f"📝  {note[:120]}{'…' if len(note) > 120 else ''}",
                    size=11, color=TEXT_SUB,
                ),
                bgcolor=BG_CARD2, border_radius=6,
                padding=ft.Padding.all(10),
                margin=ft.margin.only(top=4),
            )
        )

    return ft.Column(controls, spacing=4)


def _info_cell(label: str, value: str, color: str) -> ft.Column:
    return ft.Column([
        ft.Text(label, size=10, color=TEXT_MUTED),
        ft.Text(value or "—", size=13, color=color, weight=ft.FontWeight.BOLD),
    ], spacing=2)


def _build_pct_alert(app_state: dict) -> Optional[ft.Container]:
    """Alerte PCT urgente — port de features_module.get_pct_alert."""
    try:
        fake = _FakeApp(app_state.get("current_user", ""))
        cycle = _db.cycle_get_active(fake)
        if not cycle:
            return None
        debut_date = _parse_date_flex(cycle.get("debut", ""))
        if not debut_date:
            return None
        try:
            n_weeks = int(cycle.get("longueur_sem", 12))
        except Exception:
            n_weeks = 12
        washout_w  = 2
        pct_start  = debut_date + datetime.timedelta(weeks=n_weeks + washout_w)
        today      = datetime.date.today()
        days_left  = (pct_start - today).days
        if 0 < days_left <= 14:
            msg = (f"⚠️  PCT dans {days_left}j — Prépare Clomid & Nolvadex"
                   if days_left <= 7
                   else f"📋  PCT dans {days_left}j — Anticiper la commande PCT")
            col = "#ef4444" if days_left <= 7 else "#f59e0b"
            return ft.Container(
                content=ft.Text(f"  {msg}", size=12, color=col,
                                weight=ft.FontWeight.BOLD),
                bgcolor="#0a0d2b", border_radius=6,
                padding=ft.padding.symmetric(horizontal=12, vertical=8),
            )
        elif days_left <= 0:
            pct_end = pct_start + datetime.timedelta(weeks=4)
            if today <= pct_end:
                return ft.Container(
                    content=ft.Text("  💊  PCT EN COURS — Clomid + Nolvadex",
                                    size=12, color="#a855f7", weight=ft.FontWeight.BOLD),
                    bgcolor="#0a0d2b", border_radius=6,
                    padding=ft.padding.symmetric(horizontal=12, vertical=8),
                )
    except Exception:
        pass
    return None


def _build_weight_chart(rows_all: list) -> ft.Container:
    """
    Graphique évolution du poids.
    Flet sans matplotlib → sparkline ASCII + valeurs clés + mini tableau récent.
    """
    weights = []
    dates   = []
    for r in rows_all:
        try:
            d = _parse_date_flex(r.get("date", ""))
            w = float(r.get("poids", "").strip().replace(",", "."))
            if d and w > 0:
                weights.append(w)
                dates.append(d)
        except Exception:
            pass

    if not weights:
        return ft.Container(
            content=ft.Text("Aucune donnée de poids enregistrée.", size=12, color=TEXT_MUTED),
            bgcolor=BG_CARD2, border_radius=10,
            padding=ft.Padding.all(14),
        )

    spark = _sparkline(weights)
    w_min, w_max = min(weights), max(weights)
    w_last = weights[-1]
    delta  = w_last - weights[0] if len(weights) > 1 else 0.0
    delta_col = "#22c55e" if delta <= 0 else "#ef4444"
    delta_str = f"{delta:+.1f} kg" if delta else "stable"

    # Dernières entrées (5 max)
    recent = list(zip(dates, weights))[-5:]
    recent_rows = []
    for i, (d, w) in enumerate(reversed(recent)):
        prev_w = recent[-(i + 2)][1] if i + 1 < len(recent) else w
        arrow  = "▲" if w > prev_w else ("▼" if w < prev_w else "—")
        a_col  = "#ef4444" if w > prev_w else ("#22c55e" if w < prev_w else TEXT_MUTED)
        recent_rows.append(
            ft.Row([
                ft.Text(d.strftime(DATE_FMT), size=11, color=TEXT_SUB, width=90),
                ft.Text(f"{w:.1f} kg", size=12, color=TEXT, weight=ft.FontWeight.BOLD, width=70),
                ft.Text(arrow, size=11, color=a_col),
            ], spacing=6)
        )

    return ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Text(spark, size=14, color=ACCENT_GLOW,
                        font_family="monospace"),
                ft.Container(expand=True),
                ft.Text(delta_str, size=12, color=delta_col, weight=ft.FontWeight.BOLD),
            ]),
            ft.Row([
                ft.Text(f"Min : {w_min:.1f}", size=10, color=TEXT_MUTED),
                ft.Text(f"Max : {w_max:.1f}", size=10, color=TEXT_MUTED),
                ft.Text(f"Actuel : {w_last:.1f} kg", size=11, color=TEXT,
                        weight=ft.FontWeight.BOLD),
            ], spacing=12),
            ft.Divider(height=1, color=BORDER),
            *recent_rows,
        ], spacing=5),
        bgcolor=BG_CARD2, border_radius=10,
        padding=ft.Padding.all(14),
    )


def _build_week_card(monday: datetime.date, label: str, app_state: dict) -> ft.Container:
    """
    Carte semaine (en cours / suivante) — port complet de _render_week_view ERAGROK.
    Sections : Nutrition (moyenne réelle ou cibles) + Entraînement (planning) + Cycle.
    """
    sunday = monday + datetime.timedelta(days=6)
    date_range = f"{monday:%d/%m} → {sunday:%d/%m/%Y}"
    fake  = _FakeApp(app_state.get("current_user", ""))
    today = datetime.date.today()

    # ── SECTION NUTRITION ────────────────────────────────────────────────────
    week_set    = set(_week_dates(monday, sunday))
    nutr_rows   = []
    try:
        for r in _db.nutrition_get_all(fake):
            d = _parse_date_flex(r.get("date", ""))
            if d and d in week_set:
                nutr_rows.append([
                    r.get("date",""), r.get("poids",""), r.get("age",""),
                    r.get("calories",""), r.get("proteines",""),
                    r.get("glucides",""), r.get("lipides",""), r.get("note",""),
                ])
    except Exception:
        pass

    nutr_controls = [
        ft.Text("🍎  Nutrition", size=12, color=TEXT_ACCENT, weight=ft.FontWeight.BOLD)
    ]

    if nutr_rows:
        cal  = _avg(nutr_rows, 3)
        prot = _avg(nutr_rows, 4)
        gluc = _avg(nutr_rows, 5)
        lip  = _avg(nutr_rows, 6)
        pw   = []
        for r in nutr_rows:
            try:
                v = float(r[1]) if len(r) > 1 and r[1].strip() else None
                if v: pw.append(v)
            except Exception:
                pass
        poids_moy = sum(pw) / len(pw) if pw else None

        n = len(nutr_rows)
        jours_txt = f"{n} jour{'s' if n > 1 else ''} enregistré{'s' if n > 1 else ''}"
        nutr_controls.append(ft.Text(jours_txt, size=10, color=TEXT_SUB))
        for lbl, val, unit, col in [
            ("⚖️  Poids moy.",    poids_moy, "kg",   TEXT),
            ("🔥  Calories moy.", cal,        "kcal", ACCENT_GLOW),
            ("🥩  Prot. moy.",    prot,       "g",    "#22c55e"),
            ("🍚  Gluc. moy.",    gluc,       "g",    "#3b82f6"),
            ("🥑  Lip. moy.",     lip,        "g",    "#f59e0b"),
        ]:
            if val is None:
                continue
            nutr_controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Text(lbl, size=11, color=TEXT_SUB, width=130),
                        ft.Text(f"{val:.0f} {unit}", size=12, color=col,
                                weight=ft.FontWeight.BOLD),
                    ], spacing=4),
                    bgcolor=BG_CARD2, border_radius=5,
                    padding=ft.padding.symmetric(horizontal=8, vertical=3),
                )
            )
    elif monday > today:
        nutr_controls.append(
            ft.Text("   Aucune entrée nutrition cette semaine", size=11, color=TEXT_MUTED)
        )
    else:
        nutr_controls.append(
            ft.Text("   Aucune entrée nutrition cette semaine", size=11, color=TEXT_MUTED)
        )

    # ── SECTION ENTRAÎNEMENT ─────────────────────────────────────────────────
    sessions = []
    try:
        for r in _db.planning_get_all(fake):
            d = _parse_date_flex(r.get("date", ""))
            if d and d in week_set:
                sessions.append({
                    "date":    d,
                    "groupes": r.get("groupes", "").strip(),
                    "prog":    r.get("programme", "").strip(),
                    "types":   r.get("types", "").strip(),
                    "line":    r.get("line", "").strip(),
                })
    except Exception:
        pass

    training_controls = [
        ft.Text("🏋  Entraînement", size=12, color=TEXT_ACCENT, weight=ft.FontWeight.BOLD)
    ]

    if sessions:
        days_map = defaultdict(lambda: {"groupes": set(), "progs": set(), "lines": []})
        for s in sessions:
            d = s["date"]
            if s["groupes"]: days_map[d]["groupes"].add(s["groupes"])
            if s["prog"]:    days_map[d]["progs"].add(s["prog"])
            if s["line"]:
                clean = re.sub(r"\s*\([A-Z0-9_]+\)\s*$", "", s["line"]).strip()
                if clean and clean not in days_map[d]["lines"]:
                    days_map[d]["lines"].append(clean)

        for wd in range(7):
            d = monday + datetime.timedelta(days=wd)
            day_str = f"{DAY_FR[wd]} {d:%d/%m}"
            row_parts = [ft.Text(day_str, size=11, color=ACCENT_GLOW, width=60)]

            if d in days_map:
                info_d  = days_map[d]
                muscles = " · ".join(sorted(info_d["groupes"]))
                if muscles:
                    row_parts.append(ft.Text(f"💪 {muscles}", size=11, color=TEXT_SUB))
                for pg in sorted(info_d["progs"]):
                    row_parts.append(mk_badge(pg, color=ACCENT_DIM, text_color=ACCENT_GLOW))

                techs = info_d["lines"][:2]
                sub_rows = [ft.Row(row_parts, spacing=4, wrap=True)]
                for t in techs:
                    sub_rows.append(
                        ft.Text(f"  🔧 {t[:55]}{'…' if len(t)>55 else ''}",
                                size=10, color=TEXT_MUTED)
                    )
                if len(info_d["lines"]) > 2:
                    sub_rows.append(
                        ft.Text(f"  + {len(info_d['lines'])-2} exercice(s)…",
                                size=10, color=TEXT_MUTED)
                    )
                training_controls.append(
                    ft.Container(
                        content=ft.Column(sub_rows, spacing=2),
                        bgcolor=BG_CARD2, border_radius=6,
                        padding=ft.padding.symmetric(horizontal=8, vertical=5),
                        margin=ft.margin.only(bottom=2),
                    )
                )
            else:
                row_parts.append(ft.Text("Repos", size=11, color=TEXT_MUTED))
                training_controls.append(
                    ft.Container(
                        content=ft.Row(row_parts, spacing=4),
                        bgcolor=BG_CARD2, border_radius=6,
                        padding=ft.padding.symmetric(horizontal=8, vertical=4),
                        margin=ft.margin.only(bottom=2),
                    )
                )
    else:
        training_controls.append(
            ft.Text("   Aucune séance planifiée", size=11, color=TEXT_MUTED)
        )

    # ── SECTION CYCLE ────────────────────────────────────────────────────────
    return ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Text(f"📅  {label}", size=14, color=ACCENT,
                        weight=ft.FontWeight.BOLD, expand=True),
                ft.Text(date_range, size=10, color=TEXT_MUTED),
            ]),
            mk_sep(),
            *nutr_controls,
        ], spacing=5),
        bgcolor=BG_CARD, border_radius=R_CARD,
        border=ft.border.all(1, BORDER),
        padding=ft.Padding.all(16),
        expand=True,
    )


def _build_week_cycle(monday: datetime.date, app_state: dict) -> list:
    """
    Port de _render_week_cycle : phase, semaine N, produits filtrés (PCT masqué),
    avertissement PCT imminent.
    """
    controls = [
        ft.Text("💉  Cycle hormonal", size=12, color=TEXT_ACCENT,
                weight=ft.FontWeight.BOLD)
    ]

    try:
        fake = _FakeApp(app_state.get("current_user", ""))
        _last = _db.cycle_get_active(fake)
    except Exception:
        _last = None

    try:
        from data.cycle import PRODUCT_INFO as PINFO
    except Exception:
        PINFO = {}

    if not _last:
        controls.append(ft.Text("   Aucun cycle enregistré.", size=11, color=TEXT_MUTED))
        return controls

    debut_str  = _last.get("debut", "")
    fin_str    = _last.get("fin_estimee", "")
    longueur_s = _last.get("longueur_sem", "12")
    produits_s = _last.get("produits_doses", "")
    note_s     = _last.get("note", "")

    debut_date = _parse_date_flex(debut_str)
    try:
        n_weeks = int(str(longueur_s).strip())
    except Exception:
        n_weeks = 12

    washout_w = 2
    phase, phase_col, week_label, cycle_actif = "—", TEXT_MUTED, "—", False
    _pct_start = None

    if debut_date:
        _pct_start   = debut_date + datetime.timedelta(weeks=n_weeks + washout_w)
        debut_monday = debut_date - datetime.timedelta(days=debut_date.weekday())
        delta_weeks  = (monday - debut_monday).days // 7

        if delta_weeks < 0:
            jours = (debut_date - monday).days
            phase, phase_col = "AVANT CYCLE", TEXT_MUTED
            week_label = f"Début dans {jours}j"
        elif delta_weeks < n_weeks:
            phase, phase_col = "CYCLE", "#22c55e"
            week_label = f"S{delta_weeks+1} / {n_weeks}"
            cycle_actif = True
        elif delta_weeks < n_weeks + washout_w:
            phase, phase_col = "WASHOUT", "#f59e0b"
            week_label = f"Wash-out S{delta_weeks-n_weeks+1}/{washout_w}"
            cycle_actif = True
        else:
            phase, phase_col = "TERMINÉ", TEXT_MUTED
            week_label = f"Fin : {fin_str}"

    phase_bg = {
        "CYCLE": "#0d2b0d", "WASHOUT": "#2b1f00",
        "PCT": "#0a0d2b",   "AVANT CYCLE": "#1a1a28",
        "TERMINÉ": "#1a1a1a",
    }.get(phase, BG_CARD2)

    controls.append(
        ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Text(f"  {phase}  ", size=11, color=phase_col,
                                    weight=ft.FontWeight.BOLD),
                    bgcolor=phase_bg, border_radius=5,
                    padding=ft.padding.symmetric(horizontal=4, vertical=3),
                ),
                ft.Text(week_label, size=11, color=TEXT),
                ft.Container(expand=True),
                ft.Text(f"Début : {debut_str}", size=10, color=TEXT_MUTED) if debut_str else ft.Container(),
            ], spacing=8),
            bgcolor=BG_CARD2, border_radius=7,
            padding=ft.padding.symmetric(horizontal=10, vertical=6),
        )
    )

    # Filtre produits PCT
    def _show_this_product(entry_raw):
        pname = entry_raw.split(":")[0].strip()
        if pname.startswith("[PCT]") or "_J+" in pname:
            if _pct_start is None: return False
            return (_pct_start - monday).days <= 14
        if pname in PCT_NAMES:
            if _pct_start is None: return False
            return (_pct_start - monday).days <= 14
        return True

    if not produits_s and (cycle_actif or phase == "AVANT CYCLE"):
        controls.append(
            ft.Container(
                content=ft.Text("  Aucun produit renseigné.", size=11, color=TEXT_MUTED),
                bgcolor=BG_CARD2, border_radius=6,
                padding=ft.padding.symmetric(horizontal=10, vertical=5),
            )
        )

    if produits_s and (cycle_actif or phase == "AVANT CYCLE"):
        entries    = [p.strip() for p in produits_s.split("|") if p.strip()]
        entries    = [e for e in entries if _show_this_product(e)]
        dang_scores = []

        for entry in entries:
            parts     = entry.split(":", 1)
            prod_name = parts[0].strip()
            prod_dose = parts[1].strip() if len(parts) > 1 else ""
            info      = PINFO.get(prod_name, {})
            dang_str  = info.get("dangerosite", "")
            stars     = dang_str.count("★")
            dang_scores.append(stars if stars else 0)
            dang_col  = DANG_COL.get(stars, TEXT_SUB)

            row_parts = [ft.Text(prod_name, size=11, color=TEXT, expand=True)]
            if prod_dose:
                row_parts.append(mk_badge(f"💉 {prod_dose} mg/sem",
                                          color=ACCENT_DIM, text_color=ACCENT_GLOW))
            if info.get("dose_min") and info.get("dose_max"):
                row_parts.append(mk_badge(f"réf {info['dose_min']}–{info['dose_max']}",
                                          color="#1a2a1a", text_color=TEXT_MUTED))
            elif info.get("dose_min"):
                row_parts.append(mk_badge(f"réf {info['dose_min']}",
                                          color="#1a2a1a", text_color=TEXT_MUTED))
            if dang_str:
                row_parts.append(ft.Text(dang_str, size=11, color=dang_col))

            sub_parts = []
            if info:
                utilite  = info.get("utilite", "")
                demi_vie = info.get("demi_vie", "")
                notes_p  = info.get("notes", "")
                if utilite or demi_vie:
                    l2 = []
                    if utilite:  l2.append(ft.Text(f"🎯 {utilite}", size=10, color=TEXT_SUB))
                    if demi_vie: l2.append(ft.Text(f"⏲ {demi_vie}", size=10, color=TEXT_MUTED))
                    sub_parts.append(ft.Row(l2, spacing=10))
                if notes_p:
                    sub_parts.append(ft.Text(f"⚡ {notes_p}", size=10, color="#cc8800"))

            controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Row(row_parts, wrap=True, spacing=4),
                        *sub_parts,
                    ], spacing=2),
                    bgcolor=BG_CARD2, border_radius=6,
                    padding=ft.padding.symmetric(horizontal=10, vertical=5),
                    margin=ft.margin.only(bottom=2),
                )
            )

        if dang_scores and any(s > 0 for s in dang_scores):
            max_d  = max(dang_scores)
            controls.append(
                ft.Row([
                    ft.Text("Risque stack :", size=11, color=TEXT_MUTED, width=95),
                    ft.Text(RISK_TXT.get(max_d, "—"), size=11,
                            color=DANG_COL.get(max_d, TEXT_SUB), weight=ft.FontWeight.BOLD),
                ], spacing=4)
            )

        if note_s:
            controls.append(
                ft.Container(
                    content=ft.Text(f"📝 {note_s[:90]}{'…' if len(note_s)>90 else ''}",
                                    size=10, color=TEXT_SUB),
                    bgcolor=BG_CARD2, border_radius=6,
                    padding=ft.Padding.all(8),
                )
            )

    elif phase == "WASHOUT":
        controls.append(
            ft.Container(
                content=ft.Text("  🚫  Arrêt de tous les produits du cycle",
                                size=11, color="#f59e0b"),
                bgcolor=BG_CARD2, border_radius=6,
                padding=ft.padding.symmetric(horizontal=10, vertical=6),
            )
        )

    # Avertissement PCT imminent
    if _pct_start and phase in ("CYCLE", "WASHOUT"):
        days_left = (_pct_start - monday).days
        if 0 < days_left <= 14:
            msg = (f"⚠️  PCT dans {days_left}j — Prépare Clomid & Nolvadex"
                   if days_left <= 7
                   else f"📋  PCT dans {days_left}j — Anticiper la commande PCT")
            col = "#ef4444" if days_left <= 7 else "#f59e0b"
            controls.append(
                ft.Container(
                    content=ft.Text(f"  {msg}", size=11, color=col),
                    bgcolor="#0a0d2b", border_radius=6,
                    padding=ft.padding.symmetric(horizontal=10, vertical=5),
                )
            )
        elif days_left <= 0:
            controls.append(
                ft.Container(
                    content=ft.Text("  💊  PCT EN COURS — Clomid + Nolvadex",
                                    size=11, color="#a855f7"),
                    bgcolor="#0a0d2b", border_radius=6,
                    padding=ft.padding.symmetric(horizontal=10, vertical=5),
                )
            )

    return controls


# ══════════════════════════════════════════════════════════════════════════════
#  HELPER FAKE APP (duck typing pour les fonctions _db)
# ══════════════════════════════════════════════════════════════════════════════

class _FakeApp:
    def __init__(self, current_user: str):
        self.current_user = current_user


# ══════════════════════════════════════════════════════════════════════════════
#  CLASSE PRINCIPALE — NutritionView
# ══════════════════════════════════════════════════════════════════════════════

class NutritionView:
    """
    Module Nutrition complet — onglets :
      0 · Calculs & IMC   (poids, ajustement, macros calculées, jauge IMC, alerte PCT)
      1 · Plan alimentaire (dernier plan accepté depuis DB + bouton accepter)
      2 · Historique       (tableau triable, modifier, supprimer, tout supprimer)
      3 · Semaines         (en cours + suivante : nutrition / entraînement / cycle)
    """

    def __init__(self, page: ft.Page, app_state: dict,
                 on_navigate=None):
        self.page        = page
        self.app_state   = app_state
        self.on_navigate = on_navigate  # callable(index) — fourni par main.py

        self.state = {
            "poids":      self._default_poids(),
            "adjustment": self.app_state.get("user_info", {}).get("ajustement", "Maintien (0%)"),
            "tab":        0,
            "hist_sort":  ("date", True),   # (colonne, asc)
            "dirty":      False,
            # Édit inline historique
            "_edit_row":  None,
        }

        self._tab_body:       Optional[ft.Column] = None  # kept for compat
        self._poids_field:    Optional[ft.TextField]  = None
        self._adj_dd:         Optional[ft.Dropdown]   = None
        self._cal_text:       Optional[ft.Text]       = None
        self._prot_text:      Optional[ft.Text]       = None
        self._gluc_text:      Optional[ft.Text]       = None
        self._lip_text:       Optional[ft.Text]       = None
        self._tdee_text:      Optional[ft.Text]       = None
        self._imc_container:  Optional[ft.Container]  = None
        self._hist_col:       Optional[ft.Column]     = None
        self._plan_col:       Optional[ft.Column]     = None
        self._edit_dialog:    Optional[ft.AlertDialog] = None

        # Catalogue aliments
        self._food_cat_col:        Optional[ft.Column]    = None
        self._food_detail_name:    Optional[ft.Text]      = None
        self._food_detail_kcal:    Optional[ft.Text]      = None
        self._food_detail_macros:  Optional[ft.Text]      = None
        self._food_detail_notes:   Optional[ft.Text]      = None
        self._food_selected_nom:   Optional[str]          = None
        self._food_selected_ref:   dict = {"container": None}

        self.root_col = ft.Column(spacing=0, expand=True)
        self._build_all()

    def get_view(self) -> ft.Column:
        return self.root_col

    # ── Build ──────────────────────────────────────────────────────────────────

    def _build_all(self):
        self.root_col.controls.clear()
        self.root_col.controls.append(self._build_hero())
        # Calculs nutritionnels : section FIXE toujours visible
        self.root_col.controls.append(self._build_calculs_tab())
        # Sections collapsibles scrollables
        scroll_col = ft.Column(
            spacing=0, expand=True, scroll=ft.ScrollMode.AUTO,
            controls=[
                self._collapsible_section("  🍽  PLAN ALIMENTAIRE",
                                          self._build_plan_tab, collapsed=True,
                                          extra_widget=ft.TextButton(
                                              content=ft.Text("⚡ Générer", size=11,
                                                              color=ACCENT,
                                                              weight=ft.FontWeight.BOLD),
                                              on_click=self._on_open_meal_generator,
                                          )),
                self._collapsible_section("  📅  SEMAINES",
                                          self._build_semaines_tab, collapsed=True),
                self._collapsible_section("  🛒  LISTE DE COURSES",
                                          self._build_shopping_tab, collapsed=True,
                                          extra_widget=ft.TextButton(
                                              content=ft.Text("🔄 Maj prix", size=11,
                                                              color=ACCENT,
                                                              weight=ft.FontWeight.BOLD),
                                              on_click=self._on_shopping_maj_prix,
                                          )),
                self._collapsible_section("  📋  HISTORIQUE",
                                          self._build_historique_tab, collapsed=True),
                self._collapsible_section("  🥗  CATALOGUE ALIMENTS",
                                          self._build_food_catalogue_tab, collapsed=True),
            ],
        )
        self.root_col.controls.append(scroll_col)

    def _collapsible_section(self, title: str, builder_fn,
                              collapsed: bool = True,
                              extra_widget=None) -> ft.Container:
        """Section collapsible — même système que le dashboard."""
        icon_ref = ft.Ref[ft.Text]()
        body_ref = ft.Ref[ft.Container]()
        state    = {"open": not collapsed, "built": False}

        def _toggle(e=None):
            state["open"] = not state["open"]
            icon_ref.current.value = "▲" if state["open"] else "▼"
            if state["open"] and not state["built"]:
                try:
                    body_ref.current.content = builder_fn()
                    state["built"] = True
                except Exception:
                    body_ref.current.content = ft.Text(
                        "Erreur chargement", color=TEXT_MUTED, size=12)
            body_ref.current.visible = state["open"]
            try: e.page.update()
            except Exception: pass

        header_controls = [
            ft.Text(title, size=13, color=TEXT_ACCENT,
                    weight=ft.FontWeight.BOLD, expand=True),
        ]
        if extra_widget:
            header_controls.append(extra_widget)
        header_controls.append(
            ft.Text("▼" if collapsed else "▲", size=12, color=ACCENT, ref=icon_ref)
        )

        header = ft.Container(
            content=ft.Row(header_controls, spacing=8,
                           vertical_alignment=ft.CrossAxisAlignment.CENTER),
            on_click=_toggle,
            bgcolor=BG_CARD,
            padding=ft.Padding.symmetric(horizontal=16, vertical=12),
        )

        if not collapsed:
            try:
                initial_content = builder_fn()
                state["built"] = True
            except Exception:
                initial_content = ft.Text("Erreur chargement", color=TEXT_MUTED, size=12)
        else:
            initial_content = ft.Container()

        body = ft.Container(
            content=initial_content,
            visible=not collapsed,
            ref=body_ref,
        )

        return ft.Container(
            content=ft.Column([header, body], spacing=0),
            bgcolor=BG_CARD,
            border_radius=R_CARD,
            border=ft.border.all(1, BORDER),
            margin=ft.margin.only(bottom=8),
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
        )

    def _build_hero(self) -> ft.Container:
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("🍎  NUTRITION", size=22, color=ACCENT,
                            weight=ft.FontWeight.BOLD),
                    ft.Container(expand=True),
                    mk_badge(self.app_state.get("user_info", {}).get("name", "").upper() or "—"),
                ]),
                ft.Text("Calculs · Plan alimentaire · Semaines · Historique",
                        size=11, color=TEXT_MUTED),
            ], spacing=4),
            bgcolor=BG_CARD,
            padding=ft.padding.symmetric(horizontal=20, vertical=16),
            margin=ft.margin.only(bottom=3),
        )

    # ══════════════════════════════════════════════════════════════════════════
    # ONGLET 0 — CALCULS & IMC
    # Port de show_nutrition_screen  section "CALCULS NUTRITIONNELS" + IMC + PCT
    # ══════════════════════════════════════════════════════════════════════════

    def _build_calculs_tab(self) -> ft.Container:
        ui = self.app_state.get("user_info") or {}

        adj_keys = list(utils.ADJUSTMENTS.keys())
        cur_adj  = self.state["adjustment"]
        if cur_adj not in adj_keys:
            cur_adj = "Maintien (0%)"

        self._poids_field = mk_entry(
            label="Poids (kg)", hint="ex: 82.5",
            value=self.state["poids"], width=110,
            on_change=self._on_poids_change,
        )
        self._adj_dd = mk_dropdown(
            "Ajustement", adj_keys, value=cur_adj, width=320,
            on_change=self._on_adj_change,
        )

        # Labels macros dynamiques
        self._cal_text  = ft.Text("— kcal",  size=20, color=ACCENT_GLOW, weight=ft.FontWeight.BOLD)
        self._prot_text = ft.Text("— g",     size=18, color="#4aaa4a",   weight=ft.FontWeight.BOLD)
        self._gluc_text = ft.Text("— g",     size=18, color="#3b82f6",   weight=ft.FontWeight.BOLD)
        self._lip_text  = ft.Text("— g",     size=18, color="#a855f7",   weight=ft.FontWeight.BOLD)
        self._tdee_text = ft.Text("",        size=10, color=TEXT_MUTED)

        macro_row = ft.Column([
            ft.Row([
                ft.Column([ft.Text("🔥  Calories",  size=11, color=TEXT_MUTED), self._cal_text],
                          spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Column([ft.Text("🥩  Protéines", size=11, color=TEXT_MUTED), self._prot_text],
                          spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Column([ft.Text("🍚  Glucides",  size=11, color=TEXT_MUTED), self._gluc_text],
                          spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Column([ft.Text("🥑  Lipides",   size=11, color=TEXT_MUTED), self._lip_text],
                          spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            ], spacing=24, wrap=True, alignment=ft.MainAxisAlignment.CENTER),
            self._tdee_text,
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6)

        # Métriques profil
        poids_val = taille_val = imc_val = imc_cat = None
        try:
            poids_val  = float(self.state["poids"].replace(",", "."))
            taille_val = float(ui.get("taille", 0))
            if poids_val > 0 and taille_val > 0:
                imc_val, imc_cat = utils.calculer_imc(poids_val, taille_val)
        except Exception:
            pass

        metrics_col = _build_metrics_col(poids_val, taille_val, imc_val, imc_cat, ui)

        # Jauge IMC
        self._imc_container = ft.Container(
            content=_build_imc_gauge(imc_val, poids_val, taille_val),
            expand=True,
        )

        # Alerte PCT
        pct_alert = _build_pct_alert(self.app_state)

        # Boutons actions
        actions_row = ft.Row([
            mk_btn("📤 Exporter PDF", self._on_export_pdf,
                   color="#1a1a2e", hover="#252540", width=140, height=36),
            mk_btn("🍽 Calculateur", self._on_open_meal_calc,
                   color="#1a2a3a", hover="#223344", width=130, height=36),
            mk_btn("💾 Sauvegarder", self._on_save_nutrition,
                   color=SUCCESS, hover=SUCCESS_HVR, width=140, height=36),
        ], spacing=8, wrap=True)

        # Déclencher le calcul initial
        self._update_macros()

        return ft.Container(
            content=ft.Column([
                # En-tête + boutons
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            mk_title("  📊  CALCULS NUTRITIONNELS"),
                            ft.Container(expand=True),
                        ]),
                        mk_sep(),
                        actions_row,
                    ], spacing=8),
                    padding=ft.padding.only(left=16, right=16, top=14, bottom=10),
                ),

                # Inputs
                ft.Container(
                    content=ft.Row([self._poids_field, self._adj_dd],
                                   spacing=16, wrap=True),
                    padding=ft.padding.symmetric(horizontal=16),
                ),
                ft.Container(height=8),

                # Macros calculées
                ft.Container(
                    content=macro_row,
                    bgcolor=BG_CARD2, border_radius=10,
                    padding=ft.Padding.all(14),
                    margin=ft.margin.symmetric(horizontal=12),
                ),
                ft.Container(height=8),

                # Métriques profil en ligne (poids, IMC, taille, âge, TDEE)
                ft.Container(
                    content=metrics_col,
                    padding=ft.padding.symmetric(horizontal=16),
                ),
                ft.Container(height=6),

                # Jauge IMC pleine largeur
                ft.Container(
                    content=_build_imc_gauge(imc_val, poids_val, taille_val),
                    padding=ft.padding.symmetric(horizontal=12),
                ),

                # Alerte PCT (si active)
                *(
                    [ft.Container(content=pct_alert,
                                  padding=ft.padding.symmetric(horizontal=12, vertical=6))]
                    if pct_alert else []
                ),

                ft.Container(height=14),
            ], spacing=0),
            bgcolor=BG_CARD, border_radius=R_CARD,
            border=ft.border.all(1, BORDER),
            margin=ft.margin.symmetric(horizontal=12, vertical=6),
        )

    # ══════════════════════════════════════════════════════════════════════════
    # ONGLET 1 — PLAN ALIMENTAIRE
    # Port de la section "PLAN ALIMENTAIRE" de show_nutrition_screen + dashboard
    # ══════════════════════════════════════════════════════════════════════════

    def _build_plan_tab(self) -> ft.Container:
        self._plan_col = ft.Column(spacing=6)
        self._refresh_plan_display()
        return ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Row([
                        mk_title("  🍽  PLAN ALIMENTAIRE"),
                        ft.Container(expand=True),
                        mk_btn("⚡ Générer", self._on_open_meal_generator,
                               color=ACCENT, hover=ACCENT_HOVER, width=120, height=36),
                    ]),
                    padding=ft.padding.only(left=16, right=16, top=14, bottom=8),
                ),
                ft.Divider(height=1, color=BORDER),
                self._plan_col,
            ], spacing=0),
            bgcolor=BG_CARD, border_radius=R_CARD,
            border=ft.border.all(1, BORDER),
            margin=ft.margin.symmetric(horizontal=12, vertical=6),
        )

    def _refresh_plan_display(self):
        if self._plan_col is None:
            return
        self._plan_col.controls.clear()
        fake = self._fake_app()

        last_plan = None
        try:
            last_plan = _db.meal_plan_get_last(fake, accepted_only=False)
        except Exception:
            pass

        if not last_plan:
            self._plan_col.controls.append(ft.Container(
                content=ft.Text("Aucun plan alimentaire — génère un plan depuis ⚡ Générer.",
                                size=12, color=TEXT_MUTED),
                bgcolor=BG_CARD2, border_radius=8, padding=ft.Padding.all(14),
            ))
            self._safe_update()
            return

        plan_json = last_plan.get("plan_json") or []
        mode      = last_plan.get("mode", "jour")
        accepted  = last_plan.get("accepted", False)
        cal_t     = last_plan.get("cal_target", 0)
        prot_t    = last_plan.get("prot_target", 0)
        gluc_t    = last_plan.get("gluc_target", 0)
        lip_t     = last_plan.get("lip_target", 0)
        adj_lbl   = last_plan.get("adj_label", "")

        # Badge + macros sur une seule ligne compacte
        badge = ft.Container(
            content=ft.Text("✅ Plan accepté", size=11, color="#000000",
                            weight=ft.FontWeight.BOLD),
            bgcolor=SUCCESS, border_radius=4,
            padding=ft.padding.symmetric(horizontal=10, vertical=4),
        ) if accepted else ft.Container(
            content=ft.Row([
                ft.Text("⏳ Non accepté", size=11, color=ACCENT_GLOW),
                mk_btn("✅ Accepter", self._on_accept_plan,
                       color=SUCCESS, hover=SUCCESS_HVR, width=100, height=28),
            ], spacing=8),
            bgcolor=BG_CARD2, border_radius=4,
            padding=ft.padding.symmetric(horizontal=8, vertical=4),
        )

        self._plan_col.controls.append(ft.Container(
            content=ft.Row([
                badge,
                ft.Container(expand=True),
                ft.Text(f"🔥 {cal_t:.0f}", size=12, color=ACCENT_GLOW, weight=ft.FontWeight.BOLD),
                ft.Text(f"🥩 {prot_t:.0f}g", size=11, color="#4aaa4a"),
                ft.Text(f"🍚 {gluc_t:.0f}g", size=11, color="#3b82f6"),
                ft.Text(f"🥑 {lip_t:.0f}g",  size=11, color="#a855f7"),
                ft.Text(adj_lbl, size=10, color=TEXT_MUTED),
            ], spacing=10),
            bgcolor=BG_CARD2, border_radius=8,
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            margin=ft.margin.only(bottom=4),
        ))

        # Détecter plan journalier vs multi-jours
        is_multiday = (mode != "jour" and plan_json and
                       isinstance(plan_json[0], dict) and "plan" in plan_json[0])

        if is_multiday:
            # Plan semaine/mois : afficher onglets Jour 1, Jour 2...
            days = plan_json
            self._render_multiday_tabs(days)
        else:
            # Plan journalier simple
            meals = plan_json if isinstance(plan_json, list) else []
            self._render_meals(meals)

        self._safe_update()

    def _render_meals(self, meals: list):
        """Affiche les cartes repas pour un plan journalier."""
        SLOT_ICONS = {"matin": "🌅", "midi": "☀️", "collation": "🍎",
                      "soir": "🌙", "coucher": "🌛"}
        for i, meal in enumerate(meals):
            if not isinstance(meal, dict):
                continue
            # Clés THRESHOLD: name/items/tot_cal
            name  = meal.get("name", meal.get("nom", f"Repas {i+1}"))
            items = meal.get("items", meal.get("aliments", []))
            cal   = meal.get("tot_cal", meal.get("calories", 0))
            icon  = SLOT_ICONS.get(meal.get("type", ""), "🍽")

            item_rows = []
            for item in items:
                if not isinstance(item, dict): continue
                food = item.get("food", item.get("aliment", "?"))
                g    = item.get("g", 0)
                p    = item.get("p", 0)
                gc   = item.get("g_", 0)
                l    = item.get("l", 0)
                item_rows.append(ft.Container(
                    content=ft.Row([
                        ft.Container(width=6, height=6, bgcolor=ACCENT_GLOW,
                                     border_radius=3),
                        ft.Text(food, size=12, color=TEXT, expand=True),
                        ft.Text(f"{g:.0f}g", size=11, color=ACCENT),
                        ft.Text(f"{p:.1f}P {gc:.1f}G {l:.1f}L",
                                size=10, color=TEXT_MUTED),
                    ], spacing=8),
                    padding=ft.padding.symmetric(horizontal=4, vertical=2),
                ))

            self._plan_col.controls.append(ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text(f"{icon} {name}", size=13, color=ACCENT_GLOW,
                                weight=ft.FontWeight.BOLD, expand=True),
                        ft.Text(f"{cal:.0f} kcal", size=11, color=TEXT_MUTED),
                    ]),
                    ft.Divider(height=1, color=BORDER),
                    *item_rows,
                ], spacing=3),
                bgcolor=BG_CARD2, border_radius=8,
                padding=ft.Padding.all(10),
                margin=ft.margin.only(bottom=4),
            ))

    def _render_multiday_tabs(self, days: list):
        """Affiche navigation par onglets pour plan semaine/mois."""
        if not days: return
        self._day_idx = 0

        day_content = ft.Column(spacing=4)

        def _show_day(idx: int):
            self._day_idx = idx
            day_content.controls.clear()
            d = days[idx]
            plan = d.get("plan", [])
            date_str = str(d.get("date", f"Jour {idx+1}"))
            day_content.controls.append(ft.Container(
                content=ft.Text(f"📅 {date_str}", size=11, color=TEXT_MUTED),
                padding=ft.padding.only(bottom=4),
            ))
            for i, meal in enumerate(plan):
                if not isinstance(meal, dict): continue
                name  = meal.get("name", f"Repas {i+1}")
                items = meal.get("items", [])
                cal   = meal.get("tot_cal", 0)
                item_rows = []
                for item in items:
                    if not isinstance(item, dict): continue
                    food = item.get("food", "?")
                    g    = item.get("g", 0)
                    item_rows.append(ft.Text(f"  • {food} — {g:.0f}g",
                                             size=11, color=TEXT_SUB))
                day_content.controls.append(ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text(name, size=12, color=ACCENT_GLOW,
                                    weight=ft.FontWeight.BOLD, expand=True),
                            ft.Text(f"{cal:.0f} kcal", size=11, color=TEXT_MUTED),
                        ]),
                        *item_rows,
                    ], spacing=2),
                    bgcolor=BG_CARD2, border_radius=8,
                    padding=ft.Padding.all(8),
                    margin=ft.margin.only(bottom=4),
                ))
            try: self.page.update()
            except Exception: pass

        # Barre onglets jours
        tab_row = ft.Row(spacing=4, wrap=True)
        tab_btns = []
        for i, d in enumerate(days):
            date_str = str(d.get("date", f"Jour {i+1}"))
            label = date_str[-5:] if len(date_str) >= 5 else date_str

            def _mk_click(idx=i):
                def _click(e=None):
                    for j, b in enumerate(tab_btns):
                        b.style = ft.ButtonStyle(
                            bgcolor=ACCENT if j == idx else BG_CARD2,
                            color=TEXT if j == idx else TEXT_MUTED,
                            padding=ft.padding.symmetric(horizontal=8, vertical=4),
                            shape=ft.RoundedRectangleBorder(radius=6),
                        )
                    _show_day(idx)
                    try: self.page.update()
                    except Exception: pass
                return _click

            btn = ft.TextButton(
                content=ft.Text(f"J{i+1}", size=11),
                on_click=_mk_click(i),
                style=ft.ButtonStyle(
                    bgcolor=ACCENT if i == 0 else BG_CARD2,
                    color=TEXT if i == 0 else TEXT_MUTED,
                    padding=ft.padding.symmetric(horizontal=8, vertical=4),
                    shape=ft.RoundedRectangleBorder(radius=6),
                ),
            )
            tab_btns.append(btn)
            tab_row.controls.append(btn)

        self._plan_col.controls.append(tab_row)
        self._plan_col.controls.append(day_content)
        _show_day(0)

    # ══════════════════════════════════════════════════════════════════════════
    # ONGLET 2 — HISTORIQUE
    # Port de la section "HISTORIQUE NUTRITION" de show_nutrition_screen :
    # tableau triable (Date / Poids / Calories / Note),
    # modifier (popup), supprimer sélectionné, tout supprimer.
    # ══════════════════════════════════════════════════════════════════════════

    def _build_shopping_tab(self) -> ft.Container:
        """Liste de courses inline — réutilise ShoppingView."""
        try:
            from data.shopping import ShoppingView
            last = _db.meal_plan_get_last(self._fake_app(), accepted_only=False)
            plan = last.get("plan_json", []) if last else []
            self._shopping_view = ShoppingView(self.page, self.app_state, plan)
            inner = self._shopping_view.get_view()
        except Exception as ex:
            self._shopping_view = None
            inner = ft.Text(f"Erreur : {ex}", color=DANGER, size=12)

        popup_btn = mk_btn("🔗 Popup", self._on_shopping_list,
                           color=BG_CARD2, hover=BG_CARD, width=120, height=32)

        return ft.Container(
            content=ft.Column([
                inner,
                ft.Container(height=8),
                ft.Row([popup_btn], alignment=ft.MainAxisAlignment.END),
            ], spacing=0),
            bgcolor=BG_CARD,
            border_radius=R_CARD,
            border=ft.Border.all(1, BORDER),
            margin=ft.Margin.symmetric(horizontal=12, vertical=6),
            padding=ft.Padding.all(12),
        )

    def _build_historique_tab(self) -> ft.Container:
        self._hist_col = ft.Column(spacing=4, scroll=ft.ScrollMode.AUTO)
        self._refresh_hist()

        return ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Column([
                        mk_title("  📋  HISTORIQUE NUTRITION"),
                        ft.Text("Appuie sur une ligne pour la sélectionner · Double-tap pour modifier",
                                size=10, color=TEXT_MUTED),
                        mk_sep(),
                    ], spacing=6),
                    padding=ft.padding.only(left=16, right=16, top=14, bottom=8),
                ),
                # En-têtes colonnes (cliquables pour tri)
                ft.Container(
                    content=ft.Row([
                        ft.TextButton(
                            content=ft.Text("Date ↕", size=11, color=TEXT_SUB,
                                            weight=ft.FontWeight.BOLD),
                            on_click=lambda e: self._on_hist_sort("date"),
                            width=100,
                        ),
                        ft.TextButton(
                            content=ft.Text("Poids ↕", size=11, color=TEXT_SUB,
                                            weight=ft.FontWeight.BOLD),
                            on_click=lambda e: self._on_hist_sort("poids"),
                            width=80,
                        ),
                        ft.TextButton(
                            content=ft.Text("Calories ↕", size=11, color=TEXT_SUB,
                                            weight=ft.FontWeight.BOLD),
                            on_click=lambda e: self._on_hist_sort("calories"),
                            width=90,
                        ),
                        ft.Text("Note", size=11, color=TEXT_SUB,
                                weight=ft.FontWeight.BOLD, expand=True),
                    ], spacing=0),
                    bgcolor=BG_CARD2, border_radius=0,
                    padding=ft.padding.symmetric(horizontal=16, vertical=4),
                ),
                ft.Container(
                    content=self._hist_col,
                    expand=True,
                    padding=ft.padding.symmetric(horizontal=12, vertical=4),
                ),
                # Boutons actions
                ft.Container(
                    content=ft.Row([
                        mk_btn("✏  Modifier",       self._on_hist_edit,
                               color=GRAY, hover=GRAY_HVR, width=120, height=36),
                        mk_btn("🗑  Supprimer",      self._on_hist_delete,
                               color=DANGER, hover=DANGER_HVR, width=130, height=36),
                        mk_btn("🗑  Tout supprimer", self._on_hist_delete_all,
                               color="#5a0000", hover="#7a0000", width=150, height=36),
                    ], spacing=8, wrap=True),
                    padding=ft.padding.symmetric(horizontal=12, vertical=8),
                ),
                ft.Container(height=10),
            ], spacing=0),
            bgcolor=BG_CARD, border_radius=R_CARD,
            border=ft.border.all(1, BORDER),
            margin=ft.margin.symmetric(horizontal=12, vertical=6),
        )

    def _refresh_hist(self):
        if self._hist_col is None:
            return
        self._hist_col.controls.clear()

        try:
            rows = _db.nutrition_get_all(self._fake_app())
        except Exception:
            rows = []

        col, asc = self.state["hist_sort"]
        try:
            rows = sorted(rows, key=lambda r: str(r.get(col, "")), reverse=not asc)
        except Exception:
            pass

        if not rows:
            self._hist_col.controls.append(
                ft.Text("(Aucune entrée)", size=12, color=TEXT_MUTED)
            )
        else:
            for row in rows:
                row_id  = row.get("id", "")
                date_s  = row.get("date", "")
                poids_s = row.get("poids", "")
                cal_s   = row.get("calories", "")
                note_s  = str(row.get("note", ""))
                selected = self.state.get("_sel_row_id") == row_id

                self._hist_col.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Text(date_s,  size=12, color=TEXT,      width=100),
                            ft.Text(poids_s, size=12, color=TEXT_SUB,  width=75),
                            ft.Text(cal_s,   size=12, color=ACCENT_GLOW, width=80),
                            ft.Text(note_s[:40] + ("…" if len(note_s) > 40 else ""),
                                    size=11, color=TEXT_MUTED, expand=True),
                        ], spacing=0),
                        bgcolor="#1a2a1a" if selected else BG_CARD2,
                        border_radius=6,
                        border=ft.border.all(1, ACCENT) if selected else None,
                        padding=ft.padding.symmetric(horizontal=8, vertical=6),
                        margin=ft.margin.only(bottom=2),
                        ink=True,
                        data=row,
                        on_click=lambda e: self._on_hist_row_click(e.control.data),
                    )
                )

        self._safe_update()

    # ══════════════════════════════════════════════════════════════════════════
    # ONGLET 3 — SEMAINES
    # Port de render_dashboard sections 5 : deux cartes semaine côte à côte
    # ══════════════════════════════════════════════════════════════════════════

    def _build_semaines_tab(self) -> ft.Container:
        today       = datetime.date.today()
        monday_cur  = today - datetime.timedelta(days=today.weekday())
        monday_next = monday_cur + datetime.timedelta(weeks=1)

        week_cur  = _build_week_card(monday_cur,  "SEMAINE EN COURS",  self.app_state)
        week_next = _build_week_card(monday_next, "SEMAINE SUIVANTE",  self.app_state)

        return ft.Container(
            content=ft.Column([
                ft.Container(height=8),
                week_cur,
                ft.Container(height=10),
                week_next,
                ft.Container(height=14),
            ], spacing=0),
            margin=ft.margin.symmetric(horizontal=12, vertical=6),
        )

    # ══════════════════════════════════════════════════════════════════════════
    # HANDLERS
    # ══════════════════════════════════════════════════════════════════════════

    def _on_poids_change(self, e):
        self.state["poids"] = e.control.value
        self.state["dirty"] = True
        self.app_state["adjustment"] = self.state["adjustment"]
        # Feedback visuel : bordure rouge si valeur non numérique
        v = utils.parse_num(e.control.value, float, None, min_val=30, max_val=400)
        if self._poids_field:
            self._poids_field.border_color = (
                SUCCESS if v is not None else
                (DANGER if e.control.value.strip() else None)
            )
        self._update_macros()

    def _on_adj_change(self, e):
        self.state["adjustment"] = e.control.value
        self.app_state["adjustment"] = e.control.value
        self.state["dirty"] = True
        self._update_macros()

    def _update_macros(self):
        """Recalcule et met à jour les labels macros + TDEE + jauge IMC."""
        nut = _calculs(self.state["poids"], {**self.app_state, **self.state})
        if self._cal_text is None:
            return
        if nut:
            self._cal_text.value  = f"{nut['cal']:.0f} kcal"
            self._prot_text.value = f"{nut['proteines']:.0f} g"
            self._gluc_text.value = f"{nut['glucides']:.0f} g"
            self._lip_text.value  = f"{nut['lipides']:.0f} g"
            self._tdee_text.value = (
                f"TDEE {nut['tdee']:.0f} kcal  |  ajust. {nut['adj']*100:+.0f}%"
            )
        else:
            for txt in [self._cal_text, self._prot_text, self._gluc_text, self._lip_text]:
                txt.value = "—"
            if self._tdee_text:
                self._tdee_text.value = ""

        # Mise à jour jauge IMC en direct
        if self._imc_container is not None:
            try:
                ui = self.app_state.get("user_info") or {}
                poids_val = float(self.state["poids"].replace(",", "."))
                taille_val = float(ui.get("taille", 0))
                if poids_val > 0 and taille_val > 0:
                    imc_val, _ = utils.calculer_imc(poids_val, taille_val)
                else:
                    imc_val = None
                self._imc_container.content = _build_imc_gauge(imc_val, poids_val, taille_val)
            except Exception:
                pass

        self._safe_update()

    def _on_save_nutrition(self, e=None):
        """Sauvegarde l'entrée nutrition du jour — port de _save_nutrition ERAGROK."""
        if not self.app_state.get("current_user"):
            self._snack("Aucun profil sélectionné.", DANGER)
            return
        poids = self.state["poids"].strip().replace(",", ".")
        ui    = self.app_state.get("user_info") or {}
        adj   = utils.ADJUSTMENTS.get(self.state["adjustment"], 0.0)
        dn    = ui.get("date_naissance", "")
        age   = str(utils.age_depuis_naissance(dn) or ui.get("age") or "")
        nut   = _calculs(poids, {**self.app_state, **self.state})
        if nut:
            c, p, g, l = (int(round(nut["cal"])), nut["proteines"],
                          nut["glucides"], nut["lipides"])
        else:
            c = p = g = l = 0
        today_s = datetime.date.today().strftime(DATE_FMT)
        try:
            _db.nutrition_insert(self._fake_app(), today_s, poids, age,
                                 str(c), f"{p:.0f}", f"{g:.0f}", f"{l:.0f}", "")
            self.state["dirty"] = False
            self._snack(f"✔  Nutrition sauvegardée pour {today_s}.", SUCCESS)
            self._refresh_hist()
        except Exception as ex:
            self._snack(f"Erreur : {ex}", DANGER)

    def _on_export_pdf(self, e=None):
        """Export PDF bilan nutrition complet."""
        try:
            from data.pdf_utils import export_nutrition_full_pdf
            export_nutrition_full_pdf(self.app_state, page=self.page)
        except Exception as ex:
            self._snack(f"Erreur export PDF : {ex}", DANGER)

    def _push_screen(self, screen: ft.Control):
        """Remplace le contenu de root_col par screen + bouton Retour."""
        def _back(e=None):
            self._build_all()
            self.page.update()

        back_btn = ft.TextButton(
            "← Retour Nutrition",
            on_click=_back,
            style=ft.ButtonStyle(color=ACCENT),
        )
        self.root_col.controls.clear()
        self.root_col.controls.append(
            ft.Container(content=back_btn,
                         bgcolor=BG_CARD,
                         padding=ft.padding.symmetric(horizontal=16, vertical=8))
        )
        self.root_col.controls.append(screen)
        self.page.update()

    def _on_open_meal_generator(self, e=None):
        """Ouvre le générateur de plan alimentaire."""
        def _back_to_nutrition():
            self._build_all()
            self._refresh_plan_display()
            self.page.update()
        try:
            from data.meal_generator import build_meal_generator_screen
            screen = build_meal_generator_screen(self.page, self.app_state,
                                                  on_show_nutrition=_back_to_nutrition)
            self._push_screen(screen)
        except Exception as ex:
            self._snack(f"Erreur ouverture générateur : {ex}", DANGER)

    def _on_open_meal_calc(self, e=None):
        """Calculateur de repas — ouvre meal_generator en mode simple."""
        try:
            from data.meal_generator import build_meal_generator_screen
            screen = build_meal_generator_screen(self.page, self.app_state)
            self._push_screen(screen)
        except Exception as ex:
            self._snack(f"Erreur ouverture calculateur : {ex}", DANGER)

    def _on_shopping_maj_prix(self, e=None):
        """MAJ prix — délègue à l'instance ShoppingView courante."""
        sv = getattr(self, "_shopping_view", None)
        if sv is not None:
            sv._on_refresh_prices(e)
        else:
            self._snack("Ouvre d'abord la liste de courses.", WARNING)

    def _on_shopping_list(self, e=None):
        """Liste de courses — ouvre shopping depuis le dernier plan."""
        try:
            from data.shopping import build_shopping_screen
            last = _db.meal_plan_get_last(self._fake_app(), accepted_only=False)
            plan = last.get("plan_json", []) if last else []
            screen = build_shopping_screen(self.page, self.app_state, plan)
            self._push_screen(screen)
        except Exception as ex:
            self._snack(f"Erreur ouverture courses : {ex}", DANGER)

    def _on_accept_plan(self, e=None):
        """Accepte le plan alimentaire en attente."""
        try:
            fake = self._fake_app()
            db_plan = _db.meal_plan_get_last(fake, accepted_only=False)
            if db_plan and not db_plan.get("accepted"):
                _db.meal_plan_accept(fake, db_plan["id"])
                self._snack("✔  Plan accepté.", SUCCESS)
                self._refresh_plan_display()
            else:
                self._snack("Aucun plan en attente.", WARNING)
        except Exception as ex:
            self._snack(f"Erreur : {ex}", DANGER)

    # ── Historique ─────────────────────────────────────────────────────────────

    def _on_hist_row_click(self, row: dict):
        self.state["_sel_row_id"]  = row.get("id")
        self.state["_sel_row_data"] = row
        self._refresh_hist()

    def _on_hist_sort(self, col: str):
        cur_col, cur_asc = self.state["hist_sort"]
        if cur_col == col:
            self.state["hist_sort"] = (col, not cur_asc)
        else:
            self.state["hist_sort"] = (col, True)
        self._refresh_hist()

    def _on_hist_edit(self, e=None):
        """
        Modal d'édition d'une entrée historique — port de _edit_selected ERAGROK.
        """
        row = self.state.get("_sel_row_data")
        if not row:
            self._snack("Sélectionne d'abord une ligne.", WARNING)
            return

        f_date = ft.TextField(label="Date", value=str(row.get("date","")),
                              bgcolor=BG_INPUT, border_color=BORDER, color=TEXT,
                              focused_border_color=ACCENT, border_radius=R_INPUT)
        f_poids = ft.TextField(label="Poids (kg)", value=str(row.get("poids","")),
                               bgcolor=BG_INPUT, border_color=BORDER, color=TEXT,
                               focused_border_color=ACCENT, border_radius=R_INPUT,
                               width=140)
        f_cal  = ft.TextField(label="Calories", value=str(row.get("calories","")),
                              bgcolor=BG_INPUT, border_color=BORDER, color=TEXT,
                              focused_border_color=ACCENT, border_radius=R_INPUT,
                              width=140)
        f_note = ft.TextField(label="Note", value=str(row.get("note","")),
                              bgcolor=BG_INPUT, border_color=BORDER, color=TEXT,
                              focused_border_color=ACCENT, border_radius=R_INPUT,
                              multiline=True, min_lines=2)

        def _do_save(ev):
            try:
                _db.nutrition_update(
                    self._fake_app(),
                    row.get("id"),
                    f_date.value, f_poids.value,
                    str(row.get("age", "")),
                    f_cal.value,
                    str(row.get("proteines", "")),
                    str(row.get("glucides", "")),
                    str(row.get("lipides", "")),
                    f_note.value,
                )
                dlg.open = False
                self._safe_update()
                self._snack("✔  Entrée mise à jour.", SUCCESS)
                self._refresh_hist()
            except Exception as ex:
                self._snack(f"Erreur : {ex}", DANGER)

        def _do_cancel(ev):
            dlg.open = False
            self._safe_update()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("MODIFIER L'ENTRÉE", size=14, color=TEXT_ACCENT,
                          weight=ft.FontWeight.BOLD),
            content=ft.Column([f_date, ft.Row([f_poids, f_cal], spacing=10), f_note],
                              spacing=10, width=400),
            actions=[
                mk_btn("✔  Enregistrer", _do_save, color=SUCCESS, hover=SUCCESS_HVR, width=160),
                mk_btn("Annuler", _do_cancel, color=GRAY, hover=GRAY_HVR, width=110),
            ],
            bgcolor=BG_CARD,
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()

    def _on_hist_delete(self, e=None):
        """Supprimer l'entrée sélectionnée — port de _delete_selected ERAGROK."""
        row = self.state.get("_sel_row_data")
        if not row:
            self._snack("Sélectionne d'abord une ligne.", WARNING)
            return

        def _confirm(ev):
            try:
                row_id = row.get("id")
                if row_id:
                    _db.nutrition_delete_by_id(self._fake_app(), int(row_id))
                else:
                    _db.nutrition_delete_by_date(self._fake_app(), row.get("date", ""))
                self.state["_sel_row_id"]   = None
                self.state["_sel_row_data"] = None
                conf_dlg.open = False
                self._safe_update()
                self._snack("✔  Entrée supprimée.", SUCCESS)
                self._refresh_hist()
            except Exception as ex:
                self._snack(f"Erreur : {ex}", DANGER)

        def _cancel(ev):
            conf_dlg.open = False
            self._safe_update()

        conf_dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirmer la suppression", color=DANGER,
                          weight=ft.FontWeight.BOLD),
            content=ft.Text(f"Supprimer l'entrée du {row.get('date','?')} ?",
                            color=TEXT),
            actions=[
                mk_btn("🗑 Supprimer", _confirm, color=DANGER, hover=DANGER_HVR, width=130),
                mk_btn("Annuler", _cancel, color=GRAY, hover=GRAY_HVR, width=110),
            ],
            bgcolor=BG_CARD,
        )
        self.page.overlay.append(conf_dlg)
        conf_dlg.open = True
        self.page.update()

    def _on_hist_delete_all(self, e=None):
        """Supprimer tout l'historique — port de _delete_all ERAGROK."""
        def _confirm(ev):
            try:
                _db.nutrition_delete_all(self._fake_app())
                self.state["_sel_row_id"]   = None
                self.state["_sel_row_data"] = None
                conf_dlg.open = False
                self._safe_update()
                self._snack("✅  Tout l'historique a été supprimé.", SUCCESS)
                self._refresh_hist()
            except Exception as ex:
                self._snack(f"Erreur : {ex}", DANGER)

        def _cancel(ev):
            conf_dlg.open = False
            self._safe_update()

        conf_dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Supprimer TOUT l'historique ?", color=DANGER,
                          weight=ft.FontWeight.BOLD),
            content=ft.Text("Cette action est irréversible.", color=TEXT),
            actions=[
                mk_btn("🗑 Tout supprimer", _confirm, color="#5a0000", hover="#7a0000", width=160),
                mk_btn("Annuler", _cancel, color=GRAY, hover=GRAY_HVR, width=110),
            ],
            bgcolor=BG_CARD,
        )
        self.page.overlay.append(conf_dlg)
        conf_dlg.open = True
        self.page.update()

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _fake_app(self) -> _FakeApp:
        return _FakeApp(self.app_state.get("current_user", ""))

    def _default_poids(self) -> str:
        # 1. Dernier poids saisi en nutrition
        try:
            from data import db
            rows = db.nutrition_get_last_n(self.app_state, 1)
            if rows:
                p = rows[0]["poids"] if isinstance(rows[0], dict) else rows[0][2]
                if p and str(p).strip():
                    return str(p).strip()
        except Exception:
            pass
        # 2. Fallback : poids du profil
        try:
            ui = self.app_state.get("user_info") or {}
            p  = ui.get("poids")
            if p is not None:
                return str(int(float(p))) if float(p).is_integer() else str(p)
        except Exception:
            pass
        return ""

    def _snack(self, msg: str, color: str = SUCCESS):
        from ui.snackbar import snack, _LEVEL_COLORS
        _col_to_level = {v: k for k, v in _LEVEL_COLORS.items()}
        level = _col_to_level.get(color, "success")
        snack(self.page, msg, level)


    # ══════════════════════════════════════════════════════════════════════════
    #  CATALOGUE ALIMENTS
    # ══════════════════════════════════════════════════════════════════════════

    def _build_food_catalogue_tab(self) -> ft.Container:
        """Catalogue aliments — base + custom, style identique au catalogue cycle."""
        self._food_cat_col = ft.Column(spacing=4)

        # ── Fiche aliment ─────────────────────────────────────────────────────
        self._food_detail_name   = ft.Text("Sélectionne un aliment", size=13,
                                            color=TEXT_ACCENT, weight=ft.FontWeight.BOLD)
        self._food_detail_kcal   = ft.Text("", size=12, color=ACCENT)
        self._food_detail_macros = ft.Text("", size=12, color=TEXT)
        self._food_detail_notes  = ft.Text("", size=11, color=TEXT_MUTED, italic=True)

        detail_box = ft.Container(
            content=ft.Column([
                mk_title("  🔎  FICHE ALIMENT"),
                mk_sep(),
                ft.Container(
                    content=ft.Column([
                        self._food_detail_name,
                        self._food_detail_kcal,
                        self._food_detail_macros,
                        self._food_detail_notes,
                    ], spacing=4),
                    padding=ft.Padding.all(10),
                ),
            ]),
            bgcolor=BG_CARD2, border_radius=10,
            margin=ft.Margin.symmetric(horizontal=12),
            padding=ft.Padding.symmetric(vertical=8),
        )

        self._food_selected_ref  = {"container": None}
        self._food_selected_nom  = None

        # ── Champ recherche ───────────────────────────────────────────────────
        def _on_search(e):
            self._rebuild_food_catalogue(q=e.control.value.lower().strip())

        search_field = mk_entry(
            label="🔍 Rechercher un aliment", hint="nom...", width=280,
            on_change=_on_search,
        )

        self._rebuild_food_catalogue()

        # ── Boutons CRUD ──────────────────────────────────────────────────────
        btn_add = mk_btn("➕ Nouveau", self._on_food_add,
                         color=SUCCESS, hover=SUCCESS_HVR, width=140, height=38)
        btn_edit = mk_btn("✏ Modifier", self._on_food_edit,
                          color=ACCENT, hover=ACCENT_HOVER, width=130, height=38)
        btn_del  = mk_btn("🗑 Supprimer", self._on_food_delete,
                          color=DANGER, hover=DANGER_HVR, width=130, height=38)

        return ft.Container(
            content=ft.Column([
                ft.Container(content=search_field,
                             padding=ft.Padding.symmetric(horizontal=12, vertical=8)),
                ft.Container(content=self._food_cat_col,
                             padding=ft.Padding.symmetric(horizontal=12)),
                detail_box,
                ft.Container(
                    content=ft.Row([btn_add, btn_edit, btn_del], spacing=8, wrap=True),
                    padding=ft.Padding.symmetric(horizontal=12, vertical=10),
                ),
            ], spacing=0),
            bgcolor=BG_CARD, border_radius=R_CARD,
            border=ft.Border.all(1, BORDER),
            margin=ft.Margin.symmetric(horizontal=12, vertical=6),
        )

    def _rebuild_food_catalogue(self, q: str = ""):
        """Reconstruit la liste aliments filtrée par q."""
        if self._food_cat_col is None:
            return
        self._food_cat_col.controls.clear()

        # Charger les custom depuis la DB
        custom_list = _db.custom_food_get_all(self.app_state)
        custom_map  = {p["nom"]: p for p in custom_list}

        for cat_name, cat_info in _fc.FOOD_CATEGORIES.items():
            color = cat_info["color"]
            icon  = cat_info["icon"]
            base  = _fc.FOOD_BASE.get(cat_name, [])
            extra = [p for p in custom_list if p.get("categorie") == cat_name]
            items_base  = [f["nom"] for f in base  if not q or q in f["nom"].lower()]
            items_extra = [p["nom"] for p in extra if not q or q in p["nom"].lower()]
            items = items_base + items_extra
            if not items:
                continue

            _state    = {"open": bool(q)}
            _icon_ref = ft.Ref[ft.Text]()
            _body_ref = ft.Ref[ft.Column]()

            def _make_toggle(s, ir, br):
                def _t(e=None):
                    s["open"] = not s["open"]
                    ir.current.value   = "▼" if s["open"] else "▶"
                    br.current.visible = s["open"]
                    try: e.page.update()
                    except Exception: pass
                return _t

            def _make_item(nom, is_custom=False):
                ref = ft.Ref[ft.Container]()
                def _click(e, n=nom, r=ref):
                    prev = self._food_selected_ref["container"]
                    if prev and prev.current:
                        prev.current.bgcolor = "transparent"
                    if r.current:
                        r.current.bgcolor = ACCENT_DIM
                    self._food_selected_ref["container"] = r
                    self._food_selected_nom = n
                    self._show_food_detail(n)
                return ft.Container(
                    content=ft.Row([
                        ft.Text(f"  {nom}", size=12, color=TEXT, expand=True),
                        ft.Text("✦", size=9, color=ACCENT, tooltip="Personnalisé") if is_custom else ft.Container(width=0),
                    ]),
                    padding=ft.Padding.symmetric(horizontal=8, vertical=6),
                    border_radius=6, ink=True, bgcolor="transparent",
                    ref=ref, on_click=_click,
                )

            body_items = [_make_item(n) for n in items_base] + \
                         [_make_item(n, True) for n in items_extra]
            body_col = ft.Column(body_items, spacing=0,
                                 ref=_body_ref, visible=_state["open"])
            header = ft.Container(
                content=ft.Row([
                    ft.Text("▼" if _state["open"] else "▶", size=11, color=color,
                            weight=ft.FontWeight.BOLD, ref=_icon_ref),
                    ft.Text(f" {icon} {cat_name}", size=11, color=color,
                            weight=ft.FontWeight.BOLD, expand=True),
                    ft.Text(str(len(items)), size=10, color=TEXT_MUTED),
                ], spacing=4),
                bgcolor=BG_CARD2, border_radius=6,
                padding=ft.Padding.symmetric(horizontal=10, vertical=6),
                ink=True, on_click=_make_toggle(_state, _icon_ref, _body_ref),
            )
            self._food_cat_col.controls.extend([header, body_col])

        self._safe_update()

    def _show_food_detail(self, nom: str):
        """Affiche la fiche d'un aliment dans le panel de détail."""
        # Cherche d'abord dans la base
        info = {}
        for items in _fc.FOOD_BASE.values():
            for f in items:
                if f["nom"] == nom:
                    info = f; break

        # Sinon dans les custom DB
        if not info:
            row = _db.custom_food_get_one(self.app_state, nom)
            if row:
                info = {"nom": nom, "kcal": row["kcal"],
                        "prot": row["proteines"], "gluc": row["glucides"],
                        "lip": row["lipides"], "fibres": row["fibres"],
                        "notes": row.get("notes", "")}

        if not info:
            return

        is_custom = _db.custom_food_get_one(self.app_state, nom) is not None
        badge = "  ✦ Personnalisé" if is_custom else ""
        self._food_detail_name.value   = f"{nom}{badge}"
        self._food_detail_kcal.value   = f"⚡ {info.get('kcal', 0):.0f} kcal / 100g"
        self._food_detail_macros.value = (
            f"🥩 Prot : {info.get('prot',0):.1f}g  |  "
            f"🍚 Gluc : {info.get('gluc',0):.1f}g  |  "
            f"🫒 Lip : {info.get('lip',0):.1f}g  |  "
            f"🌾 Fibres : {info.get('fibres',0):.1f}g"
        )
        self._food_detail_notes.value = info.get("notes", "")
        self._safe_update()

    # ── CRUD aliments ─────────────────────────────────────────────────────────

    def _on_food_add(self, e=None):
        self._open_food_modal(None)

    def _on_food_scan(self, e=None):
        """Scanne un code-barres → lookup OFF → pré-remplit le modal aliment."""
        from data.barcode_scanner import scan_and_lookup

        def _on_result(food: dict | None):
            if food:
                # Pré-remplir le modal avec les données OFF
                self._open_food_modal(food)
            # Si None : annulé ou introuvable, rien à faire

        scan_and_lookup(self.page, self.app_state, _on_result)

    def _on_food_edit(self, e=None):
        nom = self._food_selected_nom
        if not nom:
            self._snack("Sélectionne d'abord un aliment.", WARNING); return
        # Base non modifiable directement → copie custom
        row = _db.custom_food_get_one(self.app_state, nom)
        if row is None:
            # Préremplir depuis la base
            info = {}
            for items in _fc.FOOD_BASE.values():
                for f in items:
                    if f["nom"] == nom:
                        info = f; break
            if info:
                # Trouver la catégorie
                cat = next((c for c, items in _fc.FOOD_BASE.items()
                            if any(f["nom"] == nom for f in items)), "Divers")
                row = {"nom": nom, "categorie": cat,
                       "kcal": info.get("kcal", 0), "proteines": info.get("prot", 0),
                       "glucides": info.get("gluc", 0), "lipides": info.get("lip", 0),
                       "fibres": info.get("fibres", 0), "unite": "g",
                       "portion_ref": 100, "notes": ""}
        self._open_food_modal(row)

    def _on_food_delete(self, e=None):
        nom = self._food_selected_nom
        if not nom:
            self._snack("Sélectionne d'abord un aliment.", WARNING); return
        if _db.custom_food_get_one(self.app_state, nom) is None:
            self._snack("Les aliments de base ne peuvent pas être supprimés.", WARNING); return
        _db.custom_food_delete(self.app_state, nom)
        self._food_selected_nom = None
        if self._food_detail_name:
            self._food_detail_name.value   = "Sélectionne un aliment"
            self._food_detail_kcal.value   = ""
            self._food_detail_macros.value = ""
            self._food_detail_notes.value  = ""
        self._rebuild_food_catalogue()
        self._snack("✔ Aliment supprimé.", SUCCESS)

    def _open_food_modal(self, food: dict | None):
        """AlertDialog — ajouter/modifier un aliment avec tous ses champs nutritionnels."""
        is_edit = food is not None

        def _mk_field(label, value="", width=160, **kw):
            return ft.TextField(
                label=label, value=str(value) if value else "",
                bgcolor=BG_INPUT, border_color=BORDER,
                focused_border_color=ACCENT, color=TEXT,
                label_style=ft.TextStyle(color=TEXT_SUB, size=11),
                border_radius=8, text_size=13, width=width, **kw)

        f_barcode = _mk_field("Code-barres EAN (optionnel)",
                               food.get("notes", "").replace("Code-barres : ", "") if food and food.get("notes", "").startswith("Code-barres") else "",
                               width=300, keyboard_type=ft.KeyboardType.NUMBER)
        f_barcode_status = ft.Text("", size=11, color=TEXT_MUTED, italic=True)

        def _on_barcode_submit(e=None):
            code = (f_barcode.value or "").strip()
            if not code:
                return
            f_barcode_status.value = "🔍 Recherche sur Open Food Facts..."
            try: self.page.update()
            except Exception: pass
            import threading
            def _lookup():
                from data.barcode_scanner import lookup_barcode
                food_data = lookup_barcode(code)
                if food_data:
                    f_nom.value     = food_data.get("nom", f_nom.value)
                    f_kcal.value    = str(food_data.get("kcal", ""))
                    f_prot.value    = str(food_data.get("proteines", ""))
                    f_gluc.value    = str(food_data.get("glucides", ""))
                    f_lip.value     = str(food_data.get("lipides", ""))
                    f_fibres.value  = str(food_data.get("fibres", ""))
                    f_cat.value     = food_data.get("categorie", f_cat.value)
                    f_notes.value   = f"Code-barres : {code}"
                    f_barcode_status.value = f"✔ Produit trouvé : {food_data.get('nom', '')}"
                else:
                    f_barcode_status.value = "⚠ Produit introuvable — remplis les champs manuellement."
                try: self.page.update()
                except Exception: pass
            threading.Thread(target=_lookup, daemon=True).start()

        f_barcode.on_submit = _on_barcode_submit

        f_nom     = _mk_field("Nom *",            food["nom"]                  if food else "", width=300)
        f_kcal    = _mk_field("Kcal / 100g *",    food.get("kcal", "")         if food else "")
        f_prot    = _mk_field("Protéines (g)",     food.get("proteines", "")    if food else "")
        f_gluc    = _mk_field("Glucides (g)",      food.get("glucides", "")     if food else "")
        f_lip     = _mk_field("Lipides (g)",       food.get("lipides", "")      if food else "")
        f_fibres  = _mk_field("Fibres (g)",        food.get("fibres", "")       if food else "")
        f_portion = _mk_field("Portion réf (g/ml)",food.get("portion_ref", 100) if food else "100")
        f_notes   = _mk_field("Notes",             food.get("notes", "")        if food else "",
                               width=300, multiline=True, min_lines=2, max_lines=3)

        cat_options = [ft.dropdown.Option(c) for c in _fc.FOOD_CATEGORIES]
        f_cat = ft.Dropdown(
            label="Catégorie *",
            value=food.get("categorie", "Divers") if food else "Divers",
            options=cat_options,
            bgcolor=BG_INPUT, border_color=BORDER,
            focused_border_color=ACCENT, color=TEXT,
            label_style=ft.TextStyle(color=TEXT_SUB, size=11),
            border_radius=8, text_size=13, width=200,
        )
        unite_opts = [ft.dropdown.Option(u) for u in ["g", "ml", "unité"]]
        f_unite = ft.Dropdown(
            label="Unité",
            value=food.get("unite", "g") if food else "g",
            options=unite_opts,
            bgcolor=BG_INPUT, border_color=BORDER,
            focused_border_color=ACCENT, color=TEXT,
            label_style=ft.TextStyle(color=TEXT_SUB, size=11),
            border_radius=8, text_size=13, width=120,
        )

        dlg = ft.AlertDialog(modal=True)

        def _close(ev=None):
            dlg.open = False
            self.page.update()

        def _parse_float(s):
            try: return float(str(s).replace(",", "."))
            except: return 0.0

        def _save(ev=None):
            nom = f_nom.value.strip()
            if not nom:
                self._snack("Le nom est obligatoire.", DANGER); return
            old_nom = food["nom"] if food else None
            if old_nom and old_nom != nom:
                _db.custom_food_delete(self.app_state, old_nom)
            ok = _db.custom_food_upsert(
                self.app_state,
                nom         = nom,
                categorie   = f_cat.value or "Divers",
                kcal        = _parse_float(f_kcal.value),
                proteines   = _parse_float(f_prot.value),
                glucides    = _parse_float(f_gluc.value),
                lipides     = _parse_float(f_lip.value),
                fibres      = _parse_float(f_fibres.value),
                unite       = f_unite.value or "g",
                portion_ref = _parse_float(f_portion.value) or 100,
                notes       = f_notes.value.strip(),
            )
            if ok:
                self._food_selected_nom = nom
                _close()
                self._rebuild_food_catalogue()
                self._snack(f"✔ Aliment « {nom} » sauvegardé.", SUCCESS)
            else:
                self._snack("Erreur lors de la sauvegarde.", DANGER)

        dlg.title = ft.Text(
            "✏ Modifier l'aliment" if is_edit else "➕ Nouvel aliment",
            color=ACCENT, weight=ft.FontWeight.BOLD, size=15,
        )
        dlg.actions = []
        dlg.actions_alignment = ft.MainAxisAlignment.END
        dlg.content = ft.Container(
            content=ft.Column([
                ft.Row([ft.Text("Code-barres", size=11, color=TEXT_MUTED)]),
                f_barcode,
                f_barcode_status,
                mk_sep(),
                f_nom,
                ft.Row([f_cat, f_unite, f_portion], spacing=8, wrap=True),
                mk_sep(),
                ft.Text("Valeurs nutritionnelles pour 100g / 100ml",
                        size=11, color=TEXT_MUTED, italic=True),
                ft.Row([f_kcal, f_prot, f_gluc], spacing=8, wrap=True),
                ft.Row([f_lip, f_fibres], spacing=8, wrap=True),
                mk_sep(),
                f_notes,
                mk_sep(),
                ft.Row([
                    ft.ElevatedButton(
                        content=ft.Text("✕ Annuler", size=13, color=TEXT,
                                        weight=ft.FontWeight.BOLD),
                        bgcolor=GRAY, on_click=_close, width=130, height=42),
                    ft.ElevatedButton(
                        content=ft.Text("💾 Sauvegarder", size=13, color=TEXT,
                                        weight=ft.FontWeight.BOLD),
                        bgcolor=SUCCESS, on_click=_save, width=170, height=42),
                ], spacing=10, alignment=ft.MainAxisAlignment.START),
            ], spacing=10, tight=True, scroll=ft.ScrollMode.AUTO),
            width=380, padding=ft.padding.only(top=8),
        )
        dlg.bgcolor = BG_CARD
        dlg.shape   = ft.RoundedRectangleBorder(radius=16)
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()

    def _safe_update(self):
        from ui.page_utils import safe_update
        safe_update(self.page)


# ══════════════════════════════════════════════════════════════════════════════
#  POINT D'ENTRÉE PUBLIC
# ══════════════════════════════════════════════════════════════════════════════

def build_nutrition_screen(page: ft.Page, app_state: dict) -> ft.Column:
    """Point d'entrée principal — appelé depuis main.py.
    La view est mise en cache dans app_state pour survivre aux navigations.
    """
    view = app_state.get("_nutrition_view")
    if view is None or view.page is not page:
        view = NutritionView(page, app_state)
        app_state["_nutrition_view"] = view
        # Ouvrir sur Plan si un plan existe, sinon Calculs
        from data import db as _db
        class _FA:
            def __init__(self, u): self.current_user = u
        has_plan = bool(_db.meal_plan_get_last(_FA(app_state.get("current_user","")), accepted_only=False))
        # _build_all déjà appelé dans __init__, pas besoin d'ouvrir un onglet spécifique
    else:
        # Revenir sur Nutrition : recharger le plan depuis DB
        view._refresh_plan_display()
        view._safe_update()
    return view.get_view()
