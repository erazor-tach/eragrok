# check_data.py
import os, csv, json
from pathlib import Path
root = Path(__file__).resolve().parent
users_dir = root / "users"
users_file = users_dir / "eragrok_users.csv"

print("Projet:", root)
print("users/ existe:", users_dir.exists())
print("eragrok_users.csv existe:", users_file.exists())
if users_file.exists():
    with open(users_file, 'r', encoding='utf-8') as f:
        lines = f.read().splitlines()
    print("Nombre de lignes dans eragrok_users.csv:", len(lines))
    print("Premières lignes (max 10):")
    for i, l in enumerate(lines[:10], start=1):
        print(f"{i}: {l}")
# lister dossiers utilisateurs
if users_dir.exists():
    print("\nDossiers utilisateurs et fichiers (max 50):")
    for u in sorted(os.listdir(users_dir))[:50]:
        p = users_dir / u
        if p.is_dir():
            files = [f.name for f in p.iterdir()]
            print(f"- {u}: {files}")