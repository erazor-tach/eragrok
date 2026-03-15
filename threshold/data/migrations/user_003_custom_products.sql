-- migration 003 · table custom_products
-- Remplace users/{folder}/custom_products.json
-- Chaque produit personnalisé créé par l'utilisateur dans le catalogue Cycle.

CREATE TABLE IF NOT EXISTS custom_products (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    nom          TEXT    NOT NULL UNIQUE,
    categorie_id INTEGER DEFAULT 0,
    dose         TEXT    DEFAULT '',
    halflife     TEXT    DEFAULT '',
    usage        TEXT    DEFAULT '',
    notes        TEXT    DEFAULT '',
    created_at   TEXT    DEFAULT (datetime('now'))
);
