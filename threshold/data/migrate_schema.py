# data/migrate_schema.py — THRESHOLD · Moteur de migrations SQLite
# ─────────────────────────────────────────────────────────────────────────────
# AMÉLIORATION #3 : Système de migrations de schéma versionné
#
# Avant : colonnes ajoutées via ALTER TABLE dans les fonctions métier (cycle_insert)
#         → fragile, non tracé, risque de régression à chaque évolution.
#
# Après : fichiers SQL numérotés dans data/migrations/, appliqués une seule fois
#         au démarrage via une table schema_version dans chaque base.
#
# Convention de nommage des fichiers :
#   global_NNN_description.sql  → migrations pour eragrok.db (base globale)
#   user_NNN_description.sql    → migrations pour {folder}.db (base utilisateur)
#
# Appel :
#   apply_migrations(con, db_type="global")   dans get_global_db()
#   apply_migrations(con, db_type="user")     dans get_user_db()
# ─────────────────────────────────────────────────────────────────────────────
from __future__ import annotations

import sqlite3
from pathlib import Path

from data.logger import log

# Dossier contenant les fichiers .sql (data/migrations/)
_MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


def _ensure_version_table(con: sqlite3.Connection) -> None:
    """Crée la table schema_version si elle n'existe pas encore."""
    con.execute("""
        CREATE TABLE IF NOT EXISTS schema_version (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            version     INTEGER NOT NULL UNIQUE,
            filename    TEXT    NOT NULL,
            applied_at  TEXT    DEFAULT (datetime('now'))
        )
    """)
    con.commit()


def _applied_versions(con: sqlite3.Connection) -> set[int]:
    """Retourne l'ensemble des versions déjà appliquées."""
    rows = con.execute("SELECT version FROM schema_version").fetchall()
    return {r[0] for r in rows}

def _load_migration_files(db_type: str) -> list[tuple[int, str, Path]]:
    """Retourne la liste triée des fichiers de migration pour db_type.

    Chaque entrée : (version_int, filename, path)
    Seuls les fichiers dont le nom commence par '{db_type}_NNN' sont sélectionnés.
    """
    if not _MIGRATIONS_DIR.exists():
        return []

    results = []
    for f in sorted(_MIGRATIONS_DIR.glob(f"{db_type}_*.sql")):
        # Extrait NNN depuis le nom : global_001_initial.sql → 1
        parts = f.stem.split("_")           # ['global', '001', 'initial']
        if len(parts) < 2:
            continue
        try:
            version = int(parts[1])
        except ValueError:
            continue
        results.append((version, f.name, f))

    return sorted(results, key=lambda x: x[0])


def apply_migrations(con: sqlite3.Connection, db_type: str) -> int:
    """Applique toutes les migrations en attente pour cette connexion.

    Args:
        con:      connexion SQLite ouverte (sans autocommit)
        db_type:  "global" ou "user"

    Returns:
        Nombre de migrations appliquées dans cette session.
    """
    _ensure_version_table(con)
    applied = _applied_versions(con)
    pending = [
        (v, name, path)
        for v, name, path in _load_migration_files(db_type)
        if v not in applied
    ]

    count = 0
    for version, filename, path in pending:
        sql = path.read_text(encoding="utf-8")
        # Exécute chaque statement indépendamment pour isoler les erreurs
        # attendues (ex: ALTER TABLE colonne déjà existante → on continue)
        for statement in _split_statements(sql):
            stmt = statement.strip()
            if not stmt:
                continue
            try:
                con.execute(stmt)
            except sqlite3.OperationalError as exc:
                msg = str(exc).lower()
                # ALTER TABLE ADD COLUMN sur colonne existante → ignoré
                if "duplicate column name" in msg or "already exists" in msg:
                    continue
                raise  # toute autre erreur est fatale

        con.execute(
            "INSERT INTO schema_version (version, filename) VALUES (?, ?)",
            (version, filename),
        )
        con.commit()
        count += 1
        log.info("Migration appliquée : %s (v%s)", filename, version)

    return count


def _split_statements(sql: str) -> list[str]:
    """Découpe un script SQL multi-statements sur les ';'.
    Ignore les commentaires de ligne (--)."""
    lines = []
    for line in sql.splitlines():
        stripped = line.strip()
        if stripped.startswith("--"):
            continue
        lines.append(line)

    return [s.strip() for s in "\n".join(lines).split(";") if s.strip()]
