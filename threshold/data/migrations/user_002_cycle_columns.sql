-- migration 002 · table cycle — ajout end_mode et days_2x_config
-- Ces colonnes étaient ajoutées à la volée dans cycle_insert() via ALTER TABLE.
-- On les gère ici proprement, une seule fois, au démarrage.
-- ALTER TABLE ADD COLUMN est no-op si la colonne existe déjà (SQLite le lève
-- comme erreur, le moteur de migrations l'ignore silencieusement).

ALTER TABLE cycle ADD COLUMN end_mode       TEXT DEFAULT 'PCT';
ALTER TABLE cycle ADD COLUMN days_2x_config TEXT DEFAULT '{}';
