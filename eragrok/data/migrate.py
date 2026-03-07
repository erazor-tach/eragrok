#!/usr/bin/env python3
# data/migrate.py — ERAGROK · Migration CSV/JSON → SQLite
#
# Usage : python -m data.migrate   (depuis la racine du projet)
#         ou automatiquement à l'import si des CSV existent encore
# ─────────────────────────────────────────────────────────────────────────────
import os, csv, json, sqlite3
from pathlib import Path

def run_migration(users_dir: str, verbose=True):
    """
    Migre eragrok_users.csv + tous les fichiers utilisateurs vers SQLite.
    Renomme chaque fichier migré en .migrated pour éviter une double migration.
    """
    def log(msg):
        if verbose: print(f"[MIGRATE] {msg}")

    users_dir = Path(users_dir)

    # ── 1. Registre global ────────────────────────────────────────────────
    global_csv = users_dir / "eragrok_users.csv"
    global_db  = users_dir / "eragrok.db"

    if global_csv.exists():
        from data.db import get_global_db
        con = get_global_db()
        migrated = 0
        with open(global_csv, newline="", encoding="utf-8") as f:
            reader = csv.reader(f); next(reader, None)
            for row in reader:
                if not row: continue
                # [ID, Name, Age, Sexe, Taille (cm), Poids (kg), Objectif, Ajustement]
                while len(row) < 8: row.append("")
                try:
                    con.execute("""
                        INSERT OR IGNORE INTO users
                        (name, age, sexe, taille, poids, objectif, ajustement)
                        VALUES (?,?,?,?,?,?,?)
                    """, (row[1], row[2], row[3], row[4], row[5], row[6], row[7]))
                    migrated += 1
                except Exception as e:
                    log(f"  skip user {row}: {e}")
        con.commit(); con.close()
        global_csv.rename(global_csv.with_suffix(".csv.migrated"))
        log(f"Utilisateurs : {migrated} migrés → eragrok.db")
    else:
        log("eragrok_users.csv absent ou déjà migré.")

    # ── 2. Données par utilisateur ────────────────────────────────────────
    for user_dir in users_dir.iterdir():
        if not user_dir.is_dir(): continue
        folder = user_dir.name

        def migrate_file(fname, handler):
            p = user_dir / fname
            if p.exists():
                handler(p, folder)
                p.rename(p.with_suffix(p.suffix + ".migrated"))

        # nutrition.csv
        def mig_nutrition(p, folder):
            from data.db import get_user_db
            con = get_user_db(folder); n = 0
            with open(p, newline="", encoding="utf-8") as f:
                reader = csv.reader(f); next(reader, None)
                for row in reader:
                    if not row: continue
                    while len(row) < 8: row.append("")
                    con.execute("""
                        INSERT INTO nutrition
                        (date,poids,age,calories,proteines,glucides,lipides,note)
                        VALUES (?,?,?,?,?,?,?,?)
                    """, tuple(row[:8])); n += 1
            con.commit(); con.close()
            log(f"  {folder}/nutrition.csv : {n} lignes → DB")

        # planning.csv
        def mig_planning(p, folder):
            from data.db import get_user_db
            con = get_user_db(folder); n = 0
            with open(p, newline="", encoding="utf-8") as f:
                reader = csv.reader(f); next(reader, None)
                for row in reader:
                    if not row: continue
                    while len(row) < 6: row.append("")
                    con.execute("""
                        INSERT INTO planning
                        (date,groupes,programme,types,note,line)
                        VALUES (?,?,?,?,?,?)
                    """, tuple(row[:6])); n += 1
            con.commit(); con.close()
            log(f"  {folder}/planning.csv : {n} lignes → DB")

        # cycle.csv
        def mig_cycle(p, folder):
            from data.db import get_user_db
            con = get_user_db(folder); n = 0
            with open(p, newline="", encoding="utf-8") as f:
                reader = csv.reader(f); next(reader, None)
                for row in reader:
                    if not row: continue
                    while len(row) < 5: row.append("")
                    con.execute("""
                        INSERT INTO cycle
                        (debut,fin_estimee,longueur_sem,produits_doses,note)
                        VALUES (?,?,?,?,?)
                    """, tuple(row[:5])); n += 1
            con.commit(); con.close()
            log(f"  {folder}/cycle.csv : {n} lignes → DB")

        # training_history.json
        def mig_history(p, folder):
            from data.db import get_user_db
            con = get_user_db(folder)
            with open(p, encoding="utf-8") as f:
                entries = json.load(f)
            for e in entries:
                con.execute("""
                    INSERT INTO training_history
                    (date,type,duration,notes,exercises,planned_for)
                    VALUES (?,?,?,?,?,?)
                """, (
                    e.get("date",""), e.get("type",""),
                    e.get("duration",""), e.get("notes",""),
                    json.dumps(e.get("exercises",[]), ensure_ascii=False),
                    e.get("planned_for",""),
                ))
            con.commit(); con.close()
            log(f"  {folder}/training_history.json : {len(entries)} entrées → DB")

        # cycle_qualified.ok → settings
        def mig_flag(p, folder):
            from data.db import get_user_db
            con = get_user_db(folder)
            content = p.read_text(encoding="utf-8").strip() or "migrated"
            con.execute("INSERT OR REPLACE INTO settings (key,value) VALUES (?,?)",
                        ("cycle_qualified", content))
            con.commit(); con.close()
            log(f"  {folder}/cycle_qualified.ok → settings.cycle_qualified")

        # Programmes JSON
        def mig_programmes(folder):
            prog_dir = user_dir / "programmes"
            if not prog_dir.exists(): return
            from data.db import get_user_db
            con = get_user_db(folder); n = 0
            for jf in prog_dir.glob("*.json"):
                try:
                    with open(jf, encoding="utf-8") as f: d = json.load(f)
                    con.execute("""
                        INSERT INTO programmes (title, created, lines)
                        VALUES (?,?,?)
                    """, (
                        d.get("title",""),
                        d.get("created",""),
                        json.dumps(d.get("lines",[]), ensure_ascii=False),
                    ))
                    jf.rename(jf.with_suffix(".json.migrated")); n += 1
                except Exception as e:
                    log(f"  skip programme {jf.name}: {e}")
            con.commit(); con.close()
            if n: log(f"  {folder}/programmes/ : {n} fichiers → DB")

        migrate_file("nutrition.csv",          mig_nutrition)
        migrate_file("planning.csv",           mig_planning)
        migrate_file("cycle.csv",              mig_cycle)
        migrate_file("training_history.json",  mig_history)
        migrate_file("cycle_qualified.ok",     mig_flag)
        mig_programmes(folder)

    log("Migration terminée ✓")


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from data.utils import USERS_DIR
    run_migration(USERS_DIR, verbose=True)
