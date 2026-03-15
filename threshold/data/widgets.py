# data/widgets.py — THRESHOLD · Widgets visuels partagés (Flet)
# ─────────────────────────────────────────────────────────────────────────────
# Port de features_module.py ERAGROK :
#   • render_macro_pie      → build_macro_pie(cal, prot, gluc, lip)
#   • render_cycle_timeline → build_cycle_timeline(app_state)
#   • show_halflife_calculator → build_halflife_calculator(page, app_state)
#
# matplotlib non utilisé — rendu Flet pur (Stack + Container + Row).
# ─────────────────────────────────────────────────────────────────────────────
from __future__ import annotations
import datetime
import math

import flet as ft

from ui.theme import (
    ACCENT, ACCENT_DIM, ACCENT_GLOW, ACCENT_HOVER,
    BG_CARD, BG_CARD2, BG_INPUT, BG_ROOT,
    BORDER, BLUE, BLUE_HVR, DANGER, DANGER_HVR,
    GRAY, GRAY_HVR, SUCCESS, SUCCESS_HVR, WARNING,
    TEXT, TEXT_MUTED, TEXT_SUB,
    R_CARD, R_INPUT,
    mk_btn, mk_sep, mk_title,
)
from data.meal_engine import _parse_date_flex


# ══════════════════════════════════════════════════════════════════════════════
#  CAMEMBERT MACROS — port de render_macro_pie
#  matplotlib → barres proportionnelles Flet (pas de dépendance externe)
# ══════════════════════════════════════════════════════════════════════════════

def build_macro_pie(cal: float, prot: float, gluc: float, lip: float) -> ft.Control | None:
    """
    Représentation visuelle de la répartition calorique des macros.
    Remplace le camembert matplotlib par des barres proportionnelles Flet.
    Retourne None si données insuffisantes.
    """
    if not cal or cal <= 0:
        return None

    cal_p = prot * 4
    cal_g = gluc * 4
    cal_l = lip  * 9
    total = cal_p + cal_g + cal_l
    if total <= 0:
        return None

    pct_p = cal_p / total * 100
    pct_g = cal_g / total * 100
    pct_l = cal_l / total * 100

    COLORS = {
        "Prot.": "#4aaa4a",
        "Gluc.": "#3b82f6",
        "Lip.":  "#a855f7",
    }
    data = [
        ("Prot.", pct_p, cal_p),
        ("Gluc.", pct_g, cal_g),
        ("Lip.",  pct_l, cal_l),
    ]

    # Barre proportionnelle horizontale
    bar_segments: list[ft.Control] = []
    for label, pct, _ in data:
        bar_segments.append(
            ft.Container(
                bgcolor=COLORS[label],
                border_radius=0,
                expand=False,
                width=None,     # géré par expand proportionnel via Row
                height=18,
                tooltip=f"{label} {pct:.0f}%",
            )
        )

    # Row avec expand proportionnel simulé via width relative
    bar_row = ft.Row(
        [
            ft.Container(bgcolor=COLORS[lbl], height=18,
                         width=pct * 2,   # 200px total → chaque % = 2px
                         tooltip=f"{lbl} {pct:.0f}%",
                         border_radius=ft.border_radius.only(
                             top_left=6 if i == 0 else 0,
                             bottom_left=6 if i == 0 else 0,
                             top_right=6 if i == len(data)-1 else 0,
                             bottom_right=6 if i == len(data)-1 else 0,
                         ))
            for i, (lbl, pct, _) in enumerate(data)
        ],
        spacing=0,
    )

    # Légende
    legend_items: list[ft.Control] = []
    for label, pct, kcal in data:
        legend_items.append(
            ft.Row([
                ft.Container(width=10, height=10, bgcolor=COLORS[label],
                             border_radius=3),
                ft.Text(f"{label} {pct:.0f}% ({kcal:.0f} kcal)",
                        size=10, color=TEXT_SUB),
            ], spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER)
        )

    return ft.Container(
        content=ft.Column([
            ft.Text("Répartition macros", size=10, color=TEXT_MUTED),
            bar_row,
            ft.Row(legend_items, spacing=12, wrap=True),
        ], spacing=6),
        bgcolor=BG_CARD2,
        border_radius=8,
        padding=ft.padding.symmetric(horizontal=12, vertical=10),
    )


# ══════════════════════════════════════════════════════════════════════════════
#  TIMELINE CYCLE — port de render_cycle_timeline
#  tk.Canvas → ft.Stack de Containers colorés + texte
# ══════════════════════════════════════════════════════════════════════════════

def build_cycle_timeline(app_state: dict) -> ft.Control:
    """
    Barre horizontale Cycle → Washout → PCT avec curseur "Aujourd'hui".
    Port direct de render_cycle_timeline ERAGROK, sans tk.Canvas.
    """
    from data import db as _db

    cycle = _db.cycle_get_active(app_state)

    if not cycle or not cycle.get("debut"):
        return ft.Container(
            content=ft.Column([
                mk_title("🧬  TIMELINE DU CYCLE"),
                mk_sep(),
                ft.Text("Aucun cycle enregistré.", size=11, color=TEXT_MUTED),
            ], spacing=8),
            bgcolor=BG_CARD, border_radius=R_CARD,
            border=ft.border.all(1, BORDER),
            padding=ft.padding.symmetric(horizontal=16, vertical=14),
        )

    debut = _parse_date_flex(cycle.get("debut", ""))
    if not debut:
        return ft.Container(
            content=ft.Text("Date de début invalide.", size=11, color=DANGER),
            bgcolor=BG_CARD, border_radius=R_CARD,
            padding=ft.Padding.all(16),
        )

    try:
        n_weeks = int(cycle.get("longueur_sem", "12"))
    except Exception:
        n_weeks = 12

    washout_w = 2
    pct_w     = 4
    total_w   = n_weeks + washout_w + pct_w

    today    = datetime.date.today()
    days_in  = (today - debut).days
    cur_week = days_in / 7

    # ── Phases ───────────────────────────────────────────────────────────────
    phases = [
        (0,                   n_weeks,            "#1a4a1a", "#22c55e", "CYCLE"),
        (n_weeks,             n_weeks + washout_w, "#2a1a00", "#f59e0b", "WASHOUT"),
        (n_weeks + washout_w, total_w,             "#0a0d2b", "#3b82f6", "PCT"),
    ]

    bar_segments: list[ft.Control] = []
    for start_w, end_w, bg_col, txt_col, label in phases:
        width_pct = (end_w - start_w) / total_w
        bar_segments.append(
            ft.Container(
                content=ft.Text(label, size=9, color=txt_col,
                                weight=ft.FontWeight.BOLD),
                bgcolor=bg_col,
                alignment=ft.Alignment(0, 0),
                expand=False,
                width=width_pct * 300,   # barre totale = 300px
                height=26,
                border_radius=ft.border_radius.only(
                    top_left=6   if start_w == 0      else 0,
                    bottom_left=6 if start_w == 0     else 0,
                    top_right=6   if end_w == total_w else 0,
                    bottom_right=6 if end_w == total_w else 0,
                ),
            )
        )

    bar_row = ft.Row(bar_segments, spacing=1)

    # ── Curseur aujourd'hui ───────────────────────────────────────────────────
    cursor: list[ft.Control] = []
    if 0 <= cur_week <= total_w:
        cursor_pct = cur_week / total_w
        cursor.append(
            ft.Row([
                ft.Container(width=cursor_pct * 300),
                ft.Column([
                    ft.Text("▼ Auj.", size=8, color=ACCENT,
                            weight=ft.FontWeight.BOLD),
                ], spacing=0),
            ], spacing=0)
        )

    # ── Ticks semaines ────────────────────────────────────────────────────────
    tick_labels_data = [0, n_weeks // 4, n_weeks // 2, n_weeks * 3 // 4,
                        n_weeks, n_weeks + washout_w, total_w]
    tick_row_controls: list[ft.Control] = []
    prev_pct = 0.0
    for wlabel in sorted(set(tick_labels_data)):
        pct = wlabel / total_w
        spacer_w = (pct - prev_pct) * 300
        if spacer_w > 0:
            tick_row_controls.append(ft.Container(width=spacer_w))
        tick_row_controls.append(
            ft.Text(f"S{wlabel}", size=7, color=TEXT_MUTED)
        )
        prev_pct = pct

    tick_row = ft.Row(tick_row_controls, spacing=0)

    # ── Phase courante ────────────────────────────────────────────────────────
    if days_in < 0:
        phase_txt = "Cycle pas encore démarré"
        phase_col = TEXT_MUTED
    elif days_in < n_weeks * 7:
        wk = days_in // 7 + 1
        left = n_weeks * 7 - days_in
        phase_txt = f"CYCLE — Semaine {wk}/{n_weeks}  ·  {left}j restants"
        phase_col = "#22c55e"
    elif days_in < (n_weeks + washout_w) * 7:
        phase_txt = "WASHOUT — Arrêt des produits en cours"
        phase_col = "#f59e0b"
    else:
        pct_day = days_in - (n_weeks + washout_w) * 7
        phase_txt = f"PCT — Jour {pct_day + 1}"
        phase_col = "#3b82f6"

    pct_start = debut + datetime.timedelta(weeks=n_weeks + washout_w)
    end_date  = debut + datetime.timedelta(weeks=total_w)
    dates_txt = (
        f"Début : {debut:%d/%m/%Y}  ·  "
        f"Fin cycle : {(debut + datetime.timedelta(weeks=n_weeks)):%d/%m/%Y}  ·  "
        f"PCT : {pct_start:%d/%m/%Y}  ·  "
        f"Fin PCT : {end_date:%d/%m/%Y}"
    )

    return ft.Container(
        content=ft.Column([
            mk_title("🧬  TIMELINE DU CYCLE"),
            mk_sep(),
            *cursor,
            bar_row,
            tick_row,
            ft.Container(height=4),
            ft.Text(f"📍  {phase_txt}", size=11, color=phase_col,
                    weight=ft.FontWeight.BOLD),
            ft.Text(dates_txt, size=9, color=TEXT_MUTED),
        ], spacing=6),
        bgcolor=BG_CARD,
        border_radius=R_CARD,
        border=ft.border.all(1, BORDER),
        padding=ft.padding.symmetric(horizontal=16, vertical=14),
    )


# ══════════════════════════════════════════════════════════════════════════════
#  CALCULATEUR DEMI-VIE — port de show_halflife_calculator
#  CTkToplevel → ft.AlertDialog ou vue inline
# ══════════════════════════════════════════════════════════════════════════════

HALF_LIVES = {
    "Testosterone Enanthate":        4.5,
    "Testosterone Cypionate":        8.0,
    "Testosterone Propionate":       0.8,
    "Testosterone Undecanoate":     21.0,
    "Nandrolone Decanoate (Deca)":   6.0,
    "Boldenone Undecylenate (EQ)":  14.0,
    "Trenbolone Acetate":            1.0,
    "Trenbolone Enanthate":          5.5,
    "Masteron Propionate":           2.5,
    "Masteron Enanthate":            8.0,
    "Oxandrolone (Anavar)":          0.4,
    "Stanozolol (Winstrol)":         0.4,
    "Methandrostenolone (Dianabol)": 0.2,
    "Anastrozole (Arimidex)":        2.0,
    "Letrozole (Femara)":            4.2,
    "Exemestane (Aromasin)":         1.0,
    "Clomiphene (Clomid)":           5.0,
    "Tamoxifen (Nolvadex)":          7.0,
    "HCG":                           1.5,
    "HGH (Somatotropine)":           0.17,
}


class HalflifeCalculatorView:
    """
    Calculateur demi-vie interactif.
    Peut s'afficher en dialog (show_dialog) ou inline (get_view).
    """

    def __init__(self, page: ft.Page):
        self.page        = page
        self._product    = list(HALF_LIVES.keys())[0]
        self._dose       = 100.0
        self._last_date  = datetime.date.today()
        self._result_col: ft.Column | None = None

    def get_view(self) -> ft.Container:
        """Vue inline intégrable dans un écran."""
        product_dd = ft.Dropdown(
            value=self._product,
            options=[ft.dropdown.Option(k) for k in HALF_LIVES],
            bgcolor=BG_INPUT,
            color=TEXT,
            border_color=BORDER,
            focused_border_color=ACCENT,
            text_size=11,
            on_select=self._on_product_change,
            width=280,
        )
        dose_field = ft.TextField(
            value="100",
            hint_text="mg",
            width=90, height=34,
            bgcolor=BG_INPUT, color=TEXT,
            border_color=BORDER, focused_border_color=ACCENT,
            text_size=12,
            on_change=self._on_dose_change,
        )
        date_field = ft.TextField(
            value=datetime.date.today().strftime("%d/%m/%Y"),
            hint_text="JJ/MM/AAAA",
            width=120, height=34,
            bgcolor=BG_INPUT, color=TEXT,
            border_color=BORDER, focused_border_color=ACCENT,
            text_size=12,
            on_change=self._on_date_change,
        )
        self._result_col = ft.Column([], spacing=4)
        self._calc()

        return ft.Container(
            content=ft.Column([
                mk_title("⏱  CALCULATEUR DE DEMI-VIE"),
                mk_sep(),
                ft.Row([
                    ft.Text("Produit :", size=10, color=TEXT_SUB),
                    product_dd,
                ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Row([
                    ft.Text("Dose (mg) :", size=10, color=TEXT_SUB),
                    dose_field,
                    ft.Text("Dernière injection :", size=10, color=TEXT_SUB),
                    date_field,
                ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER,
                   wrap=True),
                mk_sep(),
                ft.Container(
                    content=self._result_col,
                    bgcolor=BG_CARD2,
                    border_radius=8,
                    padding=ft.padding.symmetric(horizontal=12, vertical=10),
                ),
            ], spacing=10),
            bgcolor=BG_CARD,
            border_radius=R_CARD,
            border=ft.border.all(1, BORDER),
            padding=ft.padding.symmetric(horizontal=16, vertical=14),
        )

    def show_dialog(self):
        """Affiche le calculateur dans un AlertDialog."""
        view = self.get_view()
        dlg  = ft.AlertDialog(
            modal=True,
            title=ft.Text("⏱  Calculateur de demi-vie", color=ACCENT,
                          weight=ft.FontWeight.BOLD),
            content=ft.Container(content=view, width=500),
            actions=[
                ft.TextButton(content=ft.Text("Fermer", color=TEXT_MUTED), on_click=lambda e: self._close(dlg)),
            ],
        )
        self.page.dialog = dlg
        dlg.open = True
        self._safe_update()

    # ── Handlers ──────────────────────────────────────────────────────────────

    def _on_product_change(self, e):
        self._product = e.control.value or self._product
        self._calc()
        self._safe_update()

    def _on_dose_change(self, e):
        try:
            self._dose = float((e.control.value or "").replace(",", "."))
        except Exception:
            self._dose = 100.0
        self._calc()
        self._safe_update()

    def _on_date_change(self, e):
        try:
            self._last_date = datetime.datetime.strptime(
                (e.control.value or "").strip(), "%d/%m/%Y").date()
        except Exception:
            pass
        self._calc()
        self._safe_update()

    # ── Calcul — identique ERAGROK ────────────────────────────────────────────

    def _calc(self):
        if not self._result_col:
            return

        hl           = HALF_LIVES.get(self._product, 1.0)
        dose         = self._dose
        last         = self._last_date
        today        = datetime.date.today()
        days_elapsed = (today - last).days
        remaining    = dose * (0.5 ** (days_elapsed / hl))
        remaining_pct = 100 * (0.5 ** (days_elapsed / hl))

        rows: list[ft.Control] = [
            self._row("Demi-vie",       f"{hl} jours"),
            self._row("Jours écoulés",  f"{days_elapsed}j depuis dernière injection"),
            mk_sep(),
            self._row("Quantité restante aujourd'hui",
                      f"{remaining:.2f} mg  ({remaining_pct:.1f}%)"),
        ]

        thresholds = [(50, WARNING), (90, SUCCESS), (95, SUCCESS), (99, BLUE)]
        for pct, col in thresholds:
            days_needed = math.ceil(hl * math.log(100 / (100 - pct)) / math.log(2))
            elim_date   = last + datetime.timedelta(days=days_needed)
            if days_elapsed >= days_needed:
                val_txt = "✅ déjà éliminé"
                val_col = SUCCESS
            else:
                val_txt = f"{elim_date:%d/%m/%Y}  (J+{days_needed})"
                val_col = col
            rows.append(
                ft.Row([
                    ft.Text(f"Élimination à {pct}% :",
                            size=10, color=TEXT_MUTED, width=200),
                    ft.Text(val_txt, size=10, color=val_col,
                            weight=ft.FontWeight.BOLD),
                ], spacing=8)
            )

        self._result_col.controls.clear()
        self._result_col.controls.extend(rows)

    def _row(self, label: str, value: str) -> ft.Row:
        return ft.Row([
            ft.Text(label, size=10, color=TEXT_MUTED, width=200),
            ft.Text(value, size=10, color=TEXT),
        ], spacing=8)

    def _close(self, dlg: ft.AlertDialog):
        dlg.open = False
        self._safe_update()

    def _safe_update(self):
        from ui.page_utils import safe_update
        safe_update(self.page)


# ══════════════════════════════════════════════════════════════════════════════
#  POINTS D'ENTRÉE PUBLICS
# ══════════════════════════════════════════════════════════════════════════════

def build_halflife_calculator(page: ft.Page) -> ft.Control:
    """Vue inline du calculateur demi-vie."""
    return HalflifeCalculatorView(page).get_view()


def show_halflife_dialog(page: ft.Page):
    """Ouvre le calculateur en dialog (appelé depuis cycle screen)."""
    HalflifeCalculatorView(page).show_dialog()


# ══════════════════════════════════════════════════════════════════════════════
#  CALENDRIER CUSTOM — thème THRESHOLD
# ══════════════════════════════════════════════════════════════════════════════

import calendar as _cal

JOURS_FR  = ["Lu", "Ma", "Me", "Je", "Ve", "Sa", "Di"]
MOIS_FR   = ["Janvier","Février","Mars","Avril","Mai","Juin",
             "Juillet","Août","Septembre","Octobre","Novembre","Décembre"]

def show_date_picker(page: ft.Page, current_value: str, on_select):
    """
    Ouvre un calendrier custom dans un AlertDialog thème THRESHOLD.
    current_value : str "JJ/MM/AAAA"
    on_select     : callable(date_str: str) appelé quand l'utilisateur valide
    """
    import datetime as _dt

    # Initialiser la date affichée
    try:
        init = _dt.datetime.strptime(current_value.strip(), "%d/%m/%Y").date()
    except Exception:
        init = _dt.date.today()

    state = {"year": init.year, "month": init.month, "selected": init}
    dlg   = ft.AlertDialog(modal=True, bgcolor=BG_CARD,
                           shape=ft.RoundedRectangleBorder(radius=16))
    grid_col   = ft.Column(spacing=2)
    month_label = ft.Text("", size=14, color=ACCENT, weight=ft.FontWeight.BOLD)

    def _build_grid():
        grid_col.controls.clear()
        y, m = state["year"], state["month"]
        month_label.value = f"{MOIS_FR[m-1]}  {y}"

        # En-têtes jours
        grid_col.controls.append(
            ft.Row([ft.Container(
                        content=ft.Text(j, size=10, color=TEXT_MUTED,
                                        weight=ft.FontWeight.BOLD,
                                        text_align=ft.TextAlign.CENTER),
                        width=36, height=24, alignment=ft.Alignment(0,0))
                    for j in JOURS_FR], spacing=2)
        )

        # Jours du mois (lundi=0)
        first_wd = _dt.date(y, m, 1).weekday()
        days_in_month = _cal.monthrange(y, m)[1]
        today = _dt.date.today()
        cells = []

        # Cases vides avant le 1er
        for _ in range(first_wd):
            cells.append(ft.Container(width=36, height=36))

        for d in range(1, days_in_month + 1):
            date_obj  = _dt.date(y, m, d)
            is_sel    = (date_obj == state["selected"])
            is_today  = (date_obj == today)
            bg        = ACCENT      if is_sel   else (BG_CARD2 if is_today else "transparent")
            txt_col   = "#000000"   if is_sel   else (ACCENT   if is_today else TEXT)
            border    = ft.border.all(1, ACCENT) if is_today and not is_sel else None

            def _on_day(e, dt=date_obj):
                state["selected"] = dt
                _build_grid()
                try: e.page.update()
                except Exception: pass

            cells.append(ft.Container(
                content=ft.Text(str(d), size=12, color=txt_col,
                                text_align=ft.TextAlign.CENTER,
                                weight=ft.FontWeight.BOLD if is_sel else ft.FontWeight.NORMAL),
                width=36, height=36, bgcolor=bg, border_radius=8,
                alignment=ft.Alignment(0,0), ink=True,
                border=border, on_click=_on_day,
            ))

        # Regrouper en lignes de 7
        row_cells = []
        for i, cell in enumerate(cells):
            row_cells.append(cell)
            if len(row_cells) == 7:
                grid_col.controls.append(ft.Row(row_cells, spacing=2))
                row_cells = []
        if row_cells:
            while len(row_cells) < 7:
                row_cells.append(ft.Container(width=36, height=36))
            grid_col.controls.append(ft.Row(row_cells, spacing=2))

    _build_grid()
    def _prev_month(e=None):
        if state["month"] == 1:
            state["month"] = 12; state["year"] -= 1
        else:
            state["month"] -= 1
        _build_grid()
        try: e.page.update()
        except Exception: pass

    def _next_month(e=None):
        if state["month"] == 12:
            state["month"] = 1; state["year"] += 1
        else:
            state["month"] += 1
        _build_grid()
        try: e.page.update()
        except Exception: pass

    def _close(ev=None):
        dlg.open = False
        page.update()

    def _confirm(ev=None):
        date_str = state["selected"].strftime("%d/%m/%Y")
        dlg.open = False
        page.update()
        on_select(date_str)

    dlg.title = ft.Row([
        ft.ElevatedButton(content=ft.Text("‹", size=20, color=ACCENT),
                          bgcolor=BG_CARD2, on_click=_prev_month, width=40, height=40,
                          style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))),
        ft.Container(content=month_label, expand=True, alignment=ft.Alignment(0, 0)),
        ft.ElevatedButton(content=ft.Text("›", size=20, color=ACCENT),
                          bgcolor=BG_CARD2, on_click=_next_month, width=40, height=40,
                          style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))),
    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

    dlg.content = ft.Container(
        content=grid_col,
        width=290, padding=ft.padding.symmetric(horizontal=4, vertical=4),
    )
    dlg.actions = [
        ft.ElevatedButton(
            content=ft.Text("✕ Annuler", size=13, color=TEXT, weight=ft.FontWeight.BOLD),
            bgcolor=GRAY, on_click=_close, width=130, height=42,
        ),
        ft.ElevatedButton(
            content=ft.Text("✓ Confirmer", size=13, color=TEXT, weight=ft.FontWeight.BOLD),
            bgcolor=SUCCESS, on_click=_confirm, width=150, height=42,
        ),
    ]

    page.overlay.append(dlg)
    dlg.open = True
    page.update()
