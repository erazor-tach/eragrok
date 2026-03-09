# main.py — THRESHOLD · Coach Bodybuilding
# ─────────────────────────────────────────────────────────────────────────────
# Application Flet — Desktop + Mobile
# Hérite du moteur ERAGROK (30 sessions de logique métier)
# ─────────────────────────────────────────────────────────────────────────────
import os
import sys
import logging
from pathlib import Path

import flet as ft

# ── Résolution du dossier racine ──────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
os.chdir(SCRIPT_DIR)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(SCRIPT_DIR / "threshold.log", mode="a", encoding="utf-8"),
    ],
)
log = logging.getLogger("threshold")


def main(page: ft.Page):
    # ── Imports internes (après chdir) ────────────────────────────────────────
    from ui.theme import apply_page_style, bottom_nav, BG_ROOT, ACCENT, TEXT_MUTED
    from ui.theme import mk_card, mk_title, mk_btn, mk_label, mk_sep, mk_entry
    from ui.theme import mk_dropdown, mk_badge, BG_CARD, TEXT
    from ui.dashboard import build_dashboard
    from data import utils, db as _db

    apply_page_style(page, "THRESHOLD — Coach Bodybuilding")

    # ── État global de l'app ──────────────────────────────────────────────────
    app_state = {
        "current_user": None,
        "user_info": None,
        "last_meal_plan": None,
        "nav_index": 0,
    }

    # ── Zone de contenu principal ─────────────────────────────────────────────
    content_area = ft.Column([], spacing=0, expand=True,
                              scroll=ft.ScrollMode.AUTO)

    # ── Navigation handler ────────────────────────────────────────────────────
    def navigate(index: int):
        app_state["nav_index"] = index
        content_area.controls.clear()

        if index == 0:  # Dashboard
            content_area.controls.append(build_dashboard(page, app_state))
        elif index == 1:  # Nutrition
            content_area.controls.append(_build_placeholder("🍎  NUTRITION", "Module en cours de migration..."))
        elif index == 2:  # Training
            content_area.controls.append(_build_placeholder("🏋  ENTRAÎNEMENT", "Module en cours de migration..."))
        elif index == 3:  # Cycle
            content_area.controls.append(_build_placeholder("💉  CYCLE", "Module en cours de migration..."))
        elif index == 4:  # Profil
            _show_profil()
            return

        page.update()

    def _build_placeholder(title: str, msg: str) -> ft.Container:
        return ft.Container(
            content=ft.Column([
                ft.Text(title, size=22, color=ACCENT, weight=ft.FontWeight.BOLD),
                ft.Container(height=20),
                ft.Text(msg, size=14, color=TEXT_MUTED),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            alignment=ft.Alignment(0, 0),
            padding=ft.padding.all(40),
            expand=True,
        )

    # ── Écran Profil / Sélection utilisateur ──────────────────────────────────
    def _show_profil():
        content_area.controls.clear()
        utils.ensure_users_dir()
        users = utils.list_users()

        controls = [
            ft.Container(
                content=ft.Column([
                    ft.Text("⚡ THRESHOLD", size=28, color=ACCENT,
                            weight=ft.FontWeight.BOLD),
                    ft.Text("COACH BODYBUILDING", size=11, color=TEXT_MUTED),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.Alignment(0, 0),
                padding=ft.padding.only(top=40, bottom=20),
            ),
        ]

        if users:
            user_dd = mk_dropdown("Sélectionner un profil", users,
                                   value=users[0] if users else "", width=300)

            def _open_profile(e):
                sel = user_dd.value
                if not sel:
                    return
                info = utils.get_user_info(sel)
                if info:
                    app_state["current_user"] = info.get("folder",
                        sel.lower().replace(" ", "_"))
                    app_state["user_info"] = info
                    # Init prices
                    try:
                        from data.prices_module import ensure_prices_loaded

                        class _FakeApp:
                            def __init__(self, folder):
                                self.current_user = folder
                        ensure_prices_loaded(_FakeApp(app_state["current_user"]))
                    except Exception as ex:
                        log.debug("prices init: %s", ex)
                    nav_bar.visible = True
                    navigate(0)

            profile_card = mk_card([
                ft.Container(
                    content=ft.Column([
                        mk_title("  SÉLECTIONNER UN PROFIL"),
                        mk_sep(),
                        ft.Container(height=10),
                        user_dd,
                        ft.Container(height=12),
                        mk_btn("▶  OUVRIR", on_click=_open_profile,
                               width=200, height=44),
                    ]),
                    padding=ft.padding.all(20),
                ),
            ])
            controls.append(ft.Container(
                content=profile_card,
                padding=ft.padding.symmetric(horizontal=16),
            ))

        # Formulaire création profil
        name_f   = mk_entry(label="Nom / Prénom", hint="Ex : Rudy", width=300)
        sexe_dd  = mk_dropdown("Sexe", ["Homme", "Femme"], value="Homme", width=140)
        taille_f = mk_entry(label="Taille (cm)", hint="176", width=140)
        poids_f  = mk_entry(label="Poids (kg)", hint="87", width=140)
        dob_f    = mk_entry(label="Date de naissance", hint="JJ/MM/AAAA", width=200)
        adj_dd   = mk_dropdown("Ajustement", list(utils.ADJUSTMENTS.keys()),
                                value="Maintien (0%)", width=300)

        def _create(e):
            name = name_f.value.strip()
            if not name:
                page.snack_bar = ft.SnackBar(ft.Text("Le nom est obligatoire."), bgcolor=DANGER)
                page.snack_bar.open = True
                page.update()
                return
            dob = dob_f.value.strip()
            sexe = sexe_dd.value or "Homme"
            taille = taille_f.value.strip()
            poids = poids_f.value.strip()
            adj = adj_dd.value or "Maintien (0%)"
            objectif = utils.ajustement_to_objectif(adj)
            ok, msg = utils.add_user(name, dob, sexe, taille, poids, objectif, adj,
                                      date_naissance=dob)
            if ok:
                page.snack_bar = ft.SnackBar(
                    ft.Text(f"✅ Profil '{name}' créé !"), bgcolor=SUCCESS)
                page.snack_bar.open = True
                info = utils.get_user_info(name)
                if info:
                    app_state["current_user"] = info.get("folder",
                        name.lower().replace(" ", "_"))
                    app_state["user_info"] = info
                    nav_bar.visible = True
                    navigate(0)
            else:
                page.snack_bar = ft.SnackBar(ft.Text(msg), bgcolor=DANGER)
                page.snack_bar.open = True
                page.update()

        create_card = mk_card([
            ft.Container(
                content=ft.Column([
                    mk_title("  CRÉER UN PROFIL"),
                    mk_sep(),
                    ft.Container(height=10),
                    name_f,
                    ft.Row([sexe_dd, taille_f], spacing=10),
                    ft.Row([poids_f, dob_f], spacing=10),
                    adj_dd,
                    ft.Container(height=12),
                    mk_btn("✚  CRÉER", on_click=_create, width=200, height=44),
                ], spacing=8),
                padding=ft.padding.all(20),
            ),
        ])
        controls.append(ft.Container(
            content=create_card,
            padding=ft.padding.symmetric(horizontal=16),
        ))

        content_area.controls = controls
        page.update()

    # ── Navigation bar ────────────────────────────────────────────────────────
    def _on_nav(e):
        navigate(e.control.selected_index)

    nav_bar = bottom_nav(page, selected=0, on_change=_on_nav)
    nav_bar.visible = False  # masqué tant que pas de profil

    # ── Layout racine ─────────────────────────────────────────────────────────
    page.add(
        ft.Column([
            content_area,
            nav_bar,
        ], spacing=0, expand=True),
    )

    # ── Auto-login si un seul profil ──────────────────────────────────────────
    utils.ensure_users_dir()
    _users = utils.list_users()
    if len(_users) == 1:
        info = utils.get_user_info(_users[0])
        if info:
            app_state["current_user"] = info.get("folder",
                _users[0].lower().replace(" ", "_"))
            app_state["user_info"] = info
            nav_bar.visible = True
            navigate(0)
            return

    # Sinon → écran profil
    navigate(4)


if __name__ == "__main__":
    ft.app(target=main)
