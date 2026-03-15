# data/logic/cycle_logic.py — THRESHOLD · Logique métier cycle hormonal
# ─────────────────────────────────────────────────────────────────────────────
# Fonctions pures et constantes extraites de data/cycle.py (proposition #9).
# Aucun import Flet — testables indépendamment de l'UI.
#
# data/cycle.py réexporte tout via :
#   from data.logic.cycle_logic import *
# ─────────────────────────────────────────────────────────────────────────────
from __future__ import annotations

import datetime
import math
import re
from typing import Optional

DATE_FMT = "%d/%m/%Y"

# ── Constantes produits ───────────────────────────────────────────────────────

_PCT_STRICT    = {"Clomiphene (Clomid)", "Tamoxifen (Nolvadex)"}
_ORAL_PRODUCTS = {
    "Mesterolone (Proviron)", "Methandienone (Dianabol)", "Oxandrolone (Anavar)",
    "Oxymetholone (Anadrol)", "Stanozolol oral (Winstrol)", "Turinabol",
    "Halotestin", "Primobolan tablets",
}
_ESTER_WASHOUT = {
    "Testosterone Enanthate": 2,       "Testosterone Cypionate": 2,
    "Sustanon 250/300/350": 2,         "Testosterone Undecanoate (Nebido)": 5,
    "Boldenone Undecylenate (Equipoise)": 3,
    "Nandrolone Decanoate (Deca)": 3,  "Methenolone Enanthate (Primobolan)": 2,
    "Trenbolone Enanthate": 2,         "Trenbolone Acetate": 1,
    "Trenbolone Hexahydrobenzylcarbonate": 3,
    "Drostanolone Enanthate (Masteron E)": 2,
    "Drostanolone Propionate (Masteron P)": 1,
    "Cut Stack (mix Tren/Mast/Test)": 2,
}
# Protocoles PCT : liste de (semaine_debut, semaine_fin, clomid_str, nolvadex_str)
_PCT_NORMAL   = [
    (1, 2, "Clomid 50 mg/j",  "Nolvadex 20 mg/j"),
    (3, 4, "Clomid 25 mg/j",  "Nolvadex 10 mg/j"),
]
_PCT_AGRESSIF = [
    (1, 2, "Clomid 100 mg/j", "Nolvadex 40 mg/j"),
    (3, 4, "Clomid 50 mg/j",  "Nolvadex 20 mg/j"),
    (5, 6, "Clomid 25 mg/j",  "Nolvadex 10 mg/j"),
]

# ── Fonctions pures ───────────────────────────────────────────────────────────

def _parse_dose_range(dose_str: str) -> tuple[Optional[float], Optional[float]]:
    """Extrait (min, max) depuis une chaîne de dose comme '250–500 mg/sem'."""
    if not dose_str or dose_str.strip() in ("—", "", "-"):
        return (None, None)
    cleaned = re.sub(r'\d+[xX]/\S*', '', dose_str)
    nums = re.findall(r'\d+(?:[.,]\d+)?', cleaned.replace('–', '-').replace('—', '-'))
    vals = [float(n.replace(',', '.')) for n in nums]
    if not vals:
        return (None, None)
    return (vals[0], vals[-1])


def _recommended_dose(dose_min_str: str) -> str:
    """Retourne la dose recommandée (limite haute du range min) sous forme lisible."""
    _, hi = _parse_dose_range(dose_min_str)
    if hi is None:
        return "—"
    unit = ""
    m = re.search(r'[a-zA-ZéàüùôîêûæœÉ/]+.*', dose_min_str)
    if m:
        unit = " " + m.group(0).strip()
    if hi == int(hi):
        return f"{int(hi)}{unit}"
    return f"{hi}{unit}"


def _calc_vials(dose_str: str, conc_str: str, vol_str: str, weeks: int) -> str:
    """Calcule le nombre de flacons nécessaires pour un cycle."""
    try:
        dose = float(re.findall(r'\d+(?:[.,]\d+)?', dose_str)[0].replace(',', '.'))
        conc = float(re.findall(r'\d+(?:[.,]\d+)?', conc_str)[0].replace(',', '.'))
        vol  = float(re.findall(r'\d+(?:[.,]\d+)?', vol_str)[0].replace(',', '.'))
        if conc <= 0 or vol <= 0:
            return "—"
        mg_per_vial = conc * vol
        total_mg    = dose * weeks
        n_vials     = math.ceil(total_mg / mg_per_vial)
        return f"{n_vials} vial(s)  ({int(total_mg)} mg total / {int(mg_per_vial)} mg/vial)"
    except (IndexError, ValueError, ZeroDivisionError):
        return "—"


def _build_cycle_plan(state: dict, category_items: dict) -> list[dict]:
    """
    Construit le planning semaine par semaine (Cycle → Washout → PCT / Cruise).

    Args:
        state:          dict issu de CycleView.state
        category_items: CATEGORY_ITEMS de cycle.py (évite import circulaire)

    Returns:
        Liste de dicts avec clés : week_num, label, date_start, phase,
                                   produits, hcg, pct_info
    """
    n_weeks   = state.get("length", 12)
    end_opt   = state.get("end_mode", "PCT")
    pct_mode  = state.get("pct_mode", "Normal")
    start_str = state.get("start_date", "")
    doses     = state.get("product_doses", {})

    try:
        start_dt = datetime.datetime.strptime(start_str, DATE_FMT) if start_str else None
    except ValueError:
        start_dt = None

    main_products, hcg_products, pct_strict_d, ia_products = {}, {}, {}, {}
    ia_set = set(category_items.get(6, []))
    for prod, dose in doses.items():
        if prod in _PCT_STRICT:
            pct_strict_d[prod] = dose
        elif prod.strip().upper() == "HCG":
            hcg_products[prod] = dose
        elif prod in ia_set:
            ia_products[prod] = dose
        else:
            main_products[prod] = dose

    all_cycle   = {**main_products, **ia_products}
    max_washout = max((_ESTER_WASHOUT.get(p, 0) for p in main_products), default=2)
    if max_washout < 2:
        max_washout = 2

    def _date_str(offset: int) -> str:
        if start_dt is None:
            return ""
        return (start_dt + datetime.timedelta(weeks=offset)).strftime(DATE_FMT)

    def _fmt(d: dict) -> str:
        return "  |  ".join(f"{n}: {v}" if v else n for n, v in d.items())

    plan, abs_w = [], 0

    for w in range(1, n_weeks + 1):
        abs_w += 1
        hcg_str = (
            _fmt(hcg_products) if w >= 3 and hcg_products
            else ("⏳ démarrage S3" if hcg_products else "")
        )
        plan.append({
            "week_num": abs_w, "label": f"Semaine {w}",
            "date_start": _date_str(w - 1), "phase": "CYCLE",
            "produits": _fmt(all_cycle), "hcg": hcg_str, "pct_info": "",
        })

    if end_opt == "PCT":
        for w in range(1, max_washout + 1):
            abs_w += 1
            plan.append({
                "week_num": abs_w, "label": f"Wash-out S{w}",
                "date_start": _date_str(n_weeks + w - 1), "phase": "WASHOUT",
                "produits": "— Arrêt de tous les produits du cycle —",
                "hcg": "", "pct_info": f"Clomid + Nolvadex démarrent à J{max_washout * 7}",
            })
        protocol = _PCT_AGRESSIF if pct_mode == "Agressif" else _PCT_NORMAL
        n_pct_weeks = protocol[-1][1]
        for pct_w in range(1, n_pct_weeks + 1):
            abs_w += 1
            cl = nv = ""
            for (s, e, c, n) in protocol:
                if s <= pct_w <= e:
                    cl, nv = c, n
                    break
            lines = []
            if "Clomiphene (Clomid)" in pct_strict_d and cl:
                lines.append(cl)
            if "Tamoxifen (Nolvadex)" in pct_strict_d and nv:
                lines.append(nv)
            plan.append({
                "week_num": abs_w, "label": f"PCT S{pct_w}",
                "date_start": _date_str(n_weeks + max_washout + pct_w - 1),
                "phase": "PCT", "produits": "",
                "hcg": "", "pct_info": "  +  ".join(lines) if lines else "— (aucun PCT sélectionné)",
            })

    elif end_opt in ("Cruise", "TRT"):
        maint = state.get("maintenance_dose", "")
        prod_label = (
            f"Testostérone — {maint} mg/sem (maintien {end_opt})" if maint
            else f"Protocole {end_opt} — dose de maintien (à renseigner)"
        )
        for w in range(1, 5):
            abs_w += 1
            plan.append({
                "week_num": abs_w, "label": f"{end_opt} S{w}",
                "date_start": _date_str(n_weeks + w - 1),
                "phase": end_opt.upper(), "produits": prod_label,
                "hcg": "", "pct_info": "",
            })

    return plan


# ── Couleur de dose selon plage ───────────────────────────────────────────────

def _dose_color(entered_str: str, dose_min_str: str, dose_max_str: str) -> str:
    """Retourne une couleur hex selon si la dose entrée est dans la plage conseillée.

    - Vert  (#22c55e) : dans la plage min→max
    - Orange (#f59e0b) : légèrement au-dessus du max (≤ 1.5×)
    - Rouge  (#ef4444) : très au-dessus (> 1.5×) ou invalide
    - Gris   (#818aaa) : non renseigné
    """
    if not entered_str or entered_str.strip() in ("", "—"):
        return "#818aaa"

    lo, hi     = _parse_dose_range(entered_str)
    _, hi_min  = _parse_dose_range(dose_min_str)
    _, hi_max  = _parse_dose_range(dose_max_str)

    if lo is None:
        return "#818aaa"

    val = lo  # on compare la valeur basse saisie

    if hi_max and val <= hi_max:
        return "#22c55e"   # dans la plage
    if hi_max and val <= hi_max * 1.5:
        return "#f59e0b"   # légèrement au-dessus
    return "#ef4444"        # trop élevé
