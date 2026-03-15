# ui/page_utils.py — THRESHOLD · Utilitaires page Flet centralisés
# ─────────────────────────────────────────────────────────────────────────────
# AMÉLIORATION #11 : Remplace les 8 implémentations identiques de _safe_update()
# dispersées dans profil.py, nutrition.py, cycle.py, entrainement.py,
# meal_generator.py, shopping.py, widgets.py, weight_chart.py.
#
# API publique :
#   safe_update(page)   — page.update() silencieux (erreurs UI ignorées)
#
# Usage :
#   from ui.page_utils import safe_update
#   safe_update(self.page)
# ─────────────────────────────────────────────────────────────────────────────
from __future__ import annotations

import flet as ft


def safe_update(page: ft.Page | None) -> None:
    """Appelle page.update() en avalant silencieusement les exceptions UI.

    Les erreurs de rendu Flet (page détruite, thread secondaire, etc.)
    sont intentionnellement ignorées — elles ne doivent pas crasher l'app.
    À utiliser partout où page.update() est appelé dans un callback ou
    un thread secondaire.
    """
    if page is None:
        return
    try:
        page.update()
    except Exception:
        pass
