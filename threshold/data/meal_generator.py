# features/meal_generator.py — THRESHOLD · Générateur de plan alimentaire (Flet)
# ─────────────────────────────────────────────────────────────────────────────
# Port de show_meal_generator (features_module.py ERAGROK ~1 295 L)
# Architecture : MealGeneratorView (état complet) → build_meal_generator_screen()
# ─────────────────────────────────────────────────────────────────────────────
from __future__ import annotations
import datetime
import json
import random
from typing import Callable

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
from data.meal_engine import (
    FOOD_DB_EXT, FOOD_CATS, FOOD_MIN_PORTION, FOOD_MAX_PORTION, FOOD_MAX_DEFAULT,
    COOKED_TO_RAW, SLOT_DESC,
    _fiber_for, _food_swap_alternatives,
    _generate_meal_plan, _generate_multiday_plan,
    compute_diversity_score, _apply_budget_pass,
)
from data.logger import log_exc

# ── Catégories affichées (identiques ERAGROK) ─────────────────────────────────
DISPLAY_CATS = [
    ("🥚  Œufs",              ["oeuf"]),
    ("🥛  Laitiers",          ["laitier", "laitier_lent"]),
    ("🧀  Fromages",          ["fromage_dur"]),
    ("💊  Suppléments",       ["whey", "supplement_lent"]),
    ("🍗  Protéines maigres", ["proteine_maigre"]),
    ("🥩  Protéines grasses", ["proteine_grasse"]),
    ("🥣  Glucides matin",    ["glucide_matin", "pain_seulement"]),
    ("🍯  Accompagnements",   ["sucrant_matin", "boisson_matin"]),
    ("🍚  Glucides repas",    ["glucide_midi"]),
    ("🍌  Fruits",            ["fruit"]),
    ("🥦  Légumes",           ["legume"]),
    ("🥑  Lipides sains",     ["lipide_sain"]),
]

DAY_SHORT = ["L", "Ma", "Me", "J", "V", "S", "D"]


# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS PARTAGÉS
# ══════════════════════════════════════════════════════════════════════════════

def _macro_color(got: float, tgt: float) -> str:
    if tgt <= 0:
        return TEXT_MUTED
    diff = abs(got / tgt * 100 - 100)
    return SUCCESS if diff <= 5 else (ACCENT_GLOW if diff <= 12 else DANGER)


def _build_macro_boxes(macros: list[tuple]) -> ft.Row:
    """
    macros = [(label, got, tgt, unit), ...]
    Retourne une Row de cartes macros identiques ERAGROK.
    """
    cols: list[ft.Control] = []
    for label, got, tgt, unit in macros:
        clr = _macro_color(got, tgt)
        pct = (got / tgt * 100) if tgt > 0 else 0
        cols.append(
            ft.Container(
                content=ft.Column([
                    ft.Text(label,               size=10, color=TEXT_MUTED),
                    ft.Text(f"{got:.0f} {unit}", size=14, color=clr,
                            weight=ft.FontWeight.BOLD),
                    ft.Text(f"cible {tgt:.0f} ({pct:.0f}%)",
                            size=9, color=TEXT_MUTED),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                   spacing=2),
                bgcolor=BG_CARD2,
                border_radius=8,
                padding=ft.padding.symmetric(vertical=8, horizontal=6),
                expand=True,
            )
        )
    return ft.Row(cols, spacing=4)


def _build_budget_bar(week_cost: float, budget_w: float,
                      day_cost: float) -> ft.Control:
    """Bandeau bilan budget — identique ERAGROK."""
    bgt_clr = (SUCCESS if week_cost <= budget_w * 1.05
               else (ACCENT_GLOW if week_cost <= budget_w * 1.20 else DANGER))
    pct_b = (week_cost / budget_w * 100) if budget_w > 0 else 0
    ok_s  = ("✅" if week_cost <= budget_w * 1.05
             else ("⚠️" if week_cost <= budget_w * 1.20 else "❌"))

    controls: list[ft.Control] = [
        ft.Container(
            content=ft.Row([
                ft.Text("💰  Budget estimé", size=10, color=TEXT_MUTED),
                ft.Text(f"  {day_cost:.2f} €/j  ·  {week_cost:.2f} €/sem",
                        size=12, color=bgt_clr, weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                ft.Text(f"{ok_s}  {pct_b:.0f}% du budget ({budget_w:.0f} €/sem)",
                        size=10, color=bgt_clr),
            ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=BG_CARD2, border_radius=8,
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
        )
    ]
    if week_cost > budget_w * 1.20:
        controls.append(
            ft.Container(
                content=ft.Column([
                    ft.Text("⚠️  Budget insuffisant pour ce plan",
                            size=10, color=DANGER),
                    ft.Text(
                        f"Minimum estimé : {week_cost:.0f} €/sem  (budget : {budget_w:.0f} €) "
                        f"— Décoche des aliments coûteux ou augmente le budget.",
                        size=9, color=TEXT_MUTED),
                ], spacing=2),
                bgcolor="#2a1010", border_radius=8,
                padding=ft.padding.symmetric(horizontal=12, vertical=8),
            )
        )
    return ft.Column(controls, spacing=4)


# ══════════════════════════════════════════════════════════════════════════════
#  VUE PRINCIPALE
# ══════════════════════════════════════════════════════════════════════════════

class MealGeneratorView:
    """
    État complet du générateur de plan alimentaire.
    Flet ne supporte pas les variables tkinter → tout est géré en Python pur
    + page.update() pour rafraîchir.
    """

    def __init__(self, page: ft.Page, app_state: dict,
                 on_show_nutrition: Callable | None = None):
        self.page              = page
        self.app_state         = app_state
        self.on_show_nutrition = on_show_nutrition

        # ── État réglages ─────────────────────────────────────────────────────
        self.n_meals:   int   = 4
        self.gen_mode:  str   = "jour"     # "jour" | "semaine" | "mois"
        self.budget_w:  float | None = None
        self.start_date = datetime.date.today()

        # ── État aliments ─────────────────────────────────────────────────────
        self.chk_states: dict[str, bool] = {}   # food → coché
        self.blacklist:  set[str]        = set()
        self.search_query: str           = ""

        # ── Dernier plan généré ───────────────────────────────────────────────
        self._last_plan: dict | None = None

        # ── Références UI dynamiques ──────────────────────────────────────────
        self._result_col:    ft.Column | None = None
        self._accept_col:    ft.Column | None = None
        self._counter_text:  ft.Text   | None = None
        self._bl_count_text: ft.Text   | None = None
        self._budget_day_text: ft.Text | None = None
        self._food_rows:     dict[str, ft.Control] = {}
        self._cat_rows:      dict[str, tuple[ft.Control, list[str]]] = {}
        self._foods_col:     ft.Column | None = None
        self._nav_tab_btns:  list[ft.ElevatedButton] = []
        self._day_content:   ft.Column | None = None
        self._active_day:    int = 0

        self._load_prefs()

    # ── Chargement préférences ────────────────────────────────────────────────

    def _load_prefs(self):
        try:
            from data import db as _db
            raw = _db.settings_get(self.app_state, "selected_foods", "")
            if raw:
                saved = set(json.loads(raw))
                for f in FOOD_DB_EXT:
                    self.chk_states[f] = (f in saved)
            else:
                for f in FOOD_DB_EXT:
                    self.chk_states[f] = False

            raw_bl = _db.settings_get(self.app_state, "food_blacklist", "")
            if raw_bl:
                self.blacklist = set(json.loads(raw_bl))
        except Exception:
            for f in FOOD_DB_EXT:
                self.chk_states[f] = False

    def _save_food_prefs(self):
        try:
            from data import db as _db
            sel = [f for f, v in self.chk_states.items() if v]
            _db.settings_set(self.app_state, "selected_foods",
                             json.dumps(sel, ensure_ascii=False))
            self._snack(f"✔ {len(sel)} aliments sauvegardés.", SUCCESS)
        except Exception as ex:
            log_exc("_save_selection")
            self._snack(f"Erreur : {ex}", DANGER)

    def _save_blacklist(self):
        try:
            from data import db as _db
            _db.settings_set(self.app_state, "food_blacklist",
                             json.dumps(list(self.blacklist), ensure_ascii=False))
        except Exception:
            pass

    # ── Calcul macros depuis profil ───────────────────────────────────────────

    def _get_macros(self) -> tuple[float, float, float, float]:
        try:
            from data import utils
            ui  = self.app_state.get("user_info") or {}
            dn  = ui.get("date_naissance", "")
            age = str(utils.age_depuis_naissance(dn) or ui.get("age") or "30")
            poids = str(ui.get("poids") or "80")
            nut = utils.calculs_nutrition(poids, age, ui.get("sexe"),
                                          ui.get("objectif"), ui.get("taille"))
            adj = utils.ADJUSTMENTS.get(
                ui.get("ajustement", "Maintien (0%)"), 0.0)
            cal  = (nut["tdee"] * (1 + adj)) if nut else 2500
            obj_l = ui.get("objectif", "").lower()
            if "masse"   in obj_l: cp, fp = 0.47, 0.23
            elif "perte" in obj_l: cp, fp = 0.37, 0.23
            else:                   cp, fp = 0.45, 0.25
            prot = nut["proteines"] if nut else cal * 0.30 / 4
            gluc = (cal * cp) / 4
            lip  = (cal * fp) / 9
            return cal, prot, gluc, lip
        except Exception:
            return 2500.0, 180.0, 280.0, 70.0

    # ══════════════════════════════════════════════════════════════════════════
    #  CONSTRUCTION DE LA VUE
    # ══════════════════════════════════════════════════════════════════════════

    def get_view(self) -> ft.Column:
        left  = self._build_settings_panel()
        right = self._build_result_panel()

        return ft.Column([
            ft.Container(
                content=ft.Column([
                    left,
                    right,
                ], spacing=12),
                padding=ft.padding.symmetric(horizontal=16, vertical=12),
            ),
        ], scroll=ft.ScrollMode.AUTO, expand=True)

    # ── Panneau gauche — réglages ─────────────────────────────────────────────

    def _build_settings_panel(self) -> ft.Container:
        ui      = self.app_state.get("user_info") or {}
        obj     = ui.get("objectif", "—")
        adj_txt = ui.get("ajustement", "Maintien (0%)")

        controls: list[ft.Control] = [
            mk_title("⚙️  RÉGLAGES"),
            mk_sep(),

            # Objectif profil (lecture seule)
            ft.Container(
                content=ft.Column([
                    ft.Text("Objectif profil", size=10, color=TEXT_MUTED),
                    ft.Text(f"🎯  {obj}  —  {adj_txt}",
                            size=12, color=ACCENT_GLOW),
                ], spacing=2),
                bgcolor=BG_CARD2, border_radius=8,
                padding=ft.padding.symmetric(horizontal=10, vertical=8),
            ),

            # Nombre de repas
            ft.Text("Repas par jour", size=10, color=TEXT_SUB),
            self._build_n_meals_row(),

            mk_sep(),

            # Mode de génération
            ft.Text("Mode de génération", size=10, color=TEXT_SUB),
            self._build_mode_col(),

            mk_sep(),

            # Budget
            ft.Row([
                ft.Text("💰  Budget / semaine", size=10, color=TEXT_SUB),
                ft.Text("optionnel", size=9, color=TEXT_MUTED),
            ], spacing=6),
            self._build_budget_block(),

            mk_sep(),

            # Date de début
            ft.Text("Date de début", size=10, color=TEXT_SUB),
            self._build_date_row(),

            mk_sep(),

            # Légende timing
            self._build_legend(),

            mk_sep(),

            # Sélection aliments
            ft.Text("Tes aliments disponibles", size=10, color=TEXT_SUB),
            self._build_food_search(),
            self._build_chk_counter(),
            self._build_food_list(),
            self._build_food_actions(),

            mk_sep(),

            # Bouton GÉNÉRER
            ft.Container(
                content=mk_btn("⚡  GÉNÉRER", self._on_generate,
                               color=ACCENT, hover=ACCENT_HOVER,
                               width=260, height=48),
                alignment=ft.Alignment(0, 0),
                padding=ft.padding.only(top=8, bottom=4),
            ),

            # Zone accepter (visible après génération)
            self._build_accept_zone(),
        ]

        return ft.Container(
            content=ft.Column(controls, spacing=8, scroll=ft.ScrollMode.AUTO),
            bgcolor=BG_CARD,
            border_radius=R_CARD,
            border=ft.border.all(1, BORDER),
            padding=ft.padding.symmetric(horizontal=14, vertical=12),
        )

    def _build_n_meals_row(self) -> ft.Row:
        btns: list[ft.Control] = []
        for n in [3, 4, 5, 6]:
            is_sel = (n == self.n_meals)
            btn = ft.ElevatedButton(
                content=ft.Text(str(n), size=13, weight=ft.FontWeight.BOLD,
                                color=TEXT if is_sel else TEXT_SUB),
                on_click=lambda e, v=n: self._set_n_meals(v),
                style=ft.ButtonStyle(
                    bgcolor={ft.ControlState.DEFAULT: ACCENT if is_sel else BG_INPUT},
                    padding=ft.padding.symmetric(horizontal=10, vertical=6),
                    shape=ft.RoundedRectangleBorder(radius=8),
                ),
                data=n,
            )
            btns.append(btn)
        self._n_meals_btns = btns
        return ft.Row(btns, spacing=6)

    def _set_n_meals(self, n: int):
        self.n_meals = n
        for btn in self._n_meals_btns:
            sel = (btn.data == n)
            btn.content.color = TEXT if sel else TEXT_SUB
            btn.style = ft.ButtonStyle(
                bgcolor={ft.ControlState.DEFAULT: ACCENT if sel else BG_INPUT},
                padding=ft.padding.symmetric(horizontal=10, vertical=6),
                shape=ft.RoundedRectangleBorder(radius=8),
            )
        self._safe_update()

    def _build_mode_col(self) -> ft.Column:
        modes = [("1 jour", "jour"), ("Semaine (7j)", "semaine"), ("Mois (30j)", "mois")]
        btns: list[ft.Control] = []
        for lbl, val in modes:
            is_sel = (val == self.gen_mode)
            btn = ft.ElevatedButton(
                content=ft.Text(lbl, size=13, weight=ft.FontWeight.BOLD,
                                color=TEXT if is_sel else TEXT_SUB),
                on_click=lambda e, v=val: self._set_mode(v),
                style=ft.ButtonStyle(
                    bgcolor={ft.ControlState.DEFAULT: ACCENT if is_sel else BG_INPUT},
                    padding=ft.padding.symmetric(horizontal=10, vertical=6),
                    shape=ft.RoundedRectangleBorder(radius=8),
                ),
                data=val,
            )
            btns.append(btn)
        self._mode_btns = btns
        return ft.Row(btns, spacing=6, wrap=True)

    def _set_mode(self, val: str):
        self.gen_mode = val
        for btn in self._mode_btns:
            sel = (btn.data == val)
            btn.content.color = TEXT if sel else TEXT_SUB
            btn.style = ft.ButtonStyle(
                bgcolor={ft.ControlState.DEFAULT: ACCENT if sel else BG_INPUT},
                padding=ft.padding.symmetric(horizontal=10, vertical=6),
                shape=ft.RoundedRectangleBorder(radius=8),
            )
        self._safe_update()

    def _build_budget_block(self) -> ft.Container:
        self._budget_field  = ft.TextField(
            hint_text="ex: 80",
            width=90, height=36,
            bgcolor=BG_INPUT, color=TEXT,
            border_color=BORDER, focused_border_color=ACCENT,
            hint_style=ft.TextStyle(color=TEXT_MUTED),
            text_size=13,
            on_change=self._on_budget_change,
        )
        self._budget_day_text = ft.Text("", size=10, color=TEXT_MUTED)

        presets: list[ft.Control] = []
        for p in [50, 70, 80, 100, 120]:
            presets.append(
                ft.TextButton(
                    content=ft.Text(f"{p}€", color=TEXT_MUTED),
                    on_click=lambda e, v=p: self._set_budget_preset(v),
                    style=ft.ButtonStyle(
                        bgcolor={ft.ControlState.DEFAULT: BG_CARD},
                        padding=ft.padding.symmetric(horizontal=6, vertical=4),
                        shape=ft.RoundedRectangleBorder(radius=6),
                    ),
                )
            )
        presets.append(
            ft.TextButton(
                content=ft.Text("✕", color=TEXT_MUTED),
                on_click=lambda e: self._clear_budget(),
                style=ft.ButtonStyle(
                    bgcolor={ft.ControlState.DEFAULT: BG_ROOT},
                    padding=ft.padding.symmetric(horizontal=4, vertical=4),
                    shape=ft.RoundedRectangleBorder(radius=6),
                ),
            )
        )

        return ft.Container(
            content=ft.Column([
                ft.Row([
                    self._budget_field,
                    ft.Text("€ / semaine", size=12, color=ACCENT),
                    self._budget_day_text,
                ], spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Row(presets, spacing=4, wrap=True),
            ], spacing=6),
            bgcolor=BG_CARD2, border_radius=8,
            padding=ft.padding.symmetric(horizontal=10, vertical=8),
        )

    def _on_budget_change(self, e):
        raw = (e.control.value or "").strip().replace(",", ".")
        try:
            b = float(raw)
            if b > 0:
                self.budget_w = b
                if self._budget_day_text:
                    self._budget_day_text.value = f"≈ {b/7:.2f} €/j"
                    self._budget_day_text.color = SUCCESS
            else:
                self.budget_w = None
                if self._budget_day_text:
                    self._budget_day_text.value = ""
        except Exception:
            self.budget_w = None
            if self._budget_day_text:
                self._budget_day_text.value = ""
        self._safe_update()

    def _set_budget_preset(self, v: int):
        self.budget_w = float(v)
        if self._budget_field:
            self._budget_field.value = str(v)
        if self._budget_day_text:
            self._budget_day_text.value = f"≈ {v/7:.2f} €/j"
            self._budget_day_text.color = SUCCESS
        self._safe_update()

    def _clear_budget(self):
        self.budget_w = None
        if self._budget_field:
            self._budget_field.value = ""
        if self._budget_day_text:
            self._budget_day_text.value = ""
        self._safe_update()

    def _build_date_row(self) -> ft.Row:
        self._date_field = ft.TextField(
            value=self.start_date.strftime("%d/%m/%Y"),
            hint_text="jj/mm/aaaa",
            width=120, height=44,
            bgcolor=BG_INPUT, color=TEXT,
            border_color=BORDER, focused_border_color=ACCENT,
            text_size=12,
            on_change=self._on_date_change,
        )

        def _open_cal(e):
            from data.widgets import show_date_picker
            def _on_date(date_str):
                self._date_field.value = date_str
                try:
                    import datetime as _dt
                    self.start_date = _dt.datetime.strptime(date_str, "%d/%m/%Y").date()
                except Exception:
                    pass
                self._safe_update()
            show_date_picker(self.page, self._date_field.value, _on_date)

        cal_btn = ft.ElevatedButton(
            content=ft.Text("📅", size=18),
            bgcolor=BG_CARD2, color=TEXT, tooltip="Choisir une date",
            on_click=_open_cal,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8),
                                 padding=ft.Padding.all(0)),
            width=44, height=44,
        )
        return ft.Row([
            ft.Row([self._date_field, cal_btn], spacing=0),
            ft.TextButton(
                content=ft.Text("Auj.", color=TEXT_MUTED),
                on_click=lambda e: self._set_today(),
                style=ft.ButtonStyle(
                    bgcolor={ft.ControlState.DEFAULT: GRAY},
                    padding=ft.padding.symmetric(horizontal=6, vertical=4),
                    shape=ft.RoundedRectangleBorder(radius=6),
                ),
            ),
        ], spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER)

    def _on_date_change(self, e):
        try:
            self.start_date = datetime.datetime.strptime(
                (e.control.value or "").strip(), "%d/%m/%Y").date()
        except Exception:
            pass

    def _set_today(self):
        self.start_date = datetime.date.today()
        if self._date_field:
            self._date_field.value = self.start_date.strftime("%d/%m/%Y")
        self._safe_update()

    def _build_legend(self) -> ft.Container:
        icons = {"matin": "🌅", "midi": "☀️", "collation": "🍎",
                 "soir": "🌙", "coucher": "🌛"}
        rows: list[ft.Control] = [
            ft.Text("📌  Timing & compatibilité", size=12, color=TEXT_SUB),
        ]
        for slot, desc in SLOT_DESC.items():
            rows.append(
                ft.Row([
                    ft.Text(f"{icons.get(slot,'')} {slot.capitalize()}",
                            size=11, color=ACCENT_GLOW, width=90),
                    ft.Text(desc, size=11, color=TEXT_SUB, expand=True),
                ], spacing=4)
            )
        rows.append(
            ft.Text("⚠️  Les aliments incompatibles sont automatiquement séparés.",
                    size=11, color=TEXT_SUB)
        )
        return ft.Container(
            content=ft.Column(rows, spacing=3),
            bgcolor=BG_CARD2, border_radius=8,
            padding=ft.padding.symmetric(horizontal=10, vertical=8),
        )

    def _build_food_search(self) -> ft.TextField:
        self._search_field = ft.TextField(
            hint_text="🔍 Rechercher un aliment...",
            height=34,
            bgcolor=BG_INPUT, color=TEXT,
            border_color=BORDER, focused_border_color=ACCENT,
            hint_style=ft.TextStyle(color=TEXT_MUTED),
            text_size=12,
            on_change=self._on_search_change,
        )
        return self._search_field

    def _on_search_change(self, e):
        self.search_query = (e.control.value or "").strip().lower()
        self._filter_foods()
        self._safe_update()

    def _build_chk_counter(self) -> ft.Text:
        self._counter_text = ft.Text("", size=10, color=TEXT_MUTED)
        self._update_counter()
        return self._counter_text

    def _update_counter(self):
        if not self._counter_text:
            return
        n     = sum(1 for v in self.chk_states.values() if v)
        total = len(self.chk_states)
        clr   = (SUCCESS if n >= 10 else (ACCENT_GLOW if n >= 5 else TEXT_MUTED))
        self._counter_text.value = f"☑ {n}/{total} aliments sélectionnés"
        self._counter_text.color = clr

    def _build_food_list(self) -> ft.Container:
        self._food_rows = {}
        self._cat_rows  = {}
        self._foods_col = ft.Column([], spacing=2, scroll=ft.ScrollMode.AUTO)

        seen = set()
        for cat_lbl, cats in DISPLAY_CATS:
            foods_in = []
            for c in cats:
                for f in FOOD_CATS.get(c, []):
                    if f not in seen and f in FOOD_DB_EXT and f not in self.blacklist:
                        foods_in.append(f)
                        seen.add(f)
            if not foods_in:
                continue

            cat_hdr = ft.Container(
                content=ft.Text(cat_lbl, size=10, color=TEXT_MUTED),
                bgcolor=BG_CARD2, border_radius=4,
                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                data=cat_lbl,
            )
            self._foods_col.controls.append(cat_hdr)
            self._cat_rows[cat_lbl] = (cat_hdr, [])

            for food in foods_in:
                k, p, g, l = FOOD_DB_EXT[food]
                checked = self.chk_states.get(food, False)
                row = ft.Container(
                    content=ft.Row([
                        ft.Checkbox(
                            value=checked,
                            fill_color={
                                ft.ControlState.SELECTED: ACCENT,
                                ft.ControlState.DEFAULT:  BG_CARD2,
                            },
                            check_color="#000000",
                            data=food,
                            on_change=self._on_food_check,
                        ),
                        ft.Text(food, size=11, color=TEXT, expand=True),
                        ft.Text(f"{p:.0f}P/{g:.0f}G/{l:.0f}L",
                                size=9, color=TEXT_MUTED),
                    ], spacing=4,
                       vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=ft.padding.symmetric(horizontal=4, vertical=2),
                    data=food,
                )
                self._food_rows[food] = row
                self._foods_col.controls.append(row)
                self._cat_rows[cat_lbl][1].append(food)

        return ft.Container(
            content=self._foods_col,
            height=320,
            bgcolor=BG_CARD2,
            border_radius=8,
            padding=ft.Padding.all(4),
        )

    def _on_food_check(self, e):
        food = e.control.data
        self.chk_states[food] = e.control.value
        self._update_counter()
        self._safe_update()

    def _filter_foods(self):
        if not self._foods_col:
            return
        q = self.search_query
        for cat_lbl, (hdr, foods) in self._cat_rows.items():
            visible = 0
            for fname in foods:
                row = self._food_rows.get(fname)
                if not row:
                    continue
                show = not q or q in fname.lower()
                row.visible = show
                if show:
                    visible += 1
            hdr.visible = (visible > 0)

    def _build_food_actions(self) -> ft.Column:
        self._bl_count_text = ft.Text("", size=10, color=TEXT_MUTED)
        self._update_bl_label()

        n_restored = sum(1 for f, v in self.chk_states.items()
                         if v and f not in self.blacklist)
        fav_info = ft.Text(
            f"({n_restored} favoris restaurés)" if n_restored else "",
            size=9, color=TEXT_MUTED,
        )
        self._fav_info = fav_info

        return ft.Row([
            mk_btn("☑ Tout cocher",   lambda e: self._check_all(True),
                   color=ACCENT,      hover=ACCENT_HOVER, width=140, height=34),
            mk_btn("✕ Décocher",      lambda e: self._check_all(False),
                   color=BG_INPUT,    hover=GRAY_HVR,     width=110, height=34),
            mk_btn("💾 Sauver",       lambda e: self._save_food_prefs(),
                   color=BG_INPUT,    hover=GRAY_HVR,     width=100, height=34),
            mk_btn("📂 Charger",      lambda e: self._load_food_prefs(),
                   color=BG_INPUT,    hover=GRAY_HVR,     width=100, height=34),
            mk_btn("🚫 Masqués",      lambda e: self._open_blacklist_dlg(),
                   color=BG_INPUT,    hover=GRAY_HVR,     width=110, height=34),
        ], spacing=6, wrap=True)

    def _check_all(self, val: bool):
        for food in self.chk_states:
            self.chk_states[food] = val
        # Mettre à jour les checkboxes visuelles
        if self._foods_col:
            for ctrl in self._foods_col.controls:
                if isinstance(ctrl, ft.Container) and ctrl.content:
                    row = ctrl.content
                    if isinstance(row, ft.Row) and row.controls:
                        chk = row.controls[0]
                        if isinstance(chk, ft.Checkbox) and chk.data in self.chk_states:
                            chk.value = val
        self._update_counter()
        self._safe_update()

    def _load_food_prefs(self):
        try:
            from data import db as _db
            raw = _db.settings_get(self.app_state, "selected_foods", "")
            if not raw:
                self._snack("⚠️ Aucun favori sauvegardé.", WARNING)
                return
            saved = set(json.loads(raw))
            n = 0
            for food, _ in self.chk_states.items():
                v = food in saved
                self.chk_states[food] = v
                if v:
                    n += 1
            # Sync checkboxes
            if self._foods_col:
                for ctrl in self._foods_col.controls:
                    if isinstance(ctrl, ft.Container) and isinstance(ctrl.content, ft.Row):
                        row = ctrl.content
                        if row.controls and isinstance(row.controls[0], ft.Checkbox):
                            chk = row.controls[0]
                            chk.value = self.chk_states.get(chk.data, False)
            self._update_counter()
            self._snack(f"✔ {n} favoris chargés.", SUCCESS)
            self._safe_update()
        except Exception as ex:
            log_exc("_load_favorites")
            self._snack(f"Erreur : {ex}", DANGER)

    def _update_bl_label(self):
        if not self._bl_count_text:
            return
        n = len(self.blacklist)
        if n:
            self._bl_count_text.value  = f"🚫 {n} aliment{'s' if n>1 else ''} masqué{'s' if n>1 else ''}"
            self._bl_count_text.color  = DANGER
        else:
            self._bl_count_text.value = ""

    def _open_blacklist_dlg(self):
        """Dialog gestion blacklist — port de _open_blacklist_manager ERAGROK."""
        bl_items: list[ft.Control] = []

        def _restore(food: str, row: ft.Control):
            self.blacklist.discard(food)
            self._save_blacklist()
            row.visible = False
            self._update_bl_label()
            self._safe_update()

        if self.blacklist:
            bl_items.append(
                ft.Text(f"  {len(self.blacklist)} aliment(s) masqué(s) — clic pour restaurer :",
                        size=10, color=TEXT_SUB)
            )
            for bf in sorted(self.blacklist):
                r = ft.Row([
                    ft.Text(f"🚫  {bf}", size=11, color=TEXT_MUTED, expand=True),
                    mk_btn("✓ Restaurer", None,
                           color=SUCCESS, hover=SUCCESS_HVR, width=100, height=26),
                ], spacing=6)
                # Bind correct après création
                btn = r.controls[-1]
                btn.on_click = lambda e, f=bf, rw=r: _restore(f, rw)
                bl_items.append(r)
        else:
            bl_items.append(
                ft.Text("  ✅  Aucun aliment masqué.", size=10, color=SUCCESS)
            )

        bl_items.append(mk_sep())

        # Section "masquer un aliment"
        bl_items.append(
            ft.Text("  Masquer un aliment (ne sera plus proposé) :",
                    size=10, color=TEXT_SUB)
        )
        hide_search = ft.TextField(
            hint_text="🔍 Rechercher...",
            height=32, bgcolor=BG_INPUT, color=TEXT,
            border_color=BORDER, text_size=11,
            hint_style=ft.TextStyle(color=TEXT_MUTED),
        )
        hide_col = ft.Column([], spacing=2, scroll=ft.ScrollMode.AUTO, height=200)

        def _do_hide(food: str, row: ft.Control):
            self.blacklist.add(food)
            self._save_blacklist()
            row.visible = False
            # Masquer dans la liste principale
            if food in self._food_rows:
                self._food_rows[food].visible = False
            self.chk_states[food] = False
            self._update_bl_label()
            self._update_counter()
            self._safe_update()

        hide_rows: dict[str, ft.Control] = {}
        for food in sorted(FOOD_DB_EXT.keys()):
            if food in self.blacklist:
                continue
            hr = ft.Row([
                ft.Text(food, size=10, color=TEXT, expand=True),
                mk_btn("🚫", None, color=DANGER, hover=DANGER_HVR, width=36, height=22),
            ], spacing=4)
            hr.controls[-1].on_click = lambda e, f=food, r=hr: _do_hide(f, r)
            hide_col.controls.append(hr)
            hide_rows[food] = hr

        def _filter_hide(e):
            q = (e.control.value or "").strip().lower()
            for fn, rw in hide_rows.items():
                rw.visible = (not q or q in fn.lower())
            self._safe_update()

        hide_search.on_change = _filter_hide
        bl_items += [hide_search, hide_col]

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("🚫  ALIMENTS MASQUÉS", color=ACCENT,
                          weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column(bl_items, spacing=6, scroll=ft.ScrollMode.AUTO),
                width=480, height=500,
            ),
            actions=[
                ft.TextButton(content=ft.Text("Fermer", color=TEXT_MUTED), on_click=lambda e: self._close_dlg(dlg)),
            ],
        )
        self.page.dialog = dlg
        dlg.open = True
        self._safe_update()

    # ── Zone accepter ─────────────────────────────────────────────────────────

    def _build_accept_zone(self) -> ft.Column:
        self._accept_col = ft.Column([], spacing=0)
        return self._accept_col

    def _show_accept_btn(self):
        if not self._accept_col:
            return
        self._accept_col.controls.clear()
        self._accept_col.controls.append(
            ft.Container(
                content=mk_btn("✅  ACCEPTER LE PLAN", self._do_accept,
                               color=SUCCESS, hover=SUCCESS_HVR,
                               width=260, height=44),
                alignment=ft.Alignment(0, 0),
                padding=ft.padding.only(top=4, bottom=8),
            )
        )
        self._safe_update()

    def _do_accept(self, e=None):
        lp = self._last_plan
        if not lp:
            return
        try:
            from data import utils, db as _db
            plan_lp = lp.get("plan")
            days_lp = lp.get("days")
            tc = tp = tg = tl = 0.0
            if plan_lp:
                tc = sum(m["tot_cal"] for m in plan_lp)
                tp = sum(m["tot_p"]   for m in plan_lp)
                tg = sum(m["tot_g"]   for m in plan_lp)
                tl = sum(m["tot_l"]   for m in plan_lp)
            elif days_lp:
                n  = len(days_lp)
                tc = sum(sum(m["tot_cal"] for m in d["plan"]) for d in days_lp) / n
                tp = sum(sum(m["tot_p"]   for m in d["plan"]) for d in days_lp) / n
                tg = sum(sum(m["tot_g"]   for m in d["plan"]) for d in days_lp) / n
                tl = sum(sum(m["tot_l"]   for m in d["plan"]) for d in days_lp) / n

            ui   = self.app_state.get("user_info") or {}
            dn   = ui.get("date_naissance", "")
            age  = str(utils.age_depuis_naissance(dn) or ui.get("age") or "")
            poids = str(ui.get("poids", ""))
            n_m  = lp.get("n_meals", 4)

            _db.nutrition_insert(
                self.app_state,
                datetime.date.today().strftime("%d/%m/%Y"),
                poids, age,
                str(round(tc)), str(round(tp)),
                str(round(tg)), str(round(tl)),
                f"Plan alimentaire — {n_m} repas",
            )
            # Persister plan complet
            _mode     = "jour"
            plan_data = plan_lp
            if days_lp:
                _mode = "semaine" if len(days_lp) == 7 else f"{len(days_lp)}j"
                serializable = []
                for d in days_lp:
                    sd = dict(d)
                    if "date" in sd and hasattr(sd["date"], "isoformat"):
                        sd["date"] = sd["date"].isoformat()
                    serializable.append(sd)
                plan_data = serializable
            _db.meal_plan_insert(
                self.app_state,
                date=datetime.date.today().isoformat(),
                mode=_mode, n_meals=n_m,
                cal=lp.get("cal", 0), prot=lp.get("prot", 0),
                gluc=lp.get("gluc", 0), lip=lp.get("lip", 0),
                adj_label=lp.get("adj", ""),
                plan_json=json.dumps(plan_data, ensure_ascii=False),
                accepted=True,
                budget_w=lp.get("budget_w", 0) or 0,
            )
            # Mettre à jour app_state pour le dashboard
            self.app_state["last_meal_plan"] = {
                "plan": plan_lp or (days_lp[0]["plan"] if days_lp else []),
                "cal": tc, "prot": tp, "gluc": tg, "lip": tl,
            }
            self._snack("✅ Plan accepté et enregistré.", SUCCESS)
            if self.on_show_nutrition:
                self.on_show_nutrition()
        except Exception as ex:
            log_exc("_on_accept_plan")
            self._snack(f"Erreur : {ex}", DANGER)

    # ── Panneau droit — résultats ─────────────────────────────────────────────

    def _build_result_panel(self) -> ft.Container:
        self._result_col = ft.Column([
            ft.Container(
                content=ft.Text(
                    "📌  Coche tes aliments → choisis le mode → GÉNÉRER.",
                    size=12, color=TEXT_MUTED,
                ),
                bgcolor=BG_CARD, border_radius=R_CARD,
                border=ft.border.all(1, BORDER),
                padding=ft.padding.symmetric(horizontal=16, vertical=24),
            ),
        ], spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)

        return ft.Container(
            content=self._result_col,
            expand=True,
        )

    # ══════════════════════════════════════════════════════════════════════════
    #  GÉNÉRATION
    # ══════════════════════════════════════════════════════════════════════════

    def _on_generate(self, e=None):
        selected = [f for f, v in self.chk_states.items() if v]
        if len(selected) < 2:
            self._set_result([
                ft.Container(
                    content=ft.Text("⚠️  Sélectionne au moins 2 aliments.",
                                    size=12, color=DANGER),
                    bgcolor=BG_CARD, border_radius=R_CARD,
                    border=ft.border.all(1, BORDER),
                    padding=ft.padding.symmetric(horizontal=16, vertical=20),
                )
            ])
            return

        # Auto-save préférences
        try:
            from data import db as _db
            _db.settings_set(self.app_state, "selected_foods",
                             json.dumps(selected, ensure_ascii=False))
        except Exception:
            pass

        cal, prot, gluc, lip = self._get_macros()
        adj_txt = (self.app_state.get("user_info") or {}).get(
            "ajustement", "Maintien (0%)")

        # Indicateur progression
        self._set_result([
            ft.Container(
                content=ft.Text("⏳  Génération en cours...",
                                size=12, color=ACCENT_GLOW),
                bgcolor=BG_CARD, border_radius=R_CARD,
                padding=ft.padding.symmetric(horizontal=16, vertical=20),
            )
        ])

        if self.gen_mode == "jour":
            day_off = random.randint(0, 27)
            plan = _generate_meal_plan(self.n_meals, selected,
                                       cal, prot, gluc, lip,
                                       day_offset=day_off)
            if self.budget_w:
                plan = _apply_budget_pass(plan, selected,
                                          self.budget_w / 7, self.app_state)

            self._last_plan = {
                "plan": plan, "n_meals": self.n_meals,
                "cal": cal, "prot": prot, "gluc": gluc, "lip": lip,
                "adj": adj_txt, "multiday": False,
                "budget_w": self.budget_w,
            }
            self._render_day_result(plan, adj_txt, cal, prot, gluc, lip,
                                    self.budget_w)

        else:
            n_days = 7 if self.gen_mode == "semaine" else 30
            days = _generate_multiday_plan(n_days, self.n_meals, selected,
                                           cal, prot, gluc, lip,
                                           self.start_date)
            if self.budget_w:
                budget_day = self.budget_w / 7
                for d in days:
                    d["plan"] = _apply_budget_pass(
                        d["plan"], selected, budget_day, self.app_state)

            self._last_plan = {
                "days": days, "n_meals": self.n_meals,
                "cal": cal, "prot": prot, "gluc": gluc, "lip": lip,
                "adj": adj_txt, "multiday": True,
                "budget_w": self.budget_w,
            }
            self._render_multiday_result(days, adj_txt,
                                         cal, prot, gluc, lip,
                                         self.budget_w)

        self._show_accept_btn()

    # ══════════════════════════════════════════════════════════════════════════
    #  RENDU — 1 JOUR
    # ══════════════════════════════════════════════════════════════════════════

    def _render_day_result(self, plan: list, adj_lbl: str,
                           cal: float, prot: float, gluc: float, lip: float,
                           budget_w: float | None = None,
                           date_lbl: str | None = None):
        tc  = sum(m["tot_cal"] for m in plan)
        tp  = sum(m["tot_p"]   for m in plan)
        tg  = sum(m["tot_g"]   for m in plan)
        tl  = sum(m["tot_l"]   for m in plan)
        tf  = sum(_fiber_for(i["food"], i["g"]) for m in plan for i in m["items"])

        macros_row = _build_macro_boxes([
            ("🔥 Calories",  tc, cal,  "kcal"),
            ("🥩 Protéines", tp, prot, "g"),
            ("🍚 Glucides",  tg, gluc, "g"),
            ("🥑 Lipides",   tl, lip,  "g"),
        ])
        fib_c = SUCCESS if tf >= 25 else (ACCENT_GLOW if tf >= 15 else TEXT_MUTED)
        fib_box = ft.Container(
            content=ft.Column([
                ft.Text("🌾 Fibres",     size=10, color=TEXT_MUTED),
                ft.Text(f"{tf:.0f} g",   size=14, color=fib_c,
                        weight=ft.FontWeight.BOLD),
                ft.Text("reco. ≥ 25g/j", size=9, color=TEXT_MUTED),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
            bgcolor=BG_CARD2, border_radius=8,
            padding=ft.padding.symmetric(vertical=8, horizontal=6),
            expand=True,
        )

        title_txt = f"📋  {date_lbl or 'PLAN'} — {self.n_meals} repas / {adj_lbl}"
        header_controls: list[ft.Control] = [
            mk_title(title_txt),
            mk_sep(),
            ft.Row([*macros_row.controls, fib_box], spacing=4),
        ]

        # Bilan budget
        if budget_w:
            bgt_ctrl = self._compute_budget_bar(plan, budget_w)
            if bgt_ctrl:
                header_controls.append(bgt_ctrl)

        # Actions
        def _show_shopping(e=None, p=plan):
            from data.shopping import build_shopping_screen
            screen = build_shopping_screen(self.page, self.app_state, p)
            self._set_result([screen])

        def _export_pdf(e=None, p=plan):
            try:
                from data.pdf_utils import export_meal_plan_pdf
                export_meal_plan_pdf(self.app_state, p, page=self.page)
            except Exception as ex:
                log_exc("export_meal_plan_pdf")
                self._snack(f"Erreur PDF : {ex}", DANGER)

        header_controls.append(
            ft.Row([
                mk_btn("🛒  Liste de courses", _show_shopping,
                       color=BG_CARD2, hover=BG_CARD, width=180, height=32),
                mk_btn("📄  Export PDF", _export_pdf,
                       color=GRAY, hover=GRAY_HVR, width=140, height=32),
            ], spacing=8)
        )

        header_card = ft.Container(
            content=ft.Column(header_controls, spacing=8),
            bgcolor=BG_CARD, border_radius=R_CARD,
            border=ft.border.all(1, BORDER),
            padding=ft.padding.symmetric(horizontal=16, vertical=14),
        )

        meal_cards = [header_card]
        for meal in plan:
            meal_cards.append(self._build_meal_card(meal, plan,
                                                     adj_lbl, cal, prot, gluc, lip,
                                                     budget_w, date_lbl))

        self._set_result(meal_cards)

    def _build_meal_card(self, meal: dict, plan: list,
                         adj_lbl: str, cal: float, prot: float,
                         gluc: float, lip: float,
                         budget_w: float | None, date_lbl: str | None) -> ft.Container:
        slot_desc = SLOT_DESC.get(meal.get("type", ""), "")
        items_rows: list[ft.Control] = []

        if not meal.get("items"):
            items_rows.append(
                ft.Text("⚠️  Aucun aliment compatible — coche des aliments de cette catégorie.",
                        size=10, color=DANGER)
            )
        else:
            for item in meal["items"]:
                fib = _fiber_for(item["food"], item["g"])
                fib_s = f"  🌾{fib:.1f}" if fib > 0.1 else ""
                macro_s = (f"{item['g']:.0f}g → {item['kcal']:.0f}kcal | "
                           f"{item['p']:.1f}P  {item['g_']:.1f}G  {item['l']:.1f}L{fib_s}")

                swap_btn = ft.IconButton(
                    icon=ft.Icons.SWAP_HORIZ,
                    icon_color=TEXT_MUTED,
                    icon_size=16,
                    tooltip="Remplacer",
                    data=item,
                    on_click=lambda e, it=item, ml=meal, p=plan: self._open_swap_dlg(
                        it, ml, p, adj_lbl, cal, prot, gluc, lip, budget_w, date_lbl),
                )

                items_rows.append(
                    ft.Row([
                        ft.Container(width=6, height=6,
                                     bgcolor=ACCENT_GLOW, border_radius=3),
                        ft.Text(item["food"], size=11, color=TEXT, expand=True),
                        ft.Text(macro_s, size=9, color=TEXT_MUTED),
                        swap_btn,
                    ], spacing=6,
                       vertical_alignment=ft.CrossAxisAlignment.CENTER)
                )

        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Column([
                        ft.Text(meal.get("name", ""), size=12,
                                color=ACCENT_GLOW, weight=ft.FontWeight.BOLD),
                        ft.Text(slot_desc, size=9, color=TEXT_MUTED),
                    ], spacing=2, expand=True),
                    ft.Text(
                        f"{meal['tot_cal']:.0f} kcal\n"
                        f"{meal['tot_p']:.0f}P · {meal['tot_g']:.0f}G · {meal['tot_l']:.0f}L",
                        size=9, color=TEXT_SUB,
                        text_align=ft.TextAlign.RIGHT,
                    ),
                ], vertical_alignment=ft.CrossAxisAlignment.START),
                mk_sep(),
                *items_rows,
                ft.Container(height=4),
            ], spacing=4),
            bgcolor=BG_CARD, border_radius=R_CARD,
            border=ft.border.all(1, BORDER),
            padding=ft.padding.symmetric(horizontal=14, vertical=12),
        )

    def _open_swap_dlg(self, item: dict, meal: dict, plan: list,
                       adj_lbl: str, cal: float, prot: float,
                       gluc: float, lip: float,
                       budget_w: float | None, date_lbl: str | None):
        selected = {f for f, v in self.chk_states.items() if v}
        alts = _food_swap_alternatives(item["food"], meal["items"], selected)

        if not alts:
            self._snack("Aucune alternative compatible. Coche plus d'aliments.", WARNING)
            return

        old_k, old_p, old_g, old_l = FOOD_DB_EXT[item["food"]]
        if old_p >= old_g and old_p >= old_l:
            main_macro_idx = 1
        elif old_g >= old_l:
            main_macro_idx = 2
        else:
            main_macro_idx = 3
        old_dominant  = FOOD_DB_EXT[item["food"]][main_macro_idx]
        target_macro  = old_dominant * item["g"] / 100

        alt_rows: list[ft.Control] = [
            ft.Text(
                f"Portion actuelle : {item['g']:.0f}g → {item['kcal']:.0f} kcal | "
                f"{item['p']:.1f}P  {item['g_']:.1f}G  {item['l']:.1f}L",
                size=9, color=TEXT_MUTED,
            ),
            mk_sep(),
        ]

        dlg_ref: list[ft.AlertDialog] = []

        for alt_food, ak, ap, ag, al in alts:
            new_dominant = [ak, ap, ag, al][main_macro_idx]
            new_g = (round(target_macro / (new_dominant / 100))
                     if new_dominant > 0 else round(item["g"]))
            new_g = max(FOOD_MIN_PORTION.get(alt_food, 10),
                        min(FOOD_MAX_PORTION.get(alt_food, FOOD_MAX_DEFAULT), new_g))
            nk, np, ng, nl = (ak*new_g/100, ap*new_g/100,
                              ag*new_g/100, al*new_g/100)
            fib_a = _fiber_for(alt_food, new_g)
            fib_s = f"  🌾{fib_a:.1f}" if fib_a > 0.1 else ""

            def _do_swap(e,
                         f=alt_food, gm=new_g,
                         ck=nk, cp=np, cg=ng, cl=nl):
                item.update({"food": f, "g": gm,
                             "kcal": round(ck,1), "p": round(cp,1),
                             "g_": round(cg,1), "l": round(cl,1)})
                meal["tot_cal"] = sum(x["kcal"] for x in meal["items"])
                meal["tot_p"]   = sum(x["p"]    for x in meal["items"])
                meal["tot_g"]   = sum(x["g_"]   for x in meal["items"])
                meal["tot_l"]   = sum(x["l"]    for x in meal["items"])
                if dlg_ref:
                    self._close_dlg(dlg_ref[0])
                self._render_day_result(plan, adj_lbl,
                                        cal, prot, gluc, lip,
                                        budget_w, date_lbl)

            alt_rows.append(
                ft.Row([
                    mk_btn("↔", _do_swap, color=BG_CARD,
                           hover=ACCENT, width=32, height=26),
                    ft.Text(alt_food, size=11, color=TEXT, expand=True),
                    ft.Text(
                        f"{new_g:.0f}g → {nk:.0f}kcal | "
                        f"{np:.1f}P {ng:.1f}G {nl:.1f}L{fib_s}",
                        size=9, color=TEXT_MUTED,
                    ),
                ], spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER)
            )

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"↔  Remplacer {item['food']}", color=ACCENT,
                          weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column(alt_rows, spacing=6, scroll=ft.ScrollMode.AUTO),
                width=460, height=380,
            ),
            actions=[
                ft.TextButton(content=ft.Text("Annuler", color=TEXT_MUTED), on_click=lambda e: self._close_dlg(dlg)),
            ],
        )
        dlg_ref.append(dlg)
        self.page.dialog = dlg
        dlg.open = True
        self._safe_update()

    # ══════════════════════════════════════════════════════════════════════════
    #  RENDU — MULTI-JOURS
    # ══════════════════════════════════════════════════════════════════════════

    def _render_multiday_result(self, days: list, adj_lbl: str,
                                cal: float, prot: float,
                                gluc: float, lip: float,
                                budget_w: float | None = None):
        n_days   = len(days)
        mode_lbl = "Semaine" if n_days == 7 else f"{n_days} jours"

        avg_cal  = sum(sum(m["tot_cal"] for m in d["plan"]) for d in days) / n_days
        avg_prot = sum(sum(m["tot_p"]   for m in d["plan"]) for d in days) / n_days
        avg_gluc = sum(sum(m["tot_g"]   for m in d["plan"]) for d in days) / n_days
        avg_lip  = sum(sum(m["tot_l"]   for m in d["plan"]) for d in days) / n_days
        avg_fib  = sum(
            sum(_fiber_for(i["food"], i["g"])
                for m in d["plan"] for i in m["items"])
            for d in days
        ) / n_days

        macros_row = _build_macro_boxes([
            ("🔥 Cal. moy.",  avg_cal,  cal,  "kcal"),
            ("🥩 Prot. moy.", avg_prot, prot, "g"),
            ("🍚 Gluc. moy.", avg_gluc, gluc, "g"),
            ("🥑 Lip. moy.",  avg_lip,  lip,  "g"),
        ])
        fib_c = SUCCESS if avg_fib >= 25 else (ACCENT_GLOW if avg_fib >= 15 else TEXT_MUTED)
        fib_box = ft.Container(
            content=ft.Column([
                ft.Text("🌾 Fib. moy.",   size=10, color=TEXT_MUTED),
                ft.Text(f"{avg_fib:.0f} g", size=14, color=fib_c,
                        weight=ft.FontWeight.BOLD),
                ft.Text("reco. ≥ 25g/j",  size=9,  color=TEXT_MUTED),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
            bgcolor=BG_CARD2, border_radius=8,
            padding=ft.padding.symmetric(vertical=8, horizontal=6),
            expand=True,
        )

        # Score diversité
        div = compute_diversity_score(days)
        RATING_CONF = {
            "excellent": ("🏆", SUCCESS),
            "bon":       ("👍", ACCENT_GLOW),
            "moyen":     ("⚠️", WARNING),
            "faible":    ("❌", DANGER),
        }
        ico, clr_d = RATING_CONF.get(div["rating"], ("❓", TEXT_MUTED))

        streak_alerts: list[ft.Control] = []
        for food, d_start, d_end, length in div.get("streak_alerts", []):
            streak_alerts.append(
                ft.Container(
                    content=ft.Text(
                        f"⚠️  {food} en protéine principale {length}j d'affilée (J{d_start}→J{d_end})",
                        size=9, color=WARNING,
                    ),
                    bgcolor="#1a1000", border_radius=6,
                    padding=ft.padding.symmetric(horizontal=10, vertical=4),
                )
            )

        header_controls: list[ft.Control] = [
            mk_title(f"📅  PLAN {mode_lbl.upper()} — {self.n_meals} repas/j — {adj_lbl}"),
            mk_sep(),
            ft.Row([*macros_row.controls, fib_box], spacing=4),
            ft.Text(
                f"{ico}  Diversité : {div['score']:.0f}%  "
                f"({div['unique']} aliments uniques / {div['total']} portions)",
                size=10, color=clr_d,
            ),
            *streak_alerts,
        ]

        # Budget multiday
        if budget_w:
            bgt_ctrl = self._compute_multiday_budget_bar(days, budget_w)
            if bgt_ctrl:
                header_controls.append(bgt_ctrl)

        # Bouton liste de courses multiday
        def _show_shopping_multi(e=None, d=days):
            from data.shopping import build_shopping_screen
            screen = build_shopping_screen(self.page, self.app_state, d)
            self._set_result([screen])

        def _export_pdf_multi(e=None, d=days):
            try:
                from data.pdf_utils import export_multiday_plan_pdf
                export_multiday_plan_pdf(self.app_state, d, page=self.page)
            except Exception as ex:
                log_exc("export_multiday_plan_pdf")
                self._snack(f"Erreur PDF : {ex}", DANGER)

        header_controls.append(
            ft.Row([
                mk_btn(f"🛒  Liste de courses ({n_days}j)", _show_shopping_multi,
                       color=BG_CARD2, hover=BG_CARD, width=220, height=32),
                mk_btn("📄  Export PDF", _export_pdf_multi,
                       color=GRAY, hover=GRAY_HVR, width=140, height=32),
            ], spacing=8)
        )

        header_card = ft.Container(
            content=ft.Column(header_controls, spacing=8),
            bgcolor=BG_CARD, border_radius=R_CARD,
            border=ft.border.all(1, BORDER),
            padding=ft.padding.symmetric(horizontal=16, vertical=14),
        )

        # Navigation onglets jours
        self._active_day = 0
        self._nav_tab_btns = []
        self._day_content  = ft.Column([], spacing=8, scroll=ft.ScrollMode.AUTO)

        tabs: list[ft.Control] = []
        for i, d in enumerate(days):
            day_abbr = DAY_SHORT[d["date"].weekday()]
            day_num  = d["date"].strftime("%d")
            is_sel   = (i == 0)
            btn = ft.ElevatedButton(
                content=ft.Text(f"{day_abbr}\n{day_num}", size=11,
                                weight=ft.FontWeight.BOLD,
                                color="#000" if is_sel else TEXT_MUTED,
                                text_align=ft.TextAlign.CENTER),
                on_click=lambda e, idx=i, ds=days: self._show_day(idx, ds, adj_lbl,
                                                                   cal, prot, gluc, lip,
                                                                   budget_w),
                style=ft.ButtonStyle(
                    bgcolor={ft.ControlState.DEFAULT: ACCENT if is_sel else BG_CARD},
                    padding=ft.padding.symmetric(horizontal=6, vertical=4),
                    shape=ft.RoundedRectangleBorder(radius=8),
                ),
                data=i,
                width=44, height=44,
            )
            tabs.append(btn)
            self._nav_tab_btns.append(btn)

        tabs_row = ft.Container(
            content=ft.Row(tabs, spacing=4, scroll=ft.ScrollMode.AUTO),
            bgcolor=BG_CARD2, border_radius=8,
            padding=ft.padding.symmetric(horizontal=6, vertical=4),
        )

        # Afficher jour 0
        self._show_day(0, days, adj_lbl, cal, prot, gluc, lip, budget_w)

        self._set_result([
            header_card,
            tabs_row,
            self._day_content,
        ])

    def _show_day(self, idx: int, days: list,
                  adj_lbl: str, cal: float, prot: float,
                  gluc: float, lip: float, budget_w: float | None):
        self._active_day = idx
        # Mettre à jour couleurs onglets
        for btn in self._nav_tab_btns:
            sel = (btn.data == idx)
            btn.style = ft.ButtonStyle(
                bgcolor={ft.ControlState.DEFAULT: ACCENT if sel else BG_CARD},
                color={ft.ControlState.DEFAULT: "#000" if sel else TEXT_MUTED},
                padding=ft.padding.symmetric(horizontal=6, vertical=4),
                shape=ft.RoundedRectangleBorder(radius=8),
            )

        d    = days[idx]
        plan = d["plan"]
        tc   = sum(m["tot_cal"] for m in plan)
        tp   = sum(m["tot_p"]   for m in plan)
        tg   = sum(m["tot_g"]   for m in plan)
        tl   = sum(m["tot_l"]   for m in plan)
        tf   = sum(_fiber_for(i["food"], i["g"]) for m in plan for i in m["items"])

        macros_row = _build_macro_boxes([
            ("🔥 Calories",  tc, cal,  "kcal"),
            ("🥩 Protéines", tp, prot, "g"),
            ("🍚 Glucides",  tg, gluc, "g"),
            ("🥑 Lipides",   tl, lip,  "g"),
        ])
        fib_c = SUCCESS if tf >= 25 else (ACCENT_GLOW if tf >= 15 else TEXT_MUTED)
        fib_box = ft.Container(
            content=ft.Column([
                ft.Text("🌾 Fibres",     size=10, color=TEXT_MUTED),
                ft.Text(f"{tf:.0f} g",   size=14, color=fib_c,
                        weight=ft.FontWeight.BOLD),
                ft.Text("reco. ≥ 25g/j", size=9, color=TEXT_MUTED),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
            bgcolor=BG_CARD2, border_radius=8,
            padding=ft.padding.symmetric(vertical=8, horizontal=6),
            expand=True,
        )

        day_header = ft.Container(
            content=ft.Column([
                mk_title(f"📋  {d['label']} — {self.n_meals} repas / {adj_lbl}"),
                mk_sep(),
                ft.Row([*macros_row.controls, fib_box], spacing=4),
            ], spacing=8),
            bgcolor=BG_CARD, border_radius=R_CARD,
            border=ft.border.all(1, BORDER),
            padding=ft.padding.symmetric(horizontal=16, vertical=12),
        )

        meal_cards = [day_header]
        for meal in plan:
            meal_cards.append(
                self._build_meal_card(meal, plan, adj_lbl,
                                      cal, prot, gluc, lip,
                                      budget_w, d["label"])
            )

        if self._day_content is not None:
            self._day_content.controls.clear()
            self._day_content.controls.extend(meal_cards)
        self._safe_update()

    # ── Budget helpers ────────────────────────────────────────────────────────

    def _compute_budget_bar(self, plan: list,
                            budget_w: float) -> ft.Control | None:
        try:
            from data.prices_module import compute_shopping_cost
            tmp: dict = {}
            for meal in plan:
                for it in meal.get("items", []):
                    f  = it.get("food", "")
                    gr = it.get("g", it.get("grams", 0)) * COOKED_TO_RAW.get(f, 1.0)
                    tmp[f] = tmp.get(f, 0.0) + gr
            fake_shop  = {"Repas": [(f, g, f"{g:.0f}g", "") for f, g in tmp.items()]}
            costs      = compute_shopping_cost(fake_shop, self.app_state)
            day_cost   = costs["total"]
            week_cost  = day_cost * 7
            return _build_budget_bar(week_cost, budget_w, day_cost)
        except Exception:
            return None

    def _compute_multiday_budget_bar(self, days: list,
                                     budget_w: float) -> ft.Control | None:
        try:
            from data.prices_module import compute_shopping_cost
            day_costs = []
            for d in days:
                fake_shop = {"Repas": [
                    (it.get("food", ""),
                     it.get("g", it.get("grams", 0)) * COOKED_TO_RAW.get(it.get("food", ""), 1.0),
                     "", "")
                    for meal in d["plan"]
                    for it in meal.get("items", [])
                ]}
                day_costs.append(compute_shopping_cost(fake_shop, self.app_state)["total"])
            avg_day  = sum(day_costs) / len(day_costs) if day_costs else 0
            week_est = avg_day * 7
            return _build_budget_bar(week_est, budget_w, avg_day)
        except Exception:
            return None

    # ── Helpers UI ────────────────────────────────────────────────────────────

    def _set_result(self, controls: list[ft.Control]):
        if self._result_col is not None:
            self._result_col.controls.clear()
            self._result_col.controls.extend(controls)
        self._safe_update()

    def _close_dlg(self, dlg: ft.AlertDialog):
        dlg.open = False
        self._safe_update()

    def _snack(self, msg: str, color: str = SUCCESS):
        from ui.snackbar import snack, _LEVEL_COLORS
        _col_to_level = {v: k for k, v in _LEVEL_COLORS.items()}
        level = _col_to_level.get(color, "success")
        snack(self.page, msg, level)

    def _safe_update(self):
        from ui.page_utils import safe_update
        safe_update(self.page)


# ══════════════════════════════════════════════════════════════════════════════
#  POINT D'ENTRÉE PUBLIC
# ══════════════════════════════════════════════════════════════════════════════

def build_meal_generator_screen(page: ft.Page, app_state: dict,
                                on_show_nutrition: Callable | None = None) -> ft.Column:
    """
    Construit et retourne l'écran générateur de plan alimentaire.
    on_show_nutrition : callback appelé après acceptation du plan.
    """
    view = MealGeneratorView(page, app_state, on_show_nutrition)
    return view.get_view()
