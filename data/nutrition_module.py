# data/nutrition_module.py — ERAGROK  ·  Dark Bodybuilding
import os, math, csv, calendar as pycal, datetime
import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
from tkcalendar import Calendar
from data import utils
from data.theme import (
    TH, mk_btn, mk_card, mk_card2, mk_entry, mk_combo,
    mk_textbox, mk_label, mk_title, mk_sep, mk_badge,
    mk_scrollframe, screen_header, apply_treeview_style,
)

try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
except Exception:
    plt = FigureCanvasTkAgg = None


# ── Helpers ───────────────────────────────────────────────────────────────────
def _d2s(d): return d.strftime("%d/%m/%Y")

def _parse(s):
    for fmt in ["%d/%m/%Y", "%Y-%m-%d", "%m/%d/%Y"]:
        try: return datetime.datetime.strptime(str(s).strip(), fmt).date()
        except Exception: pass
    return None

def _last_entries(app, fname, n=1):
    if not getattr(app, "current_user", None): return []
    p = os.path.join(utils.USERS_DIR, app.current_user, fname)
    if not os.path.exists(p): return []
    try:
        with open(p, "r", newline="", encoding="utf-8") as f:
            rows = list(csv.reader(f))
        return [" | ".join(r) for r in rows[max(1, len(rows)-n):][::-1]]
    except Exception: return []

def _refresh_tree(app, fichier):
    if not hasattr(app, "nutrition_tree"): return
    for r in app.nutrition_tree.get_children():
        app.nutrition_tree.delete(r)
    if not os.path.exists(fichier): return
    try:
        sel = getattr(app, "selected_dates", set())
        with open(fichier, "r", newline="", encoding="utf-8") as f:
            reader = csv.reader(f); next(reader, None)
            for row in reader:
                if not row: continue
                if sel:
                    p = _parse(row[0] if row else "")
                    if p and p not in sel: continue
                app.nutrition_tree.insert("", "end", values=(
                    row[0] if len(row)>0 else "",
                    row[1] if len(row)>1 else "",
                    row[3] if len(row)>3 else "",
                    row[7] if len(row)>7 else "",
                ))
    except Exception: pass


# ── Calculs ───────────────────────────────────────────────────────────────────
def _update_calc(app):
    try:
        poids = app.poids_var.get().strip()
        age   = app.age_var.get().strip()
        if not poids or not age: return
        ui = getattr(app, "user_info", None)
        if not ui: return
        nut = utils.calculs_nutrition(poids, age,
                                       ui.get("sexe"), ui.get("objectif"), ui.get("taille"))
        if not nut: return
        adj  = utils.ADJUSTMENTS.get(app.adjustment_var.get() or "Maintien (0%)", 0.0)
        cal  = nut["tdee"] * (1 + adj)
        obj  = ui.get("objectif", "")
        if "masse" in obj.lower():   cp, fp = 0.47, 0.23
        elif "perte" in obj.lower(): cp, fp = 0.37, 0.23
        else:                        cp, fp = 0.45, 0.25
        g = (cal * cp) / 4
        l = (cal * fp) / 9
        if getattr(app, "calories_label",  None):
            app.calories_label.configure(
                text=f"🔥  {cal:.0f} kcal  (TDEE {nut['tdee']:.0f} | {adj*100:+.1f}%)")
        if getattr(app, "proteines_label", None):
            app.proteines_label.configure(text=f"🥩  {nut['proteines']:.0f} g")
        if getattr(app, "glucides_label",  None):
            app.glucides_label.configure(text=f"🍚  {g:.0f} g")
        if getattr(app, "lipides_label",   None):
            app.lipides_label.configure(text=f"🥑  {l:.0f} g")
        app._last_cal = int(round(cal))
    except Exception: pass


def _save_nutrition(app):
    if not getattr(app, "current_user", None):
        messagebox.showerror("ERAGROK", "Sélectionne un élève."); return
    sel = getattr(app, "selected_dates", set())
    if not sel:
        try: sel = {app.calendar.selection_get()}
        except Exception: sel = {datetime.date.today()}
    poids = app.poids_var.get().strip()
    age   = app.age_var.get().strip()
    note  = app.nutrition_note_text.get("1.0", "end").strip()
    ui    = getattr(app, "user_info", None)
    if not ui: messagebox.showerror("ERAGROK", "Profil manquant."); return
    adj   = utils.ADJUSTMENTS.get(app.adjustment_var.get() or "Maintien (0%)", 0.0)
    try:
        nut = utils.calculs_nutrition(poids or 70, age or 30,
                                       ui.get("sexe", "Homme"),
                                       ui.get("objectif", "Maintien"),
                                       ui.get("taille", 170))
    except Exception: nut = None
    if nut:
        cal = nut["tdee"] * (1 + adj)
        obj = ui.get("objectif", "")
        if "masse" in obj.lower():   cp, fp = 0.47, 0.23
        elif "perte" in obj.lower(): cp, fp = 0.37, 0.23
        else:                        cp, fp = 0.45, 0.25
        p, g, l = nut["proteines"], (cal*cp)/4, (cal*fp)/9
        c = int(round(cal))
    else: p = g = l = c = 0
    fichier = os.path.join(utils.USERS_DIR, app.current_user, "nutrition.csv")
    for d in sorted(sel):
        try:
            with open(fichier, "a", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow(
                    [_d2s(d), poids, age, c,
                     f"{p:.0f}", f"{g:.0f}", f"{l:.0f}", note])
        except Exception as e:
            messagebox.showerror("ERAGROK", str(e)); return
    messagebox.showinfo("ERAGROK",
                        f"✔  Nutrition sauvegardée pour {len(sel)} date(s).")
    _refresh_tree(app, fichier)


def _edit_selected(app):
    sel = app.nutrition_tree.selection()
    if not sel: messagebox.showinfo("ERAGROK", "Sélectionne une ligne."); return
    vals = app.nutrition_tree.item(sel[0], "values")
    dlg = ctk.CTkToplevel()
    dlg.title("Modifier entrée")
    dlg.geometry("520x340")
    dlg.configure(fg_color=TH.BG_CARD)
    dlg.grab_set(); dlg.focus_set()
    mk_title(dlg, "  MODIFIER L'ENTRÉE").pack(anchor="w", padx=22, pady=(18, 6))
    mk_sep(dlg).pack(fill="x", padx=22, pady=(0, 14))
    frm = ctk.CTkFrame(dlg, fg_color="transparent")
    frm.pack(fill="x", padx=22)
    entries = {}
    for i, (lbl, val) in enumerate(
            zip(["Date", "Poids (kg)", "Calories", "Note"], vals)):
        mk_label(frm, lbl+":", size="small",
                 color=TH.TEXT_SUB).grid(row=i, column=0, sticky="w",
                                          padx=6, pady=7)
        e = mk_entry(frm, width=340)
        e.insert(0, str(val))
        e.grid(row=i, column=1, padx=6, pady=7)
        entries[lbl] = e
    def _do_save():
        fichier = os.path.join(utils.USERS_DIR, app.current_user, "nutrition.csv")
        try:
            with open(fichier, "r", newline="", encoding="utf-8") as f:
                rows = list(csv.reader(f))
            hdr, data = (rows[0] if rows else []), rows[1:]
            old = vals[0] if vals else ""
            for i, row in enumerate(data):
                if row and row[0] == old:
                    if len(row)>0: row[0] = entries["Date"].get()
                    if len(row)>1: row[1] = entries["Poids (kg)"].get()
                    if len(row)>3: row[3] = entries["Calories"].get()
                    if len(row)>7: row[7] = entries["Note"].get()
                    data[i] = row; break
            with open(fichier, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                if hdr: w.writerow(hdr)
                for r in data: w.writerow(r)
            dlg.destroy()
            _refresh_tree(app, fichier)
        except Exception as e: messagebox.showerror("ERAGROK", str(e))
    mk_btn(dlg, "✔  Enregistrer", _do_save,
           color=TH.SUCCESS, hover=TH.SUCCESS_HVR, width=180).pack(pady=18)


def _delete_selected(app):
    sel = app.nutrition_tree.selection()
    if not sel: messagebox.showinfo("ERAGROK", "Sélectionne une ligne."); return
    if not messagebox.askyesno("Confirmer", "Supprimer la ligne ?"): return
    vals = app.nutrition_tree.item(sel[0], "values")
    d    = vals[0] if vals else ""
    fichier = os.path.join(utils.USERS_DIR, app.current_user, "nutrition.csv")
    try:
        with open(fichier, "r", newline="", encoding="utf-8") as f:
            rows = list(csv.reader(f))
        hdr, data = (rows[0] if rows else []), rows[1:]
        data = [r for r in data if not (r and r[0] == d)]
        with open(fichier, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            if hdr: w.writerow(hdr)
            for r in data: w.writerow(r)
        _refresh_tree(app, fichier)
    except Exception as e: messagebox.showerror("ERAGROK", str(e))


def _add_cal_sel(app):
    mode = getattr(app, "_sel_mode_var", None)
    mode = mode.get() if mode else "Single"
    try:
        d = app.calendar.selection_get()
        if not isinstance(d, datetime.date):
            d = datetime.datetime.strptime(app.calendar.get_date(), "%d/%m/%Y").date()
    except Exception: return
    if mode == "Single":   app.selected_dates = {d}
    elif mode == "Multiple": app.selected_dates.add(d)
    elif mode == "Week":
        s = d - datetime.timedelta(days=d.weekday())
        app.selected_dates = {s + datetime.timedelta(i) for i in range(7)}
    elif mode == "Month":
        _, nd = pycal.monthrange(d.year, d.month)
        app.selected_dates = {d.replace(day=i) for i in range(1, nd+1)}
    ds = sorted(app.selected_dates)
    if len(ds) == 0:   txt = "Sélection : (aucune)"
    elif len(ds) == 1: txt = f"Sélection : {_d2s(ds[0])}"
    elif len(ds) <= 3: txt = "Sélection : " + ", ".join(_d2s(x) for x in ds)
    else:              txt = f"{len(ds)} dates ({_d2s(ds[0])} → {_d2s(ds[-1])})"
    if hasattr(app, "sel_label"): app.sel_label.configure(text=txt)
    f2 = os.path.join(utils.USERS_DIR, app.current_user, "nutrition.csv") if app.current_user else None
    if f2: _refresh_tree(app, f2)


# ── Jauge IMC ─────────────────────────────────────────────────────────────────
def _imc_gauge(parent, imc, poids, taille):
    for w in parent.winfo_children(): w.destroy()
    if not plt:
        mk_label(parent, "matplotlib manquant", color=TH.TEXT_MUTED).pack(); return
    try:
        fig = plt.Figure(figsize=(3.8, 2.1), facecolor=TH.BG_CARD2, tight_layout=True)
        ax  = fig.add_subplot(111, polar=True)
        ax.set_facecolor(TH.BG_CARD2)
        segs = [
            (0.0,  18.5, "#3b82f6"), (18.5, 25.0, "#22c55e"),
            (25.0, 30.0, "#f59e0b"), (30.0, 40.0, "#ef4444"), (40.0, 45.0, "#7f1d1d"),
        ]
        bw = math.pi / len(segs)
        for i, (_, __, col) in enumerate(segs):
            ax.bar(math.pi * i / len(segs), 0.8, width=bw,
                   bottom=0.2, color=col, alpha=0.9)
        if imc is not None:
            theta = math.pi * max(0.0, min(45.0, imc)) / 45.0
            ax.annotate("", xy=(theta, 0.85), xytext=(theta, 0.0),
                        arrowprops=dict(arrowstyle="-|>", color=TH.TEXT, lw=2.5))
            ax.text(math.radians(90), -0.45, f"IMC : {imc:.1f}",
                    ha="center", fontsize=10, color=TH.TEXT, fontweight="bold")
            if poids and taille:
                try:
                    tm = float(taille) / 100
                    p  = float(poids)
                    nm, nx = 18.5*tm**2, 25.0*tm**2
                    if p < nm:   diff = f"+{nm-p:.1f} kg → 18.5"
                    elif p > nx: diff = f"-{p-nx:.1f} kg → 25.0"
                    else:        diff = "✓ Zone normale"
                    ax.text(math.radians(90), -0.88, diff,
                            ha="center", fontsize=8, color=TH.TEXT_SUB)
                except Exception: pass
        ax.set_axis_off()
        cv = FigureCanvasTkAgg(fig, master=parent)
        cv.draw()
        w = cv.get_tk_widget()
        try: w.configure(bg=TH.BG_CARD2)
        except Exception: pass
        w.pack(fill="both", expand=True)
    except Exception:
        mk_label(parent, "Erreur jauge", color=TH.TEXT_MUTED).pack()


# ════════════════════════════════════════════════════════════════════════════
#  DASHBOARD
# ════════════════════════════════════════════════════════════════════════════
def render_dashboard(app):
    for w in app.content.winfo_children(): w.destroy()

    screen_header(app.content, "🏠  DASHBOARD",
                  user_name=app.selected_user_name)
    scroll = mk_scrollframe(app.content)
    scroll.pack(fill="both", expand=True)

    main = ctk.CTkFrame(scroll, fg_color="transparent")
    main.pack(fill="both", expand=True, padx=24, pady=20)
    main.columnconfigure(0, weight=5)
    main.columnconfigure(1, weight=2)

    # ── colonne gauche ──
    left = ctk.CTkFrame(main, fg_color="transparent")
    left.grid(row=0, column=0, sticky="nsew", padx=(0, 14))

    # carte nutrition
    nc = mk_card(left)
    nc.pack(fill="x", pady=(0, 14))
    mk_title(nc, "  NUTRITION & COMPOSITION").pack(
        anchor="w", padx=16, pady=(14, 6))
    mk_sep(nc).pack(fill="x", padx=16, pady=(0, 10))

    for attr in ["poids_var", "age_var", "adjustment_var"]:
        if not hasattr(app, attr): setattr(app, attr, tk.StringVar())

    # pré-remplissage poids
    dp = ""
    last = _last_entries(app, "nutrition.csv", 1)
    if last:
        try: dp = last[0].split(" | ")[1]
        except Exception: pass
    if not dp and getattr(app, "user_info", None):
        p = app.user_info.get("poids")
        if p is not None: dp = str(int(float(p))) if float(p).is_integer() else str(p)
    app.poids_var.set(dp)
    app.age_var.set(str(app.user_info.get("age", "") or "") if app.user_info else "")
    dadj = app.user_info.get("ajustement", "Maintien (0%)") if app.user_info else "Maintien (0%)"
    if dadj not in utils.ADJUSTMENTS: dadj = "Maintien (0%)"
    app.adjustment_var.set(dadj)

    # ligne inputs
    ir = ctk.CTkFrame(nc, fg_color="transparent")
    ir.pack(fill="x", padx=16, pady=(0, 10))
    for lbl, var, w in [("Poids (kg)", app.poids_var, 100),
                         ("Age",        app.age_var,   80)]:
        cc = ctk.CTkFrame(ir, fg_color="transparent")
        cc.pack(side="left", padx=(0, 16))
        mk_label(cc, lbl, size="small", color=TH.TEXT_SUB).pack(anchor="w", pady=(0, 4))
        e = mk_entry(cc, width=w)
        e.configure(textvariable=var); e.pack()

    mc2 = ctk.CTkFrame(ir, fg_color="transparent")
    mc2.pack(side="left")
    mk_label(mc2, "Ajustement", size="small",
             color=TH.TEXT_SUB).pack(anchor="w", pady=(0, 4))
    acb = mk_combo(mc2, list(utils.ADJUSTMENTS.keys()), width=300,
                   command=lambda v: _update_calc(app))
    acb.configure(variable=app.adjustment_var); acb.pack()

    # résultats
    rr = mk_card2(nc)
    rr.pack(fill="x", padx=16, pady=(0, 14))
    rrow = ctk.CTkFrame(rr, fg_color="transparent")
    rrow.pack(fill="x", padx=12, pady=12)
    app.calories_label  = ctk.CTkLabel(rrow, text="🔥  — kcal",
                                        font=TH.F_H3, text_color=TH.ACCENT_GLOW)
    app.proteines_label = ctk.CTkLabel(rrow, text="🥩  — g",
                                        font=TH.F_BODY, text_color=TH.TEXT)
    app.glucides_label  = ctk.CTkLabel(rrow, text="🍚  — g",
                                        font=TH.F_BODY, text_color=TH.TEXT)
    app.lipides_label   = ctk.CTkLabel(rrow, text="🥑  — g",
                                        font=TH.F_BODY, text_color=TH.TEXT)
    for lb in [app.calories_label, app.proteines_label,
               app.glucides_label, app.lipides_label]:
        lb.pack(side="left", padx=14)

    try:
        app.poids_var.trace_add("write",      lambda *a: _update_calc(app))
        app.age_var.trace_add("write",        lambda *a: _update_calc(app))
        app.adjustment_var.trace_add("write", lambda *a: _update_calc(app))
    except Exception: pass

    # métriques + jauge IMC
    hg = ctk.CTkFrame(nc, fg_color="transparent")
    hg.pack(fill="both", expand=True, padx=16, pady=(0, 14))
    imc_val = poids_val = taille_val = None
    if getattr(app, "user_info", None):
        try:
            poids_val  = float(dp or app.user_info.get("poids", 0))
            taille_val = float(app.user_info.get("taille", 0))
            imc_val, imc_cat = utils.calculer_imc(poids_val, taille_val)
        except Exception: pass

    met = ctk.CTkFrame(hg, fg_color="transparent")
    met.pack(side="left", padx=(0, 20), pady=6, anchor="n")
    def mrow(lbl, val, col=TH.TEXT):
        r = ctk.CTkFrame(met, fg_color="transparent")
        r.pack(anchor="w", pady=5)
        mk_label(r, lbl, size="small", color=TH.TEXT_SUB, width=100).pack(side="left")
        mk_label(r, val, size="body",  color=col).pack(side="left")
    mrow("⚖️  Poids",  f"{poids_val:.1f} kg" if poids_val else "—")
    mrow("📏  IMC",   (f"{imc_val:.1f} — {imc_cat[0]}" if imc_val else "—"),
         col=TH.ACCENT_GLOW)

    gf = mk_card2(hg)
    gf.pack(side="left", fill="both", expand=True, pady=6)
    _imc_gauge(gf, imc_val, poids_val, taille_val)

    # ── colonne droite ──
    right = ctk.CTkFrame(main, fg_color="transparent")
    right.grid(row=0, column=1, sticky="nsew")

    def _acard(icon, title, last_txt, buttons):
        c = mk_card(right)
        c.pack(fill="x", pady=(0, 14))
        mk_title(c, f"  {icon}  {title}").pack(
            anchor="w", padx=16, pady=(14, 6))
        mk_sep(c).pack(fill="x", padx=16, pady=(0, 8))
        mk_label(c, last_txt or "Aucune entrée.", size="small",
                 color=TH.TEXT_MUTED).pack(anchor="w", padx=16, pady=(0, 10))
        br = ctk.CTkFrame(c, fg_color="transparent")
        br.pack(anchor="w", padx=14, pady=(0, 14))
        for t, cmd, col, hov in buttons:
            mk_btn(br, t, cmd, color=col, hover=hov,
                   width=106, height=TH.BTN_SM).pack(side="left", padx=3)

    lt = _last_entries(app, "entrainement.csv", 1)
    _acard("🏋", "ENTRAÎNEMENT", lt[0] if lt else None, [
        ("Ouvrir",
         lambda: __import__("data.entrainement_module")
                 .entrainement_module.show_entrainement_screen(app),
         TH.ACCENT, TH.ACCENT_HOVER),
        ("Sarco",
         lambda: __import__("data.entrainement_module")
                 .entrainement_module.show_entrainement_screen(app, program="Sarco"),
         TH.PURPLE, TH.PURPLE_HVR),
        ("Myofi",
         lambda: __import__("data.entrainement_module")
                 .entrainement_module.show_entrainement_screen(app, program="Myofi"),
         TH.BLUE, TH.BLUE_HVR),
    ])
    lc = _last_entries(app, "cycle.csv", 1)
    _acard("💉", "CYCLE", lc[0] if lc else None, [
        ("Ouvrir",
         lambda: __import__("data.cycle_module")
                 .cycle_module.show_cycle_disclaimer(app),
         TH.WARNING, TH.WARNING_HVR),
    ])
    _acard("🍎", "NUTRITION", None, [
        ("Ouvrir", lambda: show_nutrition_screen(app),
         TH.SUCCESS, TH.SUCCESS_HVR),
    ])
    _update_calc(app)


# ════════════════════════════════════════════════════════════════════════════
#  ÉCRAN NUTRITION
# ════════════════════════════════════════════════════════════════════════════
def show_nutrition_screen(app):
    for w in app.content.winfo_children(): w.destroy()

    screen_header(app.content, "🍎  NUTRITION",
                  user_name=app.selected_user_name,
                  back_cmd=lambda: render_dashboard(app))
    scroll = mk_scrollframe(app.content)
    scroll.pack(fill="both", expand=True)

    cols = ctk.CTkFrame(scroll, fg_color="transparent")
    cols.pack(fill="both", expand=True, padx=24, pady=20)
    cols.columnconfigure(0, weight=0)
    cols.columnconfigure(1, weight=1)

    # ── gauche : calendrier + sélection ──
    left = mk_card(cols)
    left.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
    mk_title(left, "  SÉLECTION DATES").pack(
        anchor="w", padx=14, pady=(14, 6))
    mk_sep(left).pack(fill="x", padx=14, pady=(0, 10))

    if not hasattr(app, "selected_dates"): app.selected_dates = set()

    _cs = dict(
        background=TH.BG_CARD2, foreground=TH.TEXT,
        selectbackground=TH.ACCENT, selectforeground=TH.TEXT,
        bordercolor=TH.BORDER,
        headersbackground=TH.BG_CARD, headersforeground=TH.TEXT_SUB,
        normalforeground=TH.TEXT, weekendforeground=TH.ACCENT_GLOW,
        font=("Inter", 10), headersfont=("Inter", 10, "bold"),
    )
    app.calendar = Calendar(left, selectmode="day", **_cs)
    app.calendar.pack(padx=14, pady=(0, 10))

    app._sel_mode_var = tk.StringVar(value="Single")
    mk_label(left, "Mode :", size="small",
             color=TH.TEXT_SUB).pack(anchor="w", padx=14, pady=(4, 2))
    for m in ["Single", "Week", "Month", "Multiple"]:
        ctk.CTkRadioButton(
            left, text=m, value=m, variable=app._sel_mode_var,
            fg_color=TH.ACCENT, hover_color=TH.ACCENT_HOVER,
            text_color=TH.TEXT, font=TH.F_SMALL,
            command=lambda: setattr(app, "selection_mode",
                                    app._sel_mode_var.get()),
        ).pack(anchor="w", padx=14, pady=2)

    mk_btn(left, "➕  Ajouter",
           lambda: _add_cal_sel(app),
           color=TH.ACCENT, hover=TH.ACCENT_HOVER,
           width=200, height=TH.BTN_SM).pack(padx=14, pady=(10, 4))
    mk_btn(left, "🗑  Effacer",
           lambda: _clear_sel(app),
           color=TH.GRAY, hover=TH.GRAY_HVR,
           width=200, height=TH.BTN_SM).pack(padx=14, pady=4)
    app.sel_label = mk_label(left, "Sélection : (aucune)",
                              size="small", color=TH.TEXT_MUTED)
    app.sel_label.pack(anchor="w", padx=14, pady=(6, 14))

    # ── droite ──
    right = ctk.CTkFrame(cols, fg_color="transparent")
    right.grid(row=0, column=1, sticky="nsew")

    for attr in ["poids_var", "age_var", "adjustment_var"]:
        if not hasattr(app, attr): setattr(app, attr, tk.StringVar())

    dp = ""
    if getattr(app, "user_info", None):
        p = app.user_info.get("poids")
        if p is not None: dp = str(int(float(p))) if float(p).is_integer() else str(p)
    app.poids_var.set(dp)
    app.age_var.set(str(app.user_info.get("age", "") or "") if app.user_info else "")
    dadj = app.user_info.get("ajustement", "Maintien (0%)") if app.user_info else "Maintien (0%)"
    if dadj not in utils.ADJUSTMENTS: dadj = "Maintien (0%)"
    app.adjustment_var.set(dadj)

    cc = mk_card(right)
    cc.pack(fill="x", pady=(0, 14))
    mk_title(cc, "  CALCULS NUTRITIONNELS").pack(
        anchor="w", padx=16, pady=(14, 6))
    mk_sep(cc).pack(fill="x", padx=16, pady=(0, 10))

    ir2 = ctk.CTkFrame(cc, fg_color="transparent")
    ir2.pack(fill="x", padx=16, pady=(0, 8))
    for lbl, var, w in [("Poids (kg)", app.poids_var, 100),
                         ("Age",        app.age_var,   80)]:
        c2 = ctk.CTkFrame(ir2, fg_color="transparent")
        c2.pack(side="left", padx=(0, 16))
        mk_label(c2, lbl, size="small",
                 color=TH.TEXT_SUB).pack(anchor="w", pady=(0, 4))
        e2 = mk_entry(c2, width=w)
        e2.configure(textvariable=var); e2.pack()

    mc3 = ctk.CTkFrame(ir2, fg_color="transparent")
    mc3.pack(side="left")
    mk_label(mc3, "Ajustement", size="small",
             color=TH.TEXT_SUB).pack(anchor="w", pady=(0, 4))
    acb3 = mk_combo(mc3, list(utils.ADJUSTMENTS.keys()), width=300,
                    command=lambda v: _update_calc(app))
    acb3.configure(variable=app.adjustment_var); acb3.pack()

    rr2 = mk_card2(cc)
    rr2.pack(fill="x", padx=16, pady=(0, 14))
    rrow2 = ctk.CTkFrame(rr2, fg_color="transparent")
    rrow2.pack(fill="x", padx=12, pady=12)
    app.calories_label  = ctk.CTkLabel(rrow2, text="🔥  — kcal",
                                        font=TH.F_H3, text_color=TH.ACCENT_GLOW)
    app.proteines_label = ctk.CTkLabel(rrow2, text="🥩  — g",
                                        font=TH.F_BODY, text_color=TH.TEXT)
    app.glucides_label  = ctk.CTkLabel(rrow2, text="🍚  — g",
                                        font=TH.F_BODY, text_color=TH.TEXT)
    app.lipides_label   = ctk.CTkLabel(rrow2, text="🥑  — g",
                                        font=TH.F_BODY, text_color=TH.TEXT)
    for lb in [app.calories_label, app.proteines_label,
               app.glucides_label, app.lipides_label]:
        lb.pack(side="left", padx=14)

    try:
        app.poids_var.trace_add("write",      lambda *a: _update_calc(app))
        app.age_var.trace_add("write",        lambda *a: _update_calc(app))
        app.adjustment_var.trace_add("write", lambda *a: _update_calc(app))
    except Exception: pass

    # note
    nc2 = mk_card(right)
    nc2.pack(fill="x", pady=(0, 14))
    mk_title(nc2, "  NOTE").pack(anchor="w", padx=16, pady=(14, 6))
    mk_sep(nc2).pack(fill="x", padx=16, pady=(0, 8))
    app.nutrition_note_text = mk_textbox(nc2, height=80)
    app.nutrition_note_text.pack(fill="x", padx=16, pady=(0, 14))

    # save
    mk_btn(right, "💾  SAUVEGARDER",
           lambda: _save_nutrition(app),
           color=TH.SUCCESS, hover=TH.SUCCESS_HVR,
           width=210, height=TH.BTN_LG).pack(anchor="e", pady=(0, 14))

    # historique
    hc = mk_card(right)
    hc.pack(fill="both", expand=True)
    mk_title(hc, "  HISTORIQUE NUTRITION").pack(
        anchor="w", padx=16, pady=(14, 6))
    mk_sep(hc).pack(fill="x", padx=16, pady=(0, 8))

    apply_treeview_style("Nutr")
    app.nutrition_tree = ttk.Treeview(
        hc, columns=("Date", "Poids", "Calories", "Note"),
        show="headings", selectmode="browse", style="Nutr.Treeview")
    for col, w in [("Date", 120), ("Poids", 80),
                   ("Calories", 100), ("Note", 340)]:
        app.nutrition_tree.heading(col, text=col)
        app.nutrition_tree.column(col, width=w,
                                   anchor="center" if col != "Note" else "w")
    app.nutrition_tree.pack(fill="both", expand=True, padx=16, pady=(0, 8))
    app.nutrition_tree.bind("<Double-1>", lambda e: _edit_selected(app))

    ar = ctk.CTkFrame(hc, fg_color="transparent")
    ar.pack(anchor="w", padx=14, pady=(0, 14))
    mk_btn(ar, "✏  Modifier",  lambda: _edit_selected(app),
           color=TH.GRAY, hover=TH.GRAY_HVR,
           width=130, height=TH.BTN_SM).pack(side="left", padx=4)
    mk_btn(ar, "🗑  Supprimer", lambda: _delete_selected(app),
           color=TH.DANGER, hover=TH.DANGER_HVR,
           width=130, height=TH.BTN_SM).pack(side="left", padx=4)

    f = os.path.join(utils.USERS_DIR, app.current_user, "nutrition.csv") if app.current_user else None
    if f: _refresh_tree(app, f)
    _update_calc(app)


def _clear_sel(app):
    app.selected_dates = set()
    if hasattr(app, "sel_label"): app.sel_label.configure(text="Sélection : (aucune)")
    f = os.path.join(utils.USERS_DIR, app.current_user, "nutrition.csv") if app.current_user else None
    if f: _refresh_tree(app, f)
