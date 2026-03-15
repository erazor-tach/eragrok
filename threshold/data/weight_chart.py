# data/weight_chart.py — THRESHOLD · Graphique évolution du poids (Flet)
# ─────────────────────────────────────────────────────────────────────────────
# Port de weight_chart.py ERAGROK (tkinter + matplotlib)
# Rendu Flet pur : sparkline via ft.canvas, stats bar, filtre période.
# Logique de données identique (lecture DB + moyenne mobile 7j).
# ─────────────────────────────────────────────────────────────────────────────
from __future__ import annotations
import datetime

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

_CHART_W = 560
_CHART_H = 160
_PAD_L   = 42
_PAD_R   = 16
_PAD_T   = 12
_PAD_B   = 28


# ══════════════════════════════════════════════════════════════════════════════
#  LECTURE DONNÉES — identique ERAGROK (sans pandas/matplotlib)
# ══════════════════════════════════════════════════════════════════════════════

def _load_weight_data(app_state: dict) -> list[tuple[datetime.date, float]]:
    try:
        from data import db as _db
        rows = _db.nutrition_get_all(app_state)
        points = []
        for r in rows:
            date_str  = r.get("date", "")
            poids_raw = r.get("poids", "")
            if not date_str or not poids_raw:
                continue
            try:
                poids = float(str(poids_raw).replace(",", "."))
                if poids <= 0:
                    continue
            except Exception:
                continue
            for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"):
                try:
                    d = datetime.datetime.strptime(date_str.strip(), fmt).date()
                    points.append((d, poids))
                    break
                except Exception:
                    pass
        return sorted(points, key=lambda x: x[0])
    except Exception:
        return []


def _load_calories_data(app_state: dict) -> list[tuple[datetime.date, float]]:
    try:
        from data import db as _db
        rows = _db.nutrition_get_all(app_state)
        points = []
        for r in rows:
            date_str = r.get("date", "")
            cal_raw  = r.get("calories", "") or r.get("kcal", "")
            if not date_str or not cal_raw:
                continue
            try:
                cal = float(str(cal_raw).replace(",", "."))
                if cal <= 0:
                    continue
            except Exception:
                continue
            for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"):
                try:
                    d = datetime.datetime.strptime(date_str.strip(), fmt).date()
                    points.append((d, cal))
                    break
                except Exception:
                    pass
        return sorted(points, key=lambda x: x[0])
    except Exception:
        return []


def _moving_average(values: list[float], window: int = 7) -> list[float]:
    result = []
    for i in range(len(values)):
        w = values[max(0, i - window + 1): i + 1]
        result.append(sum(w) / len(w))
    return result


def _filter_period(points: list[tuple[datetime.date, float]],
                   period: str) -> list[tuple[datetime.date, float]]:
    today  = datetime.date.today()
    cutoff = {
        "30j":    today - datetime.timedelta(days=30),
        "90j":    today - datetime.timedelta(days=90),
        "6 mois": today - datetime.timedelta(days=182),
        "1 an":   today - datetime.timedelta(days=365),
        "Tout":   datetime.date.min,
    }.get(period, datetime.date.min)
    return [(d, v) for d, v in points if d >= cutoff]


# ══════════════════════════════════════════════════════════════════════════════
#  SPARKLINE — barres verticales proportionnelles (Flet 0.82, pas de canvas)
# ══════════════════════════════════════════════════════════════════════════════

def _build_sparkline(points, ma7, show_cal=False, cal_points=None):
    """
    Graphique barres verticales Flet pur.
    - Barre bleue = poids, hauteur proportionnelle
    - Trait orange en haut = MA7
    - Barre verte optionnelle = calories (axe secondaire simulé)
    Limité à 90 colonnes max pour lisibilité.
    """
    if not points:
        return ft.Container(
            content=ft.Text("Aucune donnée.", size=11, color=TEXT_MUTED),
            bgcolor=BG_CARD2, border_radius=8,
            padding=ft.Padding.all(16), height=_CHART_H,
            alignment=ft.Alignment(0, 0),
        )

    poids  = [p[1] for p in points]
    p_min  = min(poids) - 0.5
    p_max  = max(poids) + 0.5
    p_rng  = max(p_max - p_min, 0.5)
    PLOT_H = _CHART_H - _PAD_B

    # Sous-échantillonnage si trop de points
    step = max(1, len(points) // 90)
    pts_s  = points[::step]
    ma7_s  = ma7[::step]
    n      = len(pts_s)

    # Calories sous-échantillonnées (alignées sur même dates)
    cal_map: dict = {}
    if show_cal and cal_points:
        c_vals = [v for _, v in cal_points]
        c_max  = max(c_vals) if c_vals else 1
        for cd, cv in cal_points:
            cal_map[cd] = cv / c_max   # normalisé 0–1

    bars: list[ft.Control] = []
    lbl_step = max(1, n // 6)

    for i, ((d, v), m) in enumerate(zip(pts_s, ma7_s)):
        h_p = max(2, int((v - p_min) / p_rng * PLOT_H))
        h_m = max(2, int((m - p_min) / p_rng * PLOT_H))
        # Trait MA7 : décalage depuis le haut de la barre poids
        ma7_top = max(0, h_p - h_m)

        # Barre calories en fond (verte, pleine hauteur relative)
        cal_frac = cal_map.get(d, 0.0)
        h_cal    = int(cal_frac * PLOT_H * 0.6) if cal_frac else 0

        inner: list[ft.Control] = []
        if h_cal:
            inner.append(ft.Container(
                width=6, height=h_cal,
                bgcolor="#4ade80", opacity=0.5,
                border_radius=ft.border_radius.only(top_left=2, top_right=2),
                margin=ft.margin.only(bottom=0),
            ))

        # Stack : barre poids + trait MA7
        inner_stack: list[ft.Control] = [
            ft.Container(
                width=6, height=h_p,
                bgcolor=BLUE, opacity=0.85,
                border_radius=ft.border_radius.only(top_left=2, top_right=2),
            ),
            ft.Container(
                width=6, height=3,
                bgcolor=ACCENT,
                margin=ft.margin.only(top=ma7_top),
            ),
        ]

        col_content: list[ft.Control] = [
            ft.Container(expand=True),  # pousse vers le bas
            ft.Stack(inner_stack, height=h_p, width=6),
        ]
        if h_cal:
            col_content.insert(1, ft.Container(
                width=6, height=h_cal,
                bgcolor="#4ade80", opacity=0.4,
                border_radius=ft.border_radius.only(top_left=2, top_right=2),
            ))

        label_txt = d.strftime("%d/%m") if (i % lbl_step == 0) else ""
        bars.append(ft.Column(
            [
                ft.Column(col_content, spacing=0,
                          horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                          height=PLOT_H),
                ft.Text(label_txt, size=7, color=TEXT_MUTED,
                        text_align=ft.TextAlign.CENTER, width=28),
            ],
            spacing=0,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True,
        ))

    # Axe Y — labels
    y_labels: list[ft.Control] = []
    for i in range(3, -1, -1):
        yv = p_min + i * p_rng / 3
        y_labels.append(ft.Container(
            content=ft.Text(f"{yv:.1f}", size=7, color=TEXT_MUTED,
                            text_align=ft.TextAlign.RIGHT),
            expand=True,
            alignment=ft.Alignment(1, -1),
        ))
    y_axis = ft.Container(
        content=ft.Column(y_labels, spacing=0, expand=True),
        width=_PAD_L - 4,
        height=PLOT_H,
    )

    return ft.Container(
        content=ft.Row(
            [y_axis, ft.Row(bars, spacing=1, expand=True,
                            vertical_alignment=ft.CrossAxisAlignment.END)],
            spacing=0,
            vertical_alignment=ft.CrossAxisAlignment.END,
        ),
        height=_CHART_H,
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
    )


# ══════════════════════════════════════════════════════════════════════════════
#  BARRE STATS — identique ERAGROK
# ══════════════════════════════════════════════════════════════════════════════

def _build_stats_bar(poids, dates):
    if not poids:
        return ft.Row([])
    current = poids[-1]
    minimum = min(poids)
    maximum = max(poids)
    moyenne = sum(poids) / len(poids)
    delta   = poids[-1] - poids[0] if len(poids) > 1 else 0.0
    jours   = (dates[-1] - dates[0]).days if len(dates) > 1 else 0
    delta_col = SUCCESS if delta <= 0 else (DANGER if delta > 2 else ACCENT_GLOW)

    stats = [
        ("Actuel",    f"{current:.1f} kg", TEXT),
        ("Min",       f"{minimum:.1f} kg", BLUE),
        ("Max",       f"{maximum:.1f} kg", DANGER),
        ("Moyenne",   f"{moyenne:.1f} kg", TEXT_SUB),
        ("Évolution", f"{delta:+.1f} kg en {jours}j", delta_col),
    ]
    cells = []
    for label, value, color in stats:
        cells.append(ft.Container(
            content=ft.Column([
                ft.Text(label, size=9,  color=TEXT_MUTED),
                ft.Text(value, size=13, color=color,
                        weight=ft.FontWeight.BOLD),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
            bgcolor=BG_CARD2, border_radius=8,
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            expand=True,
        ))
    return ft.Row(cells, spacing=6)


# ══════════════════════════════════════════════════════════════════════════════
#  VUE PRINCIPALE
# ══════════════════════════════════════════════════════════════════════════════

class WeightChartView:
    PERIODS = ["30j", "90j", "6 mois", "1 an", "Tout"]

    def __init__(self, page: ft.Page, app_state: dict):
        self.page        = page
        self.app_state   = app_state
        self._period     = "Tout"
        self._show_cal   = False
        self._all_points = _load_weight_data(app_state)
        self._cal_points = _load_calories_data(app_state)
        self._chart_box:   ft.Container | None = None
        self._stats_row:   ft.Row       | None = None
        self._period_btns: list[ft.Button] = []
        self._cal_toggle:  ft.Button | None = None

    def get_view(self) -> ft.Container:
        if not self._all_points:
            return ft.Container(
                content=ft.Column([
                    mk_title("📈  ÉVOLUTION DU POIDS"),
                    mk_sep(),
                    ft.Text(
                        "Aucune donnée de poids disponible.\n"
                        "Enregistre des entrées nutrition avec un poids.",
                        size=11, color=TEXT_MUTED),
                ], spacing=8),
                bgcolor=BG_CARD, border_radius=R_CARD,
                border=ft.border.all(1, BORDER),
                padding=ft.padding.symmetric(horizontal=16, vertical=14),
            )

        # Boutons période — mk_btn du thème (compatible Flet 0.82)
        self._period_btns = []
        for p in self.PERIODS:
            sel = (p == self._period)
            btn = mk_btn(p, lambda e, v=p: self._set_period(v),
                         color=ACCENT if sel else BG_CARD2,
                         hover=ACCENT_HOVER if sel else GRAY,
                         width=60, height=30)
            btn.data = p
            self._period_btns.append(btn)

        has_cal = bool(self._cal_points)
        self._cal_toggle = mk_btn("📊 Calories", lambda e: self._toggle_cal(),
                                  color=BG_CARD2, hover=GRAY,
                                  width=110, height=30)
        self._cal_toggle.visible = has_cal

        self._chart_box = ft.Container(
            content=self._build_chart(),
            bgcolor=BG_CARD2, border_radius=8,
            padding=ft.Padding.all(8),
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
        )

        pts = _filter_period(self._all_points, self._period)
        self._stats_row = _build_stats_bar(
            [v for _, v in pts], [d for d, _ in pts])

        legend_items = [
            ft.Container(width=20, height=3, bgcolor=BLUE),
            ft.Text("Poids", size=9, color=TEXT_MUTED),
            ft.Container(width=20, height=3, bgcolor=ACCENT),
            ft.Text("Moy. mobile 7j", size=9, color=TEXT_MUTED),
        ]
        if has_cal:
            legend_items += [
                ft.Container(width=12, height=12, bgcolor="#4ade80",
                             border_radius=2, opacity=0.7),
                ft.Text("Calories", size=9, color=TEXT_MUTED),
            ]

        return ft.Container(
            content=ft.Column([
                mk_title("📈  ÉVOLUTION DU POIDS — 30 derniers jours"),
                mk_sep(),
                ft.Row([*self._period_btns, self._cal_toggle],
                       spacing=6, wrap=True),
                self._chart_box,
                ft.Row(legend_items, spacing=6),
                self._stats_row,
            ], spacing=10),
            bgcolor=BG_CARD, border_radius=R_CARD,
            border=ft.border.all(1, BORDER),
            padding=ft.padding.symmetric(horizontal=16, vertical=14),
        )

    # ── Handlers ──────────────────────────────────────────────────────────────

    def _set_period(self, period: str):
        self._period = period
        for btn in self._period_btns:
            sel = (btn.data == period)
            btn.bgcolor = ACCENT if sel else BG_CARD2
            btn.color   = "#000000" if sel else TEXT_MUTED
        self._refresh()

    def _toggle_cal(self):
        self._show_cal = not self._show_cal
        if self._cal_toggle:
            self._cal_toggle.bgcolor = ACCENT if self._show_cal else BG_CARD2
            self._cal_toggle.color   = "#000000" if self._show_cal else TEXT_MUTED
        self._refresh()

    def _refresh(self):
        if self._chart_box:
            self._chart_box.content = self._build_chart()
        pts = _filter_period(self._all_points, self._period)
        new = _build_stats_bar([v for _, v in pts], [d for d, _ in pts])
        if self._stats_row:
            self._stats_row.controls.clear()
            self._stats_row.controls.extend(new.controls)
        self._safe_update()

    def _build_chart(self) -> ft.Control:
        pts = _filter_period(self._all_points, self._period)
        if not pts:
            return ft.Container(
                content=ft.Text("Aucune donnée pour cette période.",
                                size=11, color=TEXT_MUTED),
                height=_CHART_H, alignment=ft.Alignment(0, 0))
        ma7 = _moving_average([v for _, v in pts])
        return _build_sparkline(pts, ma7,
                                show_cal=self._show_cal,
                                cal_points=self._cal_points)

    def _safe_update(self):
        from ui.page_utils import safe_update
        safe_update(self.page)


# ══════════════════════════════════════════════════════════════════════════════
#  POINTS D'ENTRÉE PUBLICS
# ══════════════════════════════════════════════════════════════════════════════

def build_weight_chart(page: ft.Page, app_state: dict) -> ft.Control:
    """Vue inline — à insérer dans le dashboard."""
    return WeightChartView(page, app_state).get_view()


def show_weight_chart(page: ft.Page, app_state: dict):
    """Ouvre le graphique dans un AlertDialog."""
    view = WeightChartView(page, app_state).get_view()
    dlg  = ft.AlertDialog(
        modal=True,
        title=ft.Text("📈  Évolution du poids", color=ACCENT,
                      weight=ft.FontWeight.BOLD),
        content=ft.Container(content=view, width=640),
        actions=[ft.TextButton(content=ft.Text("Fermer", color=TEXT_MUTED), on_click=lambda e: _close_dlg(dlg, page))],
    )
    page.dialog = dlg
    dlg.open    = True
    try:
        page.update()
    except Exception:
        pass


def _close_dlg(dlg: ft.AlertDialog, page: ft.Page):
    dlg.open = False
    try:
        page.update()
    except Exception:
        pass
