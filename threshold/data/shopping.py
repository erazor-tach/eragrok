# features/shopping.py — THRESHOLD · Liste de courses (Flet)
# ─────────────────────────────────────────────────────────────────────────────
# Port de show_shopping_list + _render_shopping_content (features_module.py ERAGROK)
# Logique identique, UI reconstruite en Flet mobile-first.
# Point d'entrée : build_shopping_screen(page, app_state, plans_or_plan)
# ─────────────────────────────────────────────────────────────────────────────
from __future__ import annotations
import datetime

import flet as ft

from ui.theme import (
    ACCENT, ACCENT_DIM, ACCENT_GLOW, ACCENT_HOVER,
    BG_CARD, BG_CARD2, BG_INPUT, BG_ROOT,
    BORDER, BLUE, BLUE_HVR, DANGER, DANGER_HVR,
    GRAY, GRAY_HVR, SUCCESS, SUCCESS_HVR,
    TEXT, TEXT_MUTED, TEXT_SUB,
    R_CARD, R_INPUT,
    mk_btn, mk_sep, mk_title,
)
from data.meal_engine import compute_shopping_list


# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS — segmentation identique ERAGROK
# ══════════════════════════════════════════════════════════════════════════════

def _build_segments(plans_or_plan: list) -> list[tuple[str, list]]:
    """
    Découpe le plan en segments (onglets) selon sa durée.
    Retourne [(label, days_slice), ...]
    Identique à la logique show_shopping_list ERAGROK.
    """
    # Normaliser en liste de {date, plan}
    if (plans_or_plan and isinstance(plans_or_plan[0], dict)
            and "plan" in plans_or_plan[0]):
        all_days = plans_or_plan
    else:
        today = datetime.date.today()
        all_days = [{"date": today, "label": today.strftime("%d/%m/%Y"),
                     "plan": plans_or_plan}]

    n = len(all_days)
    segments: list[tuple[str, list]] = []

    if n == 1:
        d0 = all_days[0].get("date", datetime.date.today())
        if hasattr(d0, "strftime"):
            lbl = f"📅 {d0.strftime('%d/%m')}"
        else:
            lbl = "📅 Aujourd'hui"
        segments.append((lbl, all_days))
    else:
        n_full = n // 7
        leftover = n % 7
        for w in range(n_full):
            sl = all_days[w * 7:(w + 1) * 7]
            d0 = sl[0].get("date", datetime.date.today())
            d1 = sl[-1].get("date", d0)
            d0s = d0.strftime("%d/%m") if hasattr(d0, "strftime") else "?"
            d1s = d1.strftime("%d/%m") if hasattr(d1, "strftime") else "?"
            segments.append((f"Sem.{w+1} {d0s}–{d1s}", sl))
        if leftover:
            sl = all_days[n_full * 7:]
            d0 = sl[0].get("date", datetime.date.today())
            d1 = sl[-1].get("date", d0)
            d0s = d0.strftime("%d/%m") if hasattr(d0, "strftime") else "?"
            d1s = d1.strftime("%d/%m") if hasattr(d1, "strftime") else "?"
            segments.append((f"Sem.{n_full+1} {d0s}–{d1s}", sl))
        total_lbl = "Mois entier" if n >= 28 else f"Total {n}j"
        segments.append((total_lbl, all_days))

    return segments


# ══════════════════════════════════════════════════════════════════════════════
#  RENDU LISTE DE COURSES — port de _render_shopping_content
# ══════════════════════════════════════════════════════════════════════════════

def _build_shopping_controls(shopping: dict, period_lbl: str,
                              app_state: dict) -> list[ft.Control]:
    """
    Construit la liste de contrôles Flet pour une liste de courses.
    Port direct de _render_shopping_content ERAGROK.
    """
    if not shopping:
        return [ft.Text("Aucun aliment pour cette période.",
                        size=13, color=TEXT_MUTED)]

    # Calcul des coûts
    costs = None
    _cost_err = ""
    try:
        from data.prices_module import compute_shopping_cost, ensure_prices_loaded

        class _FakeApp:
            def __init__(self, cu):
                self.current_user = cu
        fake_app = _FakeApp(app_state.get("current_user", "default"))
        ensure_prices_loaded(fake_app)
        costs = compute_shopping_cost(shopping, fake_app)
    except Exception as _ex:
        _cost_err = str(_ex)

    controls: list[ft.Control] = []

    # ── Ligne résumé ─────────────────────────────────────────────────────────
    total_items = sum(len(v) for v in shopping.values())
    summary_parts: list[ft.Control] = [
        ft.Text(f"{total_items} aliments — {period_lbl}",
                size=11, color=TEXT_MUTED, expand=True),
    ]
    if costs and costs["total"] > 0:
        n_f = costs["nb_prices_found"]
        n_t = costs["nb_total"]
        summary_parts.append(
            ft.Text(f"≈ {costs['total']:.2f} €  ({n_f}/{n_t} prix)",
                    size=12, color=SUCCESS, weight=ft.FontWeight.BOLD)
        )
    elif _cost_err:
        summary_parts.append(
            ft.Text(f"⚠ prix: {_cost_err[:60]}", size=10, color="#ff6b6b")
        )
    controls.append(
        ft.Container(
            content=ft.Row(summary_parts, spacing=8),
            padding=ft.padding.symmetric(horizontal=4, vertical=6),
        )
    )

    # ── Cartes par catégorie ──────────────────────────────────────────────────
    for cat, items in shopping.items():
        if not items:
            continue

        cat_cost = costs["by_cat"].get(cat, 0) if costs else 0
        info_str = f"{len(items)} art."
        if cat_cost > 0:
            info_str += f"  ≈ {cat_cost:.2f} €"

        # En-tête catégorie
        cat_hdr = ft.Container(
            content=ft.Row([
                ft.Text(cat, size=12, color=ACCENT_GLOW,
                        weight=ft.FontWeight.BOLD, expand=True),
                ft.Text(info_str, size=10, color=TEXT_MUTED),
            ], spacing=8),
            bgcolor=BG_CARD2,
            border_radius=8,
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
        )

        # Lignes aliments
        item_rows: list[ft.Control] = [cat_hdr]
        for food, g_raw, label, note in items:
            item_cost = costs["by_item"].get(food, 0) if costs else 0
            right_parts: list[ft.Control] = []
            if item_cost > 0:
                right_parts.append(
                    ft.Text(f"≈ {item_cost:.2f} €", size=10, color=TEXT_MUTED)
                )
            right_parts.append(
                ft.Text(label, size=12, color=ACCENT, weight=ft.FontWeight.BOLD)
            )

            food_lbl = food
            if note:
                food_lbl = f"{food}  {note}"

            item_rows.append(
                ft.Container(
                    content=ft.Row([
                        ft.Container(
                            width=6, height=6, bgcolor=TEXT_MUTED,
                            border_radius=3,
                        ),
                        ft.Text(food_lbl, size=12, color=TEXT, expand=True),
                        *right_parts,
                    ], spacing=8,
                       vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=ft.padding.symmetric(horizontal=12, vertical=4),
                )
            )

        controls.append(
            ft.Container(
                content=ft.Column(item_rows, spacing=2),
                bgcolor=BG_CARD,
                border_radius=R_CARD,
                border=ft.border.all(1, BORDER),
                padding=ft.padding.symmetric(vertical=6),
                margin=ft.margin.only(bottom=6),
            )
        )

    # ── Bandeau total ─────────────────────────────────────────────────────────
    if costs and costs["total"] > 0:
        controls.append(
            ft.Container(
                content=ft.Row([
                    ft.Column([
                        ft.Text("TOTAL ESTIMÉ", size=10, color=TEXT_MUTED),
                        ft.Text("Open Food Facts + prix marché France 2025",
                                size=9, color=TEXT_MUTED),
                    ], spacing=2, expand=True),
                    ft.Text(f"≈ {costs['total']:.2f} €",
                            size=18, color=SUCCESS, weight=ft.FontWeight.BOLD),
                ], spacing=12,
                   vertical_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=BG_CARD2,
                border_radius=R_CARD,
                padding=ft.padding.symmetric(horizontal=16, vertical=12),
            )
        )

    return controls


# ══════════════════════════════════════════════════════════════════════════════
#  VUE PRINCIPALE — ShoppingView
# ══════════════════════════════════════════════════════════════════════════════

class ShoppingView:
    """
    Écran liste de courses complet :
    - Navigation par onglets (jour / semaines / total)
    - Contenu scroll par segment
    - MAJ prix, Export JSON
    """

    def __init__(self, page: ft.Page, app_state: dict, plans_or_plan: list):
        self.page       = page
        self.app_state  = app_state
        self.segments   = _build_segments(plans_or_plan)
        self._seg_idx   = 0
        self._content_col: ft.Column | None = None
        self._nav_btns:   list[ft.TextButton] = []

    def get_view(self) -> ft.Column:
        if not self.segments:
            return ft.Column([
                ft.Text("Aucun aliment dans le plan.", color=TEXT_MUTED)
            ])

        # ── Barre navigation onglets ──────────────────────────────────────────
        self._nav_btns = []
        nav_row = ft.Row([], spacing=6, scroll=ft.ScrollMode.ALWAYS)
        for i, (lbl, _) in enumerate(self.segments):
            btn = ft.ElevatedButton(
                content=ft.Text(lbl, size=13, weight=ft.FontWeight.BOLD,
                                color="#000000" if i == 0 else TEXT_MUTED),
                on_click=lambda e, idx=i: self._select_segment(idx),
                style=ft.ButtonStyle(
                    bgcolor={ft.ControlState.DEFAULT: ACCENT if i == 0 else BG_CARD2},
                    padding=ft.padding.symmetric(horizontal=12, vertical=8),
                    shape=ft.RoundedRectangleBorder(radius=10),
                ),
            )
            self._nav_btns.append(btn)
            nav_row.controls.append(btn)

        nav_container = ft.Container(
            content=ft.Column([
                ft.Container(
                    content=nav_row,
                    height=52,
                ),
            ], spacing=0),
            bgcolor=BG_CARD2,
            padding=ft.padding.symmetric(horizontal=8, vertical=6),
            border_radius=10,
            height=74,  # boutons (52) + scrollbar (~14) + paddings (8)
        )

        # ── Zone contenu ──────────────────────────────────────────────────────
        self._content_col = ft.Column([], spacing=4, scroll=ft.ScrollMode.AUTO)

        # ── Barre actions ─────────────────────────────────────────────────────
        action_row = ft.Row([
            mk_btn("🔄 MAJ prix", self._on_refresh_prices,
                   color=BLUE, hover=BLUE_HVR, width=130, height=36),
            mk_btn("📄 Export PDF", self._on_export_pdf,
                   color=GRAY, hover=GRAY_HVR, width=140, height=36),
            mk_btn("📤 Export JSON", self._on_export_json,
                   color=ACCENT_DIM, hover=ACCENT_HOVER, width=140, height=36),
        ], spacing=8, wrap=True)

        # Afficher premier segment
        self._select_segment(0)

        return ft.Column([
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text("🛒  LISTE DE COURSES", size=16, color=ACCENT,
                                weight=ft.FontWeight.BOLD, expand=True),
                        ft.Text("Quantités brutes à acheter",
                                size=10, color=TEXT_MUTED),
                    ]),
                    mk_sep(),
                ]),
                bgcolor=BG_CARD,
                padding=ft.padding.symmetric(horizontal=16, vertical=12),
                border_radius=ft.border_radius.only(top_left=R_CARD, top_right=R_CARD),
                border=ft.border.all(1, BORDER),
                margin=ft.margin.symmetric(horizontal=12),
            ),
            ft.Container(
                content=nav_container,
                padding=ft.padding.symmetric(horizontal=12),
            ),
            ft.Container(
                content=self._content_col,
                padding=ft.padding.symmetric(horizontal=12),
                expand=True,
            ),
            ft.Container(
                content=action_row,
                padding=ft.padding.symmetric(horizontal=12, vertical=8),
            ),
            ft.Container(height=16),
        ], spacing=4, scroll=ft.ScrollMode.AUTO)

    # ── Handlers ──────────────────────────────────────────────────────────────

    def _select_segment(self, idx: int):
        self._seg_idx = idx
        lbl, days_slice = self.segments[idx]

        nd = len(days_slice)
        period = f"{nd} jour{'s' if nd > 1 else ''}"
        if "Mois" in lbl:
            period = f"mois complet ({nd} jours)"

        shopping = compute_shopping_list(days_slice)
        controls = _build_shopping_controls(shopping, period, self.app_state)

        if self._content_col is not None:
            self._content_col.controls.clear()
            self._content_col.controls.extend(controls)

        # Mettre à jour couleurs onglets
        for i, btn in enumerate(self._nav_btns):
            selected = (i == idx)
            btn.style = ft.ButtonStyle(
                bgcolor={ft.ControlState.DEFAULT: ACCENT if selected else BG_CARD2},
                color={ft.ControlState.DEFAULT: "#000000" if selected else TEXT_MUTED},
                padding=ft.padding.symmetric(horizontal=12, vertical=8),
                shape=ft.RoundedRectangleBorder(radius=10),
            )

        self._safe_update()

    def _on_refresh_prices(self, e=None):
        """MAJ prix — port de _refresh_prices ERAGROK."""
        try:
            from data import db as _db
            from data.prices_module import (load_defaults, update_prices_from_off,
                                            DEFAULT_PRICES, PRICES_VERSION)

            class _FakeApp:
                def __init__(self, cu): self.current_user = cu
            fake = _FakeApp(self.app_state.get("current_user", ""))

            # Purge prix non-manuels
            con = _db.get_user_db_from_app(fake)
            con.execute("DELETE FROM food_prices WHERE source != 'manual'")
            con.commit(); con.close()

            # Recharger défauts
            load_defaults(fake)
            _db.settings_set(fake, "prices_version", str(PRICES_VERSION))
            n = len(DEFAULT_PRICES)

            # Rafraîchir affichage
            self._select_segment(self._seg_idx)
            self._snack(f"✔ {n} prix rechargés.", SUCCESS)

            # OFF en arrière-plan
            try:
                def _on_done(n_up, n_fail):
                    if n_up > 0:
                        self._select_segment(self._seg_idx)
                        self._safe_update()
                update_prices_from_off(fake, on_done=_on_done)
            except Exception:
                pass

        except Exception as ex:
            self._snack(f"Erreur MAJ prix : {ex}", DANGER)

    def _on_export_pdf(self, e=None):
        """Export liste de courses PDF du segment courant."""
        try:
            from data.pdf_utils import export_shopping_pdf
            lbl, days_slice = self.segments[self._seg_idx]
            shopping = compute_shopping_list(days_slice)
            export_shopping_pdf(self.app_state, shopping,
                                period_lbl=lbl, page=self.page)
        except Exception as ex:
            self._snack(f"Erreur export PDF : {ex}", DANGER)

    def _on_export_json(self, e=None):
        """Export liste de courses du segment courant en JSON."""
        try:
            import json, os
            from data import utils
            lbl, days_slice = self.segments[self._seg_idx]
            shopping = compute_shopping_list(days_slice)
            user = self.app_state.get("current_user", "default")
            out_dir = os.path.join(utils.USERS_DIR, user)
            os.makedirs(out_dir, exist_ok=True)
            safe_lbl = lbl.replace(" ", "_").replace("/", "-")
            path = os.path.join(out_dir, f"courses_{safe_lbl}.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(shopping, f, ensure_ascii=False, indent=2,
                          default=str)
            self._snack(f"✔ Exporté : {path}", SUCCESS)
        except Exception as ex:
            self._snack(f"Erreur export : {ex}", DANGER)

    # ── Helpers ───────────────────────────────────────────────────────────────

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

def build_shopping_screen(page: ft.Page, app_state: dict,
                          plans_or_plan: list) -> ft.Column:
    """
    Construit et retourne l'écran liste de courses.
    plans_or_plan : plan journée (list de meals)
                  OU plan multiday (list de {date, label, plan})
    """
    view = ShoppingView(page, app_state, plans_or_plan)
    return view.get_view()
