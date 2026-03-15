# data/logger.py — THRESHOLD · Logging centralisé
# ─────────────────────────────────────────────────────────────────────────────
# AMÉLIORATION #6 : Remplace les ~40 bare except: pass silencieux par des
# appels de log tracés dans threshold.log.
#
# Usage depuis n'importe quel module :
#   from data.logger import log
#   log.warning("message")
#   log.error("message", exc_info=True)   # inclut le traceback complet
#   log.debug("message")
#
# Raccourcis pratiques :
#   from data.logger import log_exc
#   log_exc("contexte de l'erreur")       # log WARNING + exception courante
# ─────────────────────────────────────────────────────────────────────────────
from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

# ── Chemin du fichier de log ──────────────────────────────────────────────────
# À côté de main.py (racine du projet), pas dans users/ (données utilisateur)
_LOG_DIR  = Path(__file__).resolve().parent.parent
_LOG_FILE = _LOG_DIR / "threshold.log"

# ── Configuration du logger ───────────────────────────────────────────────────
_FMT  = "%(asctime)s [%(levelname)-8s] %(name)s — %(message)s"
_DFMT = "%Y-%m-%d %H:%M:%S"

log = logging.getLogger("threshold")

if not log.handlers:
    log.setLevel(logging.DEBUG)

    # Handler fichier rotatif : 10 Mo × 3 fichiers de backup
    try:
        fh = RotatingFileHandler(
            _LOG_FILE,
            maxBytes=10 * 1024 * 1024,   # 10 Mo
            backupCount=3,
            encoding="utf-8",
        )
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(logging.Formatter(_FMT, _DFMT))
        log.addHandler(fh)
    except Exception as _e:
        # Impossible d'écrire le fichier (permissions, etc.) → stderr uniquement
        print(f"[threshold] Impossible d'ouvrir {_LOG_FILE} : {_e}", file=sys.stderr)

    # Handler console : WARNING+ seulement (ne pollue pas stdout en prod)
    sh = logging.StreamHandler(sys.stderr)
    sh.setLevel(logging.WARNING)
    sh.setFormatter(logging.Formatter(_FMT, _DFMT))
    log.addHandler(sh)

    # Évite la propagation vers le root logger (doublons)
    log.propagate = False


def log_exc(context: str = "", level: str = "warning") -> None:
    """Loggue l'exception courante (sys.exc_info) avec son contexte.

    À utiliser dans un bloc except :
        try:
            ...
        except Exception:
            log_exc("nutrition_insert a échoué")

    Args:
        context : description de l'opération qui a échoué
        level   : "debug" | "warning" | "error" (défaut : "warning")
    """
    import traceback as _tb

    fn = getattr(log, level, log.warning)
    msg = f"{context} — {_tb.format_exc().strip()}" if context else _tb.format_exc().strip()
    fn(msg)


def get_logger(name: str) -> logging.Logger:
    """Retourne un sous-logger nommé (ex: get_logger('db'), get_logger('cycle')).

    Les messages remontent automatiquement vers le logger 'threshold' racine.
    Permet de filtrer les logs par module si besoin.
    """
    return logging.getLogger(f"threshold.{name}")
