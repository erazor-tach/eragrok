# data/weight_chart.py
# -*- coding: utf-8 -*-
"""
Graphique d'évolution du poids (et calories optionnelles).
Fenêtre indépendante ou intégrable dans un Frame Tkinter.
Dépend de matplotlib + pandas (dégradation gracieuse si absent).
"""

import os
import csv
import datetime
import tkinter as tk
from tkinter import ttk, messagebox

from data import utils

try:
    import pandas as pd
    _PANDAS = True
except Exception:
    pd = None
    _PANDAS = False

try:
    import matplotlib
    matplotlib.use("TkAgg")
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
    _MPL = True
except Exception:
    plt = None
    _MPL = False


# ── Lecture des données poids ─────────────────────────────────────────────────

def _load_weight_data(app) -> list[tuple[datetime.date, float]]:
    """
    Lit nutrition.csv et retourne [(date, poids), ...] trié par date.
    Compatible pandas et lecture manuelle.
    """
    user_dir = utils.get_user_dir(app)
    if not user_dir:
        return []
    fichier = os.path.join(user_dir, "nutrition.csv")
    if not os.path.exists(fichier):
        return []

    points = []

    if _PANDAS:
        try:
            df = pd.read_csv(fichier, on_bad_lines='skip')
            if df.empty:
                return []
            # colonne date
            date_col  = next((c for c in df.columns if 'date' in c.lower()), df.columns[0])
            poids_col = next((c for c in df.columns if 'poids' in c.lower()), None)
            if poids_col is None:
                return []
            df['_date']  = pd.to_datetime(df[date_col],  dayfirst=True, errors='coerce')
            df['_poids'] = pd.to_numeric(df[poids_col], errors='coerce')
            df = df.dropna(subset=['_date', '_poids'])
            df = df[df['_poids'] > 0]
            for _, row in df.iterrows():
                points.append((row['_date'].date(), float(row['_poids'])))
        except Exception:
            pass
    else:
        try:
            with open(fichier, 'r', newline='', encoding='utf-8') as f:
                reader = list(csv.reader(f))
            if len(reader) < 2:
                return []
            header = reader[0]
            poids_idx = next((i for i, h in enumerate(header) if 'poids' in h.lower()), 1)
            for row in reader[1:]:
                if not row:
                    continue
                try:
                    date_str = row[0].strip()
                    poids    = float(row[poids_idx]) if len(row) > poids_idx and row[poids_idx].strip() else 0
                    if poids <= 0:
                        continue
                    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"):
                        try:
                            d = datetime.datetime.strptime(date_str, fmt).date()
                            points.append((d, poids))
                            break
                        except Exception:
                            pass
                except Exception:
                    pass
        except Exception:
            pass

    return sorted(points, key=lambda x: x[0])


def _load_calories_data(app) -> list[tuple[datetime.date, float]]:
    """Comme _load_weight_data mais pour la colonne Calories."""
    user_dir = utils.get_user_dir(app)
    if not user_dir:
        return []
    fichier = os.path.join(user_dir, "nutrition.csv")
    if not os.path.exists(fichier):
        return []
    points = []
    if _PANDAS:
        try:
            df = pd.read_csv(fichier, on_bad_lines='skip')
            if df.empty:
                return []
            date_col = next((c for c in df.columns if 'date' in c.lower()), df.columns[0])
            cal_col  = next((c for c in df.columns if 'calor' in c.lower()), None)
            if cal_col is None:
                return []
            df['_date'] = pd.to_datetime(df[date_col], dayfirst=True, errors='coerce')
            df['_cal']  = pd.to_numeric(df[cal_col], errors='coerce')
            df = df.dropna(subset=['_date', '_cal'])
            df = df[df['_cal'] > 0]
            for _, row in df.iterrows():
                points.append((row['_date'].date(), float(row['_cal'])))
        except Exception:
            pass
    return sorted(points, key=lambda x: x[0])


# ── Fenêtre graphique ─────────────────────────────────────────────────────────

def show_weight_chart(app):
    """
    Ouvre une fenêtre Toplevel avec :
    • courbe du poids dans le temps
    • moyenne mobile 7 jours
    • axe secondaire optionnel pour les calories
    • barre de navigation matplotlib (zoom, pan, export image)
    """
    if not _MPL:
        messagebox.showerror(
            "matplotlib manquant",
            "Installe matplotlib : pip install matplotlib"
        )
        return

    points = _load_weight_data(app)
    if not points:
        messagebox.showinfo(
            "Pas de données",
            "Aucune donnée de poids disponible.\n"
            "Sauvegarde d'abord des entrées nutrition avec un poids."
        )
        return

    dates  = [p[0] for p in points]
    poids  = [p[1] for p in points]

    # Moyenne mobile 7 jours
    ma7 = []
    for i in range(len(poids)):
        window = poids[max(0, i - 6): i + 1]
        ma7.append(sum(window) / len(window))

    # Calories (optionnel)
    cal_points = _load_calories_data(app)
    has_cal    = bool(cal_points)

    # ── Fenêtre Tkinter ───────────────────────────────────────────────────────
    win = tk.Toplevel()
    win.title(f"Évolution du poids — {getattr(app, 'selected_user_name', '—')}")
    win.geometry("900x600")

    # Barre d'options (filtre période)
    ctrl = tk.Frame(win, bg="#f3f4f6"); ctrl.pack(fill="x", padx=12, pady=6)
    tk.Label(ctrl, text="Période :", bg="#f3f4f6").pack(side="left")
    period_var = tk.StringVar(value="Tout")
    for p in ["30 j", "90 j", "6 mois", "1 an", "Tout"]:
        ttk.Radiobutton(ctrl, text=p, value=p, variable=period_var,
                        command=lambda: _update_chart(
                            period_var.get(), dates, poids, ma7,
                            cal_points, has_cal, canvas, fig, ax1,
                            getattr(app, "selected_user_name", "—")
                        )).pack(side="left", padx=6)
    if has_cal:
        show_cal_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(ctrl, text="Afficher calories",
                        variable=show_cal_var,
                        command=lambda: _update_chart(
                            period_var.get(), dates, poids, ma7,
                            cal_points if show_cal_var.get() else [],
                            show_cal_var.get(), canvas, fig, ax1,
                            getattr(app, "selected_user_name", "—")
                        )).pack(side="left", padx=12)

    # ── Figure matplotlib ─────────────────────────────────────────────────────
    fig, ax1 = plt.subplots(figsize=(9, 4.5), dpi=100)
    fig.patch.set_facecolor("#f9fafb")

    _draw_chart(ax1, dates, poids, ma7, cal_points if has_cal else [],
                has_cal, getattr(app, "selected_user_name", "—"))

    canvas = FigureCanvasTkAgg(fig, master=win)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=4)

    toolbar = NavigationToolbar2Tk(canvas, win)
    toolbar.update()

    # Statistiques rapides
    _draw_stats_bar(win, poids, dates)


def _draw_chart(ax1, dates, poids, ma7, cal_points, has_cal, user_name):
    ax1.clear()
    ax1.set_facecolor("#ffffff")

    # Courbe poids
    ax1.plot(dates, poids, color="#3b82f6", linewidth=1.5,
             marker="o", markersize=4, label="Poids (kg)", zorder=3)
    # Moyenne mobile
    ax1.plot(dates, ma7, color="#f97316", linewidth=2,
             linestyle="--", label="Moy. mobile 7j", zorder=4)

    # Zone entre poids et MA7 (visualiser les écarts)
    ax1.fill_between(dates, poids, ma7, alpha=0.08, color="#3b82f6")

    ax1.set_ylabel("Poids (kg)", color="#1e40af", fontsize=10)
    ax1.tick_params(axis='y', labelcolor="#1e40af")
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))
    ax1.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax1.tick_params(axis='x', rotation=35)
    ax1.grid(axis='y', linestyle='--', alpha=0.4, color="#e5e7eb")
    ax1.spines[['top','right']].set_visible(False)
    ax1.set_title(f"Évolution du poids — {user_name}", fontsize=12, fontweight="bold", pad=10)

    handles, labels = ax1.get_legend_handles_labels()

    # Axe secondaire calories
    if has_cal and cal_points:
        ax2 = ax1.twinx()
        ax2.set_facecolor("#ffffff")
        cal_dates = [p[0] for p in cal_points]
        cal_vals  = [p[1] for p in cal_points]
        ax2.bar(cal_dates, cal_vals, color="#a3e635", alpha=0.3,
                width=0.8, label="Calories (kcal)", zorder=2)
        ax2.set_ylabel("Calories (kcal)", color="#65a30d", fontsize=10)
        ax2.tick_params(axis='y', labelcolor="#65a30d")
        ax2.spines[['top']].set_visible(False)
        h2, l2 = ax2.get_legend_handles_labels()
        handles += h2; labels += l2

    ax1.legend(handles, labels, loc="upper left", fontsize=9,
               framealpha=0.8, edgecolor="#e5e7eb")


def _update_chart(period: str, dates, poids, ma7,
                  cal_points, has_cal, canvas, fig, ax1, user_name):
    """Filtre les données selon la période et redessine."""
    today  = datetime.date.today()
    cutoff = {
        "30 j":   today - datetime.timedelta(days=30),
        "90 j":   today - datetime.timedelta(days=90),
        "6 mois": today - datetime.timedelta(days=182),
        "1 an":   today - datetime.timedelta(days=365),
        "Tout":   datetime.date.min,
    }.get(period, datetime.date.min)

    mask   = [d >= cutoff for d in dates]
    fd     = [d for d, m in zip(dates, mask) if m]
    fp     = [p for p, m in zip(poids,  mask) if m]
    fm7    = [v for v, m in zip(ma7,    mask) if m]
    fcal   = [pt for pt in cal_points if pt[0] >= cutoff]

    _draw_chart(ax1, fd, fp, fm7, fcal, has_cal, user_name)
    canvas.draw()


def _draw_stats_bar(win, poids: list[float], dates: list[datetime.date]):
    """Affiche une barre de statistiques sous le graphique."""
    if not poids:
        return
    stats_f = tk.Frame(win, bg="#f3f4f6"); stats_f.pack(fill="x", padx=12, pady=(0, 8))

    current = poids[-1]
    minimum = min(poids)
    maximum = max(poids)
    moyenne = sum(poids) / len(poids)
    delta   = poids[-1] - poids[0] if len(poids) > 1 else 0.0
    jours   = (dates[-1] - dates[0]).days if len(dates) > 1 else 0

    stats = [
        ("Actuel",   f"{current:.1f} kg"),
        ("Min",      f"{minimum:.1f} kg"),
        ("Max",      f"{maximum:.1f} kg"),
        ("Moyenne",  f"{moyenne:.1f} kg"),
        ("Évolution",f"{delta:+.1f} kg en {jours}j"),
    ]
    for label, value in stats:
        cell = tk.Frame(stats_f, bg="#e0f2fe", bd=0); cell.pack(side="left", padx=6, pady=4, ipadx=8, ipady=4)
        tk.Label(cell, text=label, font=("Helvetica", 8),  bg="#e0f2fe", fg="#64748b").pack()
        tk.Label(cell, text=value, font=("Helvetica", 11, "bold"), bg="#e0f2fe", fg="#0f172a").pack()
