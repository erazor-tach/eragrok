# data/entrainement_module.py
# Écran d'entraînement : calendrier + groupes + catalogue + programmation jour/semaine/mois
# Corrections finales : affichage explicite des dates dans le planning, gestion des entrées sans date,
# bouton "Assigner la date sélectionnée", lecture/écriture robustes, Mode Débutant, templates.

import os
import csv
from pathlib import Path
import datetime
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import Calendar

from data import utils
from data import training_techniques as tt

DATE_FORMAT = "%d/%m/%Y"

def _ensure_user_dir(app):
    user_dir = os.path.join(utils.USERS_DIR, app.current_user)
    Path(user_dir).mkdir(parents=True, exist_ok=True)
    return user_dir

def _format_tech_label(t):
    return f"{t['nom']} — {t.get('reps','—')} — {t.get('charge','—')} ({t['id']})"

_BEGINNER_DESCRIPTIONS = {
    "series_10_12_standard": {
        "title": "Séries 10–12 (standard)",
        "what": "Bloc de 3–4 séries de 10–12 répétitions pour développer le volume musculaire.",
        "how": "Charge modérée (60–75% 1RM), cadence contrôlée, repos 60–90 s.",
        "tips": "Priorise la technique; commence par exercices composés puis blocs 10–12.",
        "warnings": "Évite d'aller systématiquement à l'échec sur les mouvements lourds."
    },
    "bfr": {
        "title": "Blood Flow Restriction (BFR)",
        "what": "Travail à faible charge avec occlusion partielle pour augmenter le pump.",
        "how": "Charges légères, répétitions élevées; utiliser bandes adaptées.",
        "tips": "Utilise en complément, pas sur exercices très lourds.",
        "warnings": "Consulter si antécédents vasculaires; ne pas serrer excessivement."
    }
}

def _get_beginner_text(tid, tech):
    b = _BEGINNER_DESCRIPTIONS.get(tid)
    if b:
        return f"{b['title']}\n\nQu'est-ce que c'est ?\n{b['what']}\n\nComment faire (simple) :\n{b['how']}\n\nConseils :\n{b['tips']}\n\nPrécautions :\n{b['warnings']}"
    title = tech.get('nom', 'Technique')
    what = tech.get('objectif', 'Objectif non spécifié.')
    how = f"Répétitions : {tech.get('reps','—')} ; Charge : {tech.get('charge','—')} ; Repos : {tech.get('repos','—')}"
    tips = "Commence léger, priorise la technique, augmente progressivement la charge ou le volume."
    warnings = "Évite les techniques avancées sans supervision; respecte la récupération."
    return f"{title}\n\nQu'est-ce que c'est ?\n{what}\n\nComment faire (simple) :\n{how}\n\nConseils :\n{tips}\n\nPrécautions :\n{warnings}"

# ----------------- Schedule storage helpers -----------------
def _schedule_file_for_user(app):
    user_dir = _ensure_user_dir(app)
    return os.path.join(user_dir, "entrainement.csv")

def _read_schedule(app):
    """
    Lit le fichier d'entrainement et normalise les dates.
    Retourne une liste d'entrées : {date (str or None), groupes, program, types, note, line}
    date == None signifie 'sans date'.
    """
    fichier = _schedule_file_for_user(app)
    entries = []
    if not os.path.exists(fichier):
        return entries

    def _parse_date_flexible(s):
        if not s:
            return None
        s = s.strip()
        fmts = ("%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d")
        for fmt in fmts:
            try:
                d = datetime.datetime.strptime(s, fmt).date()
                return d.strftime(DATE_FORMAT)
            except Exception:
                pass
        parts = [p for p in s.replace('-', '/').split('/') if p.strip().isdigit()]
        try:
            if len(parts) == 3:
                d, m, y = map(int, parts)
                if y < 100:
                    y += 2000 if y < 70 else 1900
                return datetime.date(y, m, d).strftime(DATE_FORMAT)
        except Exception:
            pass
        return None

    try:
        with open(fichier, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader, None)
            for row in reader:
                if not row:
                    continue
                raw_date = row[0] if len(row) > 0 else ""
                date_norm = _parse_date_flexible(raw_date)
                date_field = date_norm if date_norm else None
                groupes = row[1] if len(row) > 1 else ""
                program = row[2] if len(row) > 2 else ""
                types = row[3] if len(row) > 3 else ""
                note = row[4] if len(row) > 4 else ""
                line = row[5] if len(row) > 5 else ""
                entries.append({"date": date_field, "groupes": groupes, "program": program, "types": types, "note": note, "line": line})
    except Exception:
        return entries
    return entries

def _write_schedule_entry(app, date_str, line, groupes="", program="", types="", note=""):
    fichier = _schedule_file_for_user(app)
    new_file = not os.path.exists(fichier)
    with open(fichier, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if new_file:
            writer.writerow(["Date", "Groupes", "Programme", "Types", "Note", "Line"])
        writer.writerow([date_str or "", groupes, program, types, note, line])

def _delete_schedule_entry(app, date_str, line_text):
    fichier = _schedule_file_for_user(app)
    if not os.path.exists(fichier):
        return
    try:
        with open(fichier, 'r', newline='', encoding='utf-8') as f:
            rows = list(csv.reader(f))
        header = rows[0] if rows else []
        data = rows[1:] if len(rows) > 1 else []
        new_data = [r for r in data if not (len(r) > 0 and (r[0].strip() == (date_str or "").strip()) and (len(r) <=5 or r[5] == line_text))]
        with open(fichier, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if header:
                writer.writerow(header)
            for r in new_data:
                writer.writerow(r)
    except Exception:
        pass

# ----------------- UI principal -----------------
def show_entrainement_screen(app, program=None):
    for w in app.content.winfo_children():
        w.destroy()

    tk.Label(app.content, text=f"ENTRAÎNEMENT - Élève : {getattr(app, 'selected_user_name', '—')}",
             font=("Helvetica", 20, "bold"), bg="#f3f4f6", fg="#0f172a").pack(pady=12)

    top = tk.Frame(app.content, bg="#f3f4f6")
    top.pack(fill='x', padx=20)
    tk.Label(top, text="Programme :", bg="#f3f4f6").pack(side='left')
    app.program_selected_var = tk.StringVar(value=program if program else "Standard")
    prog_combo = ttk.Combobox(top, values=["Standard", "Sarco", "Myofi"], textvariable=app.program_selected_var, state="readonly", width=18)
    prog_combo.pack(side='left', padx=8)
    ttk.Button(top, text="Charger", command=lambda: _load_program(app, app.program_selected_var.get())).pack(side='left', padx=6)
    ttk.Button(top, text="Retour Dashboard", command=getattr(app, "show_dashboard", lambda: None)).pack(side='right')

    view_frame = tk.Frame(app.content, bg="#f3f4f6")
    view_frame.pack(fill='x', padx=20, pady=(6,0))
    tk.Label(view_frame, text="Vue :", bg="#f3f4f6").pack(side='left')
    app.view_mode_var = tk.StringVar(value="Jour")
    for m in ["Jour", "Semaine", "Mois"]:
        ttk.Radiobutton(view_frame, text=m, value=m, variable=app.view_mode_var, command=lambda: _refresh_schedule_view(app)).pack(side='left', padx=6)

    app.beginner_mode_var = tk.BooleanVar(value=True)
    cb = tk.Checkbutton(view_frame, text="Mode Débutant", variable=app.beginner_mode_var, bg="#f3f4f6")
    cb.pack(side='right')

    main = tk.Frame(app.content, bg="#f3f4f6")
    main.pack(fill='both', expand=True, padx=20, pady=10)
    main.columnconfigure(0, weight=0)
    main.columnconfigure(1, weight=1)
    main.columnconfigure(2, weight=1)

    # Left: calendar + groupes
    left_zone = tk.Frame(main, bg="#f3f4f6")
    left_zone.grid(row=0, column=0, sticky='ns', padx=(0,12))
    cal_frame = tk.Frame(left_zone, bg="#f3f4f6")
    cal_frame.pack(pady=8)
    app.calendar = Calendar(cal_frame, selectmode='day')
    app.calendar.pack()
    app.calendar.bind("<<CalendarSelected>>", lambda ev: _on_calendar_select(app))

    groupes_frame = tk.Frame(left_zone, bg="#f3f4f6")
    groupes_frame.pack(anchor='w', pady=(10,6))
    tk.Label(groupes_frame, text="Groupes musculaires :", font=("Helvetica", 12, "bold"), bg="#f3f4f6").pack(anchor='w')
    app.groupes_vars = {}
    groupes = ["Pecs", "Dos", "Cuisses", "Épaules", "Bras", "Full body", "Alpha body"]
    chk_frame = tk.Frame(groupes_frame, bg="#f3f4f6")
    chk_frame.pack(anchor='w', pady=6)
    for i, g in enumerate(groupes):
        var = tk.BooleanVar()
        cbg = tk.Checkbutton(chk_frame, text=g, variable=var, bg="#f3f4f6", anchor='w')
        cbg.grid(row=i//2, column=i%2, sticky='w', padx=8, pady=4)
        app.groupes_vars[g] = var

    # Center: catalogue
    center = tk.Frame(main, bg="#ffffff", bd=1, relief='solid')
    center.grid(row=0, column=1, sticky='nsew', padx=(0,12), pady=4)
    tk.Label(center, text="Catalogue des techniques", font=("Helvetica", 12, "bold"), bg="#ffffff").pack(anchor='w', padx=8, pady=(8,4))
    search_frame = tk.Frame(center, bg="#ffffff")
    search_frame.pack(fill='x', padx=8)
    tk.Label(search_frame, text="Rechercher :", bg="#ffffff").pack(side='left')
    app.tech_search_var = tk.StringVar()
    search_entry = ttk.Entry(search_frame, textvariable=app.tech_search_var, width=28)
    search_entry.pack(side='left', padx=6)
    ttk.Button(search_frame, text="Effacer", command=lambda: app.tech_search_var.set("")).pack(side='left', padx=4)
    tree_frame = tk.Frame(center, bg="#ffffff")
    tree_frame.pack(fill='both', expand=True, padx=8, pady=8)
    app.tech_tree = ttk.Treeview(tree_frame, show='tree')
    vsb = ttk.Scrollbar(tree_frame, orient='vertical', command=app.tech_tree.yview)
    app.tech_tree.configure(yscrollcommand=vsb.set)
    app.tech_tree.pack(side='left', fill='both', expand=True)
    vsb.pack(side='right', fill='y')
    app.tech_tree.bind("<<TreeviewSelect>>", lambda ev: _on_tech_select(app))
    app.tech_search_var.trace_add('write', lambda *a: _refresh_tech_tree(app))

    # Right: schedule + detail + programme
    right = tk.Frame(main, bg="#ffffff", bd=1, relief='solid')
    right.grid(row=0, column=2, sticky='nsew', pady=4)
    tk.Label(right, text="Planning", font=("Helvetica", 12, "bold"), bg="#ffffff").pack(anchor='w', padx=8, pady=(8,4))

    app.schedule_listbox = tk.Listbox(right, height=12)
    app.schedule_listbox.pack(fill='both', expand=False, padx=8, pady=(0,8))
    app.schedule_listbox.bind("<Double-1>", lambda ev: _on_schedule_double_click(app))

    schedule_btn_frame = tk.Frame(right, bg="#ffffff")
    schedule_btn_frame.pack(fill='x', padx=8, pady=(0,8))
    ttk.Button(schedule_btn_frame, text="Ajouter à la date sélectionnée", command=lambda: _add_selected_to_selected_date(app)).pack(side='left', padx=6)
    ttk.Button(schedule_btn_frame, text="Assigner la date sélectionnée", command=lambda: _assign_date_to_entry(app)).pack(side='left', padx=6)
    ttk.Button(schedule_btn_frame, text="Supprimer sélection", command=lambda: _delete_selected_schedule_item(app)).pack(side='left', padx=6)
    ttk.Button(schedule_btn_frame, text="Charger template Sarco", command=lambda: _load_program(app, "Sarco")).pack(side='left', padx=6)

    tk.Label(right, text="Détail (Mode Débutant si activé)", font=("Helvetica", 12, "bold"), bg="#ffffff").pack(anchor='w', padx=8, pady=(4,4))
    app.detail_text = tk.Text(right, height=10, wrap='word')
    app.detail_text.pack(fill='both', expand=True, padx=8, pady=(0,8))
    app.detail_text.config(state='disabled')

    # Programme listbox (créé avant tout appel à _load_program)
    tk.Label(right, text="Programme (séances)", font=("Helvetica", 12, "bold"), bg="#ffffff").pack(anchor='w', padx=8, pady=(4,4))
    app.program_listbox = tk.Listbox(right, height=8)
    app.program_listbox.pack(fill='both', expand=True, padx=8, pady=(0,8))
    app.program_listbox.bind("<Double-1>", lambda ev: _on_program_list_double_click(app))

    prog_btn_frame = tk.Frame(right, bg="#ffffff")
    prog_btn_frame.pack(anchor='w', pady=8, padx=8)
    ttk.Button(prog_btn_frame, text="Ajouter technique sélectionnée", command=lambda: _add_selected_tech_to_program(app)).pack(side='left', padx=6)
    ttk.Button(prog_btn_frame, text="Supprimer", command=lambda: _remove_selected_program_item(app)).pack(side='left', padx=6)
    ttk.Button(prog_btn_frame, text="Charger template", command=lambda: _load_program(app, app.program_selected_var.get())).pack(side='left', padx=6)

    app.note_text = tk.Text(app.content, height=4, width=120)
    app.note_text.pack(padx=20, pady=(6,12))
    ttk.Button(app.content, text="SAUVEGARDER ENTRAÎNEMENT", command=lambda: _sauvegarder_entrainement(app)).pack(pady=8)

    # initial load
    app._schedule_entries = _read_schedule(app)
    try:
        today = datetime.date.today()
        app.calendar.selection_set(today)
    except Exception:
        pass
    _refresh_tech_tree(app)
    _refresh_schedule_view(app)
    _load_program(app, app.program_selected_var.get())

# ----------------- catalogue -----------------
def _refresh_tech_tree(app):
    tree = app.tech_tree
    for iid in tree.get_children():
        tree.delete(iid)
    query = app.tech_search_var.get().lower().strip()
    all_tech = tt.get_all_techniques()
    cats = {"SARCOPLASMIQUE": [], "MIXTE": [], "MYOFIBRILLAIRE": []}
    for t in all_tech:
        cats.setdefault(t["categorie"], []).append(t)
    for cat in ["SARCOPLASMIQUE", "MIXTE", "MYOFIBRILLAIRE"]:
        items = cats.get(cat, [])
        if not items:
            continue
        parent = tree.insert("", "end", text=f"{cat} ({len(items)})", open=True)
        for t in items:
            label = _format_tech_label(t)
            if query:
                hay = " ".join([t.get("nom",""), t.get("id",""), t.get("reps",""), t.get("notes","")]).lower()
                if query not in hay:
                    continue
            tree.insert(parent, "end", text=label, values=(t["id"],), tags=(t["id"],))

def _on_tech_select(app):
    sel = app.tech_tree.selection()
    if not sel:
        return
    text = app.tech_tree.item(sel[0], 'text')
    tid = None
    if "(" in text and ")" in text:
        tid = text.split("(")[-1].split(")")[0].strip()
    if not tid:
        tags = app.tech_tree.item(sel[0], 'tags') or []
        if tags:
            tid = tags[0]
    tech = tt.find_technique_by_id(tid) if tid else None
    app._last_selected_tech_id = tech["id"] if tech else None

    if getattr(app, "beginner_mode_var", tk.BooleanVar(value=False)).get():
        text_block = _get_beginner_text(tid, tech) if tech else "Sélectionne une technique pour voir les explications simples."
    else:
        if tech:
            text_block = f"{tech.get('nom','—')}\n\nReps: {tech.get('reps','—')}\nCharge: {tech.get('charge','—')}\nRepos: {tech.get('repos','—')}\nObjectif: {tech.get('objectif','—')}\n\nNotes:\n{tech.get('notes','')}"
        else:
            text_block = "Sélectionne une technique pour voir le détail."
    app.detail_text.config(state='normal')
    app.detail_text.delete("1.0", tk.END)
    app.detail_text.insert("1.0", text_block)
    app.detail_text.config(state='disabled')

# ----------------- schedule view and actions -----------------
def _on_calendar_select(app):
    _refresh_schedule_view(app)

def _refresh_schedule_view(app):
    app._schedule_entries = _read_schedule(app)
    mode = app.view_mode_var.get() if hasattr(app, "view_mode_var") else "Jour"
    try:
        sel_date = app.calendar.selection_get()
        if not isinstance(sel_date, datetime.date):
            sel_date = datetime.datetime.strptime(app.calendar.get_date(), DATE_FORMAT).date()
    except Exception:
        sel_date = datetime.date.today()
    app._selected_date = sel_date
    app.schedule_listbox.delete(0, tk.END)

    def _insert_line(text):
        app.schedule_listbox.insert(tk.END, text)

    if mode == "Jour":
        date_str = sel_date.strftime(DATE_FORMAT)
        entries = [e for e in app._schedule_entries if e.get("date") == date_str]
        undated = [e for e in app._schedule_entries if e.get("date") is None]
        if not entries:
            _insert_line(f"Aucune séance programmée pour {date_str}")
        else:
            for e in entries:
                # display with explicit date to avoid confusion
                display = f"{date_str} — {e.get('line') or e.get('program') or e.get('types')}"
                _insert_line(display)
        if undated:
            _insert_line("")  # séparation visuelle
            _insert_line("Entrées sans date (sélectionne et clique 'Assigner la date sélectionnée') :")
            for e in undated:
                _insert_line("[Sans date] " + (e.get("line") or e.get("program") or "—"))
    elif mode == "Semaine":
        start = sel_date - datetime.timedelta(days=sel_date.weekday())
        days = [start + datetime.timedelta(days=i) for i in range(7)]
        for d in days:
            ds = d.strftime(DATE_FORMAT)
            day_entries = [e for e in app._schedule_entries if e.get("date") == ds]
            _insert_line(f"--- {ds} ({d.strftime('%a')}) ---")
            if not day_entries:
                _insert_line("  (aucune)")
            else:
                for e in day_entries:
                    display = f"{ds} — {e.get('line') or e.get('program') or e.get('types')}"
                    _insert_line("  " + display)
        undated = [e for e in app._schedule_entries if e.get("date") is None]
        if undated:
            _insert_line("")
            _insert_line("Entrées sans date :")
            for e in undated:
                _insert_line("  [Sans date] " + (e.get("line") or ""))
    else:
        first = sel_date.replace(day=1)
        next_month = first.replace(day=28) + datetime.timedelta(days=4)
        last = next_month - datetime.timedelta(days=next_month.day)
        for day in range(1, last.day + 1):
            d = first.replace(day=day)
            ds = d.strftime(DATE_FORMAT)
            day_entries = [e for e in app._schedule_entries if e.get("date") == ds]
            if day_entries:
                _insert_line(f"--- {ds} ---")
                for e in day_entries:
                    display = f"{ds} — {e.get('line') or e.get('program') or e.get('types')}"
                    _insert_line("  " + display)
        undated = [e for e in app._schedule_entries if e.get("date") is None]
        if undated:
            _insert_line("")
            _insert_line("Entrées sans date :")
            for e in undated:
                _insert_line("  [Sans date] " + (e.get("line") or ""))

def _add_selected_to_selected_date(app):
    tid = getattr(app, "_last_selected_tech_id", None)
    if not tid:
        messagebox.showinfo("Info", "Sélectionne une technique dans le catalogue.")
        return
    tech = tt.find_technique_by_id(tid)
    if not tech:
        messagebox.showerror("Erreur", "Technique introuvable.")
        return
    try:
        sel_date = app.calendar.selection_get()
        if not isinstance(sel_date, datetime.date):
            sel_date = datetime.datetime.strptime(app.calendar.get_date(), DATE_FORMAT).date()
    except Exception:
        sel_date = datetime.date.today()
    date_str = sel_date.strftime(DATE_FORMAT)
    groupes = ", ".join([g for g, v in app.groupes_vars.items() if v.get()]) if getattr(app, "groupes_vars", None) else ""
    program = app.program_selected_var.get() if hasattr(app, "program_selected_var") else ""
    types = f"{tech.get('categorie','')}"
    line = f"{tech['nom']} [{tech.get('reps','—')}] | {tech.get('charge','—')} ({tech['id']})"
    _write_schedule_entry(app, date_str, line, groupes=groupes, program=program, types=types, note="")
    app._schedule_entries = _read_schedule(app)
    _refresh_schedule_view(app)
    messagebox.showinfo("Ajouté", f"Technique ajoutée pour le {date_str}.")

def _assign_date_to_entry(app):
    sel = app.schedule_listbox.curselection()
    if not sel:
        messagebox.showinfo("Info", "Sélectionne d'abord une ligne sans date.")
        return
    idx = sel[0]
    text = app.schedule_listbox.get(idx)
    if not text or "[Sans date]" not in text:
        messagebox.showinfo("Info", "Sélectionne une entrée marquée [Sans date].")
        return
    line_text = text.split("[Sans date]")[-1].strip()
    try:
        sel_date = app.calendar.selection_get()
        if not isinstance(sel_date, datetime.date):
            sel_date = datetime.datetime.strptime(app.calendar.get_date(), DATE_FORMAT).date()
    except Exception:
        sel_date = datetime.date.today()
    date_str = sel_date.strftime(DATE_FORMAT)
    fichier = _schedule_file_for_user(app)
    if not os.path.exists(fichier):
        messagebox.showerror("Erreur", "Fichier introuvable.")
        return
    try:
        with open(fichier, 'r', newline='', encoding='utf-8') as f:
            rows = list(csv.reader(f))
        header = rows[0] if rows else []
        data = rows[1:] if len(rows) > 1 else []
        updated = False
        for i, r in enumerate(data):
            line_field = r[5] if len(r) > 5 else ""
            date_field = r[0] if len(r) > 0 else ""
            if (not date_field or date_field.strip() == "") and line_field.strip() == line_text:
                while len(r) < 6:
                    r.append("")
                r[0] = date_str
                data[i] = r
                updated = True
                break
        if updated:
            with open(fichier, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                if header:
                    writer.writerow(header)
                for r in data:
                    writer.writerow(r)
            app._schedule_entries = _read_schedule(app)
            _refresh_schedule_view(app)
            messagebox.showinfo("Succès", f"Date assignée : {date_str}")
        else:
            messagebox.showerror("Erreur", "Impossible de trouver l'entrée correspondante dans le fichier.")
    except Exception as e:
        messagebox.showerror("Erreur", f"Impossible d'assigner la date : {e}")

def _delete_selected_schedule_item(app):
    sel = app.schedule_listbox.curselection()
    if not sel:
        messagebox.showinfo("Info", "Sélectionne une ligne du planning à supprimer.")
        return
    idx = sel[0]
    text = app.schedule_listbox.get(idx)
    mode = app.view_mode_var.get() if hasattr(app, "view_mode_var") else "Jour"
    if mode == "Jour":
        try:
            sel_date = app.calendar.selection_get()
            if not isinstance(sel_date, datetime.date):
                sel_date = datetime.datetime.strptime(app.calendar.get_date(), DATE_FORMAT).date()
        except Exception:
            sel_date = datetime.date.today()
        date_str = sel_date.strftime(DATE_FORMAT)
        if text.startswith("Aucune séance"):
            return
        # if it's an undated entry, remove by matching line text without prefix
        if "[Sans date]" in text:
            line_text = text.split("[Sans date]")[-1].strip()
            _delete_schedule_entry(app, "", line_text)
        else:
            # remove by date + line (strip date prefix if present)
            if "—" in text:
                # format "DD/MM/YYYY — line"
                parts = text.split("—", 1)
                line_text = parts[1].strip() if len(parts) > 1 else text.strip()
            else:
                line_text = text.strip()
            _delete_schedule_entry(app, date_str, line_text)
        app._schedule_entries = _read_schedule(app)
        _refresh_schedule_view(app)
        messagebox.showinfo("Supprimé", "La séance a été supprimée.")
    else:
        list_items = app.schedule_listbox.get(0, tk.END)
        date_str = None
        for i in range(idx, -1, -1):
            it = list_items[i]
            if it.startswith("--- ") and it.endswith(" ---"):
                date_str = it.strip().strip("- ").strip()
                break
        if not date_str:
            messagebox.showerror("Erreur", "Impossible d'identifier la date de la ligne sélectionnée.")
            return
        line_text = text.strip()
        if line_text == "(aucune)":
            return
        # remove indentation if present
        line_text = line_text.lstrip()
        if line_text.startswith("[Sans date]"):
            line_text = line_text.split("[Sans date]")[-1].strip()
            _delete_schedule_entry(app, "", line_text)
        else:
            if "—" in line_text:
                parts = line_text.split("—", 1)
                line_text = parts[1].strip() if len(parts) > 1 else line_text
            _delete_schedule_entry(app, date_str, line_text)
        app._schedule_entries = _read_schedule(app)
        _refresh_schedule_view(app)
        messagebox.showinfo("Supprimé", f"Entrée supprimée pour {date_str}.")

def _on_schedule_double_click(app):
    sel = app.schedule_listbox.curselection()
    if not sel:
        return
    text = app.schedule_listbox.get(sel[0])
    if text.startswith("---") or text.strip().startswith("(aucune)") or text.startswith("Aucune séance"):
        return
    # try to extract tid from the displayed line (we display "(id)" at end)
    tid = None
    if "(" in text and ")" in text:
        # find last parentheses content
        try:
            tid = text.split("(")[-1].split(")")[0].strip()
        except Exception:
            tid = None
    tech = tt.find_technique_by_id(tid) if tid else None
    if tech:
        _open_tech_detail_dialog(app, tech)
    else:
        dlg = tk.Toplevel()
        dlg.title("Détail")
        dlg.transient(app.root if hasattr(app, "root") else app.content)
        tk.Label(dlg, text=text, wraplength=600, justify='left').pack(padx=12, pady=12)
        ttk.Button(dlg, text="Fermer", command=dlg.destroy).pack(pady=(0,12))

# ----------------- program templates -----------------
def _on_program_change(app):
    if not hasattr(app, "program_listbox"):
        return
    _load_program(app, app.program_selected_var.get())

def _load_program(app, name):
    if not hasattr(app, "program_listbox"):
        return
    app.program_listbox.delete(0, tk.END)
    if name in ["Sarco", "Myofi"]:
        template = tt.build_program_template(name, weeks=4)
        for w in template["weeks"]:
            app.program_listbox.insert(tk.END, f"--- Semaine {w['week']} ---")
            for s in w["sessions"]:
                app.program_listbox.insert(tk.END, f"  Séance {s['session']}")
                for ex in s["exercises"]:
                    tech = tt.find_technique_by_id(ex["id"])
                    if tech:
                        line = f"    {tech['nom']} [{tech['reps']}] | {tech['charge']} ({tech['id']})"
                    else:
                        line = f"    {ex.get('nom','—')} [{ex.get('reps','—')}]"
                    app.program_listbox.insert(tk.END, line)
    else:
        app.program_listbox.insert(tk.END, "Standard - Jour A : Pecs/Dos 4x8-10")
        app.program_listbox.insert(tk.END, "Standard - Jour B : Jambes 4x8-10")
        app.program_listbox.insert(tk.END, "Standard - Jour C : Épaules/Arms 4x8-10")

# ----------------- programme actions -----------------
def _add_selected_tech_to_program(app):
    tid = getattr(app, "_last_selected_tech_id", None)
    if not tid:
        messagebox.showinfo("Info", "Sélectionne une technique dans le catalogue.")
        return
    tech = tt.find_technique_by_id(tid)
    line = f"{tech['nom']} [{tech.get('reps','—')}] | {tech.get('charge','—')} ({tech['id']})"
    app.program_listbox.insert(tk.END, line)

def _remove_selected_program_item(app):
    sel = app.program_listbox.curselection()
    if not sel:
        return
    for i in reversed(sel):
        app.program_listbox.delete(i)

def _on_program_list_double_click(app):
    sel = app.program_listbox.curselection()
    if not sel:
        return
    line = app.program_listbox.get(sel[0])
    tid = None
    if "(" in line and ")" in line:
        tid = line.split("(")[-1].split(")")[0].strip()
    tech = tt.find_technique_by_id(tid) if tid else None
    if tech:
        _open_tech_detail_dialog(app, tech)
    else:
        dlg = tk.Toplevel()
        dlg.title("Détail")
        dlg.transient(app.root if hasattr(app, "root") else app.content)
        tk.Label(dlg, text=line, wraplength=600, justify='left').pack(padx=12, pady=12)
        ttk.Button(dlg, text="Fermer", command=dlg.destroy).pack(pady=(0,12))

def _open_tech_detail_dialog(app, tech):
    dlg = tk.Toplevel()
    dlg.title(tech["nom"])
    dlg.geometry("520x520")
    tk.Label(dlg, text=tech["nom"], font=("Helvetica", 14, "bold")).pack(pady=8)
    tk.Label(dlg, text=f"ID : {tech['id']}").pack()
    tk.Label(dlg, text=f"Catégorie : {tech['categorie']}").pack()
    tk.Label(dlg, text=f"Reps : {tech['reps']}").pack()
    tk.Label(dlg, text=f"Charge : {tech['charge']}").pack()
    tk.Label(dlg, text=f"Repos : {tech['repos']}").pack()
    tk.Label(dlg, text=f"Objectif : {tech['objectif']}").pack()
    tk.Label(dlg, text="Notes :", font=("Helvetica", 12, "bold")).pack(pady=(10,0))
    txt = tk.Text(dlg, height=10, width=64, wrap='word')
    txt.pack(padx=8, pady=(4,8))
    if getattr(app, "beginner_mode_var", tk.BooleanVar(value=False)).get():
        txt.insert("1.0", _get_beginner_text(tech.get('id'), tech) + "\n\n---\n\nDétails techniques complets :\n" + tech.get("notes",""))
    else:
        txt.insert("1.0", tech.get("notes",""))
    txt.config(state='disabled')
    ttk.Button(dlg, text="Fermer", command=dlg.destroy).pack(pady=8)

# ----------------- save whole training -----------------
def _sauvegarder_entrainement(app):
    if not getattr(app, "current_user", None):
        messagebox.showerror("Erreur", "Sélectionne un élève d'abord")
        return
    try:
        sel_date = app.calendar.selection_get()
        if not isinstance(sel_date, datetime.date):
            sel_date = datetime.datetime.strptime(app.calendar.get_date(), DATE_FORMAT).date()
    except Exception:
        sel_date = datetime.date.today()
    date_str = sel_date.strftime(DATE_FORMAT)
    groupes = ", ".join([g for g, v in app.groupes_vars.items() if v.get()]) if getattr(app, "groupes_vars", None) else ""
    program = app.program_selected_var.get() if hasattr(app, "program_selected_var") else ""
    note = app.note_text.get("1.0", tk.END).strip()
    raw_lines = [app.program_listbox.get(i) for i in range(app.program_listbox.size())] if hasattr(app, "program_listbox") else []
    lines = []
    for ln in raw_lines:
        s = ln.strip()
        if not s:
            continue
        if s.startswith("---") or s.lower().startswith("standard -") or s.strip().startswith("Séance") or s.strip().startswith("Séance"):
            continue
        lines.append(s)
    for line in lines:
        _write_schedule_entry(app, date_str, line, groupes=groupes, program=program, types="", note=note)
    app._schedule_entries = _read_schedule(app)
    _refresh_schedule_view(app)
    messagebox.showinfo("Succès", f"{len(lines)} ligne(s) sauvegardées pour {date_str}.")

