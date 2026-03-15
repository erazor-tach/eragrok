-- migration 001 · schéma initial base globale (eragrok.db)
-- Crée la table users si elle n'existait pas avant le système de migrations.
-- Les bases déjà initialisées par _init_global_schema() sont compatibles :
-- CREATE TABLE IF NOT EXISTS est idempotent.

CREATE TABLE IF NOT EXISTS users (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    name           TEXT    NOT NULL UNIQUE,
    age            TEXT    DEFAULT '',
    date_naissance TEXT    DEFAULT '',
    sexe           TEXT    DEFAULT 'Homme',
    taille         TEXT    DEFAULT '',
    poids          TEXT    DEFAULT '',
    objectif       TEXT    DEFAULT '',
    ajustement     TEXT    DEFAULT 'Maintien (0%)'
);
