# ui/snackbar.py — THRESHOLD · Snackbar centralisé
# ─────────────────────────────────────────────────────────────────────────────
# AMÉLIORATION #10 : Remplace les ~6 implémentations locales de _snack()
# dispersées dans profil.py, nutrition.py, cycle.py, entrainement.py,
# meal_generator.py, shopping.py, pdf_utils.py.
#
# API publique :
#   snack(page, msg, level="success")
#   snack(page, msg, level="error")
#   snack(page, msg, level="warning")
#   snack(page, msg, level="info")
#
# Les classes existantes remplacent :
#   self._snack(msg, SUCCESS)  →  snack(self.page, msg)
#   self._snack(msg, DANGER)   →  snack(self.page, msg, "error")
#   self._snack(msg, WARNING)  →  snack(self.page, msg, "warning")
#   self._snack(msg, BLUE)     →  snack(self.page, msg, "info")
# ─────────────────────────────────────────────────────────────────────────────
from __future__ import annotations

import flet as ft

# ── Couleurs par niveau ───────────────────────────────────────────────────────
_LEVEL_COLORS: dict[str, str] = {
    "success": "#22c55e",   # SUCCESS du thème
    "error":   "#ef4444",   # DANGER du thème
    "warning": "#f59e0b",   # WARNING du thème
    "info":    "#3b82f6",   # BLUE du thème
}
_DEFAULT_LEVEL = "success"

# Durée d'affichage en ms par niveau
_LEVEL_DURATION: dict[str, int] = {
    "success": 3000,
    "error":   5000,   # plus long pour que l'erreur soit lue
    "warning": 4000,
    "info":    3000,
}


def snack(
    page: ft.Page,
    msg: str,
    level: str = _DEFAULT_LEVEL,
    duration: int | None = None,
) -> None:
    """Affiche un SnackBar centré, non-bloquant, avec niveau sémantique.

    Args:
        page:     page Flet courante
        msg:      texte à afficher
        level:    "success" | "error" | "warning" | "info"
        duration: durée ms (None = valeur par défaut du niveau)
    """
    if page is None:
        return
    color = _LEVEL_COLORS.get(level, _LEVEL_COLORS[_DEFAULT_LEVEL])
    dur   = duration if duration is not None else _LEVEL_DURATION.get(level, 3000)
    try:
        sb = ft.SnackBar(
            content=ft.Text(msg),
            bgcolor=color,
            duration=dur,
            open=True,
        )
        # Flet >= 0.21 : on peut soit utiliser page.snack_bar soit overlay.
        # On utilise overlay pour compatibilité maximale (même pattern qu'entrainement.py).
        page.overlay.append(sb)
        page.update()
    except Exception:
        pass
