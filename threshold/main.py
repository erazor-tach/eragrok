# main.py — THRESHOLD · Coach Bodybuilding
# ─────────────────────────────────────────────────────────────────────────────
# Application Flet — Desktop + Mobile
# ─────────────────────────────────────────────────────────────────────────────
# AMÉLIORATION #2 : Chargements asynchrones (UI non-bloquante)
#
# Avant : navigate() appelait build_*_screen() directement sur le thread UI
#         → interface gelée pendant la construction des écrans lourds.
#
# Après : async_navigate() affiche un spinner immédiatement, puis exécute la
#         construction de l'écran dans asyncio.to_thread() (thread séparé),
#         et remplace le spinner par le vrai contenu sans jamais bloquer l'UI.
#
#   Règle Flet : toute modification de page.controls DOIT se faire sur le
#   thread UI (celui qui a appelé main()). asyncio.to_thread() exécute la
#   *construction* hors thread UI, mais l'*affichage* final (content_area + update)
#   revient toujours sur le thread UI via await (coroutine du loop Flet).
# ─────────────────────────────────────────────────────────────────────────────
import asyncio
import os
import sys
from pathlib import Path

import flet as ft

SCRIPT_DIR = Path(__file__).resolve().parent
os.chdir(SCRIPT_DIR)


def _meal_plan_from_db(db_plan: dict) -> dict | None:
    """Raccourci vers db.meal_plan_to_dashboard — conservé pour compatibilité."""
    from data.db import meal_plan_to_dashboard
    return meal_plan_to_dashboard(db_plan)


def _build_spinner(label: str = "Chargement…") -> ft.Container:
    """Spinner centré affiché pendant la construction asynchrone d'un écran."""
    return ft.Container(
        content=ft.Column(
            [
                ft.ProgressRing(width=40, height=40, stroke_width=3),
                ft.Text(label, size=13, color="#818aaa"),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=16,
        ),
        expand=True,
        alignment=ft.Alignment(0, 0),
    )


def main(page: ft.Page):
    from ui.theme import apply_page_style, bottom_nav, ACCENT, TEXT_MUTED
    from ui.dashboard import build_dashboard
    from data import utils, db as _db
    from data.app_state import AppState
    from data.logger import log_exc

    apply_page_style(page, "THRESHOLD — Coach Bodybuilding")

    app_state = AppState()

    content_area = ft.Column(
        [], spacing=0, expand=True, scroll=ft.ScrollMode.AUTO
    )

    # ── Spinners par onglet ───────────────────────────────────────────────────
    _SPINNER_LABELS = {
        0: "Chargement du dashboard…",
        1: "Chargement de la nutrition…",
        2: "Chargement de l'entraînement…",
        3: "Chargement du cycle…",
        4: "Chargement du profil…",
    }

    # ── Construction d'écran hors thread UI ──────────────────────────────────
    def _build_screen_sync(index: int) -> ft.Control:
        """Construit l'écran correspondant à l'index. S'exécute dans un thread worker."""
        if index == 0:
            return build_dashboard(page, app_state)
        elif index == 1:
            from data.nutrition import build_nutrition_screen
            return build_nutrition_screen(page, app_state)
        elif index == 2:
            from data.entrainement import build_entrainement_screen
            return build_entrainement_screen(page, app_state)
        elif index == 3:
            from data.cycle import build_cycle_screen
            return build_cycle_screen(page, app_state)
        elif index == 4:
            from data.profil import build_profil_screen

            def _on_open_profile(info: dict):
                app_state["current_user"] = info.get(
                    "folder", info.get("name", "").lower().replace(" ", "_")
                )
                app_state["user_info"] = info
                nav_bar.visible = True
                # Pré-charge le dernier plan accepté pour ce profil
                try:
                    db_plan = _db.meal_plan_get_last(app_state, accepted_only=True)
                    if db_plan and db_plan.get("plan_json"):
                        app_state["last_meal_plan"] = _meal_plan_from_db(db_plan)
                    else:
                        app_state["last_meal_plan"] = None
                except Exception:
                    log_exc("_on_open_profile — pré-chargement meal_plan")
                    app_state["last_meal_plan"] = None

            return build_profil_screen(page, app_state, _on_open_profile)

        return ft.Container()  # fallback

    # ── Navigate asynchrone ───────────────────────────────────────────────────
    async def async_navigate(index: int):
        """Affiche le spinner, construit l'écran en thread, affiche le résultat."""
        app_state["nav_index"] = index

        # 1. Spinner immédiat sur le thread UI
        content_area.controls.clear()
        content_area.controls.append(_build_spinner(_SPINNER_LABELS.get(index, "Chargement…")))
        page.update()

        # 2. Construction hors thread UI (DB + calculs)
        try:
            screen = await asyncio.to_thread(_build_screen_sync, index)
        except Exception as exc:
            screen = ft.Container(
                content=ft.Column(
                    [
                        ft.Text("Erreur de chargement", size=16, color="#ef4444"),
                        ft.Text(str(exc), size=12, color="#818aaa"),
                    ],
                    spacing=8,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                expand=True,
                alignment=ft.Alignment(0, 0),
                padding=ft.Padding.all(32),
            )

        # 3. Affichage sur le thread UI
        content_area.controls.clear()
        content_area.controls.append(screen)
        page.update()

    # ── Wrapper synchrone pour les callbacks Flet (on_change etc.) ───────────
    def navigate(index: int):
        """Pont synchrone → async_navigate. Utilisé par la nav bar et _show_profil."""
        page.run_task(async_navigate, index)


    # ── Navigation bar ────────────────────────────────────────────────────────
    def _on_nav(e):
        navigate(e.control.selected_index)

    nav_bar = bottom_nav(page, selected=0, on_change=_on_nav)
    nav_bar.visible = False

    # ── Layout racine ─────────────────────────────────────────────────────────
    page.add(
        ft.Column(
            [content_area, nav_bar],
            spacing=0,
            expand=True,
        )
    )

    # ── Auto-login si un seul profil (synchrone — avant le premier rendu) ────
    utils.ensure_users_dir()
    _users = utils.list_users()
    if len(_users) == 1:
        info = utils.get_user_info(_users[0])
        if info:
            app_state["current_user"] = info.get(
                "folder", _users[0].lower().replace(" ", "_")
            )
            app_state["user_info"] = info
            nav_bar.visible = True
            # ── Pré-charge le dernier plan accepté depuis la DB ───────────────
            # Nécessaire car app_state.last_meal_plan est None au démarrage.
            # Le dashboard lit d'abord last_meal_plan avant son fallback DB,
            # mais le fallback s'exécute dans asyncio.to_thread() (thread worker)
            # qui a son propre pool SQLite — on charge ici sur le thread principal
            # pour garantir que la valeur est disponible dès le premier rendu.
            try:
                db_plan = _db.meal_plan_get_last(app_state, accepted_only=True)
                if db_plan and db_plan.get("plan_json"):
                    app_state["last_meal_plan"] = _meal_plan_from_db(db_plan)
            except Exception:
                log_exc("auto-login — pré-chargement meal_plan")
            navigate(0)
            return

    # Sinon → écran profil
    navigate(4)


if __name__ == "__main__":
    # ── Supprime l'erreur asyncio ProactorBasePipeTransport sur Windows ───────
    if sys.platform == "win32":
        _orig_handler = asyncio.BaseEventLoop.call_exception_handler

        def _silent_handler(self, ctx):
            if "connection_lost" in str(ctx.get("message", "")).lower():
                return
            exc = ctx.get("exception")
            if isinstance(exc, (ConnectionResetError, OSError)):
                return
            _orig_handler(self, ctx)

        asyncio.BaseEventLoop.call_exception_handler = _silent_handler

    ft.run(main)
