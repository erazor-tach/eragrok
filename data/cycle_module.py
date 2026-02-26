# data/cycle_module.py
import os
import csv
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from tkcalendar import Calendar
from data import utils

def _ensure_user_dir(app):
    user_dir = os.path.join(utils.USERS_DIR, app.current_user)
    Path(user_dir).mkdir(parents=True, exist_ok=True)
    return user_dir

def show_cycle_disclaimer(app):
    if not getattr(app, 'cycle_disclaimer_shown', False):
        disclaimer_text = (
            "AVERTISSEMENT IMPORTANT\n\n"
            "Les produits anabolisants et hormones (testostérone, hCG, etc.) peuvent causer des effets secondaires graves. "
            "Consultez toujours un médecin. En cliquant sur 'Accepter', vous assumez la responsabilité."
        )
        fen = tk.Toplevel(app.root)
        fen.title("Avertissement - Cycle hormonal")
        fen.geometry("600x400")
        sc = scrolledtext.ScrolledText(fen, wrap=tk.WORD, width=70, height=15, font=("Helvetica", 10))
        sc.insert(tk.INSERT, disclaimer_text)
        sc.config(state=tk.DISABLED)
        sc.pack(pady=10, padx=10)
        btnf = tk.Frame(fen); btnf.pack(pady=10)
        def accept():
            fen.destroy()
            app.cycle_disclaimer_shown = True
            show_cycle_screen(app)
        ttk.Button(btnf, text="ACCEPTER", command=accept).pack(side='left', padx=20)
        ttk.Button(btnf, text="REFUSER", command=fen.destroy).pack(side='left', padx=20)
    else:
        show_cycle_screen(app)

def show_cycle_screen(app):
    for w in app.content.winfo_children():
        w.destroy()
    tk.Label(app.content, text=f"CYCLE HORMONAL - Élève : {app.selected_user_name}", font=("Helvetica", 20, "bold"), bg="#f3f4f6", fg="#0f172a").pack(pady=12)
    date_frame = tk.Frame(app.content, bg="#f3f4f6"); date_frame.pack(pady=10, fill='x', padx=20)
    tk.Label(date_frame, text="Date :", font=("Helvetica", 14, "bold"), bg="#f3f4f6").pack(side='left', padx=10)
    app.cycle_date_entry = Calendar(date_frame, selectmode='day')
    app.cycle_date_entry.pack(side='left', padx=10)
    champs_frame = tk.Frame(app.content, bg="#f3f4f6"); champs_frame.pack(pady=20, padx=40, fill='x')
    champs = [("Dose testo (mg/sem)", "mg/sem"), ("hCG (UI/sem)", "UI/sem"), ("Phase (blast/cruise)", "")]
    app.cycle_entries = {}
    for label_text, unit in champs:
        row = tk.Frame(champs_frame, bg="#f3f4f6"); row.pack(fill='x', pady=8)
        tk.Label(row, text=f"{label_text} :", font=("Helvetica", 12), bg="#f3f4f6", fg="#0f172a").pack(side='left', padx=10)
        entry = ttk.Entry(row, width=20); entry.pack(side='left', padx=5)
        tk.Label(row, text=unit, font=("Helvetica", 12), bg="#f3f4f6").pack(side='left', padx=5)
        app.cycle_entries[label_text] = entry
    tk.Label(app.content, text="Note :", font=("Helvetica", 14, "bold"), bg="#f3f4f6", fg="#0f172a").pack(pady=15, anchor='w', padx=20)
    app.cycle_note_text = tk.Text(app.content, height=6, width=80, bg="white", fg="black"); app.cycle_note_text.pack(padx=20, pady=5)
    btn_frame = tk.Frame(app.content, bg="#f3f4f6"); btn_frame.pack(pady=30)
    ttk.Button(btn_frame, text="SAUVEGARDER", command=lambda: _sauvegarder_cycle(app)).pack(side='left', padx=20)
    ttk.Button(btn_frame, text="Retour Dashboard", command=app.show_dashboard).pack(side='left', padx=20)

def _sauvegarder_cycle(app):
    if not app.current_user:
        messagebox.showerror("Erreur", "Sélectionne un élève d'abord")
        return
    try:
        date = app.cycle_date_entry.get_date()
        dose_testo = app.cycle_entries["Dose testo (mg/sem)"].get().strip() or "0"
        hcg = app.cycle_entries["hCG (UI/sem)"].get().strip() or "0"
        phase = app.cycle_entries["Phase (blast/cruise)"].get().strip()
        note = app.cycle_note_text.get("1.0", tk.END).strip()
        user_dir = _ensure_user_dir(app)
        fichier = os.path.join(user_dir, "cycle.csv")
        with open(fichier, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([date, dose_testo, hcg, phase, note])
        messagebox.showinfo("Succès", "Cycle sauvegardé")
    except Exception as e:
        messagebox.showerror("Erreur", str(e))