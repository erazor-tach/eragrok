-- migration 001 · schéma initial base utilisateur ({folder}.db)
-- Crée toutes les tables si elles n'existaient pas.

CREATE TABLE IF NOT EXISTS nutrition (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    date           TEXT NOT NULL,
    poids          TEXT DEFAULT '',
    age            TEXT DEFAULT '',
    date_naissance TEXT DEFAULT '',
    calories       TEXT DEFAULT '',
    proteines      TEXT DEFAULT '',
    glucides       TEXT DEFAULT '',
    lipides        TEXT DEFAULT '',
    note           TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS planning (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    date       TEXT NOT NULL,
    groupes    TEXT DEFAULT '',
    programme  TEXT DEFAULT '',
    types      TEXT DEFAULT '',
    note       TEXT DEFAULT '',
    line       TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS cycle (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    debut           TEXT DEFAULT '',
    fin_estimee     TEXT DEFAULT '',
    longueur_sem    TEXT DEFAULT '',
    produits_doses  TEXT DEFAULT '',
    note            TEXT DEFAULT '',
    end_mode        TEXT DEFAULT 'PCT'
);

CREATE TABLE IF NOT EXISTS training_history (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    date        TEXT DEFAULT '',
    type        TEXT DEFAULT '',
    duration    TEXT DEFAULT '',
    notes       TEXT DEFAULT '',
    exercises   TEXT DEFAULT '[]',
    planned_for TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS programmes (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    title   TEXT DEFAULT '',
    created TEXT DEFAULT '',
    lines   TEXT DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS food_prices (
    food        TEXT PRIMARY KEY,
    prix_kg     REAL DEFAULT 0,
    unite       TEXT DEFAULT 'kg',
    source      TEXT DEFAULT 'default',
    last_update TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS meal_plans (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    date        TEXT    NOT NULL,
    mode        TEXT    DEFAULT 'jour',
    n_meals     INTEGER DEFAULT 4,
    cal_target  REAL    DEFAULT 0,
    prot_target REAL    DEFAULT 0,
    gluc_target REAL    DEFAULT 0,
    lip_target  REAL    DEFAULT 0,
    adj_label   TEXT    DEFAULT '',
    plan_json   TEXT    DEFAULT '[]',
    accepted    INTEGER DEFAULT 0,
    budget_w    REAL    DEFAULT 0
);
