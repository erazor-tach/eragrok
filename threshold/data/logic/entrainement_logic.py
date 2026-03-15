# data/logic/entrainement_logic.py — THRESHOLD · Logique métier entraînement
# ─────────────────────────────────────────────────────────────────────────────
# Fonctions pures extraites de data/entrainement.py (proposition #9).
# Aucun import Flet — testables indépendamment de l'UI.
#
# data/entrainement.py réexporte tout via :
#   from data.logic.entrainement_logic import *
# ─────────────────────────────────────────────────────────────────────────────
from __future__ import annotations

import calendar
import datetime
import random

from data import training_techniques as tt

DATE_FMT = "%d/%m/%Y"
DAY_FR   = {0: "Lun", 1: "Mar", 2: "Mer", 3: "Jeu", 4: "Ven", 5: "Sam", 6: "Dim"}


def _parse_date(s: str) -> str:
    """Parse une date depuis plusieurs formats et retourne JJ/MM/AAAA."""
    for fmt in [DATE_FMT, "%Y-%m-%d", "%m/%d/%Y"]:
        try:
            return datetime.datetime.strptime(str(s).strip(), fmt).strftime(DATE_FMT)
        except Exception:
            pass
    return s or ""


def _fmt_tech(t: dict) -> str:
    """Formate une technique en string affichable."""
    return f"{t['nom']} [{t.get('reps', '—')}] | {t.get('charge', '—')} ({t['id']})"


def _pool(cats: list) -> list:
    """Retourne le pool de techniques disponibles pour les catégories données."""
    # Mapping noms UI français → codes internes
    _MAP = {
        "PECS":         "PECS",
        "DOS":          "DOS",
        "ÉPAULES":      "EPAULES",
        "EPAULES":      "EPAULES",
        "BRAS":         ["BICEPS", "TRICEPS"],
        "BICEPS":       "BICEPS",
        "TRICEPS":      "TRICEPS",
        "ABDOMINAUX":   "ABDOS",
        "ABDOS":        "ABDOS",
        "FESSIERS":     "FESSIERS",
        "CUISSES":      ["QUADRICEPS", "ISCHIO"],
        "QUADRICEPS":   "QUADRICEPS",
        "ISCHIO":       "ISCHIO",
        "MOLLETS":      "MOLLETS",
        "SARCOPLASMIQUE": "SARCOPLASMIQUE",
        "MYOFIBRILLAIRE": "MYOFIBRILLAIRE",
        "MIXTE":        "MIXTE",
        "FULL BODY":    ["PECS","DOS","EPAULES","BICEPS","TRICEPS","QUADRICEPS","FESSIERS","ISCHIO"],
        "ALPHA BODY":   ["PECS","DOS","EPAULES","BICEPS","TRICEPS","QUADRICEPS","FESSIERS"],
        "POPULAIRES":   "POPULAIRES",
    }
    want_codes: set[str] = set()
    for c in cats:
        key = c.strip().upper()
        mapped = _MAP.get(key, key)
        if isinstance(mapped, list):
            want_codes.update(mapped)
        else:
            want_codes.add(mapped)

    seen, pool = set(), []
    for t in tt.get_all_techniques():
        tid = t.get("id")
        if tid not in seen and t.get("categorie", "").upper() in want_codes:
            seen.add(tid)
            pool.append(t)
    return pool

def _gen_month_lines(year: int, month: int, cats: list,
                     sat_focus: str = "Off", sun_focus: str = "Off") -> list[str]:
    """
    Génère les lignes du programme mensuel.
    Retourne une liste de strings prête à l'affichage.
    """
    pool = _pool(cats)
    if not pool:
        return ["(Aucune technique disponible pour les catégories sélectionnées)"]

    first = datetime.date(year, month, 1)
    _, nd = calendar.monthrange(year, month)

    weeks, current_week = [], []
    for i in range(1, nd + 1):
        d = first.replace(day=i)
        if d.weekday() == 0 and current_week:
            weeks.append(current_week)
            current_week = []
        current_week.append(d)
    if current_week:
        weeks.append(current_week)

    n_weeks = len(weeks)
    ids_shuffled = [t["id"] for t in pool]
    random.shuffle(ids_shuffled)

    pool_cycle = list(ids_shuffled)
    if len(pool_cycle) < n_weeks:
        extended, source = [], list(ids_shuffled)
        while len(extended) < n_weeks:
            random.shuffle(source)
            for tid in source:
                if not extended or extended[-1] != tid:
                    extended.append(tid)
                if len(extended) >= n_weeks:
                    break
        pool_cycle = extended

    week_techs, last_id = [], None
    for w_idx in range(n_weeks):
        for attempt in range(len(pool_cycle)):
            tid = pool_cycle[(w_idx + attempt) % len(pool_cycle)]
            if tid != last_id:
                week_techs.append(tid)
                last_id = tid
                break
        else:
            week_techs.append(pool_cycle[w_idx % len(pool_cycle)])
            last_id = week_techs[-1]

    lines = [f"─── Programme {first.strftime('%B %Y')} ───"]
    for w_idx, week_days in enumerate(weeks):
        tech = tt.find_technique_by_id(week_techs[w_idx]) if w_idx < len(week_techs) else None
        if not tech:
            continue
        monday, sunday = week_days[0], week_days[-1]
        lines.append(
            f"── Semaine {w_idx + 1}  ({monday.strftime('%d/%m')}→{sunday.strftime('%d/%m')}) "
            f"│ {tech['nom']} [{tech.get('categorie', '')}] ──"
        )
        for d in week_days:
            wd = d.weekday()
            ds = d.strftime(DATE_FMT)
            if wd == 5 and sat_focus == "Off":
                lines.append(f"  {ds} ({DAY_FR[wd]})  —  Repos")
                continue
            if wd == 6 and sun_focus == "Off":
                lines.append(f"  {ds} ({DAY_FR[wd]})  —  Repos")
                continue
            line = (
                f"  {ds} ({DAY_FR[wd]})  —  {tech['nom']} "
                f" [{tech.get('reps', '—')}] | {tech.get('charge', '—')}"
            )
            if wd in (5, 6) and (sat_focus if wd == 5 else sun_focus) != "Off":
                focus = sat_focus if wd == 5 else sun_focus
                line += f"  +  {focus}"
            lines.append(line)
    return lines
