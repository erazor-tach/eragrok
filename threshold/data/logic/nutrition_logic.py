# data/logic/nutrition_logic.py — THRESHOLD · Logique métier nutrition
# ─────────────────────────────────────────────────────────────────────────────
# Fonctions pures extraites de data/nutrition.py (proposition #9).
# Aucun import Flet — testables indépendamment de l'UI.
#
# Les modules UI (nutrition.py) réexportent ces fonctions via :
#   from data.logic.nutrition_logic import *
# → compatibilité totale, zéro changement dans le reste du code.
# ─────────────────────────────────────────────────────────────────────────────
from __future__ import annotations

import datetime
from functools import lru_cache
from typing import Optional

from data import utils

DATE_FMT = "%d/%m/%Y"

# Zones IMC — style Threshold
IMC_ZONES = [
    (16.0, 18.5, "#60a5fa", "Maigreur"),
    (18.5, 25.0, "#22c55e", "Optimal"),
    (25.0, 30.0, "#f97316", "Surpoids"),
    (30.0, 40.0, "#ef4444", "Obésité"),
]
IMC_MIN, IMC_MAX = 16.0, 40.0


def _d2s(d: datetime.date) -> str:
    """Formate une date en string JJ/MM/AAAA."""
    return d.strftime(DATE_FMT)


def _parse_date_flex(s) -> Optional[datetime.date]:
    """Parse une date depuis plusieurs formats possibles."""
    if not s:
        return None
    s = str(s).strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y"):
        try:
            return datetime.datetime.strptime(s, fmt).date()
        except Exception:
            pass
    return None


def _week_dates(monday: datetime.date, sunday: datetime.date) -> list:
    """Retourne la liste de toutes les dates entre monday et sunday inclus."""
    d, out = monday, []
    while d <= sunday:
        out.append(d)
        d += datetime.timedelta(days=1)
    return out

def _calculs(poids_str: str, app_state: dict) -> Optional[dict]:
    """
    Calcule TDEE + macros depuis le poids saisi et le profil utilisateur.
    Retourne dict {tdee, cal, adj, proteines, glucides, lipides} ou None.
    """
    try:
        poids = str(poids_str).strip().replace(",", ".")
        if not poids:
            return None
        ui        = app_state.get("user_info") or {}
        dn        = ui.get("date_naissance", "")
        age       = str(utils.age_depuis_naissance(dn) or ui.get("age") or "")
        if not age:
            return None
        adj_label = app_state.get("adjustment", "Maintien (0%)")
        adj       = utils.ADJUSTMENTS.get(adj_label, 0.0)
        nut       = utils.calculs_nutrition(
            poids, age, ui.get("sexe"), ui.get("objectif"), ui.get("taille")
        )
        if not nut:
            return None
        cal = nut["tdee"] * (1 + adj)
        obj = ui.get("objectif", "")
        if "masse" in obj.lower():    cp, fp = 0.47, 0.23
        elif "perte" in obj.lower():  cp, fp = 0.37, 0.23
        else:                          cp, fp = 0.45, 0.25
        return {
            "tdee":      nut["tdee"],
            "cal":       cal,
            "adj":       adj,
            "proteines": nut["proteines"],
            "glucides":  (cal * cp) / 4,
            "lipides":   (cal * fp) / 9,
        }
    except Exception:
        return None


@lru_cache(maxsize=128)
def _imc_zone(imc: float) -> tuple[str, str]:
    """Retourne (couleur hex, label) pour un IMC donné."""
    for lo, hi, col, lbl in IMC_ZONES:
        if lo <= imc < hi:
            return col, lbl
    return IMC_ZONES[-1][2], IMC_ZONES[-1][3]


@lru_cache(maxsize=128)
def _imc_diff_text(imc: float, poids: float, taille_cm: float) -> tuple[str, str]:
    """
    Calcule le différentiel de poids vers la zone normale.
    Retourne (texte, couleur hex).
    """
    try:
        tm   = float(taille_cm) / 100
        p_lo = round(18.5 * tm ** 2, 1)
        p_hi = round(25.0 * tm ** 2, 1)
        if poids < p_lo:
            return f"↑  +{p_lo - poids:.1f} kg pour atteindre IMC 18.5", "#60a5fa"
        elif poids > p_hi:
            return f"↓  −{poids - p_hi:.1f} kg pour atteindre IMC 25", "#f59e0b"
        else:
            return "✓  Dans la zone normale", "#22c55e"
    except Exception:
        return "", "#3c405a"


def _avg(rows: list, col: int) -> Optional[float]:
    """Moyenne d'une colonne numérique dans une liste de listes."""
    vals = []
    for r in rows:
        try:
            v = float(r[col]) if len(r) > col and str(r[col]).strip() else None
            if v:
                vals.append(v)
        except Exception:
            pass
    return sum(vals) / len(vals) if vals else None


def _sparkline(values: list, width: int = 20) -> str:
    """Génère un mini sparkline ASCII depuis une liste de valeurs flottantes."""
    BARS = "▁▂▃▄▅▆▇█"
    if not values:
        return ""
    mn, mx = min(values), max(values)
    rng = mx - mn or 1
    chars = [BARS[int((v - mn) / rng * (len(BARS) - 1))] for v in values[-width:]]
    return "".join(chars)
