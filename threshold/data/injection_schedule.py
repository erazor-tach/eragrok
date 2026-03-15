# data/injection_schedule.py — THRESHOLD · Planificateur d'injections
# ─────────────────────────────────────────────────────────────────────────────
# Génère le planning d'injections/prises pour un cycle complet.
# Gère ED, EOD, E3D, 2x/sem (jours choisis), 1x/sem, PCT.
# ─────────────────────────────────────────────────────────────────────────────
from __future__ import annotations
import datetime
from typing import Optional

# ── Fréquences disponibles ────────────────────────────────────────────────────
FREQ_ED      = "ED"        # chaque jour
FREQ_EOD     = "EOD"       # tous les 2 jours
FREQ_E3D     = "E3D"       # tous les 3 jours
FREQ_2X_SEM  = "2x/sem"    # 2x/semaine — jours choisis par l'utilisateur
FREQ_1X_SEM  = "1x/sem"    # 1x/semaine
FREQ_PCT     = "PCT"       # post-cycle (Clomid/Nolvadex)

# Combinaisons classiques pour 2x/sem (lundi=0 ... dimanche=6)
COMBOS_2X_SEM = [
    (0, 3, "Lundi / Jeudi"),
    (1, 4, "Mardi / Vendredi"),
    (2, 5, "Mercredi / Samedi"),
    (6, 3, "Dimanche / Mercredi"),
    (5, 2, "Samedi / Mercredi"),
    (4, 1, "Vendredi / Mardi"),
]
JOURS_FR = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]

# ── Fréquence par défaut selon les produits ───────────────────────────────────
PRODUCT_FREQ: dict[str, str] = {
    # Base Test — 2x/sem
    "Sustanon 250/300/350":                  FREQ_2X_SEM,
    "Testosterone Enanthate":                FREQ_2X_SEM,
    "Testosterone Cypionate":                FREQ_2X_SEM,
    "Testosterone Propionate":               FREQ_EOD,
    "Testosterone Undecanoate (Nebido)":     "10sem",
    # Injectables
    "Boldenone Undecylenate (Equipoise)":    FREQ_2X_SEM,
    "Drostanolone Enanthate (Masteron E)":   FREQ_2X_SEM,
    "Drostanolone Propionate (Masteron P)":  FREQ_EOD,
    "Methenolone Enanthate (Primobolan)":    FREQ_2X_SEM,
    "Nandrolone Decanoate (Deca)":           FREQ_2X_SEM,
    "Nandrolone Phenylpropionate (NPP)":     FREQ_E3D,
    "Trenbolone Hexahydrobenzylcarbonate":   FREQ_E3D,
    "Trenbolone Acetate":                    FREQ_EOD,
    "Trenbolone Enanthate":                  FREQ_2X_SEM,
    "Stanozolol Injection (Winstrol depot)": FREQ_EOD,
    "Cut Stack (mix Tren/Mast/Test)":        FREQ_EOD,
    # Oraux — ED
    "Mesterolone (Proviron)":               FREQ_ED,
    "Methandienone (Dianabol)":             FREQ_ED,
    "Oxandrolone (Anavar)":                 FREQ_ED,
    "Oxymetholone (Anadrol)":              FREQ_ED,
    "Stanozolol oral (Winstrol)":           FREQ_ED,
    "Turinabol":                            FREQ_ED,
    "Halotestin":                           FREQ_ED,
    "Primobolan tablets":                   FREQ_ED,
    # Peptides
    "Melanotan 2":              FREQ_ED,
    "BPC-157":                  FREQ_ED,
    "TB-500":                   FREQ_2X_SEM,
    "CJC-1295 sans DAC":        FREQ_ED,
    "CJC-1295 with DAC":        FREQ_1X_SEM,
    "Ipamorelin":               FREQ_ED,
    "GHRP-6":                   FREQ_ED,
    "GHRP-2":                   FREQ_ED,
    "HGH Fragment 176-191":     FREQ_ED,
    "PEG MGF":                  FREQ_E3D,
    "Tirzepatide":              FREQ_1X_SEM,
    "Semaglutide":              FREQ_1X_SEM,
    # Hormones
    "HGH Somatropin":           FREQ_ED,
    "HCG":                      FREQ_2X_SEM,
    "Liothyronine T3":          FREQ_ED,
    "Lévothyroxine T4":         FREQ_ED,
    "IGF-1 LR3":                FREQ_ED,
    # PCT
    "Clomiphene (Clomid)":      FREQ_PCT,
    "Tamoxifen (Nolvadex)":     FREQ_PCT,
    # IA / Anti-prolactine — ED ou EOD selon produit
    "Anastrozole (Arimidex)":   FREQ_EOD,
    "Exemestane (Aromasin)":    FREQ_EOD,
    "Letrozole (Femara)":       FREQ_EOD,
    "Cabergoline (Dostinex)":   FREQ_2X_SEM,
}

# ══════════════════════════════════════════════════════════════════════════════
#  MOTEUR DE CALCUL
# ══════════════════════════════════════════════════════════════════════════════

def get_freq(product_name: str) -> str:
    """Retourne la fréquence d'un produit (défaut ED si inconnu)."""
    return PRODUCT_FREQ.get(product_name, FREQ_ED)


def _testo_days(days_2x_config: dict[str, tuple[int, int]]) -> set[int]:
    """Retourne les jours de semaine (0=lun) des injections de testostérone base."""
    TESTO_PRODS = {"Testosterone Enanthate", "Testosterone Cypionate",
                   "Sustanon 250/300/350", "Testosterone Propionate",
                   "Testosterone Undecanoate (Nebido)"}
    wdays = set()
    for prod, wd in days_2x_config.items():
        if prod in TESTO_PRODS:
            wdays.add(wd[0]); wdays.add(wd[1])
    return wdays


def build_injection_dates(
    product: str,
    start_date: datetime.date,
    n_weeks: int,
    freq_override: Optional[str] = None,
    days_2x: Optional[tuple[int, int]] = None,
    days_2x_config: Optional[dict[str, tuple[int, int]]] = None,
) -> list[datetime.date]:
    """
    Calcule toutes les dates d'injection/prise pour un produit sur n_weeks.

    Règles de timing spéciales :
    - HCG          → veille de l'injection de testostérone (J-1)
    - Anastrozole  → lendemain de l'injection de testostérone (J+1)
    - Exemestane   → lendemain de l'injection de testostérone (J+1)
    - Letrozole    → lendemain de l'injection de testostérone (J+1)
    """
    freq = freq_override or get_freq(product)
    end_date = start_date + datetime.timedelta(weeks=n_weeks)
    dates = []
    current = start_date

    # ── Règles de timing spéciales ─────────────────────────────────────────────
    testo_wdays = _testo_days(days_2x_config or {})

    # HCG — la veille des jours testo
    if product == "HCG" and testo_wdays:
        veille_wdays = {(wd - 1) % 7 for wd in testo_wdays}
        while current < end_date:
            if current.weekday() in veille_wdays:
                dates.append(current)
            current += datetime.timedelta(days=1)
        return dates

    # IA (Anastrozole, Exemestane, Letrozole) — lendemain des jours testo
    IA_PRODS = {"Anastrozole (Arimidex)", "Exemestane (Aromasin)", "Letrozole (Femara)"}
    if product in IA_PRODS and testo_wdays:
        lendemain_wdays = {(wd + 1) % 7 for wd in testo_wdays}
        while current < end_date:
            if current.weekday() in lendemain_wdays:
                dates.append(current)
            current += datetime.timedelta(days=1)
        return dates

    # ── Fréquences standard ────────────────────────────────────────────────────
    if freq == FREQ_ED:
        while current < end_date:
            dates.append(current)
            current += datetime.timedelta(days=1)

    elif freq == FREQ_EOD:
        day_idx = 0
        while current < end_date:
            if day_idx % 2 == 0:
                dates.append(current)
            current += datetime.timedelta(days=1)
            day_idx += 1

    elif freq == FREQ_E3D:
        day_idx = 0
        while current < end_date:
            if day_idx % 3 == 0:
                dates.append(current)
            current += datetime.timedelta(days=1)
            day_idx += 1

    elif freq == FREQ_2X_SEM:
        wd1, wd2 = days_2x if days_2x else (0, 3)
        while current < end_date:
            if current.weekday() in (wd1, wd2):
                dates.append(current)
            current += datetime.timedelta(days=1)

    elif freq == FREQ_1X_SEM:
        target_wd = start_date.weekday()
        while current < end_date:
            if current.weekday() == target_wd:
                dates.append(current)
            current += datetime.timedelta(days=1)

    elif freq == FREQ_PCT:
        pct_start = start_date + datetime.timedelta(weeks=n_weeks + 2)
        pct_end   = pct_start + datetime.timedelta(weeks=4)
        current   = pct_start
        while current < pct_end:
            dates.append(current)
            current += datetime.timedelta(days=1)

    return dates

# ══════════════════════════════════════════════════════════════════════════════
#  FONCTIONS UTILITAIRES
# ══════════════════════════════════════════════════════════════════════════════

def get_today_injections(
    products_doses: dict[str, str],
    start_date: datetime.date,
    n_weeks: int,
    days_2x_config: dict[str, tuple[int, int]],
    today: Optional[datetime.date] = None,
) -> list[dict]:
    """
    Retourne la liste des injections/prises AUJOURD'HUI.
    Passe days_2x_config à build_injection_dates pour le timing HCG/IA.
    """
    today = today or datetime.date.today()
    result = []
    for prod, dose in products_doses.items():
        days_2x = days_2x_config.get(prod)
        dates = build_injection_dates(
            prod, start_date, n_weeks,
            days_2x=days_2x,
            days_2x_config=days_2x_config,
        )
        if today in dates:
            freq = get_freq(prod)
            # Ajouter note de timing pour HCG et IA
            timing_note = ""
            if prod == "HCG":
                timing_note = " ⚡ veille testo"
            elif prod in {"Anastrozole (Arimidex)", "Exemestane (Aromasin)", "Letrozole (Femara)"}:
                timing_note = " ⏱ lendemain testo"
            result.append({
                "product":      prod,
                "dose":         dose or "—",
                "freq":         freq,
                "timing_note":  timing_note,
            })
    return result


def get_next_injections(
    products_doses: dict[str, str],
    start_date: datetime.date,
    n_weeks: int,
    days_2x_config: dict[str, tuple[int, int]],
    days_ahead: int = 3,
    today: Optional[datetime.date] = None,
) -> dict[datetime.date, list[dict]]:
    """
    Retourne les injections des prochains `days_ahead` jours (aujourd'hui inclus).
    Retourne un dict {date: [{"product", "dose", "freq"}, ...]}
    """
    today = today or datetime.date.today()
    result: dict[datetime.date, list[dict]] = {}
    for i in range(days_ahead):
        day = today + datetime.timedelta(days=i)
        items = get_today_injections(
            products_doses, start_date, n_weeks,
            days_2x_config, today=day
        )
        if items:
            result[day] = items
    return result


def combo_label(wd1: int, wd2: int) -> str:
    """Retourne le label humain d'une combo 2x/sem."""
    for c_wd1, c_wd2, label in COMBOS_2X_SEM:
        if (c_wd1, c_wd2) == (wd1, wd2) or (c_wd2, c_wd1) == (wd1, wd2):
            return label
    return f"{JOURS_FR[wd1]} / {JOURS_FR[wd2]}"
