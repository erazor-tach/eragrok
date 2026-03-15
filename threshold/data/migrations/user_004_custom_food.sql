-- Migration 004 : Table custom_food (catalogue aliments personnalisés)
-- Remplace tout stockage JSON éventuel pour les aliments custom.

CREATE TABLE IF NOT EXISTS custom_food (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    nom          TEXT    NOT NULL UNIQUE,
    categorie    TEXT    DEFAULT 'Divers',
    kcal         REAL    DEFAULT 0,
    proteines    REAL    DEFAULT 0,
    glucides     REAL    DEFAULT 0,
    lipides      REAL    DEFAULT 0,
    fibres       REAL    DEFAULT 0,
    unite        TEXT    DEFAULT 'g',
    portion_ref  REAL    DEFAULT 100,
    notes        TEXT    DEFAULT '',
    created_at   TEXT    DEFAULT (datetime('now'))
);
