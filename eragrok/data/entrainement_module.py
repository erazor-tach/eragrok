# data/entrainement_module.py — ERAGROK  ·  Dark Bodybuilding
import os, csv, json, datetime, random, calendar, tempfile, webbrowser, textwrap
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import customtkinter as ctk
from tkcalendar import Calendar
from data import utils
from data import db as _db
from data import training_techniques as tt
from data.theme import (
    TH, mk_btn, mk_card, mk_card2, mk_entry, mk_combo,
    mk_textbox, mk_label, mk_title, mk_sep, mk_checkbox, mk_radio,
    mk_scrollframe, screen_header, apply_treeview_style,
)

try:
    from reportlab.pdfgen import canvas as pdf_canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    RL = True
except Exception:
    RL = False

DATE_FMT   = "%d/%m/%Y"
TS_FMT     = "%Y-%m-%d %H:%M"
DAY_FR     = {0:"Lundi", 1:"Mardi", 2:"Mercredi", 3:"Jeudi",
              4:"Vendredi", 5:"Samedi", 6:"Dimanche"}
WE_OPTIONS = ["Off","Pecs","Cuisses","Épaules","Dos","Bras"]
DIFF_COL   = {1:"#d1fae5",2:"#fef3c7",3:"#fee2e2",4:"#fce7f3",5:"#ede9fe"}


# ── Helpers ───────────────────────────────────────────────────────────────────
def _user(app):      return getattr(app, "current_user", None)
def _udir(app):
    d = os.path.join(utils.USERS_DIR, _user(app) or "default")
    Path(d).mkdir(parents=True, exist_ok=True); return d

def _fmt(t):
    return f"{t['nom']} — {t.get('reps','—')} — {t.get('charge','—')} ({t['id']})"

def _parse_date(s):
    for fmt in [DATE_FMT, "%Y-%m-%d", "%m/%d/%Y"]:
        try: return datetime.datetime.strptime(str(s).strip(), fmt).strftime(DATE_FMT)
        except Exception: pass
    return s or ""

# ── Planning CSV ──────────────────────────────────────────────────────────────
def _plan_file(app): return os.path.join(_udir(app), "planning.csv")

def _read_plan(app):
    try:
        rows = _db.planning_get_all(app)
        return [{"date": r.get("date"), "line": r.get("line",""),
                 "prog": r.get("programme",""), "grp": r.get("groupes","")} for r in rows]
    except Exception: return []

def _write_plan(app, date_str, line, grp="", prog="", typ="", note=""):
    if isinstance(date_str, datetime.date):
        date_str = date_str.strftime(DATE_FMT)
    elif date_str: date_str = _parse_date(date_str)
    _db.planning_insert(app, date_str or "", grp, prog, typ, note, line)
    _add_history(app, {"date": datetime.datetime.now().strftime(TS_FMT),
                        "type": prog or "séance", "duration": "",
                        "notes": note, "exercises": [line],
                        "planned_for": date_str})

def _del_plan(app, date_str, line_text):
    if isinstance(date_str, datetime.date): date_str = date_str.strftime(DATE_FMT)
    _db.planning_delete(app, (date_str or "").strip(), line_text)

# ── Historique JSON ───────────────────────────────────────────────────────────
def _hist_file(app): return os.path.join(_udir(app), "training_history.json")

def _load_hist(app):
    try: return _db.history_get_all(app)
    except Exception: return []

def _save_hist(app, h):
    try: _db.history_save_all(app, h)
    except Exception: pass

def _add_history(app, entry):
    try: _db.history_insert(app, entry)
    except Exception:
        h = _load_hist(app); h.append(entry); _save_hist(app, h)

# ── Rotation ──────────────────────────────────────────────────────────────────
def _pool(cats):
    want = {c.upper() for c in cats}
    seen, pool = set(), []
    for t in tt.get_all_techniques():
        if t.get("id") not in seen and (t.get("categorie","")).upper() in want:
            seen.add(t["id"]); pool.append(t)
    return pool

class _Rot:
    def __init__(self, pool):
        self.pool = pool or []
        ids = [t["id"] for t in pool]
        random.shuffle(ids); self._ids = ids; self._i = 0
    def next(self):
        if not self._ids: return None
        if self._i >= len(self._ids):
            random.shuffle(self._ids); self._i = 0
        v = self._ids[self._i]; self._i += 1; return v
    def all_ids(self): return list(self._ids)

# ── PDF ───────────────────────────────────────────────────────────────────────
def _lines_from_listbox(app):
    if not hasattr(app, "program_lb"): return []
    return [app.program_lb.get(i) for i in range(app.program_lb.size())]

def _export_pdf(app, path=None, full_notes=False):
    if not RL:
        messagebox.showerror("ERAGROK", "reportlab manquant."); return None
    # Essaie d'abord la listbox (si écran entraînement ouvert)
    lines = _lines_from_listbox(app)
    # Fallback : dernier programme sauvegardé en DB
    if not lines:
        try:
            from data import db as _db
            progs = _db.programmes_get_all(app)
            if progs:
                # Prendre le plus récent
                prog = progs[-1]
                lines = prog.get("lines", [])
        except Exception:
            pass
    if not lines:
        messagebox.showinfo("ERAGROK", "Aucun programme à exporter.\nOuvre l'écran Entraînement ou sauvegarde d'abord un programme.")
        return None
    if path is None:
        path = filedialog.asksaveasfilename(
            title="Exporter PDF", defaultextension=".pdf",
            filetypes=[("PDF","*.pdf")])
        if not path: return None
    try:
        pw, ph = A4; ml = 18*mm; uw = pw - 2*ml
        c = pdf_canvas.Canvas(path, pagesize=A4)
        y = ph - 18*mm
        for line in lines:
            if y < 20*mm: c.showPage(); y = ph - 18*mm
            tid  = _extract_id(line)
            tech = tt.find_technique_by_id(tid) if tid else None
            dl   = int(tech.get("difficulty_level", 3) if tech else 3)
            hx   = DIFF_COL.get(max(1,min(5,dl)), "#f3f4f6")
            r,g,b = int(hx[1:3],16)/255, int(hx[3:5],16)/255, int(hx[5:7],16)/255
            c.setFillColorRGB(r,g,b)
            wrapped = textwrap.wrap(line, 90)
            rh = max(10*mm, len(wrapped)*5.5*mm + 3*mm)
            c.rect(ml-2*mm, y-rh+2*mm, uw+4*mm, rh, fill=1, stroke=0)
            c.setFillColor(colors.black); c.setFont("Helvetica", 9)
            ty = y - 4*mm
            for wl in wrapped: c.drawString(ml+1*mm, ty, wl); ty -= 5.5*mm
            y = y - rh - 2*mm
        c.save()
        messagebox.showinfo("ERAGROK", f"✔  PDF exporté :\n{path}")
        return path
    except Exception as e:
        messagebox.showerror("ERAGROK", str(e)); return None

def _preview_pdf(app):
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    tmp.close()
    p = _export_pdf(app, path=tmp.name)
    if p:
        try: webbrowser.open_new(p)
        except Exception: messagebox.showinfo("PDF", p)

def _extract_id(line):
    if "(" in line and ")" in line:
        try: return line.split("(")[-1].split(")")[0].strip()
        except Exception: pass
    return None

# ── Catalogue ─────────────────────────────────────────────────────────────────
def _rebuild_tree(app):
    if not hasattr(app, "tech_tree"): return
    app.tech_tree.delete(*app.tech_tree.get_children())
    q = app.tech_search_var.get().lower() if hasattr(app, "tech_search_var") else ""
    cats = {}
    for t in tt.get_all_techniques():
        if q and q not in t["nom"].lower(): continue
        cats.setdefault(t.get("categorie","Autre"), []).append(t)
    for cat, lst in sorted(cats.items()):
        p = app.tech_tree.insert("","end", text=f"▶ {cat}", open=True)
        for t in lst:
            app.tech_tree.insert(p,"end", text=_fmt(t), tags=(t["id"],))

def _on_tech_sel(app):
    sel = app.tech_tree.selection()
    if not sel: return
    tags = app.tech_tree.item(sel[0], "tags")
    if not tags: return
    tid = tags[0]; app._last_tid = tid
    tech = tt.find_technique_by_id(tid)
    if not tech: return
    lines = [
        f"Technique : {tech['nom']}",
        f"Catégorie : {tech.get('categorie','—')}",
        f"Reps      : {tech.get('reps','—')}",
        f"Charge    : {tech.get('charge','—')}",
        f"Repos     : {tech.get('repos','—')}",
        f"Objectif  : {tech.get('objectif','—')}",
        f"Difficulté: {tech.get('difficulty_level','—')}/5",
    ]
    if tech.get("notes"): lines += ["", f"Notes : {tech['notes']}"]
    app.detail_text.configure(state="normal")
    app.detail_text.delete("1.0","end")
    app.detail_text.insert("1.0","\n".join(lines))
    app.detail_text.configure(state="disabled")

# ── Planning affichage ────────────────────────────────────────────────────────
def _refresh_plan(app):
    app._plan = _read_plan(app)
    try:
        sd = app.calendar.selection_get()
        if not isinstance(sd, datetime.date):
            sd = datetime.datetime.strptime(app.calendar.get_date(), DATE_FMT).date()
    except Exception: sd = datetime.date.today()
    app._sel_date = sd
    lb = app.schedule_lb; lb.delete(0, tk.END)
    mode = app.view_var.get() if hasattr(app, "view_var") else "Jour"

    def ins(t): lb.insert(tk.END, t)

    if mode == "Jour":
        ds = sd.strftime(DATE_FMT)
        ents = [e for e in app._plan if e.get("date") == ds]
        if not ents: ins(f"Aucune séance pour {ds}")
        else:
            for e in ents: ins(f"{ds} — {e['line'] or e['prog']}")
    elif mode == "Semaine":
        start = sd - datetime.timedelta(days=sd.weekday())
        for i in range(7):
            d = start + datetime.timedelta(i)
            ds = d.strftime(DATE_FMT)
            ins(f"─── {ds} ({d.strftime('%a')}) ───")
            ents = [e for e in app._plan if e.get("date") == ds]
            for e in ents: ins(f"  {e['line'] or e['prog']}")
            if not ents: ins("  (repos)")
    else:
        first = sd.replace(day=1)
        nm = first.replace(day=28) + datetime.timedelta(4)
        last = nm - datetime.timedelta(nm.day)
        for d in range(1, last.day+1):
            day = first.replace(day=d)
            ds  = day.strftime(DATE_FMT)
            ents = [e for e in app._plan if e.get("date") == ds]
            if ents:
                ins(f"─── {ds} ───")
                for e in ents: ins(f"  {e['line'] or e['prog']}")
    # sans date
    undated = [e for e in app._plan if not e.get("date")]
    if undated:
        ins(""); ins("── Sans date ──")
        for e in undated: ins(f"  [?] {e['line']}")

def _add_to_plan(app):
    tid = getattr(app, "_last_tid", None)
    if not tid: messagebox.showinfo("ERAGROK", "Sélectionne une technique."); return
    tech = tt.find_technique_by_id(tid)
    if not tech: return
    try:
        sd = app.calendar.selection_get()
        if not isinstance(sd, datetime.date):
            sd = datetime.datetime.strptime(app.calendar.get_date(), DATE_FMT).date()
    except Exception: sd = datetime.date.today()
    ds  = sd.strftime(DATE_FMT)
    grp = ", ".join(g for g, v in app.groupes_vars.items() if v.get())
    line = f"{tech['nom']} [{tech.get('reps','—')}] | {tech.get('charge','—')} ({tech['id']})"
    _write_plan(app, ds, line, grp=grp,
                prog=app.prog_var.get() if hasattr(app,"prog_var") else "")
    app._plan = _read_plan(app); _refresh_plan(app)
    messagebox.showinfo("ERAGROK", f"✔  Ajouté pour le {ds}.")

def _del_plan_item(app):
    sel = app.schedule_lb.curselection()
    if not sel: return
    txt = app.schedule_lb.get(sel[0])
    if "─" in txt or txt.strip().startswith("(") or txt.strip().startswith("Aucune"): return
    if not messagebox.askyesno("Confirmer","Supprimer cette entrée ?"): return
    ds = None; line = txt
    if " — " in txt:
        parts = txt.split(" — ", 1)
        try: datetime.datetime.strptime(parts[0].strip(), DATE_FMT); ds = parts[0].strip(); line = parts[1].strip()
        except Exception: pass
    _del_plan(app, ds, line)
    app._plan = _read_plan(app); _refresh_plan(app)

# ── Génération programme ──────────────────────────────────────────────────────
# ── Gestion programmes — fichier unique + 4 backups ────────────────────────
_PROG_FILE    = "programmes.json"   # fichier principal
_PROG_BACKUPS = 4                    # nombre de backups rotatifs

def _prog_file(app):
    """Chemin du fichier programmes.json de l'utilisateur."""
    return os.path.join(_udir(app), _PROG_FILE)

def _load_all_programmes(app):
    """Charge les programmes depuis SQLite → liste de dicts [{id, title, created, lines}, ...]."""
    try: return _db.programmes_get_all(app)
    except Exception: return []

def _write_all_programmes(app, programmes):
    """Sauvegarde tous les programmes dans SQLite (remplace programmes.json)."""
    try:
        from data.db import get_user_db_from_app
        import json as _json
        con = get_user_db_from_app(app)
        con.execute("DELETE FROM programmes")
        for p in programmes:
            con.execute(
                "INSERT INTO programmes (title, created, lines) VALUES (?,?,?)",
                (p.get("title",""), p.get("created",""),
                 _json.dumps(p.get("lines",[]), ensure_ascii=False))
            )
        con.commit(); con.close()
    except Exception as e:
        import logging; logging.warning(f"_write_all_programmes: {e}")


def _save_programme(app):
    """Ajoute ou met à jour un programme dans programmes.json."""
    if not _user(app):
        messagebox.showerror("ERAGROK", "Aucun utilisateur."); return
    lines = [app.program_lb.get(i) for i in range(app.program_lb.size())]
    if not lines:
        messagebox.showinfo("ERAGROK", "Le programme est vide."); return
    # Titre depuis la 1ère ligne (ex: "─── Programme mars 2026 ───")
    raw_title = lines[0].strip("─ ").strip()
    title = raw_title if raw_title else "Programme"
    now_iso = datetime.datetime.now().isoformat()
    programmes = _load_all_programmes(app)
    # Chercher si un programme avec ce titre existe déjà
    existing = next((p for p in programmes if p.get("title") == title), None)
    if existing:
        if not messagebox.askyesno("Confirmer",
                f"Un programme « {title} » existe déjà.\nÉcraser ?"):
            return
        existing["lines"]   = lines
        existing["updated"] = now_iso
    else:
        prog_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        programmes.append({
            "id":      prog_id,
            "title":   title,
            "created": now_iso,
            "lines":   lines,
        })
    _write_all_programmes(app, programmes)
    messagebox.showinfo("ERAGROK",
        f"✔  Programme « {title} » sauvegardé.\n"
        f"({len(programmes)} programme(s) au total, {_PROG_BACKUPS} backups)")
    _refresh_saved_programmes(app)

def _list_programmes(app):
    """Retourne la liste des programmes [{id, title, created, lines}]."""
    return _load_all_programmes(app)

def _refresh_saved_programmes(app):
    """Met à jour le listbox des programmes sauvegardés."""
    if not hasattr(app, "saved_prog_lb"): return
    lb = app.saved_prog_lb; lb.delete(0, tk.END)
    progs = _list_programmes(app)
    app._saved_progs = progs
    if not progs:
        lb.insert(tk.END, "(aucun programme sauvegardé)")
        return
    for p in reversed(progs):   # plus récent en haut
        try:
            dt = datetime.datetime.fromisoformat(
                    p.get("created","")).strftime("%d/%m/%Y %H:%M")
        except Exception:
            dt = p.get("created", "?")[:16]
        n_lines = len(p.get("lines", []))
        lb.insert(tk.END, f"{dt}  —  {p['title']}  ({n_lines} lignes)")

def _load_saved_programme(app):
    """Charge le programme sélectionné dans program_lb."""
    if not hasattr(app, "saved_prog_lb"): return
    sel = app.saved_prog_lb.curselection()
    if not sel:
        messagebox.showinfo("ERAGROK", "Sélectionne un programme."); return
    progs = list(reversed(getattr(app, "_saved_progs", _list_programmes(app))))
    if sel[0] >= len(progs): return
    prog = progs[sel[0]]
    lines = prog.get("lines", [])
    app.program_lb.delete(0, tk.END)
    for l in lines:
        app.program_lb.insert(tk.END, l)
    messagebox.showinfo("ERAGROK",
        f"✔  Programme « {prog['title']} » chargé ({len(lines)} lignes).")

def _del_saved_programme(app):
    """Supprime le programme sélectionné de programmes.json."""
    if not hasattr(app, "saved_prog_lb"): return
    sel = app.saved_prog_lb.curselection()
    if not sel:
        messagebox.showinfo("ERAGROK", "Sélectionne un programme."); return
    progs_rev = list(reversed(getattr(app, "_saved_progs", _list_programmes(app))))
    if sel[0] >= len(progs_rev): return
    prog = progs_rev[sel[0]]
    if not messagebox.askyesno("Confirmer",
            f"Supprimer le programme\n« {prog['title']} » ?"):
        return
    all_progs = _load_all_programmes(app)
    all_progs = [p for p in all_progs if p.get("id") != prog.get("id")
                                       and p.get("title") != prog.get("title")]
    _write_all_programmes(app, all_progs)
    messagebox.showinfo("ERAGROK", "✔  Programme supprimé.")
    _refresh_saved_programmes(app)


def _gen_month(app):
    """
    Génère un programme mensuel avec la logique :
    • 1 technique différente par semaine (tous les jours actifs d'une semaine = même entraînement)
    • Jamais deux semaines consécutives avec la même technique
    • Pas de répétition sur le mois
    • Chaque semaine est délimitée par un séparateur lisible
    """
    try:
        sd = app.calendar.selection_get()
        if not isinstance(sd, datetime.date):
            sd = datetime.datetime.strptime(app.calendar.get_date(), DATE_FMT).date()
    except Exception:
        sd = datetime.date.today()

    cats = []
    if app.gen_sarco.get(): cats.append("SARCOPLASMIQUE")
    if app.gen_mixte.get(): cats.append("MIXTE")
    if app.gen_myofi.get(): cats.append("MYOFIBRILLAIRE")
    if not cats:
        messagebox.showinfo("ERAGROK", "Sélectionne au moins une catégorie."); return
    pool = _pool(cats)
    if not pool:
        messagebox.showinfo("ERAGROK", "Aucune technique disponible."); return

    sat = app.gen_sat.get()
    sun = app.gen_sun.get()
    first = sd.replace(day=1)
    _, nd = calendar.monthrange(first.year, first.month)

    # ── Calculer les semaines du mois ────────────────────────────────────────
    # Chaque semaine = lundi→dimanche. On découpe le mois en blocs de 7j.
    weeks = []
    current_week = []
    for i in range(1, nd + 1):
        d = first.replace(day=i)
        if d.weekday() == 0 and current_week:
            weeks.append(current_week)
            current_week = []
        current_week.append(d)
    if current_week:
        weeks.append(current_week)

    n_weeks = len(weeks)

    # ── Assigner une technique unique par semaine ────────────────────────────
    # Mélanger le pool, prendre n_weeks techniques distinctes.
    # Si pool < n_weeks → réutiliser mais jamais consécutif.
    ids_shuffled = [t["id"] for t in pool]
    random.shuffle(ids_shuffled)

    week_techs = []
    last_id = None
    pool_cycle = list(ids_shuffled)
    # S'assurer qu'on a assez d'IDs sans répétition consécutive
    if len(pool_cycle) < n_weeks:
        # Dupliquer le pool en évitant les voisins identiques
        extended = []
        source = list(ids_shuffled)
        while len(extended) < n_weeks:
            random.shuffle(source)
            for tid in source:
                if not extended or extended[-1] != tid:
                    extended.append(tid)
                if len(extended) >= n_weeks:
                    break
        pool_cycle = extended

    for w_idx in range(n_weeks):
        # Chercher une technique différente de la précédente
        for attempt in range(len(pool_cycle)):
            tid = pool_cycle[(w_idx + attempt) % len(pool_cycle)]
            if tid != last_id:
                week_techs.append(tid)
                last_id = tid
                break
        else:
            # Fallback : prendre la première disponible
            week_techs.append(pool_cycle[w_idx % len(pool_cycle)])
            last_id = week_techs[-1]

    # ── Construire le programme dans le listbox ──────────────────────────────
    app.program_lb.delete(0, tk.END)
    app.program_lb.insert(tk.END, f"─── Programme {first.strftime('%B %Y')} ───")

    prog_name = app.prog_var.get() if hasattr(app, "prog_var") else ""

    for w_idx, week_days in enumerate(weeks):
        tech = tt.find_technique_by_id(week_techs[w_idx]) if w_idx < len(week_techs) else None
        if not tech:
            continue

        # Séparateur de semaine avec la technique assignée
        week_num = w_idx + 1
        monday = week_days[0]
        sunday = week_days[-1]
        app.program_lb.insert(
            tk.END,
            f"── Semaine {week_num}  ({monday.strftime('%d/%m')}→{sunday.strftime('%d/%m')}) "
            f"│ {tech['nom']} [{tech.get('categorie','')}] ──"
        )

        for d in week_days:
            wd = d.weekday()
            ds = d.strftime(DATE_FMT)
            # Gestion repos week-end
            if wd == 5 and sat == "Off":
                app.program_lb.insert(tk.END, f"  {ds} ({DAY_FR[wd]})  —  Repos")
                continue
            if wd == 6 and sun == "Off":
                app.program_lb.insert(tk.END, f"  {ds} ({DAY_FR[wd]})  —  Repos")
                continue

            focus = (sat if wd == 5 else sun if wd == 6 else "")
            reps  = tech.get("reps", "—")
            charge = tech.get("charge", "—")
            line  = f"  {ds} ({DAY_FR[wd]})  —  {tech['nom']}  [{reps}] | {charge}"
            if focus:
                line += f"  [Focus:{focus}]"
            app.program_lb.insert(tk.END, line)

            # Écrire dans planning.csv
            _write_plan(
                app, ds,
                f"{tech['nom']} [{reps}] | {charge} ({tech['id']})",
                grp=focus or tech.get("categorie", ""),
                prog=prog_name,
                typ=tech.get("categorie", ""),
            )

    app._plan = _read_plan(app)
    _refresh_plan(app)
    messagebox.showinfo(
        "ERAGROK",
        f"✔  Programme {first.strftime('%B %Y')} généré — {n_weeks} semaines, "
        f"{n_weeks} techniques distinctes."
    )

# ── Sauvegarde séance ─────────────────────────────────────────────────────────
def _save_session(app):
    if not _user(app): messagebox.showerror("ERAGROK","Sélectionne un élève."); return
    try:
        sd = app.calendar.selection_get()
        if not isinstance(sd, datetime.date):
            sd = datetime.datetime.strptime(app.calendar.get_date(), DATE_FMT).date()
    except Exception: sd = datetime.date.today()
    ds   = sd.strftime(DATE_FMT)
    grp  = ", ".join(g for g, v in app.groupes_vars.items() if v.get())
    prog = app.prog_var.get() if hasattr(app,"prog_var") else ""
    note = app.note_text.get("1.0","end").strip()
    fichier = os.path.join(_udir(app), "entrainement.csv")
    with open(fichier, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([ds, grp, prog, note])
    exs = [app.program_lb.get(i) for i in range(app.program_lb.size())]
    _add_history(app, {"date": datetime.datetime.now().strftime(TS_FMT),
                        "type": prog or "général","duration":"","notes":note,
                        "exercises":exs,"planned_for":ds})
    messagebox.showinfo("ERAGROK", f"✔  Séance du {ds} sauvegardée.")
    _hist_refresh(app)

# ── Historique inline ─────────────────────────────────────────────────────────
def _hist_refresh(app):
    lb = app.hist_lb; lb.delete(0, tk.END)
    h = _load_hist(app)
    if not h: lb.insert(tk.END, "(Aucun historique)"); return
    for e in h:
        lb.insert(tk.END,
                  f"{e.get('date','?')} — {e.get('type','?')}")

def _hist_show(app):
    sel = app.hist_lb.curselection()
    if not sel: return
    h = _load_hist(app)
    if sel[0] >= len(h): return
    e = h[sel[0]]
    lines = [f"Date : {e.get('date','-')}",
             f"Type : {e.get('type','-')}"]
    if e.get("notes"): lines += ["", "Notes :", e["notes"]]
    if isinstance(e.get("exercises"), list):
        lines.append(""); lines.append("Exercices :")
        for ex in e["exercises"]: lines.append(f"  · {ex}")
    app.hist_detail.configure(state="normal")
    app.hist_detail.delete("1.0","end")
    app.hist_detail.insert("end","\n".join(lines))
    app.hist_detail.configure(state="disabled")

def _hist_del(app):
    sel = app.hist_lb.curselection()
    if not sel: return
    if not messagebox.askyesno("Confirmer","Supprimer la séance ?"): return
    h = _load_hist(app)
    if sel[0] < len(h): h.pop(sel[0]); _save_hist(app, h)
    _hist_refresh(app)
    app.hist_detail.configure(state="normal")
    app.hist_detail.delete("1.0","end")
    app.hist_detail.configure(state="disabled")

def _hist_import(app):
    p = filedialog.askopenfilename(title="Importer",
                                    filetypes=[("JSON","*.json"),("Tous","*.*")])
    if not p: return
    try:
        with open(p,"r",encoding="utf-8") as f: imp = json.load(f)
        h = _load_hist(app)
        h.extend(imp if isinstance(imp,list) else [imp])
        _save_hist(app,h); _hist_refresh(app)
        messagebox.showinfo("ERAGROK",f"✔  {len(imp)} entrées importées.")
    except Exception as e: messagebox.showerror("ERAGROK",str(e))

def _hist_export(app):
    h = _load_hist(app)
    if not h: messagebox.showinfo("ERAGROK","Aucun historique."); return
    p = filedialog.asksaveasfilename(title="Exporter",
                                      defaultextension=".json",
                                      filetypes=[("JSON","*.json")])
    if not p: return
    try:
        with open(p,"w",encoding="utf-8") as f: json.dump(h,f,ensure_ascii=False,indent=2)
        messagebox.showinfo("ERAGROK",f"✔  Exporté : {p}")
    except Exception as e: messagebox.showerror("ERAGROK",str(e))


# ════════════════════════════════════════════════════════════════════════════
#  UI PRINCIPALE
# ════════════════════════════════════════════════════════════════════════════
def show_entrainement_screen(app, program=None):
    for w in app.content.winfo_children(): w.destroy()
    for _c in getattr(app, "_mpl_canvases", []):
        try:
            _w = _c.get_tk_widget()
            if _w.winfo_exists(): _w.destroy()
        except Exception: pass
    app._mpl_canvases = []

    screen_header(app.content, "🏋  ENTRAÎNEMENT",
                  user_name=getattr(app,"selected_user_name",""),
                  back_cmd=app.show_dashboard)

    # barre programme + vue
    top = ctk.CTkFrame(app.content, fg_color=TH.BG_CARD, height=46, corner_radius=0)
    top.pack(fill="x")
    top.pack_propagate(False)
    top_inner = ctk.CTkFrame(top, fg_color="transparent")
    top_inner.pack(fill="x", padx=20)
    mk_label(top_inner, "Programme :", size="small",
             color=TH.TEXT_SUB).pack(side="left", pady=12)
    app.prog_var = tk.StringVar(value=program or "Standard")
    ctk.CTkLabel(top_inner, textvariable=app.prog_var,
                 font=TH.F_H3, text_color=TH.ACCENT_GLOW).pack(side="left", padx=8)
    app.view_var = tk.StringVar(value="Jour")
    for m in ["Jour","Semaine","Mois"]:
        ctk.CTkRadioButton(
            top_inner, text=m, value=m, variable=app.view_var,
            fg_color=TH.ACCENT, hover_color=TH.ACCENT_HOVER,
            text_color=TH.TEXT, font=TH.F_SMALL,
            command=lambda: _refresh_plan(app),
        ).pack(side="left", padx=8, pady=12)

    # layout 3 colonnes
    main = ctk.CTkFrame(app.content, fg_color="transparent")
    main.pack(fill="both", expand=True, padx=16, pady=12)
    main.columnconfigure(0, weight=0)
    main.columnconfigure(1, weight=1)
    main.columnconfigure(2, weight=1)

    # ── col 0 : calendrier + groupes ──────────────────────────────────
    c0 = ctk.CTkFrame(main, fg_color="transparent")
    c0.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

    cal_card = mk_card(c0)
    cal_card.pack(fill="x", pady=(0, 10))
    _cs = dict(
        background=TH.BG_CARD2, foreground=TH.TEXT,
        selectbackground=TH.ACCENT, selectforeground=TH.TEXT,
        bordercolor=TH.BORDER,
        headersbackground=TH.BG_CARD, headersforeground=TH.TEXT_SUB,
        normalforeground=TH.TEXT, weekendforeground=TH.ACCENT_GLOW,
        font=("Inter",10), headersfont=("Inter",10,"bold"),
    )
    app.calendar = Calendar(cal_card, selectmode="day", **_cs)
    app.calendar.pack(padx=10, pady=10)
    app.calendar.bind("<<CalendarSelected>>", lambda e: _refresh_plan(app))

    grp_card = mk_card(c0)
    grp_card.pack(fill="x")
    mk_title(grp_card, "  GROUPES MUSCULAIRES").pack(
        anchor="w", padx=14, pady=(12, 6))
    mk_sep(grp_card).pack(fill="x", padx=14, pady=(0, 8))
    app.groupes_vars = {}
    gf = ctk.CTkFrame(grp_card, fg_color="transparent")
    gf.pack(padx=14, pady=(0, 12))
    groupes = ["Pecs","Dos","Cuisses","Épaules","Bras",
               "Fessiers","Mollets","Abdominaux","Full body","Alpha body"]
    for i, g in enumerate(groupes):
        v = tk.BooleanVar()
        mk_checkbox(gf, g, v).grid(
            row=i//2, column=i%2, sticky="w", padx=6, pady=3)
        app.groupes_vars[g] = v

    # ── col 1 : catalogue ─────────────────────────────────────────────
    c1 = mk_card(main)
    c1.grid(row=0, column=1, sticky="nsew", padx=(0, 10))
    mk_title(c1, "  CATALOGUE TECHNIQUES").pack(
        anchor="w", padx=14, pady=(12, 6))
    mk_sep(c1).pack(fill="x", padx=14, pady=(0, 8))

    sr = ctk.CTkFrame(c1, fg_color="transparent")
    sr.pack(fill="x", padx=14, pady=(0, 8))
    app.tech_search_var = tk.StringVar()
    mk_label(sr, "🔍", size="body").pack(side="left")
    se = mk_entry(sr, width=220, placeholder="Rechercher…")
    se.configure(textvariable=app.tech_search_var); se.pack(side="left", padx=6)
    mk_btn(sr, "✕", lambda: app.tech_search_var.set(""),
           color=TH.GRAY, hover=TH.GRAY_HVR,
           width=36, height=TH.BTN_SM, radius=8).pack(side="left")

    apply_treeview_style("Tech")
    tf = ctk.CTkFrame(c1, fg_color="transparent")
    tf.pack(fill="both", expand=True, padx=14, pady=(0, 10))
    app.tech_tree = ttk.Treeview(tf, show="tree",
                                   style="Tech.Treeview")
    vsb = ttk.Scrollbar(tf, orient="vertical",
                         command=app.tech_tree.yview)
    app.tech_tree.configure(yscrollcommand=vsb.set)
    app.tech_tree.pack(side="left", fill="both", expand=True)
    vsb.pack(side="right", fill="y")
    app.tech_tree.bind("<<TreeviewSelect>>",
                        lambda e: _on_tech_sel(app))
    app.tech_search_var.trace_add("write",
                                   lambda *a: _rebuild_tree(app))

    # détail
    mk_title(c1, "  DÉTAIL").pack(anchor="w", padx=14, pady=(4, 4))
    app.detail_text = mk_textbox(c1, height=130)
    app.detail_text.pack(fill="x", padx=14, pady=(0, 10))
    app.detail_text.configure(state="disabled")

    # ── col 2 : planning + programme + générateur + historique ────────
    c2 = ctk.CTkFrame(main, fg_color="transparent")
    c2.grid(row=0, column=2, sticky="nsew")

    # planning
    plan_card = mk_card(c2)
    plan_card.pack(fill="x", pady=(0, 10))
    mk_title(plan_card, "  PLANNING").pack(
        anchor="w", padx=14, pady=(12, 6))
    mk_sep(plan_card).pack(fill="x", padx=14, pady=(0, 6))
    app.schedule_lb = tk.Listbox(
        plan_card, height=10,
        bg=TH.BG_CARD2, fg=TH.TEXT,
        selectbackground=TH.ACCENT_DIM,
        selectforeground=TH.ACCENT_GLOW,
        relief="flat", bd=0,
        font=("Inter", 10), activestyle="none")
    app.schedule_lb.pack(fill="x", padx=14, pady=(0, 6))
    pb = ctk.CTkFrame(plan_card, fg_color="transparent")
    pb.pack(anchor="w", padx=14, pady=(0, 12))
    mk_btn(pb, "➕ Ajouter", lambda: _add_to_plan(app),
           color=TH.ACCENT, hover=TH.ACCENT_HOVER,
           width=110, height=TH.BTN_SM).pack(side="left", padx=3)
    mk_btn(pb, "🗑 Supprimer", lambda: _del_plan_item(app),
           color=TH.DANGER, hover=TH.DANGER_HVR,
           width=110, height=TH.BTN_SM).pack(side="left", padx=3)

    # programme
    prog_card = mk_card(c2)
    prog_card.pack(fill="x", pady=(0, 10))
    mk_title(prog_card, "  PROGRAMME (SÉANCES)").pack(
        anchor="w", padx=14, pady=(12, 6))
    mk_sep(prog_card).pack(fill="x", padx=14, pady=(0, 6))
    app.program_lb = tk.Listbox(
        prog_card, height=7,
        bg=TH.BG_CARD2, fg=TH.TEXT,
        selectbackground=TH.ACCENT_DIM,
        selectforeground=TH.ACCENT_GLOW,
        relief="flat", bd=0,
        font=("Inter", 10), activestyle="none")
    app.program_lb.pack(fill="x", padx=14, pady=(0, 6))
    pbb = ctk.CTkFrame(prog_card, fg_color="transparent")
    pbb.pack(anchor="w", padx=14, pady=(0, 12))
    def _add_to_prog():
        tid = getattr(app, "_last_tid", None)
        if not tid: messagebox.showinfo("ERAGROK","Sélectionne une technique."); return
        tech = tt.find_technique_by_id(tid)
        app.program_lb.insert(tk.END, _fmt(tech))
    mk_btn(pbb, "+ Technique", _add_to_prog,
           color=TH.ACCENT, hover=TH.ACCENT_HOVER,
           width=110, height=TH.BTN_SM).pack(side="left", padx=3)
    mk_btn(pbb, "Supprimer",
           lambda: [app.program_lb.delete(i)
                    for i in reversed(app.program_lb.curselection())],
           color=TH.DANGER, hover=TH.DANGER_HVR,
           width=100, height=TH.BTN_SM).pack(side="left", padx=3)
    mk_btn(pbb, "Effacer tout",
           lambda: (messagebox.askyesno("Confirmer","Effacer ?")
                    and app.program_lb.delete(0, tk.END)),
           color=TH.GRAY, hover=TH.GRAY_HVR,
           width=100, height=TH.BTN_SM).pack(side="left", padx=3)

    # générateur mensuel
    gen_card = mk_card(c2)
    gen_card.pack(fill="x", pady=(0, 10))
    mk_title(gen_card, "  GÉNÉRATEUR MENSUEL").pack(
        anchor="w", padx=14, pady=(12, 6))
    mk_sep(gen_card).pack(fill="x", padx=14, pady=(0, 8))
    app.gen_sarco = tk.BooleanVar(value=True)
    app.gen_mixte = tk.BooleanVar(value=True)
    app.gen_myofi = tk.BooleanVar(value=True)
    cgf = ctk.CTkFrame(gen_card, fg_color="transparent")
    cgf.pack(anchor="w", padx=14, pady=(0, 6))
    for lbl, var in [("Sarco", app.gen_sarco),
                      ("Mixte", app.gen_mixte),
                      ("Myofi", app.gen_myofi)]:
        mk_checkbox(cgf, lbl, var).pack(side="left", padx=6)

    wef = ctk.CTkFrame(gen_card, fg_color="transparent")
    wef.pack(anchor="w", padx=14, pady=(0, 8))
    mk_label(wef, "Sam:", size="small",
             color=TH.TEXT_SUB).pack(side="left", padx=(0,4))
    app.gen_sat = tk.StringVar(value="Off")
    mk_combo(wef, WE_OPTIONS, width=90,
             command=lambda v: app.gen_sat.set(v)).pack(side="left", padx=(0,10))
    mk_label(wef, "Dim:", size="small",
             color=TH.TEXT_SUB).pack(side="left", padx=(0,4))
    app.gen_sun = tk.StringVar(value="Off")
    mk_combo(wef, WE_OPTIONS, width=90,
             command=lambda v: app.gen_sun.set(v)).pack(side="left")

    gbf = ctk.CTkFrame(gen_card, fg_color="transparent")
    gbf.pack(anchor="w", padx=14, pady=(0, 6))
    mk_btn(gbf, "⚡ Générer mois", lambda: _gen_month(app),
           color=TH.ACCENT, hover=TH.ACCENT_HOVER,
           width=140, height=TH.BTN_SM).pack(side="left", padx=3)
    mk_btn(gbf, "💾 Sauvegarder", lambda: _save_programme(app),
           color=TH.SUCCESS, hover=TH.SUCCESS_HVR,
           width=120, height=TH.BTN_SM).pack(side="left", padx=3)
    mk_btn(gbf, "🔍 Visu PDF", lambda: _preview_pdf(app),
           color=TH.BLUE, hover=TH.BLUE_HVR,
           width=100, height=TH.BTN_SM).pack(side="left", padx=3)
    mk_btn(gbf, "📄 Export PDF", lambda: _export_pdf(app),
           color=TH.PURPLE, hover=TH.PURPLE_HVR,
           width=100, height=TH.BTN_SM).pack(side="left", padx=3)

    # ── Programmes sauvegardés ───────────────────────────────────────────
    saved_card = mk_card(c2)
    saved_card.pack(fill="x", pady=(0, 10))
    mk_title(saved_card, "  📂  PROGRAMMES SAUVEGARDÉS").pack(
        anchor="w", padx=14, pady=(12, 6))
    mk_sep(saved_card).pack(fill="x", padx=14, pady=(0, 8))

    app.saved_prog_lb = tk.Listbox(
        saved_card, height=5,
        bg=TH.BG_CARD2, fg=TH.TEXT,
        selectbackground=TH.ACCENT_DIM,
        selectforeground=TH.ACCENT_GLOW,
        relief="flat", bd=0,
        font=("Inter", 10), activestyle="none")
    app.saved_prog_lb.pack(fill="x", padx=14, pady=(0, 6))

    spbf = ctk.CTkFrame(saved_card, fg_color="transparent")
    spbf.pack(anchor="w", padx=14, pady=(0, 12))
    mk_btn(spbf, "📂 Charger", lambda: _load_saved_programme(app),
           color=TH.ACCENT, hover=TH.ACCENT_HOVER,
           width=110, height=TH.BTN_SM).pack(side="left", padx=3)
    mk_btn(spbf, "🗑 Supprimer", lambda: _del_saved_programme(app),
           color=TH.DANGER, hover=TH.DANGER_HVR,
           width=110, height=TH.BTN_SM).pack(side="left", padx=3)
    mk_btn(spbf, "↻", lambda: _refresh_saved_programmes(app),
           color=TH.GRAY, hover=TH.GRAY_HVR,
           width=40, height=TH.BTN_SM).pack(side="left", padx=3)

    # notes + sauvegarde
    note_card = mk_card(c2)
    note_card.pack(fill="x", pady=(0, 10))
    mk_title(note_card, "  NOTES DE SÉANCE").pack(
        anchor="w", padx=14, pady=(12, 6))
    mk_sep(note_card).pack(fill="x", padx=14, pady=(0, 8))
    app.note_text = mk_textbox(note_card, height=70)
    app.note_text.pack(fill="x", padx=14, pady=(0, 8))
    mk_btn(note_card, "💾  SAUVEGARDER LA SÉANCE",
           lambda: _save_session(app),
           color=TH.SUCCESS, hover=TH.SUCCESS_HVR,
           width=260, height=TH.BTN_LG).pack(anchor="e", padx=14, pady=(0, 14))

    # historique inline
    hist_card = mk_card(c2)
    hist_card.pack(fill="both", expand=True)
    mk_title(hist_card, "  HISTORIQUE SÉANCES").pack(
        anchor="w", padx=14, pady=(12, 6))
    mk_sep(hist_card).pack(fill="x", padx=14, pady=(0, 8))
    hinner = ctk.CTkFrame(hist_card, fg_color="transparent")
    hinner.pack(fill="both", expand=True, padx=14, pady=(0, 12))

    hleft = ctk.CTkFrame(hinner, fg_color="transparent", width=240)
    hleft.pack(side="left", fill="y", padx=(0,8))
    hleft.pack_propagate(False)
    app.hist_lb = tk.Listbox(
        hleft, height=9,
        bg=TH.BG_CARD2, fg=TH.TEXT,
        selectbackground=TH.ACCENT_DIM,
        selectforeground=TH.ACCENT_GLOW,
        relief="flat", bd=0,
        font=("Inter", 10), activestyle="none")
    app.hist_lb.pack(fill="both", expand=True)
    app.hist_lb.bind("<<ListboxSelect>>", lambda e: _hist_show(app))

    hbf = ctk.CTkFrame(hleft, fg_color="transparent")
    hbf.pack(fill="x", pady=4)
    mk_btn(hbf, "🗑 Suppr.", lambda: _hist_del(app),
           color=TH.DANGER, hover=TH.DANGER_HVR,
           width=90, height=TH.BTN_SM).pack(side="left", padx=2)
    mk_btn(hbf, "↻", lambda: _hist_refresh(app),
           color=TH.GRAY, hover=TH.GRAY_HVR,
           width=40, height=TH.BTN_SM, radius=TH.R_BTN).pack(side="left", padx=2)
    mk_btn(hbf, "📥", lambda: _hist_import(app),
           color=TH.BLUE, hover=TH.BLUE_HVR,
           width=40, height=TH.BTN_SM, radius=TH.R_BTN).pack(side="left", padx=2)
    mk_btn(hbf, "📤", lambda: _hist_export(app),
           color=TH.GRAY, hover=TH.GRAY_HVR,
           width=40, height=TH.BTN_SM, radius=TH.R_BTN).pack(side="left", padx=2)

    hright = ctk.CTkFrame(hinner, fg_color="transparent")
    hright.pack(side="left", fill="both", expand=True)
    mk_title(hright, "  Détail", color=TH.TEXT_SUB).pack(
        anchor="w", pady=(0, 4))
    app.hist_detail = mk_textbox(hright, height=150)
    app.hist_detail.pack(fill="both", expand=True)
    app.hist_detail.configure(state="disabled")

    # ── init ──
    app._plan = _read_plan(app)
    try: app.calendar.selection_set(datetime.date.today())
    except Exception: pass
    _refresh_plan(app)
    _rebuild_tree(app)
    if program: _load_template(app, program)
    _hist_refresh(app)
    _refresh_saved_programmes(app)

    # Auto-charger le dernier programme sauvegardé
    def _auto_load_prog():
        try:
            progs = _load_all_programmes(app)
            if progs and hasattr(app, "program_lb"):
                last = progs[-1]
                lines = last.get("lines", [])
                if lines:
                    app.program_lb.delete(0, tk.END)
                    for l in lines:
                        app.program_lb.insert(tk.END, l)
        except Exception:
            pass
    try: app.root.after(200, _auto_load_prog)
    except Exception: pass


def _load_template(app, name):
    if not hasattr(app,"program_lb"): return
    app.program_lb.delete(0, tk.END)
    if name in ["Sarco","Myofi"]:
        try:
            tmpl = tt.build_program_template(name, weeks=4)
            for w in tmpl["weeks"]:
                app.program_lb.insert(tk.END, f"─── Semaine {w['week']} ───")
                for s in w["sessions"]:
                    app.program_lb.insert(tk.END, f"  Séance {s['session']}")
                    for ex in s["exercises"]:
                        tech = tt.find_technique_by_id(ex["id"])
                        if tech:
                            app.program_lb.insert(
                                tk.END,
                                f"    {tech['nom']} [{tech['reps']}] | {tech['charge']} ({tech['id']})")
        except Exception:
            app.program_lb.insert(tk.END, f"Template {name}")
    else:
        for l in [f"Standard — Jour A : Pecs/Dos 4×8",
                  f"Standard — Jour B : Jambes 4×8",
                  f"Standard — Jour C : Épaules/Bras 4×8"]:
            app.program_lb.insert(tk.END, l)
