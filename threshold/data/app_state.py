# data/app_state.py — THRESHOLD · État global de l'application
# ─────────────────────────────────────────────────────────────────────────────
# AMÉLIORATION #4 : AppState typé — remplace le dict libre app_state
#
# Avant : app_state = {"current_user": None, "user_info": None, ...}
#         → clés string libres, aucun type, KeyError silencieux,
#           aucune autocomplétion IDE, contrat implicite entre modules.
#
# Après : classe AppState avec :
#   • Attributs typés et documentés (autocomplétion, détection d'erreurs)
#   • Interface dict-compatible (__getitem__ / __setitem__ / .get())
#     → tous les modules existants (nutrition.py, profil.py, meal_generator.py,
#       db.py) continuent de fonctionner sans modification grâce au protocole
#       dict émulé.
#   • Propriété .folder → raccourci vers current_user (utilisé par db.py)
#   • Méthode .reset_user() → déconnexion propre en un appel
#
# Compatibilité garantie :
#   app_state["current_user"]   ←→  app_state.current_user
#   app_state.get("user_info")  ←→  app_state.user_info
#   isinstance(app_state, dict) retourne False — mais duck typing suffit partout
# ─────────────────────────────────────────────────────────────────────────────
from __future__ import annotations

from typing import Any


class AppState:
    """État global de l'application THRESHOLD.

    Toutes les clés qui transitaient dans le dict libre sont maintenant des
    attributs typés. Un protocole dict-compatible (__getitem__ / __setitem__ /
    __contains__ / get / items) permet aux modules existants de continuer à
    utiliser la syntaxe app_state["clé"] sans aucune modification.

    Les clés «privées» préfixées par '_' (ex: _nutrition_view) sont stockées
    dans un dict interne _extras pour ne pas polluer l'espace d'attributs public.
    """

    # ── Clés publiques typées ─────────────────────────────────────────────────

    current_user: str | None
    """Identifiant du dossier utilisateur actif (ex: 'erazor'). None si déconnecté."""

    user_info: dict | None
    """Dictionnaire complet du profil actif tel que retourné par utils.get_user_info()."""

    last_meal_plan: dict | None
    """Dernier plan alimentaire accepté : {plan, cal, prot, gluc, lip}."""

    nav_index: int
    """Index de l'onglet de navigation actif (0=Dashboard … 4=Profil)."""

    adjustment: str
    """Label d'ajustement calorique actif (ex: 'Maintien (0%)')."""

    def __init__(
        self,
        current_user: str | None = None,
        user_info: dict | None = None,
        last_meal_plan: dict | None = None,
        nav_index: int = 0,
        adjustment: str = "Maintien (0%)",
    ) -> None:
        self.current_user  = current_user
        self.user_info     = user_info
        self.last_meal_plan = last_meal_plan
        self.nav_index     = nav_index
        self.adjustment    = adjustment
        self._extras: dict[str, Any] = {}  # clés privées / dynamiques

    # ── Propriétés raccourcis ─────────────────────────────────────────────────

    @property
    def folder(self) -> str:
        """Alias de current_user — utilisé par db.get_user_db_from_app()."""
        return self.current_user or "default"

    @property
    def is_logged_in(self) -> bool:
        """True si un utilisateur est actuellement chargé."""
        return self.current_user is not None and self.user_info is not None

    # ── Méthodes utilitaires ──────────────────────────────────────────────────

    def reset_user(self) -> None:
        """Déconnecte l'utilisateur courant (remet les champs à None/défaut)."""
        self.current_user   = None
        self.user_info      = None
        self.last_meal_plan = None
        self.nav_index      = 0
        self.adjustment     = "Maintien (0%)"
        self._extras.clear()
        # Invalide le cache LRU des calculs nutritionnels — le nouveau profil
        # aura des paramètres différents (poids, taille, âge, objectif).
        try:
            from data.utils import clear_nutrition_cache
            clear_nutrition_cache()
        except Exception:
            pass

    # ── Protocole dict-compatible ─────────────────────────────────────────────
    # Permet aux modules existants d'utiliser app_state["clé"] sans modification.

    # Clés publiques gérées comme attributs
    _PUBLIC_KEYS = frozenset({
        "current_user", "user_info", "last_meal_plan", "nav_index", "adjustment",
    })

    def __getitem__(self, key: str) -> Any:
        if key in self._PUBLIC_KEYS:
            return getattr(self, key)
        return self._extras[key]  # KeyError si absent — comportement dict standard

    def __setitem__(self, key: str, value: Any) -> None:
        if key in self._PUBLIC_KEYS:
            setattr(self, key, value)
        else:
            self._extras[key] = value

    def __contains__(self, key: object) -> bool:
        if key in self._PUBLIC_KEYS:
            return True
        return key in self._extras

    def get(self, key: str, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default

    def __len__(self) -> int:
        return len(self._PUBLIC_KEYS) + len(self._extras)

    def keys(self):
        """Retourne toutes les clés — requis pour le protocole ** (unpacking dict)."""
        yield from self._PUBLIC_KEYS
        yield from self._extras.keys()

    def values(self):
        for k in self._PUBLIC_KEYS:
            yield getattr(self, k)
        yield from self._extras.values()

    def items(self):
        """Itère sur toutes les clés publiques + extras (utile pour le debug)."""
        for k in self._PUBLIC_KEYS:
            yield k, getattr(self, k)
        yield from self._extras.items()

    def __repr__(self) -> str:
        parts = ", ".join(f"{k}={v!r}" for k, v in self.items())
        return f"AppState({parts})"
