# data/entrainement_module.py
# -*- coding: utf-8 -*-
"""
Écran d'entraînement — UI uniquement.
La persistence est déléguée à :
  • entrainement_schedule.py  (CSV planning)
  • entrainement_history.py   (JSON historique)
  • entrainement_pdf.py       (export PDF)
"""

import os
import calendar
import datetime
import random
import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from tkcalendar import Calendar

from data import utils
from data import training_techniques as tt
from data import entrainement_schedule as sched
from data import entrainement_history  as hist
from data import entrainement_pdf      as pdf_mod

DATE_FORMAT   = "%d/%m/%Y"
WEEKEND_OPT   = ["Off", "Pecs", "Cuisses", "Épaules", "Dos", "Bras"]
WEEKDAY_FR    = {0:"Lundi", 1:"Mardi", 2:"Mercredi", 3:"Jeudi",
                 4:"Vendredi", 5:"Samedi", 6:"Dimanche"}
DAY_TO_GROUP  = {0:"Pectoraux", 1:"Cuisses", 2:"Épaules", 3:"Dos", 4:"Bras"}


# ══════════════════════════════════════════════════════════════════════════════
#  DESCRIPTIONS PÉDAGOGIQUES
# ══════════════════════════════════════════════════════════════════════════════

_BEGINNER = {
    "series_10_12_standard": {
        "title":    "Séries 10–12 (standard)",
        "what":     "Bloc de 3–4 séries de 10–12 répétitions pour développer le volume musculaire.",
        "how":      "Charge modérée (60–75% 1RM), cadence contrôlée, repos 60–90 s.",
        "tips":     "Priorise la technique; commence par exercices composés puis blocs 10–12.",
        "warnings": "Évite d'aller systématiquement à l'échec sur les mouvements lourds.",
    },
    "bfr": {
        "title":    "Blood Flow Restriction (BFR)",
        "what":     "Travail à faible charge avec occlusion partielle pour augmenter le pump.",
        "how":      "Charges légères, répétitions élevées; utiliser bandes adaptées.",
        "tips":     "Utilise en complément, pas sur exercices très lourds.",
        "warnings": "Consulter si antécédents vasculaires; ne pas serrer excessivement.",
    },
}

def _beginner_text(tid: str, tech: dict) -> str:
    b = _BEGINNER.get(tid)
    if b:
        return (
            f"{b['title']}\n\nQu'est-ce que c'est ?\n{b['what']}\n\n"
            f"Comment faire :\n{b['how']}\n\nConseils :\n{b['tips']}\n\n"
            f"Précautions :\n{b['warnings']}"
        )
    if not tech:
        return "Sélectionne une technique pour voir les explications."
    return (
        f"{tech.get('nom','Technique')}\n\n"
        f"Qu'est-ce que c'est ?\n{tech.get('objectif','—')}\n\n"
        f"Comment faire :\n"
        f"Répétitions : {tech.get('reps','—')} ; "
        f"Charge : {tech.get('charge','—')} ; "
        f"Repos : {tech.get('repos','—')}\n\n"
        f"Conseils :\nCommence léger, priorise la technique.\n\n"
        f"Précautions :\nRespectez la récupération."
    )


# ══════════════════════════════════════════════════════════════════════════════
#  ROTATION
# ══════════════════════════════════════════════════════════════════════════════

def _build_rotation(pool: list) -> list[str]:
    seen, ids = set(), []
    for t in pool:
        tid = t.get("id")
        if tid and tid not in seen:
            seen.add(tid); ids.append(tid)
    random.shuffle(ids)
    return ids


class _RotationIter:
    def __init__(self, pool):
        self.pool = pool or []
        self._reset()

    def _reset(self):
        self._rot = _build_rotation(self.pool)
        self._idx = 0

    def next(self) -> str | None:
        if not self._rot or self._idx >= len(self._rot):
            self._reset()
        if not self._rot:
            return None
        val = self._rot[self._idx]
        self._idx += 1
        return val

    def all_ids(self) -> list[str]:
        return list(self._rot)


# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS FORMAT / CATALOGUE
# ══════════════════════════════════════════════════════════════════════════════

def _tech_label(t: dict) -> str:
    return f"{t['nom']} — {t.get('reps','—')} — {t.get('charge','—')} ({t['id']})"


def _tech_line(tech: dict) -> str:
    return (
        f"{tech['nom']} [{tech.get('reps','—')}] | "
        f"{tech.get('charge','—')} ({tech['id']})"
    )


def _pool_for_cats(cats: list[str]) -> list[dict]:
    wanted = {c.upper() for c in cats}
    seen, pool = set(), []
    for t in tt.get_all_techniques():
        cat = (t.get("categorie") or "").upper()
        tid = t.get("id")
        if tid and cat in wanted and tid not in seen:
            pool.append(t); seen.add(tid)
    return pool


def _selected_cats(app) -> list[str]:
    cats = []
    if getattr(app, "gen_cat_sarco", tk.BooleanVar()).get(): cats.append("SARCOPLASMIQUE")
    if getattr(app, "gen_cat_mixte",  tk.BooleanVar()).get(): cats.append("MIXTE")
    if getattr(app, "gen_cat_myofi",  tk.BooleanVar()).get(): cats.append("MYOFIBRILLAIRE")
    return cats


def _weekend_for_day(app, weekday: int) -> str:
    if weekday == 5: return getattr(app, "gen_saturday_var", tk.StringVar(value="Off")).get()
    if weekday == 6: return getattr(app, "gen_sunday_var",   tk.StringVar(value="Off")).get()
    return "Off"


def _sel_date(app) -> datetime.date:
    try:
        d = app.calendar.selection_get()
        if isinstance(d, datetime.date):
            return d
    except Exception:
        pass
    try:
        return datetime.datetime.strptime(app.calendar.get_date(), DATE_FORMAT).date()
    except Exception:
        return datetime.date.today()


# ══════════════════════════════════════════════════════════════════════════════
#  ÉCRAN PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════

def show_entrainement_screen(app, program=None):
    for w in app.content.winfo_children():
        w.destroy()

    tk.Label(app.content,
             text=f"ENTRAÎNEMENT — {getattr(app,'selected_user_name','—')}",
             font=("Helvetica", 20, "bold"), bg="#f3f4f6", fg="#0f172a").pack(pady=12)

    # ── Barre supérieure ─────────────────────────────────────────────────────
    top = tk.Frame(app.content, bg="#f3f4f6"); top.pack(fill="x", padx=20)
    tk.Label(top, text="Programme :", bg="#f3f4f6").pack(side="left")
    app.program_selected_var = tk.StringVar(value=program or "Standard")
    tk.Label(top, textvariable=app.program_selected_var,
             bg="#f3f4f6", font=("Helvetica", 10, "bold")).pack(side="left", padx=8)
    ttk.Button(top, text="Retour Dashboard",
               command=getattr(app, "show_dashboard", lambda: None)).pack(side="right")

    # ── Vue (Jour / Semaine / Mois) ──────────────────────────────────────────
    view_f = tk.Frame(app.content, bg="#f3f4f6"); view_f.pack(fill="x", padx=20, pady=(6,0))
    tk.Label(view_f, text="Vue :", bg="#f3f4f6").pack(side="left")
    app.view_mode_var = tk.StringVar(value="Jour")
    for m in ["Jour", "Semaine", "Mois"]:
        ttk.Radiobutton(view_f, text=m, value=m, variable=app.view_mode_var,
                        command=lambda: _refresh_schedule(app)).pack(side="left", padx=6)

    # ── Grille principale ────────────────────────────────────────────────────
    main = tk.Frame(app.content, bg="#f3f4f6"); main.pack(fill="both", expand=True, padx=20, pady=10)
    main.columnconfigure(0, weight=0)
    main.columnconfigure(1, weight=1)
    main.columnconfigure(2, weight=1)

    # Colonne gauche : calendrier + groupes musculaires
    _build_left_col(app, main)
    # Colonne centre : catalogue
    _build_centre_col(app, main)
    # Colonne droite : planning + détail + programme + historique
    _build_right_col(app, main)

    # ── Note + Sauvegarder ───────────────────────────────────────────────────
    app.note_text = tk.Text(app.content, height=4, width=120)
    app.note_text.pack(padx=20, pady=(6, 12))
    ttk.Button(app.content, text="SAUVEGARDER ENTRAÎNEMENT",
               command=lambda: _save_training(app)).pack(pady=8)

    # ── Init ─────────────────────────────────────────────────────────────────
    app._schedule_entries = sched.read_schedule(app)
    try:
        app.calendar.selection_set(datetime.date.today())
    except Exception:
        pass
    _refresh_tech_tree(app)
    _refresh_schedule(app)
    _load_program(app, app.program_selected_var.get())
    _history_refresh(app)


# ── Colonne gauche ────────────────────────────────────────────────────────────

def _build_left_col(app, parent):
    left = tk.Frame(parent, bg="#f3f4f6")
    left.grid(row=0, column=0, sticky="ns", padx=(0, 12))

    cal_f = tk.Frame(left, bg="#f3f4f6"); cal_f.pack(pady=8)
    app.calendar = Calendar(cal_f, selectmode="day")
    app.calendar.pack()
    app.calendar.bind("<<CalendarSelected>>", lambda ev: _refresh_schedule(app))

    grp_f = tk.Frame(left, bg="#f3f4f6"); grp_f.pack(anchor="w", pady=(10, 6))
    tk.Label(grp_f, text="Groupes musculaires :",
             font=("Helvetica", 12, "bold"), bg="#f3f4f6").pack(anchor="w")
    app.groupes_vars = {}
    groupes = ["Pecs", "Dos", "Cuisses", "Épaules", "Bras", "Full body", "Alpha body"]
    chk = tk.Frame(grp_f, bg="#f3f4f6"); chk.pack(anchor="w", pady=6)
    for i, g in enumerate(groupes):
        var = tk.BooleanVar()
        tk.Checkbutton(chk, text=g, variable=var, bg="#f3f4f6", anchor="w").grid(
            row=i // 2, column=i % 2, sticky="w", padx=8, pady=4)
        app.groupes_vars[g] = var


# ── Colonne centre ────────────────────────────────────────────────────────────

def _build_centre_col(app, parent):
    center = tk.Frame(parent, bg="#ffffff", bd=1, relief="solid")
    center.grid(row=0, column=1, sticky="nsew", padx=(0, 12), pady=4)

    tk.Label(center, text="Catalogue des techniques",
             font=("Helvetica", 12, "bold"), bg="#ffffff").pack(anchor="w", padx=8, pady=(8, 4))

    sf = tk.Frame(center, bg="#ffffff"); sf.pack(fill="x", padx=8)
    tk.Label(sf, text="Rechercher :", bg="#ffffff").pack(side="left")
    app.tech_search_var = tk.StringVar()
    ttk.Entry(sf, textvariable=app.tech_search_var, width=28).pack(side="left", padx=6)
    ttk.Button(sf, text="Effacer",
               command=lambda: app.tech_search_var.set("")).pack(side="left", padx=4)

    tf = tk.Frame(center, bg="#ffffff"); tf.pack(fill="both", expand=True, padx=8, pady=8)
    app.tech_tree = ttk.Treeview(tf, show="tree")
    vsb = ttk.Scrollbar(tf, orient="vertical", command=app.tech_tree.yview)
    app.tech_tree.configure(yscrollcommand=vsb.set)
    app.tech_tree.pack(side="left", fill="both", expand=True)
    vsb.pack(side="right", fill="y")
    app.tech_tree.bind("<<TreeviewSelect>>", lambda ev: _on_tech_select(app))
    app.tech_search_var.trace_add("write", lambda *a: _refresh_tech_tree(app))


# ── Colonne droite ────────────────────────────────────────────────────────────

def _build_right_col(app, parent):
    right = tk.Frame(parent, bg="#ffffff", bd=1, relief="solid")
    right.grid(row=0, column=2, sticky="nsew", pady=4)

    # Planning
    tk.Label(right, text="Planning", font=("Helvetica", 12, "bold"),
             bg="#ffffff").pack(anchor="w", padx=8, pady=(8, 4))
    app.schedule_listbox = tk.Listbox(right, height=12)
    app.schedule_listbox.pack(fill="both", expand=False, padx=8, pady=(0, 8))
    app.schedule_listbox.bind("<Double-1>", lambda ev: _on_schedule_dbl(app))

    sbf = tk.Frame(right, bg="#ffffff"); sbf.pack(fill="x", padx=8, pady=(0, 8))
    ttk.Button(sbf, text="Ajouter à la date sélectionnée",
               command=lambda: _add_tech_to_date(app)).pack(side="left", padx=4)
    ttk.Button(sbf, text="Assigner la date sélectionnée",
               command=lambda: _assign_date(app)).pack(side="left", padx=4)
    ttk.Button(sbf, text="Supprimer sélection",
               command=lambda: _delete_schedule_item(app)).pack(side="left", padx=4)
    ttk.Button(sbf, text="Charger template Sarco",
               command=lambda: _load_program(app, "Sarco")).pack(side="left", padx=4)

    # Détail technique
    tk.Label(right, text="Détail", font=("Helvetica", 12, "bold"),
             bg="#ffffff").pack(anchor="w", padx=8, pady=(4, 4))
    app.detail_text = tk.Text(right, height=10, wrap="word")
    app.detail_text.pack(fill="both", expand=True, padx=8, pady=(0, 8))
    app.detail_text.config(state="disabled")

    # Programme (séances)
    tk.Label(right, text="Programme (séances)", font=("Helvetica", 12, "bold"),
             bg="#ffffff").pack(anchor="w", padx=8, pady=(4, 4))
    app.program_listbox = tk.Listbox(right, height=8)
    app.program_listbox.pack(fill="both", expand=True, padx=8, pady=(0, 8))
    app.program_listbox.bind("<Double-1>", lambda ev: _on_program_dbl(app))

    pbf = tk.Frame(right, bg="#ffffff"); pbf.pack(anchor="w", pady=8, padx=8)
    ttk.Button(pbf, text="Ajouter technique sélectionnée",
               command=lambda: _add_tech_to_program(app)).pack(side="left", padx=4)
    ttk.Button(pbf, text="Supprimer",
               command=lambda: _remove_program_item(app)).pack(side="left", padx=4)
    ttk.Button(pbf, text="Charger template",
               command=lambda: _load_program(app, app.program_selected_var.get())).pack(side="left", padx=4)

    # Générateur mensuel
    _build_generator(app, right)

    # Historique intégré
    _build_history_panel(app, right)


def _build_generator(app, parent):
    gen = tk.Frame(parent, bg="#ffffff"); gen.pack(fill="x", padx=8, pady=(4, 8))
    tk.Label(gen, text="Générer programme mensuel :", bg="#ffffff").pack(anchor="w")

    app.gen_cat_sarco = tk.BooleanVar(value=True)
    app.gen_cat_mixte = tk.BooleanVar(value=True)
    app.gen_cat_myofi = tk.BooleanVar(value=True)
    chk = tk.Frame(gen, bg="#ffffff"); chk.pack(anchor="w", pady=4)
    tk.Checkbutton(chk, text="Sarcoplasmique",  variable=app.gen_cat_sarco, bg="#ffffff").grid(row=0, column=0, sticky="w", padx=4)
    tk.Checkbutton(chk, text="Mixte",           variable=app.gen_cat_mixte, bg="#ffffff").grid(row=0, column=1, sticky="w", padx=4)
    tk.Checkbutton(chk, text="Myofibrillaire",  variable=app.gen_cat_myofi, bg="#ffffff").grid(row=0, column=2, sticky="w", padx=4)

    wef = tk.Frame(gen, bg="#ffffff"); wef.pack(anchor="w", pady=6)
    tk.Label(wef, text="Samedi :", bg="#ffffff").grid(row=0, column=0, sticky="w", padx=(0, 6))
    app.gen_saturday_var = tk.StringVar(value="Off")
    ttk.Combobox(wef, values=WEEKEND_OPT, textvariable=app.gen_saturday_var,
                 state="readonly", width=12).grid(row=0, column=1, sticky="w", padx=(0, 12))
    tk.Label(wef, text="Dimanche :", bg="#ffffff").grid(row=0, column=2, sticky="w", padx=(0, 6))
    app.gen_sunday_var = tk.StringVar(value="Off")
    ttk.Combobox(wef, values=WEEKEND_OPT, textvariable=app.gen_sunday_var,
                 state="readonly", width=12).grid(row=0, column=3, sticky="w")

    bf = tk.Frame(gen, bg="#ffffff"); bf.pack(anchor="w", pady=6)
    ttk.Button(bf, text="Générer mois",
               command=lambda: _gen_month(app)).pack(side="left", padx=4)
    ttk.Button(bf, text="Générer intégralité (rotation)",
               command=lambda: _gen_full_rotation(app)).pack(side="left", padx=4)
    ttk.Button(bf, text="Tout effacer",
               command=lambda: _clear_program(app)).pack(side="left", padx=4)
    ttk.Button(bf, text="Visualiser PDF",
               command=lambda: pdf_mod.preview_pdf(app)).pack(side="left", padx=4)
    ttk.Button(bf, text="Exporter PDF",
               command=lambda: pdf_mod.export_to_pdf(app)).pack(side="left", padx=4)


def _build_history_panel(app, parent):
    hf = ttk.Frame(parent); hf.pack(fill="both", expand=True, padx=8, pady=(8, 12))
    ttk.Label(hf, text="Historique des séances",
              font=("Helvetica", 12, "bold")).pack(anchor="w", pady=(0, 6))

    inner = ttk.Frame(hf); inner.pack(fill="both", expand=True)
    left_h = ttk.Frame(inner, width=260)
    left_h.pack(side="left", fill="y", padx=(0, 8), pady=4)

    app.history_listbox = tk.Listbox(left_h, height=12)
    app.history_listbox.pack(fill="both", expand=True)

    hbf = ttk.Frame(left_h); hbf.pack(fill="x", pady=6)
    ttk.Button(hbf, text="Voir",
               command=lambda: _history_view(app)).pack(side="left", padx=4)
    ttk.Button(hbf, text="Supprimer",
               command=lambda: _history_delete(app)).pack(side="left", padx=4)
    ttk.Button(hbf, text="Actualiser",
               command=lambda: _history_refresh(app)).pack(side="left", padx=4)

    right_h = ttk.Frame(inner); right_h.pack(side="left", fill="both", expand=True)
    ttk.Label(right_h, text="Détail séance",
              font=("Helvetica", 12, "bold")).pack(anchor="w", pady=(0, 6))
    app.history_detail = tk.Text(right_h, wrap="word", state="disabled", height=10)
    app.history_detail.pack(fill="both", expand=True)

    top_h = tk.Frame(hf); top_h.pack(fill="x", pady=(6, 0))
    ttk.Button(top_h, text="Importer",
               command=lambda: _history_import(app)).pack(side="left", padx=6)
    ttk.Button(top_h, text="Exporter",
               command=lambda: _history_export(app)).pack(side="left", padx=6)

    app.history_listbox.bind("<<ListboxSelect>>", lambda ev: _history_on_select(app))


# ══════════════════════════════════════════════════════════════════════════════
#  CATALOGUE
# ══════════════════════════════════════════════════════════════════════════════

def _refresh_tech_tree(app):
    tree = app.tech_tree
    for iid in tree.get_children():
        tree.delete(iid)
    query = app.tech_search_var.get().lower().strip()
    cats  = {"SARCOPLASMIQUE": [], "MIXTE": [], "MYOFIBRILLAIRE": []}
    for t in tt.get_all_techniques():
        cats.setdefault((t.get("categorie") or "").upper(), []).append(t)
    for cat in ["SARCOPLASMIQUE", "MIXTE", "MYOFIBRILLAIRE"]:
        items = cats.get(cat, [])
        if not items:
            continue
        parent = tree.insert("", "end", text=f"{cat} ({len(items)})", open=True)
        for t in items:
            if query:
                hay = " ".join([t.get("nom",""), t.get("id",""),
                                t.get("reps",""), t.get("notes","")]).lower()
                if query not in hay:
                    continue
            tree.insert(parent, "end", text=_tech_label(t),
                        values=(t["id"],), tags=(t["id"],))


def _on_tech_select(app):
    sel = app.tech_tree.selection()
    if not sel:
        return
    text = app.tech_tree.item(sel[0], "text")
    tid  = None
    if "(" in text and ")" in text:
        tid = text.split("(")[-1].split(")")[0].strip()
    if not tid:
        tags = app.tech_tree.item(sel[0], "tags") or []
        if tags:
            tid = tags[0]
    tech = tt.find_technique_by_id(tid) if tid else None
    app._last_selected_tech_id = tech["id"] if tech else None

    if tech:
        block = (
            _beginner_text(tid, tech) +
            "\n\n---\n\nDétails techniques complets :\n"
            f"Nom: {tech.get('nom','—')}\n"
            f"Reps: {tech.get('reps','—')}\n"
            f"Charge: {tech.get('charge','—')}\n"
            f"Repos: {tech.get('repos','—')}\n"
            f"Objectif: {tech.get('objectif','—')}\n\nNotes:\n{tech.get('notes','')}"
        )
    else:
        block = "Sélectionne une technique pour voir le détail."

    app.detail_text.config(state="normal")
    app.detail_text.delete("1.0", tk.END)
    app.detail_text.insert("1.0", block)
    app.detail_text.config(state="disabled")


# ══════════════════════════════════════════════════════════════════════════════
#  PLANNING — AFFICHAGE
# ══════════════════════════════════════════════════════════════════════════════

def _refresh_schedule(app):
    app._schedule_entries = sched.read_schedule(app)
    mode = app.view_mode_var.get() if hasattr(app, "view_mode_var") else "Jour"
    sel_date = _sel_date(app)
    lb = app.schedule_listbox
    lb.delete(0, tk.END)

    def ins(t): lb.insert(tk.END, t)

    if mode == "Jour":
        ds = sel_date.strftime(DATE_FORMAT)
        entries = [e for e in app._schedule_entries if e.get("date") == ds]
        undated = [e for e in app._schedule_entries if not e.get("date")]
        ins(f"Aucune séance pour {ds}") if not entries else None
        for e in entries:
            ins(f"{ds} — {e.get('line') or e.get('program') or e.get('types')}")
        if undated:
            ins(""); ins("Entrées sans date (sélectionne + 'Assigner la date') :")
            for e in undated:
                ins("[Sans date] " + (e.get("line") or e.get("program") or "—"))

    elif mode == "Semaine":
        start = sel_date - datetime.timedelta(days=sel_date.weekday())
        for i in range(7):
            d  = start + datetime.timedelta(days=i)
            ds = d.strftime(DATE_FORMAT)
            day_entries = [e for e in app._schedule_entries if e.get("date") == ds]
            ins(f"--- {ds} ({d.strftime('%a')}) ---")
            if not day_entries:
                ins(" (aucune)")
            else:
                for e in day_entries:
                    ins(f" {ds} — {e.get('line') or e.get('program') or e.get('types')}")

    else:  # Mois
        first = sel_date.replace(day=1)
        nxt   = first.replace(day=28) + datetime.timedelta(days=4)
        last  = nxt - datetime.timedelta(days=nxt.day)
        for day in range(1, last.day + 1):
            d  = first.replace(day=day)
            ds = d.strftime(DATE_FORMAT)
            day_entries = [e for e in app._schedule_entries if e.get("date") == ds]
            if day_entries:
                ins(f"--- {ds} ---")
                for e in day_entries:
                    ins(f" {ds} — {e.get('line') or e.get('program') or e.get('types')}")


# ══════════════════════════════════════════════════════════════════════════════
#  PLANNING — ACTIONS
# ══════════════════════════════════════════════════════════════════════════════

def _add_tech_to_date(app):
    tid = getattr(app, "_last_selected_tech_id", None)
    if not tid:
        messagebox.showinfo("Info", "Sélectionne une technique dans le catalogue.")
        return
    tech = tt.find_technique_by_id(tid)
    if not tech:
        messagebox.showerror("Erreur", "Technique introuvable.")
        return
    date_str = _sel_date(app).strftime(DATE_FORMAT)
    groupes  = ", ".join([g for g, v in app.groupes_vars.items() if v.get()])
    program  = app.program_selected_var.get() if hasattr(app, "program_selected_var") else ""
    line     = _tech_line(tech)

    sched.write_entry(app, date_str, line, groupes=groupes,
                      program=program, types=tech.get("categorie", ""), note="")

    # Aussi dans l'historique
    hist.add_entry(app, {
        "date":        datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "type":        program or "séance",
        "duration":    "",
        "notes":       f"Ajouté depuis le planning pour le {date_str}",
        "exercises":   [line],
        "planned_for": date_str,
    })

    app._schedule_entries = sched.read_schedule(app)
    _refresh_schedule(app)
    messagebox.showinfo("Ajouté", f"Technique ajoutée pour le {date_str}.")


def _assign_date(app):
    sel = app.schedule_listbox.curselection()
    if not sel:
        messagebox.showinfo("Info", "Sélectionne une ligne [Sans date].")
        return
    text = app.schedule_listbox.get(sel[0])
    if "[Sans date]" not in text:
        messagebox.showinfo("Info", "Sélectionne une entrée [Sans date].")
        return
    line_text = text.split("[Sans date]")[-1].strip()
    date_str  = _sel_date(app).strftime(DATE_FORMAT)
    ok = sched.assign_date_to_undated(app, line_text, date_str)
    if ok:
        hist.update_planned_for(app, line_text, date_str)
        app._schedule_entries = sched.read_schedule(app)
        _refresh_schedule(app)
        messagebox.showinfo("Succès", f"Date assignée : {date_str}")
    else:
        messagebox.showerror("Erreur", "Impossible de trouver l'entrée dans le fichier.")


def _delete_schedule_item(app):
    sel = app.schedule_listbox.curselection()
    if not sel:
        messagebox.showinfo("Info", "Sélectionne une ligne à supprimer.")
        return
    text = app.schedule_listbox.get(sel[0])
    mode = app.view_mode_var.get() if hasattr(app, "view_mode_var") else "Jour"
    if text.startswith("---") or "(aucune)" in text or text.startswith("Aucune séance"):
        return

    if "[Sans date]" in text:
        line_text = text.split("[Sans date]")[-1].strip()
        sched.delete_entry(app, "", line_text)
        hist.delete_matching(app, "", line_text)
    elif "—" in text:
        ds   = text.split("—")[0].strip()
        line = text.split("—", 1)[1].strip() if "—" in text else text.strip()
        sched.delete_entry(app, ds, line)
        hist.delete_matching(app, ds, line)
    else:
        sched.delete_entry(app, _sel_date(app).strftime(DATE_FORMAT), text.strip())

    app._schedule_entries = sched.read_schedule(app)
    _refresh_schedule(app)
    messagebox.showinfo("Supprimé", "La séance a été supprimée.")


def _on_schedule_dbl(app):
    sel = app.schedule_listbox.curselection()
    if not sel:
        return
    text = app.schedule_listbox.get(sel[0])
    if text.startswith("---") or "(aucune)" in text or text.startswith("Aucune séance"):
        return
    tid = None
    if "(" in text and ")" in text:
        tid = text.split("(")[-1].split(")")[0].strip()
    tech = tt.find_technique_by_id(tid) if tid else None
    if tech:
        _open_tech_dialog(app, tech)
    else:
        _simple_dialog(app, text)


# ══════════════════════════════════════════════════════════════════════════════
#  PROGRAMME (séances)
# ══════════════════════════════════════════════════════════════════════════════

def _load_program(app, name: str):
    if not hasattr(app, "program_listbox"):
        return
    app.program_listbox.delete(0, tk.END)
    if name in ("Sarco", "Myofi"):
        template = tt.build_program_template(name, weeks=4)
        for w in template["weeks"]:
            app.program_listbox.insert(tk.END, f"--- Semaine {w['week']} ---")
            for s in w["sessions"]:
                app.program_listbox.insert(tk.END, f" Séance {s['session']}")
                for ex in s["exercises"]:
                    tech = tt.find_technique_by_id(ex["id"])
                    if tech:
                        app.program_listbox.insert(tk.END, f"  {_tech_line(tech)}")
                    else:
                        app.program_listbox.insert(tk.END, f"  {ex.get('nom','—')} [{ex.get('reps','—')}]")
    else:
        for line in [
            "Standard — Jour A : Pecs/Dos 4×8-10",
            "Standard — Jour B : Jambes 4×8-10",
            "Standard — Jour C : Épaules/Bras 4×8-10",
        ]:
            app.program_listbox.insert(tk.END, line)


def _add_tech_to_program(app):
    tid = getattr(app, "_last_selected_tech_id", None)
    if not tid:
        messagebox.showinfo("Info", "Sélectionne une technique.")
        return
    tech = tt.find_technique_by_id(tid)
    if tech:
        app.program_listbox.insert(tk.END, _tech_line(tech))


def _remove_program_item(app):
    for i in reversed(app.program_listbox.curselection()):
        app.program_listbox.delete(i)


def _clear_program(app):
    if messagebox.askyesno("Confirmer", "Effacer toute la liste Programme (séances) ?"):
        app.program_listbox.delete(0, tk.END)


def _on_program_dbl(app):
    sel = app.program_listbox.curselection()
    if not sel:
        return
    line = app.program_listbox.get(sel[0])
    tid  = line.split("(")[-1].split(")")[0].strip() if "(" in line else None
    tech = tt.find_technique_by_id(tid) if tid else None
    if tech:
        _open_tech_dialog(app, tech)
    else:
        _simple_dialog(app, line)


# ══════════════════════════════════════════════════════════════════════════════
#  GÉNÉRATEURS
# ══════════════════════════════════════════════════════════════════════════════

def _gen_month(app):
    sd   = _sel_date(app)
    cats = _selected_cats(app)
    if not cats:
        messagebox.showwarning("Catégories", "Sélectionne au moins une catégorie.")
        return
    pool = _pool_for_cats(cats)
    if not pool:
        messagebox.showwarning("Pool vide", "Aucune technique trouvée.")
        return

    rot = _RotationIter(pool)
    cal = calendar.Calendar(firstweekday=0)
    app.program_listbox.delete(0, tk.END)

    for w_idx, week in enumerate(cal.monthdatescalendar(sd.year, sd.month), start=1):
        wid  = rot.next()
        tech = tt.find_technique_by_id(wid) if wid else None
        app.program_listbox.insert(tk.END, f"--- Semaine {w_idx} ---")
        for d in week:
            if d.month != sd.month:
                continue
            wd = d.weekday()
            if wd in DAY_TO_GROUP:
                line = (f"{d.strftime(DATE_FORMAT)} - {DAY_TO_GROUP[wd]} : "
                        f"{tech['nom']} [{tech.get('reps','—')}] | "
                        f"{tech.get('charge','—')} ({tech['id']})"
                        if tech else f"{d.strftime(DATE_FORMAT)} - {DAY_TO_GROUP[wd]} : (manquant)")
            else:
                sel = _weekend_for_day(app, wd)
                dn  = WEEKDAY_FR.get(wd, d.strftime("%A"))
                if sel == "Off":
                    line = f"{d.strftime(DATE_FORMAT)} - {dn} : Off"
                else:
                    line = (f"{d.strftime(DATE_FORMAT)} - {sel} : "
                            f"{tech['nom']} [{tech.get('reps','—')}] | "
                            f"{tech.get('charge','—')} ({tech['id']})"
                            if tech else f"{d.strftime(DATE_FORMAT)} - {sel} : (manquant)")
            app.program_listbox.insert(tk.END, line)

    messagebox.showinfo("OK", "Programme mensuel généré.")


def _gen_full_rotation(app):
    sd   = _sel_date(app)
    cats = _selected_cats(app)
    if not cats:
        messagebox.showwarning("Catégories", "Sélectionne au moins une catégorie.")
        return
    pool = _pool_for_cats(cats)
    if not pool:
        messagebox.showwarning("Pool vide", "Aucune technique trouvée.")
        return

    rotation_ids = _build_rotation(pool)
    if not rotation_ids:
        messagebox.showwarning("Rotation", "Impossible de construire la rotation.")
        return

    monday = sd - datetime.timedelta(days=sd.weekday())
    app.program_listbox.delete(0, tk.END)

    for offset, tech_id in enumerate(rotation_ids):
        week_start = monday + datetime.timedelta(weeks=offset)
        iso_week   = week_start.isocalendar()[1]
        app.program_listbox.insert(tk.END, f"--- Semaine {iso_week} (+{offset}) ---")
        tech = tt.find_technique_by_id(tech_id)
        for wd in range(7):
            d = week_start + datetime.timedelta(days=wd)
            if wd in DAY_TO_GROUP:
                line = (f"{d.strftime(DATE_FORMAT)} - {DAY_TO_GROUP[wd]} : "
                        f"{tech['nom']} [{tech.get('reps','—')}] | "
                        f"{tech.get('charge','—')} ({tech['id']})"
                        if tech else f"{d.strftime(DATE_FORMAT)} - {DAY_TO_GROUP[wd]} : (manquant)")
            else:
                sel = _weekend_for_day(app, wd)
                dn  = WEEKDAY_FR.get(wd, d.strftime("%A"))
                if sel == "Off":
                    line = f"{d.strftime(DATE_FORMAT)} - {dn} : Off"
                else:
                    line = (f"{d.strftime(DATE_FORMAT)} - {sel} : "
                            f"{tech['nom']} [{tech.get('reps','—')}] | "
                            f"{tech.get('charge','—')} ({tech['id']})"
                            if tech else f"{d.strftime(DATE_FORMAT)} - {sel} : (manquant)")
            app.program_listbox.insert(tk.END, line)

    messagebox.showinfo("OK", f"Rotation complète : {len(rotation_ids)} semaine(s).")


# ══════════════════════════════════════════════════════════════════════════════
#  SAUVEGARDE GLOBALE
# ══════════════════════════════════════════════════════════════════════════════

def _save_training(app):
    if not utils.get_current_user_folder(app):
        messagebox.showerror("Erreur", "Sélectionne un élève d'abord.")
        return
    date_str = _sel_date(app).strftime(DATE_FORMAT)
    groupes  = ", ".join([g for g, v in app.groupes_vars.items() if v.get()])
    program  = app.program_selected_var.get() if hasattr(app, "program_selected_var") else ""
    note     = app.note_text.get("1.0", tk.END).strip() if hasattr(app, "note_text") else ""
    lines    = [
        app.program_listbox.get(i).strip()
        for i in range(app.program_listbox.size())
        if app.program_listbox.get(i).strip()
           and not app.program_listbox.get(i).strip().startswith("---")
           and not app.program_listbox.get(i).strip().lower().startswith("standard")
           and not app.program_listbox.get(i).strip().startswith("Séance")
    ] if hasattr(app, "program_listbox") else []

    for line in lines:
        sched.write_entry(app, date_str, line,
                          groupes=groupes, program=program, note=note)
        hist.add_entry(app, {
            "date":        datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "type":        program or "séance",
            "duration":    "",
            "notes":       note or f"Ajoutée pour le {date_str}",
            "exercises":   [line],
            "planned_for": date_str,
        })

    app._schedule_entries = sched.read_schedule(app)
    _refresh_schedule(app)
    messagebox.showinfo("Succès", f"{len(lines)} ligne(s) sauvegardées pour {date_str}.")


# ══════════════════════════════════════════════════════════════════════════════
#  HISTORIQUE — HANDLERS UI
# ══════════════════════════════════════════════════════════════════════════════

def _history_refresh(app):
    lb = getattr(app, "history_listbox", None)
    if not lb:
        return
    lb.delete(0, tk.END)
    if not utils.get_current_user_folder(app):
        lb.insert(tk.END, "(Aucun profil)")
        return
    history = hist.load(app)
    if not history:
        lb.insert(tk.END, "(Aucun historique)")
        return
    for e in history:
        date = e.get("date", "inconnue")
        typ  = e.get("type", "général")
        dur  = e.get("duration", "")
        label = f"{date} — {typ}" + (f" — {dur}" if dur else "")
        lb.insert(tk.END, label)


def _show_history_detail(app, entry: dict):
    w = getattr(app, "history_detail", None)
    if not w:
        return
    w.configure(state="normal"); w.delete("1.0", tk.END)
    lines = [
        f"Date : {entry.get('date','-')}",
        f"Type : {entry.get('type','-')}",
    ]
    if entry.get("duration"):
        lines.append(f"Durée : {entry['duration']}")
    if entry.get("notes"):
        lines += ["", "Notes :", entry["notes"]]
    if isinstance(entry.get("exercises"), list):
        lines += ["", "Exercices :"]
        for ex in entry["exercises"]:
            if isinstance(ex, dict):
                lines.append(f"- {ex.get('name','?')} sets:{ex.get('sets','')} reps:{ex.get('reps','')}")
            else:
                lines.append(f"- {ex}")
    if entry.get("planned_for"):
        lines += ["", f"Planifiée pour : {entry['planned_for']}"]
    w.insert(tk.END, "\n".join(lines))
    w.configure(state="disabled")


def _history_on_select(app):
    sel = app.history_listbox.curselection()
    if not sel:
        return
    history = hist.load(app)
    if sel[0] < len(history):
        _show_history_detail(app, history[sel[0]])


def _history_view(app):
    sel = app.history_listbox.curselection()
    if not sel:
        messagebox.showinfo("Sélection", "Sélectionnez une séance.")
        return
    history = hist.load(app)
    if sel[0] < len(history):
        _show_history_detail(app, history[sel[0]])


def _history_delete(app):
    sel = app.history_listbox.curselection()
    if not sel:
        messagebox.showinfo("Sélection", "Sélectionnez une séance à supprimer.")
        return
    if not messagebox.askyesno("Confirmer", "Supprimer la séance sélectionnée ?"):
        return
    if hist.delete_at(app, sel[0]):
        messagebox.showinfo("Supprimé", "Séance supprimée.")
        _history_refresh(app)
        w = getattr(app, "history_detail", None)
        if w:
            w.configure(state="normal"); w.delete("1.0", tk.END); w.configure(state="disabled")
    else:
        messagebox.showerror("Erreur", "Impossible de supprimer.")


def _history_import(app):
    if not utils.get_current_user_folder(app):
        messagebox.showwarning("Profil requis", "Sélectionnez un profil.")
        return
    path = filedialog.askopenfilename(title="Importer séance (JSON)",
                                      filetypes=[("JSON", "*.json"), ("All", "*.*")])
    if not path:
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        entries = [data] if isinstance(data, dict) else (data if isinstance(data, list) else [])
        for e in entries:
            if isinstance(e, dict):
                e.setdefault("date", datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
                hist.add_entry(app, e)
        messagebox.showinfo("Importé", f"{len(entries)} séance(s) importée(s).")
    except Exception as e:
        messagebox.showerror("Erreur", f"Import impossible : {e}")
    _history_refresh(app)


def _history_export(app):
    if not utils.get_current_user_folder(app):
        messagebox.showwarning("Profil requis", "Sélectionnez un profil.")
        return
    history = hist.load(app)
    if not history:
        messagebox.showinfo("Vide", "Aucun historique à exporter.")
        return
    path = filedialog.asksaveasfilename(title="Exporter historique",
                                        defaultextension=".json",
                                        filetypes=[("JSON", "*.json")])
    if not path:
        return
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        messagebox.showinfo("Exporté", f"Historique exporté : {path}")
    except Exception as e:
        messagebox.showerror("Erreur", f"Export impossible : {e}")


# ══════════════════════════════════════════════════════════════════════════════
#  DIALOGUES DÉTAIL TECHNIQUE
# ══════════════════════════════════════════════════════════════════════════════

def _open_tech_dialog(app, tech: dict):
    root = getattr(app, "root", app.content)
    dlg  = tk.Toplevel(); dlg.title(tech["nom"]); dlg.geometry("520x520")
    dlg.transient(root)
    tk.Label(dlg, text=tech["nom"], font=("Helvetica", 14, "bold")).pack(pady=8)
    for label, key in [("ID", "id"), ("Catégorie","categorie"),
                       ("Reps","reps"), ("Charge","charge"),
                       ("Repos","repos"), ("Objectif","objectif")]:
        tk.Label(dlg, text=f"{label} : {tech.get(key,'—')}").pack()
    tk.Label(dlg, text="Notes :", font=("Helvetica", 12, "bold")).pack(pady=(10, 0))
    txt = tk.Text(dlg, height=10, width=64, wrap="word")
    txt.pack(padx=8, pady=(4, 8))
    content = (_beginner_text(tech.get("id",""), tech) +
               "\n\n---\n\nDétails :\n" + tech.get("notes",""))
    txt.insert("1.0", content); txt.config(state="disabled")
    ttk.Button(dlg, text="Fermer", command=dlg.destroy).pack(pady=8)


def _simple_dialog(app, text: str):
    root = getattr(app, "root", app.content)
    dlg  = tk.Toplevel(); dlg.title("Détail"); dlg.transient(root)
    tk.Label(dlg, text=text, wraplength=600, justify="left").pack(padx=12, pady=12)
    ttk.Button(dlg, text="Fermer", command=dlg.destroy).pack(pady=(0, 12))
