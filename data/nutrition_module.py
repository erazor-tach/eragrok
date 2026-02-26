# data/nutrition_module.py
# Module Nutrition pour ERAGROK
# - Dashboard + écran Nutrition
# - Sélection multi‑dates (Single / Week / Month / Multiple)
# - Historique filtré par sélection (affiche les lignes correspondant aux dates sélectionnées)
# - Edition / suppression des lignes depuis le tableau (Treeview)
# Robustification : comparaison par objets datetime.date (normalisation fiable des formats)
# Dépendances optionnelles : pandas, matplotlib, tkcalendar
# Place ce fichier dans data/nutrition_module.py (remplace l'ancien)

import os
import math
import csv
import calendar as pycalendar
import datetime
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import Calendar

from data import utils

# optional imports (degrade gracieusement si absents)
try:
    import pandas as pd
except Exception:
    pd = None

try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
except Exception:
    plt = None
    FigureCanvasTkAgg = None

IMC_TABLE_5 = utils.IMC_TABLE_5 if hasattr(utils, "IMC_TABLE_5") else [
    (0.0, 18.5, "Maigreur"),
    (18.5, 25.0, "Normal"),
    (25.0, 30.0, "Surpoids"),
    (30.0, 40.0, "Obésité modérée"),
    (40.0, 999.0, "Obésité sévère")
]

# ----------------- Helpers date / parsing -----------------
def _date_to_str(d: datetime.date) -> str:
    return d.strftime("%d/%m/%Y")

def _try_parse_date(s: str):
    """Retourne datetime.date ou None. Essaie plusieurs formats courants."""
    if s is None:
        return None
    s = str(s).strip()
    if not s:
        return None
    fmts = ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%m/%d/%Y", "%d/%m/%y", "%m/%d/%y")
    for fmt in fmts:
        try:
            return datetime.datetime.strptime(s, fmt).date()
        except Exception:
            continue
    if pd is not None:
        try:
            dt = pd.to_datetime(s, dayfirst=True, errors='coerce')
            if not pd.isna(dt):
                return dt.date()
        except Exception:
            pass
    try:
        parts = [int(p) for p in s.replace('-', '/').split('/') if p.isdigit()]
        if len(parts) == 3:
            d, m, y = parts
            if y < 100:
                y += 2000 if y < 70 else 1900
            return datetime.date(y, m, d)
    except Exception:
        pass
    return None

def _week_range_for_date(d: datetime.date):
    start = d - datetime.timedelta(days=d.weekday())
    end = start + datetime.timedelta(days=6)
    return start, end

def _month_range_for_date(d: datetime.date):
    first = d.replace(day=1)
    last_day = pycalendar.monthrange(d.year, d.month)[1]
    last = d.replace(day=last_day)
    return first, last

# ----------------- Small helpers for robust column extraction -----------------
def _get_from_row_by_names_or_pos(row_like, columns_list, name_candidates, pos_index):
    """
    row_like: pandas Series or list-like row
    columns_list: list of column names (if pandas) or None
    name_candidates: list of candidate substrings to match column names (lowercase)
    pos_index: integer index to use if no matching name found
    Returns value or empty string.
    """
    # If pandas Series with columns_list
    try:
        if pd is not None and hasattr(row_like, 'index') and columns_list:
            for c in row_like.index:
                low = str(c).lower()
                for cand in name_candidates:
                    if cand in low:
                        val = row_like.get(c, "")
                        try:
                            if pd is not None and pd.isna(val):
                                return ""
                        except Exception:
                            pass
                        return val if val is not None else ""
            # fallback to positional if available
            try:
                if pos_index < len(row_like):
                    val = row_like.iloc[pos_index]
                    try:
                        if pd is not None and pd.isna(val):
                            return ""
                    except Exception:
                        pass
                    return val if val is not None else ""
            except Exception:
                return ""
    except Exception:
        pass

    # If row_like is list-like (from csv.reader)
    try:
        if isinstance(row_like, (list, tuple)):
            if pos_index < len(row_like):
                return row_like[pos_index]
            return ""
    except Exception:
        pass

    # Generic fallback
    try:
        val = row_like.get(pos_index, "")
        return val if val is not None else ""
    except Exception:
        return ""

# ----------------- Dashboard renderer -----------------
def render_dashboard(app):
    for w in app.content.winfo_children():
        w.destroy()

    header = tk.Frame(app.content, bg="#f3f4f6")
    header.pack(fill='x', pady=12, padx=20)
    tk.Label(header, text=f"Élève : {app.selected_user_name}", font=("Inter", 20, "bold"), bg="#f3f4f6", fg="#0f172a").pack(side='left')
    ttk.Button(header, text="Changer d'élève", command=app.show_user_selection_screen).pack(side='right')

    main = tk.Frame(app.content, bg="#f3f4f6")
    main.pack(fill='both', expand=True, padx=20, pady=10)
    main.columnconfigure(0, weight=2)
    main.columnconfigure(1, weight=1)

    # Left card: metrics + gauge
    card = tk.Frame(main, bg="#e0f2fe", bd=0, relief="flat")
    card.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
    card.configure(padx=12, pady=12)
    tk.Label(card, text="📊 Metrics Nutrition & IMC", font=("Inter", 14, "bold"), bg="#e0f2fe").pack(anchor='w')

    # fetch last weight
    poids_val = None
    user_dir = os.path.join(utils.USERS_DIR, app.current_user) if getattr(app, "current_user", None) else None
    fichier_nut = os.path.join(user_dir, "nutrition.csv") if user_dir else None
    if fichier_nut and os.path.exists(fichier_nut) and pd is not None:
        try:
            df = pd.read_csv(fichier_nut, on_bad_lines='skip')
            if not df.empty:
                col_candidates = [c for c in df.columns if 'poids' in c.lower()]
                if col_candidates:
                    col = col_candidates[0]
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                    df_valid = df.dropna(subset=[col])
                    if not df_valid.empty:
                        last_p = df_valid[col].iloc[-1]
                        if last_p not in [0, None]:
                            poids_val = float(last_p)
        except Exception:
            poids_val = None

    if poids_val is None and getattr(app, "user_info", None):
        poids_val = app.user_info.get('poids')

    taille_val = app.user_info.get('taille') if getattr(app, "user_info", None) else None
    age_val = app.user_info.get('age') if getattr(app, "user_info", None) else None
    sexe_val = app.user_info.get('sexe') if getattr(app, "user_info", None) else None
    objectif_val = app.user_info.get('objectif') if getattr(app, "user_info", None) else None
    ajustement_profile = app.user_info.get('ajustement') if getattr(app, "user_info", None) else "Maintien (0%)"

    # compute IMC
    imc_text = "—"
    imc_val = None
    imc_cat = None
    if poids_val and taille_val:
        if hasattr(utils, "calculer_imc"):
            imc_val, imc_cat = utils.calculer_imc(poids_val, taille_val)
        else:
            try:
                taille_m = float(taille_val) / 100.0
                imc_val = float(poids_val) / (taille_m ** 2)
                for low, high, label in IMC_TABLE_5:
                    if imc_val >= low and imc_val < high:
                        imc_cat = (label, low, high)
                        break
            except Exception:
                imc_val, imc_cat = None, None
        if imc_val is not None:
            label = imc_cat[0] if imc_cat else "—"
            imc_text = f"{imc_val:.1f} ({label})"

    # macros
    calories_text = "—"
    proteines_text = "—"
    glucides_text = "—"
    lipides_text = "—"
    if poids_val and age_val and sexe_val and objectif_val and taille_val:
        nut = utils.calculs_nutrition(poids_val, age_val, sexe_val, objectif_val, taille_val) if hasattr(utils, "calculs_nutrition") else None
        if nut:
            adj_label = ajustement_profile if ajustement_profile in utils.ADJUSTMENTS else "Maintien (0%)"
            adj_frac = utils.ADJUSTMENTS.get(adj_label, 0.0)
            adjusted_cal = nut['tdee'] * (1 + adj_frac)
            proteines = nut['proteines']
            if objectif_val == "Gain de masse":
                carb_pct = 0.47; fat_pct = 0.23
            elif objectif_val == "Perte de poids":
                carb_pct = 0.37; fat_pct = 0.23
            else:
                carb_pct = 0.45; fat_pct = 0.25
            glucides = (adjusted_cal * carb_pct) / 4
            lipides = (adjusted_cal * fat_pct) / 9

            calories_text = f"{adjusted_cal:.0f} kcal"
            proteines_text = f"{proteines:.0f} g"
            glucides_text = f"{glucides:.0f} g"
            lipides_text = f"{lipides:.0f} g"

    # layout metrics + gauge
    hg = tk.Frame(card, bg="#e0f2fe")
    hg.pack(fill='both', expand=True, pady=(8,0))

    metrics = tk.Frame(hg, bg="#e0f2fe")
    metrics.pack(side='left', padx=(6,18), pady=6, anchor='n')

    def metric_row(parent, label, value, emoji=""):
        row = tk.Frame(parent, bg="#e0f2fe")
        row.pack(anchor='w', pady=6)
        tk.Label(row, text=emoji, font=("Helvetica", 12), bg="#e0f2fe").pack(side='left', padx=(0,6))
        tk.Label(row, text=label, font=("Helvetica", 11, "bold"), bg="#e0f2fe").pack(side='left')
        tk.Label(row, text=value, font=("Helvetica", 11), bg="#e0f2fe", fg="#0f172a").pack(side='left', padx=8)

    metric_row(metrics, "Poids :", f"{poids_val if poids_val else '—'} kg", "⚖️")
    metric_row(metrics, "IMC :", imc_text, "📏")
    metric_row(metrics, "Protéines :", proteines_text, "🥩")
    metric_row(metrics, "Glucides :", glucides_text, "🍚")
    metric_row(metrics, "Lipides :", lipides_text, "🥑")

    gauge_holder = tk.Frame(hg, bg="#e0f2fe")
    gauge_holder.pack(side='left', fill='both', expand=True, padx=(6,6), pady=6)
    _draw_imc_gauge(gauge_holder, imc_val, poids_val, taille_val, bg_color="#e0f2fe")

    # Right column: cards (entrainement, cycle, shortcuts)
    right = tk.Frame(main, bg="#f3f4f6")
    right.grid(row=0, column=1, sticky="nsew", padx=6, pady=6)
    right.columnconfigure(0, weight=1)

    # Entraînement card
    card_train = tk.Frame(right, bg="#ffffff", bd=0)
    card_train.pack(fill='x', pady=(0,8), padx=6)
    card_train.configure(padx=12, pady=12)
    tk.Label(card_train, text="Entraînement", font=("Inter", 12, "bold"), bg="#ffffff").pack(anchor='w')
    last_train = _get_last_entries(app, "entrainement.csv", 1)
    summary_text = last_train[0] if last_train else "Aucun entraînement enregistré."
    tk.Label(card_train, text=summary_text, bg="#ffffff", wraplength=320).pack(anchor='w', pady=(8,6))
    btns = tk.Frame(card_train, bg="#ffffff")
    btns.pack(anchor='w')
    ttk.Button(btns, text="Ouvrir Entraînement", command=lambda: __import__('data.entrainement_module').entrainement_module.show_entrainement_screen(app)).pack(side='left', padx=6)
    ttk.Button(btns, text="Sarco", command=lambda: __import__('data.entrainement_module').entrainement_module.show_entrainement_screen(app, program="Sarco")).pack(side='left', padx=6)
    ttk.Button(btns, text="Myofi", command=lambda: __import__('data.entrainement_module').entrainement_module.show_entrainement_screen(app, program="Myofi")).pack(side='left', padx=6)

    # Cycle card
    card_cycle = tk.Frame(right, bg="#ffffff", bd=0)
    card_cycle.pack(fill='x', pady=(8,8), padx=6)
    card_cycle.configure(padx=12, pady=12)
    tk.Label(card_cycle, text="Cycle hormonal", font=("Inter", 12, "bold"), bg="#ffffff").pack(anchor='w')
    last_cycle = _get_last_entries(app, "cycle.csv", 1)
    summary_cycle = last_cycle[0] if last_cycle else "Aucun cycle enregistré."
    tk.Label(card_cycle, text=summary_cycle, bg="#ffffff", wraplength=320).pack(anchor='w', pady=(8,6))
    ttk.Button(card_cycle, text="Ouvrir Cycle", command=lambda: __import__('data.cycle_module').cycle_module.show_cycle_disclaimer(app)).pack(anchor='w')

    # Shortcuts
    card_short = tk.Frame(right, bg="#ffffff", bd=0)
    card_short.pack(fill='x', pady=(8,0), padx=6)
    card_short.configure(padx=12, pady=12)
    tk.Label(card_short, text="Raccourcis", font=("Inter", 12, "bold"), bg="#ffffff").pack(anchor='w')
    btns2 = tk.Frame(card_short, bg="#ffffff")
    btns2.pack(anchor='w', pady=8)
    ttk.Button(btns2, text="Nutrition", command=lambda: show_nutrition_screen(app)).pack(side='left', padx=6)
    ttk.Button(btns2, text="Exporter CSV", command=lambda: messagebox.showinfo("Export", "Export CSV (placeholder)")).pack(side='left', padx=6)


# ----------------- Helpers -----------------
def _get_last_entries(app, filename, n=1):
    if not getattr(app, "current_user", None):
        return []
    path = os.path.join(utils.USERS_DIR, app.current_user, filename)
    if not os.path.exists(path):
        return []
    try:
        if pd is not None:
            df = pd.read_csv(path, on_bad_lines='skip')
            if df.empty:
                return []
            rows = []
            for i in range(min(n, len(df))):
                r = df.iloc[-1 - i].tolist()
                rows.append(" | ".join([str(x) for x in r if str(x) != "nan"]))
            return rows
        else:
            with open(path, 'r', newline='', encoding='utf-8') as f:
                reader = list(csv.reader(f))
                if len(reader) <= 1:
                    return []
                rows = []
                for i in range(1, min(n, len(reader)-1)+1):
                    r = reader[-i]
                    rows.append(" | ".join([str(x) for x in r if x != ""]))
                return rows
    except Exception:
        return []

def _draw_imc_gauge(parent_frame, imc_value, poids_actuel, taille_cm, bg_color="#e0f2fe"):
    for w in parent_frame.winfo_children():
        w.destroy()

    if plt is None or FigureCanvasTkAgg is None:
        tk.Label(parent_frame, text="Jauge IMC non disponible (matplotlib manquant)", bg=bg_color).pack()
        return

    try:
        fig = plt.Figure(figsize=(4.2, 2.4), dpi=120, facecolor=bg_color)
        ax = fig.add_subplot(111, polar=True)
        fig.patch.set_facecolor(bg_color)
        ax.set_facecolor(bg_color)
        ax.set_theta_offset(math.pi)
        ax.set_theta_direction(-1)
        ax.set_ylim(0, 10)
        ax.set_yticks([])
        ax.set_xticks([])

        segments = [
            (10, 18.5, '#3b82f6'),
            (18.5, 25.0, '#10b981'),
            (25.0, 30.0, '#facc15'),
            (30.0, 40.0, '#fb923c'),
            (40.0, 60.0, '#ef4444')
        ]

        def imc_to_angle(imc):
            min_imc = 10.0
            max_imc = 60.0
            v = imc if imc is not None else min_imc
            v = max(min_imc, min(max_imc, v))
            return math.radians(180 * ((v - min_imc) / (max_imc - min_imc)))

        for low, high, color in segments:
            a1 = imc_to_angle(low)
            a2 = imc_to_angle(high)
            n = 120
            thetas = [a1 + (a2 - a1) * i / n for i in range(n)]
            widths = (a2 - a1) / n
            ax.bar(thetas, [6.6] * n, width=widths, bottom=1.8, color=color, edgecolor=color, align='edge')

        ticks = list(range(10, 61))
        for t in ticks:
            ang = imc_to_angle(t)
            ax.plot([ang, ang], [7.2, 7.6], color='#0f172a', linewidth=0.5)
            if t % 5 == 0:
                ax.text(ang, 8.2, str(t), horizontalalignment='center', verticalalignment='center', fontsize=8, fontweight='bold', color='#0f172a')

        if imc_value is not None:
            ang = imc_to_angle(imc_value)
            ax.plot([ang, ang], [1.8, 7.0], color='#0f172a', linewidth=3, zorder=10)
            ax.scatter([ang], [7.1], s=80, color='#0f172a', zorder=11)
            cat_label = "—"
            for low, high, cat in IMC_TABLE_5:
                if imc_value >= low and imc_value < high:
                    cat_label = cat
                    break
            ax.text(math.radians(90), 0.6, cat_label, horizontalalignment='center', fontsize=12, fontweight='bold', color='#071133')
            ax.text(math.radians(90), -0.1, f"IMC {imc_value:.1f}", horizontalalignment='center', fontsize=16, fontweight='bold', color='#071133')
            if poids_actuel and taille_cm:
                try:
                    taille_m = float(taille_cm) / 100.0
                    normal_min = 18.5 * (taille_m ** 2)
                    normal_max = 25.0 * (taille_m ** 2)
                    if poids_actuel < normal_min:
                        diff = normal_min - float(poids_actuel)
                        diff_text = f"+{diff:.1f} kg → IMC 18.5"
                    elif poids_actuel > normal_max:
                        diff = float(poids_actuel) - normal_max
                        diff_text = f"-{diff:.1f} kg → IMC 25.0"
                    else:
                        diff_text = "Dans la zone normale"
                    ax.text(math.radians(90), -0.9, diff_text, horizontalalignment='center', fontsize=9, color='#0f172a')
                except Exception:
                    pass

        ax.set_axis_off()
        canvas = FigureCanvasTkAgg(fig, master=parent_frame)
        canvas.draw()
        widget = canvas.get_tk_widget()
        widget.configure(bg=bg_color)
        widget.pack(fill='both', expand=True)
    except Exception:
        for w in parent_frame.winfo_children():
            w.destroy()
        tk.Label(parent_frame, text="Erreur affichage jauge IMC", bg=bg_color).pack()

# ----------------- Écran Nutrition (détail) avec multi-sélection -----------------
def show_nutrition_screen(app):
    for w in app.content.winfo_children():
        w.destroy()
    tk.Label(app.content, text=f"NUTRITION - Élève : {app.selected_user_name}", font=("Helvetica", 20, "bold"), bg="#f3f4f6", fg="#0f172a").pack(pady=12)

    # top: calendar + selection mode controls
    top_frame = tk.Frame(app.content, bg="#f3f4f6")
    top_frame.pack(fill='x', padx=20)

    cal_frame = tk.Frame(top_frame, bg="#f3f4f6")
    cal_frame.pack(side='left', padx=8, pady=6)

    # Calendar: single-day selection (we handle multi-selection ourselves)
    app.calendar = Calendar(cal_frame, selectmode='day')
    app.calendar.pack()

    # selection state stored on app (store datetime.date objects)
    if not hasattr(app, "selected_dates"):
        app.selected_dates = set()
    if not hasattr(app, "selection_mode"):
        app.selection_mode = "Single"  # Single / Week / Month / Multiple

    # controls for selection mode
    ctrl_frame = tk.Frame(top_frame, bg="#f3f4f6")
    ctrl_frame.pack(side='left', padx=12, pady=6, anchor='n')

    tk.Label(ctrl_frame, text="Mode sélection :", bg="#f3f4f6").pack(anchor='w')
    modes = ["Single", "Week", "Month", "Multiple"]
    app.selection_mode_var = tk.StringVar(value=app.selection_mode)
    for m in modes:
        rb = ttk.Radiobutton(ctrl_frame, text=m, value=m, variable=app.selection_mode_var, command=lambda: _on_mode_change(app))
        rb.pack(anchor='w', pady=2)

    # quick action buttons
    btns = tk.Frame(ctrl_frame, bg="#f3f4f6")
    btns.pack(pady=6, anchor='w')
    ttk.Button(btns, text="Sélectionner la semaine", command=lambda: _select_week_from_calendar(app)).pack(side='left', padx=4)
    ttk.Button(btns, text="Sélectionner le mois", command=lambda: _select_month_from_calendar(app)).pack(side='left', padx=4)
    ttk.Button(btns, text="Effacer sélection", command=lambda: _clear_selection(app)).pack(side='left', padx=4)

    # summary of selected dates
    app.selected_summary_label = tk.Label(ctrl_frame, text="Aucune date sélectionnée", bg="#f3f4f6", justify='left', wraplength=260)
    app.selected_summary_label.pack(pady=(8,0), anchor='w')

    # bind calendar selection event
    app.calendar.bind("<<CalendarSelected>>", lambda ev: _on_calendar_select(app))

    # rest of nutrition form (below)
    calc_frame = tk.Frame(app.content, bg="#ffffff", bd=0, relief="flat")
    calc_frame.pack(padx=20, pady=10, fill='x')
    calc_frame.configure(padx=12, pady=12)

    # dernier poids
    dernier_poids = ""
    user_dir = os.path.join(utils.USERS_DIR, app.current_user) if getattr(app, "current_user", None) else None
    fichier_nut = os.path.join(user_dir, "nutrition.csv") if user_dir else None
    if fichier_nut and os.path.exists(fichier_nut) and pd is not None:
        try:
            df = pd.read_csv(fichier_nut, on_bad_lines='skip')
            if not df.empty:
                col_candidates = [c for c in df.columns if 'poids' in c.lower()]
                if col_candidates:
                    col = col_candidates[0]
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                    df_valid = df.dropna(subset=[col])
                    if not df_valid.empty:
                        last_p = df_valid[col].iloc[-1]
                        if last_p not in [0, None]:
                            dernier_poids = str(int(last_p)) if float(last_p).is_integer() else str(float(last_p))
        except Exception:
            pass
    if not dernier_poids and getattr(app, "user_info", None) and app.user_info.get('poids') is not None:
        dernier_poids = str(int(app.user_info['poids'])) if float(app.user_info['poids']).is_integer() else str(app.user_info['poids'])

    # ensure app has variables used across screens
    if not hasattr(app, "poids_var"):
        app.poids_var = tk.StringVar()
    if not hasattr(app, "age_var"):
        app.age_var = tk.StringVar()
    if not hasattr(app, "adjustment_var"):
        app.adjustment_var = tk.StringVar()

    app.poids_var.set(dernier_poids)
    app.age_var.set(str(app.user_info.get('age','') or ''))

    left = tk.Frame(calc_frame, bg="#ffffff"); left.pack(side='left', padx=8, pady=4, fill='x', expand=True)
    tk.Label(left, text="Poids (kg) :", bg="#ffffff").grid(row=0, column=0, sticky='w', padx=6, pady=4)
    ttk.Entry(left, textvariable=app.poids_var, width=12).grid(row=0, column=1, padx=6)
    tk.Label(left, text="Age :", bg="#ffffff").grid(row=1, column=0, sticky='w', padx=6, pady=4)
    ttk.Entry(left, textvariable=app.age_var, width=12).grid(row=1, column=1, padx=6)

    mid = tk.Frame(calc_frame, bg="#ffffff"); mid.pack(side='left', padx=8, pady=4, fill='x', expand=True)
    default_adj = app.user_info.get('ajustement') if getattr(app, "user_info", None) else "Maintien (0%)"
    if default_adj not in utils.ADJUSTMENTS:
        default_adj = "Maintien (0%)"
    app.adjustment_var.set(default_adj)
    adj_combo = ttk.Combobox(mid, values=list(utils.ADJUSTMENTS.keys()), textvariable=app.adjustment_var, state="readonly", width=36)
    adj_combo.grid(row=0, column=1, padx=6, pady=4)

    right = tk.Frame(calc_frame, bg="#ffffff"); right.pack(side='right', padx=8, pady=4, fill='x', expand=True)
    app.calories_label = tk.Label(right, text="🔥 Calories : -", bg="#ffffff", justify='left')
    app.calories_label.pack(anchor='w', pady=2)
    app.proteines_label = tk.Label(right, text="🥩 Protéines : -", bg="#ffffff", justify='left')
    app.proteines_label.pack(anchor='w', pady=2)
    app.glucides_label = tk.Label(right, text="🍚 Glucides : -", bg="#ffffff", justify='left')
    app.glucides_label.pack(anchor='w', pady=2)
    app.lipides_label = tk.Label(right, text="🥑 Lipides : -", bg="#ffffff", justify='left')
    app.lipides_label.pack(anchor='w', pady=2)

    # traces pour mise à jour en temps réel
    try:
        app.poids_var.trace_add('write', lambda *a: _update_calc(app))
        app.age_var.trace_add('write', lambda *a: _update_calc(app))
        app.adjustment_var.trace_add('write', lambda *a: _update_calc(app))
    except Exception:
        try:
            app.poids_var.trace('w', lambda *a: _update_calc(app))
            app.age_var.trace('w', lambda *a: _update_calc(app))
            app.adjustment_var.trace('w', lambda *a: _update_calc(app))
        except Exception:
            pass

    app.nutrition_note_text = tk.Text(app.content, height=6, width=100)
    app.nutrition_note_text.pack(padx=20, pady=8)
    btn_frame = tk.Frame(app.content); btn_frame.pack(pady=6)
    ttk.Button(btn_frame, text="SAUVEGARDER NUTRITION (sur sélection)", command=lambda: _save_nutrition(app)).pack(side='left', padx=6)
    ttk.Button(btn_frame, text="Retour Dashboard", command=lambda: render_dashboard(app)).pack(side='left', padx=6)

    # historique
    hist_frame = tk.Frame(app.content); hist_frame.pack(padx=20, pady=8, fill='both', expand=True)
    tk.Label(hist_frame, text="Historique nutrition (filtré par sélection si applicable)", font=("Helvetica", 12, "bold")).pack(anchor='w')

    # store tree on app so we can refresh it
    app.nutrition_tree = ttk.Treeview(hist_frame, columns=("Date","Poids","Calories","Note"), show="headings", selectmode='browse')
    app.nutrition_tree.heading("Date", text="Date"); app.nutrition_tree.heading("Poids", text="Poids (kg)"); app.nutrition_tree.heading("Calories", text="Calories"); app.nutrition_tree.heading("Note", text="Note")
    app.nutrition_tree.column("Date", width=120, anchor='center')
    app.nutrition_tree.column("Poids", width=80, anchor='center')
    app.nutrition_tree.column("Calories", width=100, anchor='center')
    app.nutrition_tree.column("Note", width=400, anchor='w')
    app.nutrition_tree.pack(fill='both', expand=True)

    # bind double click to edit
    app.nutrition_tree.bind("<Double-1>", lambda ev: _edit_selected(app))
    # add edit/delete buttons
    action_frame = tk.Frame(hist_frame)
    action_frame.pack(anchor='w', pady=(6,0))
    ttk.Button(action_frame, text="Modifier sélection", command=lambda: _edit_selected(app)).pack(side='left', padx=6)
    ttk.Button(action_frame, text="Supprimer sélection", command=lambda: _delete_selected(app)).pack(side='left', padx=6)

    # initial fill of history (filtered if selection exists)
    _refresh_history(app, fichier_nut)

    _update_calc(app)
    _render_selected_summary(app)

# ----------------- Selection handlers -----------------
def _on_mode_change(app):
    app.selection_mode = app.selection_mode_var.get()
    if app.selection_mode == "Single":
        app.selected_dates = set()
        _render_selected_summary(app)
        user_dir = os.path.join(utils.USERS_DIR, app.current_user) if getattr(app, "current_user", None) else None
        fichier_nut = os.path.join(user_dir, "nutrition.csv") if user_dir else None
        _refresh_history(app, fichier_nut)

def _on_calendar_select(app):
    try:
        d = app.calendar.selection_get()
        if not isinstance(d, datetime.date):
            d = _try_parse_date(app.calendar.get_date())
            if d is None:
                return
    except Exception:
        d = _try_parse_date(app.calendar.get_date())
        if d is None:
            return

    mode = getattr(app, "selection_mode", "Single")
    if mode == "Single":
        app.selected_dates = {d}
    elif mode == "Week":
        start, end = _week_range_for_date(d)
        app.selected_dates = set(start + datetime.timedelta(days=i) for i in range(7))
    elif mode == "Month":
        first, last = _month_range_for_date(d)
        delta = (last - first).days + 1
        app.selected_dates = set(first + datetime.timedelta(days=i) for i in range(delta))
    elif mode == "Multiple":
        if not hasattr(app, "selected_dates"):
            app.selected_dates = set()
        if d in app.selected_dates:
            app.selected_dates.remove(d)
        else:
            app.selected_dates.add(d)
    _render_selected_summary(app)
    user_dir = os.path.join(utils.USERS_DIR, app.current_user) if getattr(app, "current_user", None) else None
    fichier_nut = os.path.join(user_dir, "nutrition.csv") if user_dir else None
    _refresh_history(app, fichier_nut)

def _select_week_from_calendar(app):
    try:
        d = app.calendar.selection_get()
    except Exception:
        d = _try_parse_date(app.calendar.get_date())
    if d is None:
        return
    start, end = _week_range_for_date(d)
    app.selected_dates = set(start + datetime.timedelta(days=i) for i in range(7))
    app.selection_mode_var.set("Week")
    app.selection_mode = "Week"
    _render_selected_summary(app)
    user_dir = os.path.join(utils.USERS_DIR, app.current_user) if getattr(app, "current_user", None) else None
    fichier_nut = os.path.join(user_dir, "nutrition.csv") if user_dir else None
    _refresh_history(app, fichier_nut)

def _select_month_from_calendar(app):
    try:
        d = app.calendar.selection_get()
    except Exception:
        d = _try_parse_date(app.calendar.get_date())
    if d is None:
        return
    first, last = _month_range_for_date(d)
    delta = (last - first).days + 1
    app.selected_dates = set(first + datetime.timedelta(days=i) for i in range(delta))
    app.selection_mode_var.set("Month")
    app.selection_mode = "Month"
    _render_selected_summary(app)
    user_dir = os.path.join(utils.USERS_DIR, app.current_user) if getattr(app, "current_user", None) else None
    fichier_nut = os.path.join(user_dir, "nutrition.csv") if user_dir else None
    _refresh_history(app, fichier_nut)

def _clear_selection(app):
    app.selected_dates = set()
    _render_selected_summary(app)
    user_dir = os.path.join(utils.USERS_DIR, app.current_user) if getattr(app, "current_user", None) else None
    fichier_nut = os.path.join(user_dir, "nutrition.csv") if user_dir else None
    _refresh_history(app, fichier_nut)

def _render_selected_summary(app):
    sel = getattr(app, "selected_dates", set())
    if not sel:
        app.selected_summary_label.config(text="Aucune date sélectionnée")
        return
    sorted_dates = sorted(sel)
    preview = ", ".join(d.strftime("%d/%m") for d in sorted_dates[:10])
    more = f" (+{len(sorted_dates)-10} autres)" if len(sorted_dates) > 10 else ""
    app.selected_summary_label.config(text=f"{len(sorted_dates)} date(s) sélectionnée(s) : {preview}{more}")

# ----------------- History refresh (filter by selection) -----------------
def _refresh_history(app, fichier_nut):
    """
    Remplit app.nutrition_tree avec :
      - si app.selected_dates non vide : toutes les lignes dont la date est dans la sélection (triées)
      - sinon : les dernières 30 entrées (triées par date)
    IMPORTANT: chaque item Treeview reçoit un iid égal à l'index de la ligne dans le fichier
    (pour permettre édition/suppression fiables).
    """
    tree = getattr(app, "nutrition_tree", None)
    if tree is None:
        return
    # clear tree
    for i in tree.get_children():
        tree.delete(i)

    if not fichier_nut or not os.path.exists(fichier_nut):
        return

    try:
        rows = []  # list of tuples (file_index, date_obj, date_str, poids, calories, note)
        if pd is not None:
            df = pd.read_csv(fichier_nut, on_bad_lines='skip')
            if df.empty:
                return
            # find date column
            date_col = None
            for c in df.columns:
                if c.lower().strip() == 'date' or 'date' in c.lower():
                    date_col = c
                    break
            if date_col is None:
                date_col = df.columns[0]
            # parse dates robustly
            df['__parsed'] = pd.to_datetime(df[date_col], dayfirst=True, errors='coerce')
            df = df.dropna(subset=['__parsed'])
            df['__date'] = df['__parsed'].dt.date
            df = df.sort_values('__date').reset_index(drop=False)  # keep original index in 'index' column
            cols = list(df.columns)
            for _, r in df.iterrows():
                file_index = int(r['index'])  # original pandas index -> use as file_index
                date_obj = r['__date']
                date_str = date_obj.strftime("%d/%m/%Y")
                poids = _get_from_row_by_names_or_pos(r, cols, ['poids', 'poids (kg)'], 1)
                calories = _get_from_row_by_names_or_pos(r, cols, ['calories'], 3)
                note = _get_from_row_by_names_or_pos(r, cols, ['note'], 7)
                rows.append((file_index, date_obj, date_str, poids, calories, note))
        else:
            with open(fichier_nut, 'r', newline='', encoding='utf-8') as f:
                reader = list(csv.reader(f))
                if len(reader) <= 1:
                    return
                header = reader[0]
                for idx, r in enumerate(reader[1:], start=1):
                    date_raw = r[0] if len(r) > 0 else ""
                    date_obj = _try_parse_date(date_raw)
                    if date_obj is None:
                        continue
                    date_str = date_obj.strftime("%d/%m/%Y")
                    poids = r[1] if len(r) > 1 else ""
                    calories = r[3] if len(r) > 3 else ""
                    note = r[7] if len(r) > 7 else ""
                    rows.append((idx, date_obj, date_str, poids, calories, note))

        if not rows:
            return

        sel = getattr(app, "selected_dates", set())
        if sel:
            sel_set = set(sel)
            filtered = [r for r in rows if r[1] in sel_set]
            filtered_sorted = sorted(filtered, key=lambda x: x[1])
            for r in filtered_sorted:
                iid = str(r[0])
                tree.insert("", "end", iid=iid, values=(r[2], r[3], r[4], r[5]))
        else:
            # show last 30 entries sorted by date
            rows_sorted = sorted(rows, key=lambda x: x[1])
            last = rows_sorted[-30:]
            for r in last:
                iid = str(r[0])
                tree.insert("", "end", iid=iid, values=(r[2], r[3], r[4], r[5]))
    except Exception:
        # fallback simple read (last 30 lines)
        try:
            with open(fichier_nut, 'r', newline='', encoding='utf-8') as f:
                reader = list(csv.reader(f))
                if len(reader) <= 1:
                    return
                for idx, r in enumerate(reader[-30:], start=max(1, len(reader)-29)):
                    date = r[0] if len(r) > 0 else ""
                    poids = r[1] if len(r) > 1 else ""
                    calories = r[3] if len(r) > 3 else ""
                    note = r[7] if len(r) > 7 else ""
                    iid = str(idx)
                    tree.insert("", "end", iid=iid, values=(date, poids, calories, note))
        except Exception:
            return

# ----------------- Edit / Delete handlers -----------------
def _get_selected_item_iid(app):
    tree = getattr(app, "nutrition_tree", None)
    if tree is None:
        return None
    sel = tree.selection()
    if not sel:
        return None
    return sel[0]

def _edit_selected(app):
    iid = _get_selected_item_iid(app)
    if not iid:
        messagebox.showinfo("Modifier", "Sélectionne d'abord une ligne à modifier.")
        return
    # read current values from tree
    tree = app.nutrition_tree
    vals = tree.item(iid, 'values')
    # vals = (date_str, poids, calories, note)
    date_str, poids, calories, note = (vals[0], vals[1], vals[2], vals[3])
    # open edit dialog
    _open_edit_dialog(app, iid, date_str, poids, calories, note)

def _open_edit_dialog(app, iid, date_str, poids, calories, note):
    dlg = tk.Toplevel()
    dlg.title("Modifier entrée nutrition")
    dlg.transient(app.root if hasattr(app, "root") else app.content)
    dlg.grab_set()
    tk.Label(dlg, text="Date (jj/mm/aaaa) :").grid(row=0, column=0, sticky='e', padx=8, pady=6)
    date_var = tk.StringVar(value=date_str)
    tk.Entry(dlg, textvariable=date_var, width=16).grid(row=0, column=1, padx=8, pady=6)

    tk.Label(dlg, text="Poids (kg) :").grid(row=1, column=0, sticky='e', padx=8, pady=6)
    poids_var = tk.StringVar(value=str(poids))
    tk.Entry(dlg, textvariable=poids_var, width=12).grid(row=1, column=1, padx=8, pady=6)

    tk.Label(dlg, text="Calories :").grid(row=2, column=0, sticky='e', padx=8, pady=6)
    cal_var = tk.StringVar(value=str(calories))
    tk.Entry(dlg, textvariable=cal_var, width=12).grid(row=2, column=1, padx=8, pady=6)

    tk.Label(dlg, text="Note :").grid(row=3, column=0, sticky='ne', padx=8, pady=6)
    note_text = tk.Text(dlg, height=6, width=40)
    note_text.grid(row=3, column=1, padx=8, pady=6)
    note_text.insert("1.0", str(note))

    btn_frame = tk.Frame(dlg)
    btn_frame.grid(row=4, column=0, columnspan=2, pady=8)
    ttk.Button(btn_frame, text="Enregistrer", command=lambda: _save_edit(app, dlg, iid, date_var.get().strip(), poids_var.get().strip(), cal_var.get().strip(), note_text.get("1.0", tk.END).strip())).pack(side='left', padx=6)
    ttk.Button(btn_frame, text="Annuler", command=lambda: dlg.destroy()).pack(side='left', padx=6)

def _save_edit(app, dlg, iid, date_str, poids, calories, note):
    # validate date
    d = _try_parse_date(date_str)
    if d is None:
        messagebox.showerror("Erreur", "Date invalide. Utilise jj/mm/aaaa.")
        return
    # update file (pandas or manual)
    user_dir = os.path.join(utils.USERS_DIR, app.current_user)
    fichier = os.path.join(user_dir, "nutrition.csv")
    if not os.path.exists(fichier):
        messagebox.showerror("Erreur", "Fichier nutrition introuvable.")
        dlg.destroy()
        return
    try:
        if pd is not None:
            # read df, update row with index == int(iid)
            df = pd.read_csv(fichier, on_bad_lines='skip')
            # ensure index exists
            try:
                idx = int(iid)
            except Exception:
                messagebox.showerror("Erreur", "Impossible d'identifier la ligne dans le fichier.")
                return
            if idx not in df.index:
                # if index not present, try to match by date and first occurrence
                parsed = pd.to_datetime(df.iloc[:,0], dayfirst=True, errors='coerce').dt.date
                matches = parsed[parsed == d]
                if not matches.empty:
                    idx = matches.index[0]
                else:
                    messagebox.showerror("Erreur", "Ligne introuvable dans le fichier.")
                    return
            # update columns carefully: try to find columns by name
            cols = list(df.columns)
            # Date column -> set to formatted string
            date_col = cols[0]
            df.at[idx, date_col] = d.strftime("%d/%m/%Y")
            # poids
            for c in cols:
                if 'poids' in str(c).lower():
                    df.at[idx, c] = poids
                    break
            # calories
            for c in cols:
                if 'calor' in str(c).lower():
                    df.at[idx, c] = calories
                    break
            # note
            for c in cols:
                if 'note' in str(c).lower():
                    df.at[idx, c] = note
                    break
            # write back
            df.to_csv(fichier, index=False)
        else:
            # manual CSV: header + data rows
            with open(fichier, 'r', newline='', encoding='utf-8') as f:
                reader = list(csv.reader(f))
            if len(reader) <= 1:
                messagebox.showerror("Erreur", "Fichier vide ou sans données.")
                return
            header = reader[0]
            data = reader[1:]
            try:
                idx = int(iid) - 1  # our iid for manual CSV used 1-based index
            except Exception:
                messagebox.showerror("Erreur", "Impossible d'identifier la ligne dans le fichier.")
                return
            if idx < 0 or idx >= len(data):
                # try to find by date
                found = False
                for j, row in enumerate(data):
                    dt = _try_parse_date(row[0] if len(row) > 0 else "")
                    if dt == d:
                        idx = j
                        found = True
                        break
                if not found:
                    messagebox.showerror("Erreur", "Ligne introuvable dans le fichier.")
                    return
            # ensure row has at least 8 columns
            row = data[idx]
            while len(row) < 8:
                row.append("")
            row[0] = d.strftime("%d/%m/%Y")
            row[1] = poids
            row[3] = calories
            row[7] = note
            data[idx] = row
            # write back
            with open(fichier, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(header)
                for r in data:
                    writer.writerow(r)
        # refresh UI
        dlg.destroy()
        _refresh_history(app, fichier)
        messagebox.showinfo("Succès", "Entrée modifiée.")
    except Exception as e:
        messagebox.showerror("Erreur", f"Impossible d'enregistrer la modification : {e}")

def _delete_selected(app):
    iid = _get_selected_item_iid(app)
    if not iid:
        messagebox.showinfo("Supprimer", "Sélectionne d'abord une ligne à supprimer.")
        return
    if not messagebox.askyesno("Confirmer suppression", "Supprimer la ligne sélectionnée ?"):
        return
    user_dir = os.path.join(utils.USERS_DIR, app.current_user)
    fichier = os.path.join(user_dir, "nutrition.csv")
    if not os.path.exists(fichier):
        messagebox.showerror("Erreur", "Fichier nutrition introuvable.")
        return
    try:
        if pd is not None:
            df = pd.read_csv(fichier, on_bad_lines='skip')
            try:
                idx = int(iid)
            except Exception:
                # try to match by date in tree
                vals = app.nutrition_tree.item(iid, 'values')
                date_str = vals[0]
                d = _try_parse_date(date_str)
                parsed = pd.to_datetime(df.iloc[:,0], dayfirst=True, errors='coerce').dt.date
                matches = parsed[parsed == d]
                if matches.empty:
                    messagebox.showerror("Erreur", "Impossible d'identifier la ligne à supprimer.")
                    return
                idx = matches.index[0]
            if idx not in df.index:
                messagebox.showerror("Erreur", "Ligne introuvable dans le fichier.")
                return
            df = df.drop(index=idx).reset_index(drop=True)
            df.to_csv(fichier, index=False)
        else:
            with open(fichier, 'r', newline='', encoding='utf-8') as f:
                reader = list(csv.reader(f))
            if len(reader) <= 1:
                messagebox.showerror("Erreur", "Fichier vide ou sans données.")
                return
            header = reader[0]
            data = reader[1:]
            try:
                idx = int(iid) - 1
            except Exception:
                vals = app.nutrition_tree.item(iid, 'values')
                date_str = vals[0]
                d = _try_parse_date(date_str)
                found = False
                for j, row in enumerate(data):
                    dt = _try_parse_date(row[0] if len(row) > 0 else "")
                    if dt == d:
                        idx = j
                        found = True
                        break
                if not found:
                    messagebox.showerror("Erreur", "Impossible d'identifier la ligne à supprimer.")
                    return
            if idx < 0 or idx >= len(data):
                messagebox.showerror("Erreur", "Ligne introuvable dans le fichier.")
                return
            data.pop(idx)
            with open(fichier, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(header)
                for r in data:
                    writer.writerow(r)
        _refresh_history(app, fichier)
        messagebox.showinfo("Succès", "Ligne supprimée.")
    except Exception as e:
        messagebox.showerror("Erreur", f"Impossible de supprimer la ligne : {e}")

# ----------------- Calculs / sauvegarde -----------------
def _update_calc(app):
    try:
        poids = app.poids_var.get().strip()
        age = app.age_var.get().strip()
        if not poids or not age:
            return
        if not getattr(app, "user_info", None):
            return
        sexe = app.user_info.get('sexe')
        taille = app.user_info.get('taille')
        objectif = app.user_info.get('objectif')
        if not all([sexe, taille, objectif]):
            return
        nut = utils.calculs_nutrition(poids, age, sexe, objectif, taille) if hasattr(utils, "calculs_nutrition") else None
        if not nut:
            return
        adj_label = app.adjustment_var.get() or "Maintien (0%)"
        adj_frac = utils.ADJUSTMENTS.get(adj_label, 0.0)
        adjusted_cal = nut['tdee'] * (1 + adj_frac)
        proteines = nut['proteines']
        if objectif == "Gain de masse":
            carb_pct = 0.47; fat_pct = 0.23
        elif objectif == "Perte de poids":
            carb_pct = 0.37; fat_pct = 0.23
        else:
            carb_pct = 0.45; fat_pct = 0.25
        glucides = (adjusted_cal * carb_pct) / 4
        lipides = (adjusted_cal * fat_pct) / 9

        if getattr(app, "calories_label", None):
            app.calories_label.config(text=f"🔥 Calories : {adjusted_cal:.0f} kcal\n(TDEE: {nut['tdee']:.0f} | Ajust: {adj_frac*100:+.1f}%)")
        if getattr(app, "proteines_label", None):
            pct_p = (proteines*4/adjusted_cal*100) if adjusted_cal>0 else 0
            app.proteines_label.config(text=f"🥩 Protéines : {proteines:.0f} g ({pct_p:.0f}%)")
        if getattr(app, "glucides_label", None):
            pct_c = (glucides*4/adjusted_cal*100) if adjusted_cal>0 else 0
            app.glucides_label.config(text=f"🍚 Glucides : {glucides:.0f} g ({pct_c:.0f}%)")
        if getattr(app, "lipides_label", None):
            pct_f = (lipides*9/adjusted_cal*100) if adjusted_cal>0 else 0
            app.lipides_label.config(text=f"🥑 Lipides : {lipides:.0f} g ({pct_f:.0f}%)")

        app._last_computed_calories = int(round(adjusted_cal))
    except Exception:
        app._last_computed_calories = None

def _save_nutrition(app):
    """
    Sauvegarde l'entrée nutrition pour toutes les dates sélectionnées.
    Si aucune date sélectionnée, sauvegarde pour la date active du calendrier.
    """
    if not getattr(app, "current_user", None):
        messagebox.showerror("Erreur", "Sélectionne un élève d'abord")
        return

    # determine dates to save (we store datetime.date objects)
    sel = getattr(app, "selected_dates", set())
    if not sel:
        # fallback to calendar date
        try:
            d = app.calendar.selection_get()
            if not isinstance(d, datetime.date):
                d = _try_parse_date(app.calendar.get_date())
        except Exception:
            d = _try_parse_date(app.calendar.get_date())
        if d is None:
            d = datetime.date.today()
        sel = {d}

    # normalize selection to date objects
    sel_dates = set()
    for s in sel:
        if isinstance(s, datetime.date):
            sel_dates.add(s)
        else:
            d = _try_parse_date(str(s))
            if d:
                sel_dates.add(d)
    if not sel_dates:
        messagebox.showerror("Erreur", "Aucune date valide à sauvegarder.")
        return

    poids = app.poids_var.get().strip()
    age = app.age_var.get().strip()
    calories = str(app._last_computed_calories) if hasattr(app, '_last_computed_calories') and app._last_computed_calories else ""
    note = app.nutrition_note_text.get("1.0", tk.END).strip() if getattr(app, "nutrition_note_text", None) else ""
    user_dir = os.path.join(utils.USERS_DIR, app.current_user)
    os.makedirs(user_dir, exist_ok=True)
    fichier = os.path.join(user_dir, "nutrition.csv")

    try:
        # ensure header exists
        if not os.path.exists(fichier):
            with open(fichier, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Date", "Poids (kg)", "Age", "Calories", "Protéines (g)", "Glucides (g)", "Lipides (g)", "Note"])

        # append one row per date (date in dd/mm/YYYY)
        with open(fichier, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            for date_obj in sorted(sel_dates):
                date_str = _date_to_str(date_obj)
                writer.writerow([date_str, poids, age, calories, "", "", "", note])
        messagebox.showinfo("Succès", f"Entrée sauvegardée pour {len(sel_dates)} date(s).")
        # refresh history and UI
        _render_selected_summary(app)
        _refresh_history(app, fichier)
    except Exception as e:
        messagebox.showerror("Erreur", str(e))

