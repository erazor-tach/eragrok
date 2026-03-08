# data/features_module.py — ERAGROK · Nouvelles fonctionnalités
# ─────────────────────────────────────────────────────────────────────────────
# • Graphique évolution poids 30j (matplotlib)
# • Alerte poids non enregistré
# • Camembert macros
# • Timeline cycle colorée
# • Calculateur demi-vie
# • Bibliothèque repas / aliments
# ─────────────────────────────────────────────────────────────────────────────
import tkinter as tk
import datetime
from data.theme import TH
import customtkinter as ctk
from data.theme import (mk_card, mk_card2, mk_label, mk_sep, mk_title,
                        mk_btn, mk_entry, mk_combo, mk_badge, mk_scrollframe)

try:
    import matplotlib
    matplotlib.use("TkAgg")
    import matplotlib.pyplot as plt
    import matplotlib.dates
    import matplotlib.ticker
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    MPL_OK = True
except Exception:
    MPL_OK = False


def _embed_canvas(fig, master, app=None):
    """
    Intègre une figure matplotlib dans Tkinter de façon sécurisée.
    Annule PROACTIVEMENT les after() du backend TkAgg (matplotlib 3.x)
    pour supprimer les bgerror 'check_dpi_scaling' / 'update' à la navigation.
    """
    canvas = FigureCanvasTkAgg(fig, master=master)
    canvas.draw()
    widget = canvas.get_tk_widget()

    if app is not None:
        if not hasattr(app, "_mpl_canvases"):
            app._mpl_canvases = []
        app._mpl_canvases.append((canvas, fig))   # stocker le tuple (canvas, fig)

    widget.bind("<Destroy>", lambda e, c=canvas, f=fig: _cancel_mpl(c, f), add="+")
    return canvas, widget


def _cancel_mpl(canvas, fig):
    """Annule tous les after() pendants d'un canvas TkAgg (matplotlib 3.x)."""
    try:
        tkw = canvas._tkcanvas          # widget tk interne (pas get_tk_widget)
        # Attributs matplotlib 3.x : _idle_draw_id, _event_loop_id
        for attr in ("_idle_draw_id", "_event_loop_id"):
            aid = getattr(canvas, attr, None)
            if aid:
                try: tkw.after_cancel(aid)
                except Exception: pass
                try: setattr(canvas, attr, None)
                except Exception: pass
        # Ancien matplotlib : _idle, _resize_callback
        for attr in ("_idle", "_resize_callback"):
            aid = getattr(canvas, attr, None)
            if aid:
                try: tkw.after_cancel(aid)
                except Exception: pass
    except Exception:
        pass
    try: plt.close(fig)
    except Exception: pass

# ══════════════════════════════════════════════════════════════════════════════
#  GRAPHIQUE ÉVOLUTION DU POIDS (30 jours)
# ══════════════════════════════════════════════════════════════════════════════
def render_weight_chart(parent, app):
    """Courbe poids sur les 30 derniers jours + alerte si poids non saisi depuis Xj."""
    from data import db as _db
    frame = mk_card(parent)
    frame.pack(fill="x", pady=(0, 14))
    mk_title(frame, "  📈  ÉVOLUTION DU POIDS — 30 derniers jours").pack(
        anchor="w", padx=16, pady=(14, 4))
    mk_sep(frame).pack(fill="x", padx=16, pady=(0, 8))

    # Lire les données
    today = datetime.date.today()
    cutoff = today - datetime.timedelta(days=30)
    dates, weights = [], []
    try:
        rows = _db.nutrition_get_all(app)
        for r in rows:
            d = _parse_date_flex(r.get("date",""))
            if d and d >= cutoff:
                try:
                    w = float(r.get("poids",""))
                    if w > 0:
                        dates.append(d)
                        weights.append(w)
                except Exception:
                    pass
    except Exception:
        pass

    # Alerte poids non saisi
    if dates:
        last_entry = max(dates)
        gap = (today - last_entry).days
        if gap >= 3:
            col = "#ef4444" if gap >= 7 else "#f59e0b"
            alert_f = ctk.CTkFrame(frame, fg_color="#1a0a00" if gap>=7 else "#1a1000", corner_radius=6)
            alert_f.pack(fill="x", padx=16, pady=(0, 6))
            ico = "🔴" if gap >= 7 else "🟡"
            mk_label(alert_f,
                f"  {ico}  Dernier poids enregistré il y a {gap} jours — pense à saisir ton poids !",
                size="small", color=col).pack(anchor="w", padx=10, pady=5)
    else:
        alert_f = ctk.CTkFrame(frame, fg_color="#111122", corner_radius=6)
        alert_f.pack(fill="x", padx=16, pady=(0, 6))
        mk_label(alert_f, "  ℹ️  Aucun poids enregistré — saisis ton poids dans Nutrition",
                 size="small", color=TH.TEXT_MUTED).pack(anchor="w", padx=10, pady=5)

    if not MPL_OK or not dates:
        mk_label(frame, "  (matplotlib requis pour le graphique  —  pip install matplotlib)",
                 size="small", color=TH.TEXT_MUTED).pack(anchor="w", padx=16, pady=(0,10))
        return frame

    # Trier
    pairs = sorted(zip(dates, weights))
    dates_s, weights_s = zip(*pairs)

    # Tracer
    bg = "#10101e"
    fig, ax = plt.subplots(figsize=(7.5, 2.4), facecolor=bg)
    ax.set_facecolor(bg)
    ax.plot(dates_s, weights_s, color="#f97316", linewidth=2, marker="o",
            markersize=4, markerfacecolor="#fdba74", markeredgecolor="#f97316")
    ax.fill_between(dates_s, weights_s, min(weights_s)-0.5,
                    alpha=0.15, color="#f97316")

    # Style axes
    for spine in ax.spines.values():
        spine.set_edgecolor("#1e1e38")
    ax.tick_params(colors="#818aaa", labelsize=8)
    ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%d/%m"))
    fig.autofmt_xdate(rotation=30, ha="right")
    ax.yaxis.set_major_formatter(matplotlib.ticker.FormatStrFormatter("%.1f kg"))
    ax.grid(axis="y", color="#1e1e38", linewidth=0.5)

    # Min / max / tendance
    if len(weights_s) >= 3:
        import numpy as np, warnings as _warn
        x_num = matplotlib.dates.date2num(list(dates_s))
        with _warn.catch_warnings():
            _warn.simplefilter("ignore", np.RankWarning)
            z = np.polyfit(x_num, weights_s, 1)
        p = np.poly1d(z)
        trend_dates = [dates_s[0], dates_s[-1]]
        ax.plot(trend_dates, p(matplotlib.dates.date2num(trend_dates)),
                "--", color="#818aaa", linewidth=1, alpha=0.6, label="tendance")

    fig.tight_layout(pad=0.5)

    canvas, widget = _embed_canvas(fig, frame, app=app)
    widget.pack(fill="x", padx=12, pady=(0, 10))
    return frame


# ══════════════════════════════════════════════════════════════════════════════
#  CAMEMBERT MACROS
# ══════════════════════════════════════════════════════════════════════════════
def render_macro_pie(parent, cal, prot, gluc, lip, app=None):
    """Mini camembert des macros en calories. Retourne un frame CTk."""
    if not MPL_OK or not cal or cal <= 0:
        return None

    frame = ctk.CTkFrame(parent, fg_color="transparent")

    cal_p = prot * 4
    cal_g = gluc * 4
    cal_l = lip  * 9
    total = cal_p + cal_g + cal_l
    if total <= 0:
        return None

    labels  = ["Prot.", "Gluc.", "Lip."]
    sizes   = [cal_p/total*100, cal_g/total*100, cal_l/total*100]
    colors  = ["#4aaa4a", "#3b82f6", "#a855f7"]
    explode = [0.04, 0.04, 0.04]

    bg = "#10101e"
    fig, ax = plt.subplots(figsize=(2.2, 2.2), facecolor=bg)
    ax.set_facecolor(bg)
    wedges, texts, autotexts = ax.pie(
        sizes, labels=labels, colors=colors, explode=explode,
        autopct="%1.0f%%", startangle=90,
        textprops={"color":"#818aaa","fontsize":7},
        pctdistance=0.72,
    )
    for at in autotexts:
        at.set_color("#eef2ff")
        at.set_fontsize(7)
    ax.axis("equal")
    fig.tight_layout(pad=0.3)

    canvas, widget = _embed_canvas(fig, frame, app=app)
    widget.pack()
    return frame


# ══════════════════════════════════════════════════════════════════════════════
#  TIMELINE CYCLE COLORÉE
# ══════════════════════════════════════════════════════════════════════════════
def render_cycle_timeline(parent, app):
    """Barre horizontale colorée : Cycle → Washout → PCT."""
    from data import db as _db
    frame = mk_card(parent)
    frame.pack(fill="x", pady=(0, 14))
    mk_title(frame, "  🧬  TIMELINE DU CYCLE").pack(
        anchor="w", padx=16, pady=(14, 4))
    mk_sep(frame).pack(fill="x", padx=16, pady=(0, 8))

    cycle = _db.cycle_get_active(app)
    if not cycle or not cycle.get("debut"):
        mk_label(frame, "  Aucun cycle enregistré.", size="small",
                 color=TH.TEXT_MUTED).pack(anchor="w", padx=16, pady=(0, 10))
        return frame

    debut = _parse_date_flex(cycle.get("debut",""))
    if not debut:
        return frame
    try:
        n_weeks = int(cycle.get("longueur_sem","12"))
    except Exception:
        n_weeks = 12
    washout_w = 2
    pct_w     = 4
    total_w   = n_weeks + washout_w + pct_w

    today     = datetime.date.today()
    days_in   = (today - debut).days

    # Canvas timeline
    W, H  = 780, 56
    PAD   = 16
    BAR_Y = 20
    BAR_H = 22
    bg    = TH.BG_CARD2

    cv = tk.Canvas(frame, width=W, height=H, bg=bg, highlightthickness=0)
    cv.pack(anchor="center", padx=16, pady=(0, 10))

    def week_to_x(w):
        return PAD + (w / total_w) * (W - 2*PAD)

    # Phases
    phases = [
        (0,         n_weeks,              "#1a4a1a", "#22c55e", "CYCLE"),
        (n_weeks,   n_weeks+washout_w,    "#2a1a00", "#f59e0b", "WASHOUT"),
        (n_weeks+washout_w, total_w,      "#0a0d2b", "#3b82f6", "PCT"),
    ]
    for start_w, end_w, bg_col, txt_col, label in phases:
        x0 = week_to_x(start_w)
        x1 = week_to_x(end_w)
        cv.create_rectangle(x0, BAR_Y, x1, BAR_Y+BAR_H, fill=bg_col, outline="")
        mid = (x0+x1)/2
        cv.create_text(mid, BAR_Y+BAR_H//2, text=label,
                       fill=txt_col, font=("Inter",8,"bold"))
        # Tick semaine de début
        if start_w > 0:
            cv.create_line(x0, BAR_Y, x0, BAR_Y+BAR_H, fill="#1e1e38", width=1)

    # Bordure
    cv.create_rectangle(PAD, BAR_Y, W-PAD, BAR_Y+BAR_H,
                        outline="#1e1e38", width=1)

    # Labels semaines en bas
    for wlabel in [0, n_weeks//4, n_weeks//2, n_weeks*3//4,
                   n_weeks, n_weeks+washout_w, total_w]:
        x = week_to_x(wlabel)
        cv.create_line(x, BAR_Y+BAR_H, x, BAR_Y+BAR_H+4, fill="#818aaa", width=1)
        cv.create_text(x, BAR_Y+BAR_H+10, text=f"S{wlabel}",
                       fill="#818aaa", font=("Inter",7))

    # Curseur "Aujourd'hui"
    cur_week = days_in / 7
    if 0 <= cur_week <= total_w:
        cx = week_to_x(cur_week)
        cv.create_polygon(
            cx-5, BAR_Y-1, cx+5, BAR_Y-1, cx, BAR_Y+BAR_H+1,
            fill="#f97316", outline=""
        )
        cv.create_text(cx, BAR_Y-7, text="▼ Auj.",
                       fill="#f97316", font=("Inter",7,"bold"))

    # Résumé texte sous timeline
    info_f = ctk.CTkFrame(frame, fg_color="transparent")
    info_f.pack(fill="x", padx=16, pady=(0, 10))

    if days_in < 0:
        phase_txt = "Cycle pas encore démarré"
        phase_col = TH.TEXT_MUTED
    elif days_in < n_weeks*7:
        week_cur  = days_in//7 + 1
        days_left_cycle = n_weeks*7 - days_in
        phase_txt = f"CYCLE — Semaine {week_cur}/{n_weeks}  ·  {days_left_cycle}j restants"
        phase_col = "#22c55e"
    elif days_in < (n_weeks+washout_w)*7:
        phase_txt = "WASHOUT — Arrêt des produits en cours"
        phase_col = "#f59e0b"
    else:
        pct_day = days_in - (n_weeks+washout_w)*7
        phase_txt = f"PCT — Jour {pct_day+1}"
        phase_col = "#3b82f6"

    mk_label(info_f, f"  📍  {phase_txt}", size="small",
             color=phase_col).pack(side="left", padx=4)

    # Dates clés
    pct_start = debut + datetime.timedelta(weeks=n_weeks+washout_w)
    end_date  = debut + datetime.timedelta(weeks=total_w)
    dates_txt = (f"  Début : {debut:%d/%m/%Y}  ·  "
                 f"Fin cycle : {(debut+datetime.timedelta(weeks=n_weeks)):%d/%m/%Y}  ·  "
                 f"PCT : {pct_start:%d/%m/%Y}  ·  "
                 f"Fin PCT : {end_date:%d/%m/%Y}")
    mk_label(info_f, dates_txt, size="small",
             color=TH.TEXT_MUTED).pack(side="left", padx=8)

    return frame


# ══════════════════════════════════════════════════════════════════════════════
#  CALCULATEUR DEMI-VIE
# ══════════════════════════════════════════════════════════════════════════════
# Demi-vies en jours
HALF_LIVES = {
    "Testosterone Enanthate":       4.5,
    "Testosterone Cypionate":       8.0,
    "Testosterone Propionate":      0.8,
    "Testosterone Undecanoate":    21.0,
    "Nandrolone Decanoate (Deca)":  6.0,
    "Boldenone Undecylenate (EQ)": 14.0,
    "Trenbolone Acetate":           1.0,
    "Trenbolone Enanthate":         5.5,
    "Masteron Propionate":          2.5,
    "Masteron Enanthate":           8.0,
    "Oxandrolone (Anavar)":         0.4,
    "Stanozolol (Winstrol)":        0.4,
    "Methandrostenolone (Dianabol)":0.2,
    "Anastrozole (Arimidex)":       2.0,
    "Letrozole (Femara)":           4.2,
    "Exemestane (Aromasin)":        1.0,
    "Clomiphene (Clomid)":          5.0,
    "Tamoxifen (Nolvadex)":         7.0,
    "HCG":                          1.5,
    "HGH (Somatotropine)":          0.17,
}

def show_halflife_calculator(app):
    """Popup calculateur de demi-vie — élimination à 50% / 90% / 95% / 99%."""
    dlg = ctk.CTkToplevel(app.root)
    dlg.title("Calculateur de demi-vie")
    dlg.geometry("540x520")
    dlg.configure(fg_color=TH.BG_CARD)
    dlg.grab_set()
    dlg.focus_set()

    mk_title(dlg, "  ⏱  CALCULATEUR DE DEMI-VIE").pack(
        anchor="w", padx=20, pady=(16,4))
    mk_sep(dlg).pack(fill="x", padx=20, pady=(0,12))

    row_top = ctk.CTkFrame(dlg, fg_color="transparent")
    row_top.pack(fill="x", padx=20, pady=(0,8))

    mk_label(row_top, "Produit :", size="small", color=TH.TEXT_SUB).pack(side="left",padx=(0,8))
    prod_var = tk.StringVar(value=list(HALF_LIVES.keys())[0])
    cb = mk_combo(row_top, list(HALF_LIVES.keys()), width=300,
                  command=lambda v: _calc_hl(v, dose_var, last_var, result_frame))
    cb.configure(variable=prod_var)
    cb.pack(side="left")

    row2 = ctk.CTkFrame(dlg, fg_color="transparent")
    row2.pack(fill="x", padx=20, pady=(0,8))
    mk_label(row2, "Dose (mg) :", size="small", color=TH.TEXT_SUB).pack(side="left",padx=(0,8))
    dose_var = tk.StringVar(value="100")
    e1 = mk_entry(row2, width=100)
    e1.configure(textvariable=dose_var); e1.pack(side="left",padx=(0,20))

    mk_label(row2, "Dernière injection :", size="small", color=TH.TEXT_SUB).pack(side="left",padx=(0,8))
    last_var = tk.StringVar(value=datetime.date.today().strftime("%d/%m/%Y"))
    e2 = mk_entry(row2, width=110, placeholder="JJ/MM/AAAA")
    e2.configure(textvariable=last_var); e2.pack(side="left")

    result_frame = ctk.CTkFrame(dlg, fg_color=TH.BG_CARD2, corner_radius=8)
    result_frame.pack(fill="both", expand=True, padx=20, pady=(4,16))

    def _calc_hl(*_):
        for w in result_frame.winfo_children(): w.destroy()
        prod = prod_var.get()
        hl   = HALF_LIVES.get(prod, 1.0)
        try: dose = float(dose_var.get())
        except: dose = 100.0
        try:
            last = datetime.datetime.strptime(last_var.get().strip(), "%d/%m/%Y").date()
        except:
            last = datetime.date.today()

        import math
        today = datetime.date.today()
        days_elapsed = (today - last).days

        rows_data = [
            ("Demi-vie",      f"{hl} jours"),
            ("Jours écoulés", f"{days_elapsed}j depuis dernière injection"),
            ("",              ""),
            ("Quantité restante aujourd'hui",
             f"{dose * (0.5 ** (days_elapsed/hl)):.2f} mg  "
             f"({100 * (0.5**(days_elapsed/hl)):.1f}%)"),
        ]
        thresholds = [(50, "#f59e0b"), (90, "#22c55e"), (95, "#22c55e"), (99, "#3b82f6")]
        for pct, col in thresholds:
            days_needed = math.ceil(hl * math.log(100/(100-pct)) / math.log(2))
            elim_date   = last + datetime.timedelta(days=days_needed)
            already = "✅ déjà éliminé" if days_elapsed >= days_needed else f"{elim_date:%d/%m/%Y}  (J+{days_needed})"
            rows_data.append((f"Élimination à {pct}% :", already))

        for lbl_txt, val_txt in rows_data:
            if not lbl_txt:
                mk_sep(result_frame).pack(fill="x", padx=12, pady=3)
                continue
            r = ctk.CTkFrame(result_frame, fg_color="transparent")
            r.pack(fill="x", padx=12, pady=3)
            mk_label(r, lbl_txt, size="small", color=TH.TEXT_MUTED, width=230).pack(side="left")
            mk_label(r, val_txt, size="small", color=TH.TEXT).pack(side="left")

    # Tracer auto
    dose_var.trace_add("write", _calc_hl)
    last_var.trace_add("write", _calc_hl)
    prod_var.trace_add("write", lambda *_: _calc_hl())
    _calc_hl()

    mk_btn(dlg, "Fermer", dlg.destroy,
           color=TH.GRAY, hover=TH.GRAY_HVR,
           width=120, height=TH.BTN_SM).pack(pady=(0,12))


# ══════════════════════════════════════════════════════════════════════════════
#  BIBLIOTHÈQUE REPAS / ALIMENTS
# ══════════════════════════════════════════════════════════════════════════════
FOOD_DB = {
    # (kcal/100g, prot/100g, gluc/100g, lip/100g)
    "Blanc de poulet (cuit)":     (165, 31,  0,   3.6),
    "Blanc de dinde (cuit)":      (135, 29,  0,   2.5),
    "Boeuf haché 5% MG":          (152, 26,  0,   5.0),
    "Saumon (cuit)":              (208, 22,  0,  13.0),
    "Thon (en boîte, eau)":       (116, 26,  0,   1.0),
    "Oeuf entier":                (155, 13,  1.1, 11.0),
    "Blanc d'oeuf":               ( 52, 11,  0.7,  0.2),
    "Fromage blanc 0%":           ( 45, 8,   4,    0.1),
    "Yaourt grec 0%":             ( 59, 10,  3.6,  0.4),
    "Lait écrémé":                ( 35,  3.5, 5,   0.1),
    "Whey protéine":              (380, 80,   8,   5.0),
    "Caséine":                    (370, 78,   9,   3.0),
    "Riz cuit":                   (130,  2.7,28,   0.3),
    "Pâtes cuites":               (131,  5.0,26,   1.1),
    "Flocons d'avoine":           (379, 13,  60,   7.0),
    "Pain complet":               (247,  9,  45,   3.5),
    "Patate douce (cuite)":       ( 90,  2,  21,   0.1),
    "Quinoa (cuit)":              (120,  4.4,22,   1.9),
    "Banane":                     ( 89,  1.1,23,   0.3),
    "Pomme":                      ( 52,  0.3,14,   0.2),
    "Brocoli (cuit)":             ( 35,  2.4, 7,   0.4),
    "Épinards (crus)":            ( 23,  2.9, 3.6, 0.4),
    "Avocat":                     (160,  2,   9,  15.0),
    "Amandes":                    (579, 21,  22,  49.0),
    "Huile d'olive":              (884,  0,   0, 100.0),
    "Beurre de cacahuète":        (588, 25,  20,  50.0),
}

def show_meal_calculator(app, on_apply=None):
    """Popup calculateur de repas avec bibliothèque d'aliments."""
    dlg = ctk.CTkToplevel(app.root)
    dlg.title("Calculateur de repas")
    dlg.geometry("700x580")
    dlg.configure(fg_color=TH.BG_CARD)
    dlg.grab_set(); dlg.focus_set()

    mk_title(dlg, "  🍽  CALCULATEUR DE REPAS").pack(
        anchor="w", padx=20, pady=(16,4))
    mk_sep(dlg).pack(fill="x", padx=20, pady=(0,8))

    # Zone de saisie des aliments
    items = []  # liste de (aliment, grammes)

    top = ctk.CTkFrame(dlg, fg_color="transparent")
    top.pack(fill="x", padx=20, pady=(0,6))

    food_var  = tk.StringVar(value=list(FOOD_DB.keys())[0])
    grams_var = tk.StringVar(value="150")

    mk_label(top, "Aliment :", size="small", color=TH.TEXT_SUB).pack(side="left",padx=(0,6))
    cb = mk_combo(top, list(FOOD_DB.keys()), width=260)
    cb.configure(variable=food_var); cb.pack(side="left",padx=(0,14))
    mk_label(top, "Quantité (g) :", size="small", color=TH.TEXT_SUB).pack(side="left",padx=(0,6))
    e = mk_entry(top, width=80)
    e.configure(textvariable=grams_var); e.pack(side="left",padx=(0,10))

    list_frame = ctk.CTkScrollableFrame(dlg, fg_color=TH.BG_CARD2,
                                         corner_radius=8, height=220)
    list_frame.pack(fill="x", padx=20, pady=(0,6))

    total_frame = ctk.CTkFrame(dlg, fg_color=TH.BG_INPUT, corner_radius=8)
    total_frame.pack(fill="x", padx=20, pady=(0,6))

    def _refresh_list():
        for w in list_frame.winfo_children(): w.destroy()
        # En-tête
        hdr = ctk.CTkFrame(list_frame, fg_color="transparent")
        hdr.pack(fill="x", pady=(2,4))
        for lbl, w in [("Aliment",180),("g",50),("kcal",55),("Prot",50),("Gluc",50),("Lip",50),("",30)]:
            mk_label(hdr, lbl, size="small", color=TH.TEXT_MUTED, width=w).pack(side="left",padx=2)
        mk_sep(list_frame).pack(fill="x")

        total_cal = total_p = total_g = total_l = 0.0
        for i, (food, grams) in enumerate(items):
            vals = FOOD_DB.get(food)
            if not vals: continue
            cal_100, p_100, g_100, l_100 = vals
            factor = grams / 100
            cal  = cal_100 * factor
            p    = p_100 * factor
            g    = g_100 * factor
            l    = l_100 * factor
            total_cal += cal; total_p += p; total_g += g; total_l += l

            row = ctk.CTkFrame(list_frame, fg_color="transparent")
            row.pack(fill="x", pady=1)
            def _v(t, w): mk_label(row, t, size="small", color=TH.TEXT, width=w).pack(side="left",padx=2)
            _v(food[:22], 180); _v(f"{grams:.0f}", 50)
            _v(f"{cal:.0f}", 55); _v(f"{p:.1f}", 50)
            _v(f"{g:.1f}", 50);  _v(f"{l:.1f}", 50)
            idx = i
            ctk.CTkButton(row, text="✕", width=28, height=24,
                          fg_color=TH.DANGER, hover_color="#b91c1c",
                          font=TH.F_SMALL,
                          command=lambda i=idx: (_del(i))).pack(side="left",padx=2)

        # Totaux
        for w in total_frame.winfo_children(): w.destroy()
        tf = ctk.CTkFrame(total_frame, fg_color="transparent")
        tf.pack(anchor="center", pady=8)
        for lbl, val, col in [
            ("Calories",  f"{total_cal:.0f} kcal", TH.ACCENT_GLOW),
            ("Protéines", f"{total_p:.1f} g",       "#4aaa4a"),
            ("Glucides",  f"{total_g:.1f} g",        "#3b82f6"),
            ("Lipides",   f"{total_l:.1f} g",         "#a855f7"),
        ]:
            c = ctk.CTkFrame(tf, fg_color="transparent")
            c.pack(side="left", padx=16)
            mk_label(c, lbl, size="small", color=TH.TEXT_MUTED).pack(anchor="center")
            mk_label(c, val, size="body",  color=col).pack(anchor="center")

        return total_cal, total_p, total_g, total_l

    def _del(idx):
        if 0 <= idx < len(items):
            items.pop(idx)
        _refresh_list()

    def _add():
        food  = food_var.get()
        try: grams = float(grams_var.get())
        except: grams = 100.0
        if food in FOOD_DB and grams > 0:
            items.append((food, grams))
            _refresh_list()

    btn_row = ctk.CTkFrame(dlg, fg_color="transparent")
    btn_row.pack(fill="x", padx=20, pady=(0,6))
    mk_btn(btn_row, "+ Ajouter", _add,
           color=TH.SUCCESS, hover=TH.SUCCESS_HVR,
           width=120, height=TH.BTN_SM).pack(side="left",padx=(0,10))

    if on_apply:
        def _apply():
            totals = _refresh_list()
            on_apply(*totals)
            dlg.destroy()
        mk_btn(btn_row, "✔ Utiliser ces valeurs", _apply,
               color=TH.ACCENT, hover=TH.ACCENT_HOVER,
               width=180, height=TH.BTN_SM).pack(side="left",padx=(0,10))

    mk_btn(btn_row, "Fermer", dlg.destroy,
           color=TH.GRAY, hover=TH.GRAY_HVR,
           width=100, height=TH.BTN_SM).pack(side="right")

    _refresh_list()


# ══════════════════════════════════════════════════════════════════════════════
#  ALERTES PCT (pour dashboard)
# ══════════════════════════════════════════════════════════════════════════════
def get_pct_alert(app):
    """Retourne (message, couleur) si une alerte PCT est active, sinon (None,None)."""
    from data import db as _db
    cycle = _db.cycle_get_active(app)
    if not cycle: return None, None
    debut = _parse_date_flex(cycle.get("debut",""))
    if not debut: return None, None
    try: n_weeks = int(cycle.get("longueur_sem","12"))
    except: n_weeks = 12
    pct_start = debut + datetime.timedelta(weeks=n_weeks + 2)
    today = datetime.date.today()
    days_left = (pct_start - today).days
    if days_left > 14: return None, None
    if days_left > 7:
        return f"📋  PCT dans {days_left}j — Anticiper la commande (Clomid + Nolvadex)", "#f59e0b"
    if days_left > 0:
        return f"⚠️  PCT dans {days_left}j — Préparer le protocole maintenant !", "#ef4444"
    if days_left == 0:
        return "🔴  PCT COMMENCE AUJOURD'HUI — Débuter Clomid + Nolvadex", "#ef4444"
    # PCT en cours
    pct_day = -days_left + 1
    return f"💊  PCT EN COURS — Jour {pct_day}", "#a855f7"


def _parse_date_flex(s):
    for fmt in ("%d/%m/%Y","%Y-%m-%d","%d-%m-%Y"):
        try: return datetime.datetime.strptime(str(s or "").strip(),fmt).date()
        except: pass
    return None



# ══════════════════════════════════════════════════════════════════════════════
#  GÉNÉRATEUR DE PLAN ALIMENTAIRE — BODYBUILDING / FITNESS  v2
#
#  Logique nutritionnelle stricte :
#   🌅 Matin    : œufs / laitiers / flocons / fruits / whey  — jamais viande
#   ☀️  Midi     : repas principal — protéines grasses OK (steak, saumon)
#   🍎 Collation : laitiers + fruits + whey
#   🌙 Soir     : protéines maigres UNIQUEMENT + légumes
#   🌛 Coucher  : protéines lentes (caséine/cottage) — zéro glucide
#
#  Précision macro :
#   1. Distribuer les protéines par slot → calculer grammes précis
#   2. Distribuer les glucides par slot  → calculer grammes précis
#   3. Calculer le déficit lipidique global
#   4. Redistribuer les lipides manquants (huile d'olive, noix…)
#   5. Résultat garanti ≤ 5% d'écart sur chaque macro
# ══════════════════════════════════════════════════════════════════════════════

# ── Base nutritionnelle étendue : (kcal, prot, gluc, lip) pour 100 g ─────────
FOOD_DB_EXT = {
    **FOOD_DB,
    # ── Protéines suppléments ─────────────────────────────────────────────────
    "EvoWhey HSN":               (380, 76.0,  7.0,  6.0),  # WPC 80% HSN
    # ── Laitiers ─────────────────────────────────────────────────────────────
    "Skyr 0%":                   ( 57, 10.0,  4.0,  0.1),
    "Cottage cheese":            ( 72, 12.0,  3.4,  1.2),
    "Fromage blanc 20%":         (100,  8.0,  4.0,  5.5),
    "Ricotta":                   (174,  7.5,  3.3, 13.0),
    "Yaourt 0% nature":          ( 36,  4.5,  5.0,  0.1),
    # ── Œufs ─────────────────────────────────────────────────────────────────
    "Œuf dur entier":            (155, 13.0,  1.1, 11.0),
    # ── Protéines maigres ─────────────────────────────────────────────────────
    "Cabillaud (cuit)":          (105, 23.0,  0.0,  1.5),
    "Merlan (cuit)":             ( 92, 21.0,  0.0,  0.8),
    "Dinde (blanc cuit)":        (135, 29.0,  0.0,  2.5),
    "Tilapia (cuit)":            (128, 26.0,  0.0,  2.7),
    "Crevettes (cuites)":        ( 99, 21.0,  0.9,  1.1),
    "Filet de sole (cuit)":      ( 86, 17.0,  0.0,  1.2),
    "Escalope de veau (cuite)":  (131, 24.0,  0.0,  3.8),
    # ── Protéines grasses ─────────────────────────────────────────────────────
    "Boeuf haché 15% MG":        (215, 20.0,  0.0, 14.0),
    "Boeuf haché 20% MG":        (254, 19.0,  0.0, 20.0),
    "Steak (rumsteck, cuit)":    (195, 29.0,  0.0,  8.5),
    "Maquereau (cuit)":          (262, 24.0,  0.0, 18.0),
    "Sardines (en boîte, huile)":(208, 25.0,  0.0, 11.0),
    "Jambon blanc (dégraissé)":  ( 97, 17.0,  1.5,  2.8),
    # ── Glucides matin ────────────────────────────────────────────────────────
    "Müesli nature (sans sucre)": (354, 11.0, 59.0,  8.0),
    "Galettes de riz nature":    (385,  7.0, 82.0,  2.5),
    # ── Glucides repas ────────────────────────────────────────────────────────
    "Riz brun (cuit)":           (123,  2.7, 26.0,  1.0),
    "Pâtes complètes (cuites)":  (124,  5.5, 23.0,  1.2),
    "Pâtes blanches (cuites)":   (131,  5.0, 26.0,  1.1),
    "Lentilles (cuites)":        (116,  9.0, 20.0,  0.4),
    "Pois chiches (cuits)":      (164,  8.9, 27.0,  2.6),
    "Haricots rouges (cuits)":   (127,  8.7, 23.0,  0.5),
    "Boulgour (cuit)":           (113,  4.0, 23.0,  0.6),
    "Pomme de terre (cuite)":    ( 86,  1.9, 20.0,  0.1),
    "Patate douce violette (cuite)":(90, 2.0, 21.0,  0.1),
    # ── Fruits ───────────────────────────────────────────────────────────────
    "Orange":                    ( 47,  0.9, 12.0,  0.1),
    "Kiwi":                      ( 61,  1.1, 15.0,  0.5),
    "Fraises":                   ( 32,  0.7,  7.7,  0.3),
    "Myrtilles":                 ( 57,  0.7, 14.5,  0.3),
    "Mangue":                    ( 65,  0.5, 17.0,  0.3),
    "Ananas":                    ( 50,  0.5, 13.0,  0.1),
    "Poire":                     ( 57,  0.4, 15.0,  0.1),
    "Pastèque":                  ( 30,  0.6,  7.6,  0.2),
    "Raisins":                   ( 69,  0.7, 18.0,  0.2),
    # ── Légumes ──────────────────────────────────────────────────────────────
    "Courgette (cuite)":         ( 17,  1.2,  3.3,  0.1),
    "Haricots verts (cuits)":    ( 31,  1.9,  6.2,  0.2),
    "Asperges (cuites)":         ( 22,  2.4,  3.7,  0.2),
    "Poivron (cru)":             ( 31,  1.0,  6.0,  0.3),
    "Tomate (crue)":             ( 18,  0.9,  3.9,  0.2),
    "Salade verte":              ( 15,  1.4,  2.3,  0.3),
    "Champignons (cuits)":       ( 28,  3.1,  4.0,  0.3),
    "Chou-fleur (cuit)":         ( 23,  2.3,  3.8,  0.2),
    "Concombre (cru)":           ( 15,  0.7,  3.6,  0.1),
    # ── Lipides sains ─────────────────────────────────────────────────────────
    "Noix":                      (654, 15.0, 14.0, 65.0),
    "Noix de cajou":             (553, 18.0, 30.0, 44.0),
    "Graines de chia":           (486, 17.0, 42.0, 31.0),
    "Graines de lin":            (534, 18.0, 29.0, 42.0),
    "Tahini (purée sésame)":     (595, 17.0, 23.0, 54.0),
    "Huile de coco":             (862,  0.0,  0.0,100.0),

    # ── Produits HSN FoodSeries ───────────────────────────────────────────────
    "Crème de riz HSN":          (340,  6.0, 77.0,  0.5),  # poudre prégélatinisée
    "Farine d'avoine HSN":       (392, 13.0, 68.0,  6.9),  # instantanée micronisée

    # ── Sucrants / condiments ─────────────────────────────────────────────────
    "Confiture (moyenne)":       (255,  0.5, 63.0,  0.1),  # moy. fraise/abricot/framboise
    "Miel":                      (305,  0.3, 80.0,  0.0),
    "Sirop d'agave":             (310,  0.1, 76.0,  0.1),

    # ── Matières grasses / chocolat ───────────────────────────────────────────
    "Beurre doux":               (750,  0.6,  0.5, 83.0),
    "Chocolat noir 70%":         (570,  8.5, 40.0, 40.0),
    "Cacao pur en poudre":       (230, 20.0, 14.0, 12.0),

    # ── Boissons ─────────────────────────────────────────────────────────────
    "Jus d'orange (pur jus)":    ( 45,  0.7, 10.4,  0.2),   # pour 100 ml
    "Chocolat au lait chaud":    (385,  5.5, 80.0,  3.5),   # poudre type Nesquik / 100g

    # ── Pain ─────────────────────────────────────────────────────────────────
    "Pain blanc":                (265,  8.0, 51.0,  2.5),

    # ── Fromages ─────────────────────────────────────────────────────────────
    "Emmental":                  (385, 28.0,  0.5, 30.0),
    "Comté":                     (415, 27.0,  0.3, 34.0),
    "Gruyère":                   (413, 29.0,  0.4, 32.0),

    # ── Lait & alternatives ───────────────────────────────────────────────────
    "Lait entier":               ( 65,  3.2,  4.8,  3.5),
    "Lait de soja":              ( 45,  3.5,  2.7,  2.0),
    "Yaourt grec entier (5%)":   ( 97,  9.0,  3.9,  5.0),

    # ── Protéines végétales ───────────────────────────────────────────────────
    "Tofu ferme":                ( 76,  8.0,  1.8,  4.2),
    "Edamame (cuit)":            (121, 11.0,  9.0,  5.0),

    # ── Légumineuses supplémentaires ─────────────────────────────────────────
    "Haricots blancs (cuits)":   (119,  8.0, 21.0,  0.4),
    "Semoule (cuite)":           (114,  4.0, 24.0,  0.3),

    # ── Oléagineux ───────────────────────────────────────────────────────────
    "Cacahuètes":                (567, 26.0, 16.0, 49.0),
    "Beurre d'amande":           (615, 21.0,  8.0, 56.0),
}


# ── Portions maximales réalistes par aliment (g ou ml) ───────────────────────
# Empêche des quantités immangables (ex: 600g de riz, 400g de blanc d'oeuf)
FOOD_MAX_PORTION = {
    # Protéines animales
    "Oeuf entier":               240,   # ~4-5 œufs max
    "Blanc d'oeuf":              280,   # ~9 blancs max
    "Œuf dur entier":            200,
    "Blanc de poulet (cuit)":    250,
    "Blanc de dinde (cuit)":     250,
    "Dinde (blanc cuit)":        250,
    "Boeuf haché 5% MG":         250,
    "Boeuf haché 15% MG":        220,
    "Boeuf haché 20% MG":        200,
    "Saumon (cuit)":             220,
    "Thon (en boîte, eau)":      200,
    "Cabillaud (cuit)":          250,
    "Merlan (cuit)":             250,
    "Tilapia (cuit)":            250,
    "Crevettes (cuites)":        200,
    "Filet de sole (cuit)":      250,
    "Escalope de veau (cuite)":  220,
    "Steak (rumsteck, cuit)":    250,
    "Maquereau (cuit)":          200,
    "Sardines (en boîte, huile)":150,
    "Jambon blanc (dégraissé)":  150,
    "Tofu ferme":                250,
    # Glucides cuits
    "Riz cuit":                  280,
    "Riz brun (cuit)":           280,
    "Pâtes cuites":              250,
    "Pâtes blanches (cuites)":   250,
    "Pâtes complètes (cuites)":  250,
    "Patate douce (cuite)":      250,
    "Patate douce violette (cuite)": 250,
    "Pomme de terre (cuite)":    300,
    "Quinoa (cuit)":             250,
    "Lentilles (cuites)":        250,
    "Pois chiches (cuits)":      250,
    "Haricots rouges (cuits)":   250,
    "Haricots blancs (cuits)":   250,
    "Boulgour (cuit)":           250,
    "Semoule (cuite)":           250,
    "Edamame (cuit)":            200,
    # Glucides secs / poudres
    "Flocons d'avoine":          100,
    "Pain complet":              100,
    "Pain blanc":                100,
    "Müesli nature (sans sucre)":  80,
    "Galettes de riz nature":      60,
    "Crème de riz HSN":            80,   # poudre
    "Farine d'avoine HSN":        100,   # poudre
    # Laitiers
    "Skyr 0%":                   200,
    "Cottage cheese":            200,
    "Fromage blanc 0%":          200,
    "Fromage blanc 20%":         200,
    "Yaourt grec 0%":            200,
    "Yaourt grec entier (5%)":   200,
    "Yaourt 0% nature":          200,
    "Ricotta":                   150,
    "Lait écrémé":               300,
    "Lait entier":               300,
    "Lait de soja":              300,
    # Protéines poudre
    "EvoWhey HSN":                50,
    "Whey protéine":              50,
    "Caséine":                    50,
    # Fromages durs (riches en lipides)
    "Emmental":                   50,
    "Comté":                      50,
    "Gruyère":                    50,
    # Lipides / oléagineux
    "Avocat":                    150,
    "Amandes":                    40,
    "Noix":                       40,
    "Noix de cajou":              40,
    "Beurre de cacahuète":        40,
    "Beurre d'amande":            35,
    "Cacahuètes":                 40,
    "Graines de chia":            30,
    "Graines de lin":             30,
    "Tahini (purée sésame)":      30,
    "Huile d'olive":              25,
    "Huile de coco":              20,
    "Beurre doux":                25,
    "Chocolat noir 70%":          40,
    "Cacao pur en poudre":        15,
    # Sucrants / condiments
    "Confiture (moyenne)":        30,
    "Miel":                       25,
    "Sirop d'agave":              25,
    "Chocolat au lait chaud":     30,
    # Boissons (ml)
    "Jus d'orange (pur jus)":    250,
    # Fruits
    "Banane":                    200,
    "Pomme":                     200,
    "Orange":                    200,
    "Kiwi":                      150,
    "Fraises":                   200,
    "Myrtilles":                 150,
    "Mangue":                    200,
    "Ananas":                    200,
    "Poire":                     200,
    "Pastèque":                  300,
    "Raisins":                   150,
}

# ── Portions MINIMALES anti-gaspillage ───────────────────────────────────────
# Un aliment ne sera JAMAIS servi sous ce seuil dans un repas généré.
# Si la macro cible est trop faible pour justifier la portion minimale :
#   → l'aliment est SKIPPÉ (remplacé/omis), jamais servi à 5g.
#
# Philosophie de chaque catégorie :
#   "unité"  → aliment indivisible (1 œuf, 1 banane, 1 yaourt)
#   "oxyde"  → s'oxyde en 30min une fois ouvert (avocat, tomate coupée)
#   "dose"   → en dessous = goût nul / quantité inutile (5g d'amandes...)
#   "portion"→ conditionnement standard (1 filet, 1 steak, 1 fleurette)
#   "pot"    → entamer un pot = le finir dans la journée (yaourt, skyr)
FOOD_MIN_PORTION = {
    # ── FRUITS ENTIERS (unité indivisible) ─────────────────────────────────
    "Banane":                 100,   # 1 banane pelée ~100g
    "Pomme":                  100,   # 1 petite pomme
    "Poire":                  100,   # 1 poire
    "Kiwi":                    60,   # 1 kiwi
    "Orange":                 120,   # 1 orange
    "Mangue":                 150,   # demi-mangue minimum
    "Ananas":                 100,   # 1 tranche
    "Pastèque":               150,   # 1 tranche
    "Raisins":                 50,   # petite grappe
    "Fraises":                 80,   # petit bol
    "Myrtilles":               60,   # petit bol
    # ── OXYDATION RAPIDE (s'oxyde en 30min une fois ouvert) ────────────────
    "Avocat":                  80,   # demi-avocat — ouvrir pour moins = poubelle
    "Poivron (cru)":           80,   # demi-poivron minimum
    "Tomate (crue)":           80,   # 1 petite tomate
    "Concombre (cru)":        100,   # tronçon de 10cm
    "Salade verte":            60,   # base d'une salade
    # ── OLÉAGINEUX (dose homéopathique en dessous) ──────────────────────────
    "Amandes":                 15,   # ~10-12 amandes
    "Noix":                    15,   # 4-5 cerneaux
    "Noix de cajou":           15,   # ~10 noix
    "Noix du Brésil":          10,   # 2-3 noix
    "Cacahuètes":              15,   # petite poignée
    "Pistaches":               15,   # petite poignée
    "Noisettes":               12,   # ~10 noisettes
    "Graines de chia":         10,   # 1 càs rase
    "Graines de lin":          10,   # 1 càs rase
    "Tahini (purée sésame)":   15,   # 1 càs
    # ── CORPS GRAS (en dessous = goût nul, gaspillage) ─────────────────────
    "Beurre de cacahuète":     15,   # 1 càs bien remplie
    "Beurre d'amande":         15,   # 1 càs
    "Beurre doux":             10,   # 1 noisette
    "Huile d'olive":            8,   # 1 càc
    "Huile de coco":            8,   # 1 càc
    "Huile de colza":           8,   # 1 càc
    "Huile de tournesol":       8,   # 1 càc
    # ── FROMAGES (ouverture d'un bloc/portion) ──────────────────────────────
    "Emmental":                20,   # 1-2 tranches
    "Comté":                   25,   # 2 fines tranches
    "Parmesan":                15,   # 1 càs râpé
    "Cheddar":                 20,   # 1 tranche
    "Gruyère":                 20,   # 2 tranches
    "Mozzarella":              50,   # demi-boule minimum
    "Fromage de chèvre":       40,   # 1 rondelle
    # ── CHOCOLAT / CACAO ────────────────────────────────────────────────────
    "Chocolat noir 70%":       15,   # 2 carrés
    "Chocolat noir 85%":       10,   # 1-2 carrés
    "Cacao pur en poudre":      8,   # 1 càc
    # ── POISSONS (filet entier minimum) ─────────────────────────────────────
    "Saumon (cuit)":          100,   # 1 pavé minimum
    "Maquereau (cuit)":        80,   # 1 filet
    "Cabillaud (cuit)":       100,   # 1 filet
    "Merlan (cuit)":           80,   # 1 filet
    "Tilapia (cuit)":         100,   # 1 filet
    "Filet de sole (cuit)":    80,   # 1 filet de sole
    "Sardines (en boîte, huile)": 75,  # 1/2 boîte minimum
    # ── VIANDES (steak/escalope entière) ────────────────────────────────────
    "Steak (rumsteck, cuit)": 120,   # 1 steak minimum
    "Escalope de veau (cuite)":100,  # 1 escalope
    "Crevettes (cuites)":      80,   # portion décongélée minimum
    # ── LÉGUMES FRAIS (s'abîment vite coupés) ───────────────────────────────
    "Brocoli (cuit)":          80,   # 1 fleurette minimum
    "Courgette (cuite)":       80,   # demi-courgette
    "Chou-fleur (cuit)":       80,   # quelques fleurettes
    "Asperges (cuites)":       60,   # 4-5 asperges
    "Champignons (cuits)":     60,   # quelques champignons
    "Haricots verts (cuits)":  70,   # petite portion
    # ── LAITIERS (entamer un pot = le finir dans la journée) ────────────────
    "Skyr 0%":                125,   # 1/2 pot 250g minimum
    "Yaourt 0% nature":       125,   # 1 yaourt standard
    "Yaourt grec 0%":         125,   # 1 yaourt
    "Yaourt grec entier (5%)":125,   # 1 yaourt
    "Cottage cheese":         100,   # 1/2 pot
    "Fromage blanc 0%":       100,   # 1/2 pot
    "Fromage blanc 20%":      100,   # 1/2 pot
    "Ricotta":                 80,   # portion minimum
    "Lait entier":            100,   # 1 verre
    "Lait écrémé":            100,   # 1 verre
    "Lait de soja":           100,   # 1 verre
    # ── CONDIMENTS / SUCRANTS (en dessous = invisible) ──────────────────────
    "Miel":                    10,   # 1 càc
    "Confiture (moyenne)":     15,   # 1 càs
    "Sirop d'agave":            8,   # 1 càc
    # ── JAMBON (tranches minimum) ───────────────────────────────────────────
    "Jambon blanc (dégraissé)": 40,  # 2 tranches minimum
    # ── ŒUFS (unité entière) ────────────────────────────────────────────────
    "Oeuf entier":             55,   # 1 œuf minimum (55-60g)
    "Œuf dur entier":          55,   # 1 œuf dur
    # ── PROTÉINES VÉGÉTALES ─────────────────────────────────────────────────
    "Tofu ferme":              80,   # 1/4 bloc minimum
    "Edamame (cuit)":          60,   # petite portion
}

# ── Ratio "skip" anti-gaspillage ──────────────────────────────────────────────
# Si la macro cible ne justifie même pas MIN × SKIP_RATIO → skip l'aliment
# (plutôt que forcer une portion minimum qui fausserait les macros)
FOOD_MIN_SKIP_RATIO = 0.60  # si besoin < 60% du minimum → skip




# ── Catégories fonctionnelles (utilisées par les templates) ───────────────────
FOOD_CATS = {
    "oeuf":             ["Oeuf entier", "Blanc d'oeuf", "Œuf dur entier"],
    "glucide_matin":    ["Flocons d'avoine", "Pain complet", "Pain blanc",
                         "Müesli nature (sans sucre)", "Galettes de riz nature"],
    # Glucides rapides post-WO : collation / avant coucher uniquement
    "glucide_collation": ["Crème de riz HSN", "Farine d'avoine HSN", "Flocons d'avoine"],
    "glucide_midi":     ["Riz cuit", "Riz brun (cuit)", "Pâtes blanches (cuites)",
                         "Pâtes complètes (cuites)", "Patate douce (cuite)",
                         "Pomme de terre (cuite)", "Quinoa (cuit)",
                         "Lentilles (cuites)", "Pois chiches (cuits)",
                         "Haricots rouges (cuits)", "Boulgour (cuit)",
                         "Patate douce violette (cuite)", "Semoule (cuite)",
                         "Haricots blancs (cuits)", "Pâtes cuites"],
    "glucide_soir":     ["Riz cuit", "Riz brun (cuit)", "Patate douce (cuite)",
                         "Quinoa (cuit)", "Pâtes complètes (cuites)",
                         "Boulgour (cuit)", "Lentilles (cuites)",
                         "Haricots blancs (cuits)", "Semoule (cuite)",
                         "Pâtes cuites"],
    "fruit":            ["Banane", "Pomme", "Orange", "Kiwi", "Fraises",
                         "Myrtilles", "Mangue", "Ananas", "Poire",
                         "Pastèque", "Raisins"],
    "legume":           ["Brocoli (cuit)", "Épinards (crus)", "Courgette (cuite)",
                         "Haricots verts (cuits)", "Asperges (cuites)",
                         "Poivron (cru)", "Tomate (crue)", "Salade verte",
                         "Champignons (cuits)", "Chou-fleur (cuit)",
                         "Concombre (cru)"],
    "lipide_sain":      ["Huile d'olive", "Avocat", "Amandes",
                         "Beurre de cacahuète", "Beurre d'amande", "Noix",
                         "Noix de cajou", "Cacahuètes", "Graines de chia",
                         "Graines de lin", "Tahini (purée sésame)",
                         "Huile de coco", "Beurre doux"],
    "laitier":          ["Skyr 0%", "Fromage blanc 0%", "Yaourt grec 0%",
                         "Cottage cheese", "Lait écrémé", "Fromage blanc 20%",
                         "Yaourt 0% nature", "Ricotta", "Lait entier",
                         "Lait de soja", "Yaourt grec entier (5%)"],
    "laitier_lent":     ["Cottage cheese", "Skyr 0%", "Fromage blanc 0%",
                         "Fromage blanc 20%"],  # caséine naturelle
    "whey":             ["EvoWhey HSN", "Whey protéine"],
    "supplement_lent":  ["Caséine"],
    "proteine_maigre":  ["Blanc de poulet (cuit)", "Dinde (blanc cuit)",
                         "Thon (en boîte, eau)", "Cabillaud (cuit)",
                         "Merlan (cuit)", "Tilapia (cuit)",
                         "Crevettes (cuites)", "Filet de sole (cuit)",
                         "Escalope de veau (cuite)", "Blanc de dinde (cuit)",
                         "Jambon blanc (dégraissé)", "Tofu ferme"],
    "proteine_grasse":  ["Boeuf haché 5% MG", "Boeuf haché 15% MG",
                         "Boeuf haché 20% MG", "Saumon (cuit)",
                         "Oeuf entier", "Steak (rumsteck, cuit)",
                         "Maquereau (cuit)", "Sardines (en boîte, huile)"],
    "proteine_midi":    ["Boeuf haché 5% MG", "Boeuf haché 15% MG",
                         "Boeuf haché 20% MG", "Saumon (cuit)",
                         "Oeuf entier", "Steak (rumsteck, cuit)",
                         "Maquereau (cuit)", "Sardines (en boîte, huile)",
                         "Blanc de poulet (cuit)", "Dinde (blanc cuit)",
                         "Thon (en boîte, eau)", "Cabillaud (cuit)",
                         "Merlan (cuit)", "Tilapia (cuit)",
                         "Crevettes (cuites)", "Filet de sole (cuit)",
                         "Escalope de veau (cuite)", "Blanc de dinde (cuit)",
                         "Blanc d'oeuf", "Jambon blanc (dégraissé)",
                         "Tofu ferme", "Edamame (cuit)"],
    "fromage_dur":      ["Emmental", "Comté", "Gruyère"],
    "sucrant_matin":    ["Confiture (moyenne)", "Miel", "Sirop d'agave",
                         "Cacao pur en poudre"],
    # Pain uniquement (pour template pain + beurre)
    "pain_seulement":   ["Pain blanc", "Pain complet"],
    # Lipides adaptés au matin (sur pain ou dans laitier)
    "lipide_matin":     ["Beurre de cacahuète", "Beurre d'amande",
                         "Amandes", "Noix", "Cacahuètes"],
    # Beurre doux : uniquement sur pain (template dédié)
    "beurre_pain":      ["Beurre doux"],
    # Lipides pour collation
    "lipide_collation": ["Beurre de cacahuète", "Beurre d'amande",
                         "Amandes", "Noix", "Noix de cajou", "Cacahuètes",
                         "Chocolat noir 70%"],
    "boisson_matin":    ["Jus d'orange (pur jus)", "Chocolat au lait chaud"],
    # Matière grasse de cuisson — toujours huile d'olive en priorité, huile de coco possible
    "huile_cuisson":    ["Huile d'olive", "Huile de coco"],
    # Lipides au coucher — ordre différent de lipide_collation pour la variation
    "lipide_coucher":   ["Noix", "Amandes", "Noix de cajou", "Cacahuètes",
                         "Beurre de cacahuète", "Beurre d'amande",
                         "Chocolat noir 70%"],
}

# ── Templates de repas par slot ───────────────────────────────────────────────
# Chaque template = liste de (cat, macro_mode)
#  macro_mode :
#    "prot"  → calculer g pour atteindre t_prot du slot
#    "gluc"  → calculer g pour atteindre t_gluc du slot
#    int     → portion fixe (légumes, lipides de base)
SLOT_TEMPLATES = {
    # ── MATIN ─────────────────────────────────────────────────────────────────
    # Whey et crème de riz/farine d'avoine réservés à la collation.
    # Paires fortes : pain+beurre, laitier+beurre de cac, oeuf+fromage.
    "matin": [
        # Oeufs à la poêle (huile cuisson) + flocons + fruit + skyr
        [("oeuf","prot"),          ("glucide_matin","gluc"), ("huile_cuisson",10), ("fruit",120), ("laitier","prot_rest")],
        # Oeufs à la poêle + flocons + fruit (sans laitier)
        [("oeuf","prot"),          ("glucide_matin","gluc"), ("huile_cuisson",10), ("fruit",120)],
        # Laitier + flocons + beurre de cacahuète (dans le skyr) + fruit
        [("laitier","prot"),       ("glucide_matin","gluc"), ("lipide_matin",25),  ("fruit",120)],
        # Pain + beurre doux + oeuf poché/cuit + fromage (continental)
        [("pain_seulement","gluc"),("beurre_pain",20),       ("oeuf","prot"),       ("fromage_dur",40)],
        # Pain + beurre doux + laitier (pain beurré + fromage blanc)
        [("pain_seulement","gluc"),("beurre_pain",20),       ("laitier","prot")],
        # Omelette + glucide + sucrant (huile cuisson + pain + confiture)
        [("oeuf","prot"),          ("glucide_matin","gluc"), ("huile_cuisson",10), ("sucrant_matin",20)],
        # Laitier + glucide + fromage dur (yaourt + flocons + comté)
        [("laitier","prot"),       ("glucide_matin","gluc"), ("fromage_dur",40),   ("fruit",100)],
        # Oeuf poêlé + pain + fromage dur (huile cuisson)
        [("oeuf","prot"),          ("pain_seulement","gluc"),("huile_cuisson",10), ("fromage_dur",40)],
        # Laitier seul + glucide (simple — pas de cuisson)
        [("laitier","prot"),       ("glucide_matin","gluc")],
        # Laitier + glucide + boisson chaude (skyr + flocons + cacao/chocolat chaud)
        [("laitier","prot"),       ("glucide_matin","gluc"), ("boisson_matin",200)],
    ],
    # ── MIDI ──────────────────────────────────────────────────────────────────
    "midi": [
        [("proteine_midi","prot"), ("glucide_midi","gluc"),  ("legume",150), ("huile_cuisson",12)],
        [("proteine_midi","prot"), ("glucide_midi","gluc"),  ("legume",150), ("lipide_sain",15)],
        [("proteine_midi","prot"), ("glucide_midi","gluc"),  ("legume",150), ("fromage_dur",30)],
        [("proteine_midi","prot"), ("glucide_midi","gluc"),  ("legume",150)],
    ],
    # ── COLLATION ─────────────────────────────────────────────────────────────
    # Crème de riz / farine d'avoine ici (post-workout), whey ici aussi.
    # Beurre de cacahuète dans le skyr = combo classique bodybuilding.
    "collation": [
        # Shake post-workout : whey + glucide_collation (crème de riz / farine avoine)
        [("whey","prot"),          ("glucide_collation","gluc")],
        # Laitier + glucide collation + beurre de cac (skyr + crème de riz + beurre cac)
        [("laitier","prot"),       ("glucide_collation","gluc"), ("lipide_collation",25)],
        # Skyr + beurre de cacahuète + fruit (combo très courant)
        [("laitier","prot"),       ("lipide_collation",30),      ("fruit",130)],
        # Laitier + fruit (simple)
        [("laitier","prot"),       ("fruit",130)],
        # Whey seule
        [("whey","prot")],
        # Fromage dur + fruit (plateau léger)
        [("fromage_dur",50),       ("fruit",150)],
        # Laitier + lipide (skyr + amandes)
        [("laitier","prot"),       ("lipide_collation",30)],
    ],
    # ── SOIR ──────────────────────────────────────────────────────────────────
    "soir": [
        [("proteine_maigre","prot"), ("legume",180), ("glucide_soir","gluc"), ("huile_cuisson",12)],
        [("proteine_maigre","prot"), ("legume",180), ("glucide_soir","gluc"), ("lipide_sain",15)],
        [("proteine_maigre","prot"), ("legume",200), ("huile_cuisson",12)],
    ],
    # ── AVANT COUCHER ─────────────────────────────────────────────────────────
    # Whey OK ici mais SANS glucides. Protéines lentes privilégiées.
    "coucher": [
        # Protéines lentes en priorité — whey UNIQUEMENT en dernier recours
        # 0. Caséine seule (protéine lente pure — shaker avant dodo)
        [("supplement_lent","prot")],
        # 1. Cottage/skyr + noix (protéines lentes + lipides lents)
        [("laitier_lent","prot"),    ("lipide_coucher",20)],
        # 2. Fromage blanc + amandes
        [("laitier_lent","prot"),    ("lipide_coucher",25)],
        # 3. Yaourt grec/skyr + lipides
        [("laitier","prot"),         ("lipide_coucher",20)],
        # 4. Caséine seule
        [("supplement_lent","prot")],
        # 5. Cottage seul
        [("laitier_lent","prot")],
        # 6. Caséine + noix
        [("supplement_lent","prot"), ("lipide_coucher",20)],
        # 7. Yaourt seul (simple)
        [("laitier","prot")],
        # 8. Whey — DERNIER RECOURS si aucun laitier/caséine coché
        [("whey","prot")],
    ],
}

SLOT_DESC = {
    "matin":     "Œufs / laitiers / pain+beurre / flocons / fruits",
    "midi":      "Repas principal — grasses OK — glucides complets",
    "collation": "Whey+crème de riz · skyr+beurre de cac · fruit",
    "soir":      "Protéines maigres uniquement — légumes",
    "coucher":   "Protéines lentes (caséine/cottage/whey) — zéro glucide",
}

MEAL_SLOTS = {
    3: [
        {"name":"🌅  Petit-déjeuner",       "type":"matin",     "ratio":0.28},
        {"name":"☀️  Déjeuner",              "type":"midi",      "ratio":0.44},
        {"name":"🌙  Dîner",                "type":"soir",      "ratio":0.28},
    ],
    4: [
        {"name":"🌅  Petit-déjeuner",       "type":"matin",     "ratio":0.22},
        {"name":"☀️  Déjeuner",              "type":"midi",      "ratio":0.35},
        {"name":"🍎  Collation",            "type":"collation", "ratio":0.18},
        {"name":"🌙  Dîner",                "type":"soir",      "ratio":0.25},
    ],
    5: [
        {"name":"🌅  Petit-déjeuner",       "type":"matin",     "ratio":0.20},
        {"name":"☀️  Déjeuner",              "type":"midi",      "ratio":0.30},
        {"name":"🍎  Collation après-midi", "type":"collation", "ratio":0.15},
        {"name":"🌙  Dîner",                "type":"soir",      "ratio":0.25},
        {"name":"🌛  Avant coucher",        "type":"coucher",   "ratio":0.10},
    ],
    6: [
        {"name":"🌅  Petit-déjeuner",       "type":"matin",     "ratio":0.16},
        {"name":"🍎  Collation matin",      "type":"collation", "ratio":0.10},
        {"name":"☀️  Déjeuner",              "type":"midi",      "ratio":0.30},
        {"name":"🍎  Collation après-midi", "type":"collation", "ratio":0.14},
        {"name":"🌙  Dîner",                "type":"soir",      "ratio":0.20},
        {"name":"🌛  Avant coucher",        "type":"coucher",   "ratio":0.10},
    ],
}


# ── Matrice d'incompatibilité alimentaire ─────────────────────────────────
# Paires d'aliments qui ne doivent PAS apparaître dans le même repas.
# Règles basées sur le goût, la texture et la logique culinaire bodybuilding.
FOOD_INCOMPATIBLE = [
    # Céréales / flocons → incompatibles avec poisson et viandes
    ("Flocons d'avoine",           "Sardines (en boîte, huile)"),
    ("Flocons d'avoine",           "Maquereau (cuit)"),
    ("Flocons d'avoine",           "Thon (en boîte, eau)"),
    ("Flocons d'avoine",           "Cabillaud (cuit)"),
    ("Flocons d'avoine",           "Merlan (cuit)"),
    ("Flocons d'avoine",           "Saumon (cuit)"),
    ("Flocons d'avoine",           "Tilapia (cuit)"),
    ("Flocons d'avoine",           "Filet de sole (cuit)"),
    ("Flocons d'avoine",           "Crevettes (cuites)"),
    ("Flocons d'avoine",           "Blanc de poulet (cuit)"),
    ("Flocons d'avoine",           "Dinde (blanc cuit)"),
    ("Flocons d'avoine",           "Blanc de dinde (cuit)"),
    ("Flocons d'avoine",           "Boeuf haché 5% MG"),
    ("Flocons d'avoine",           "Boeuf haché 15% MG"),
    ("Flocons d'avoine",           "Boeuf haché 20% MG"),
    ("Flocons d'avoine",           "Steak (rumsteck, cuit)"),
    ("Flocons d'avoine",           "Escalope de veau (cuite)"),
    ("Müesli nature (sans sucre)", "Sardines (en boîte, huile)"),
    ("Müesli nature (sans sucre)", "Maquereau (cuit)"),
    ("Müesli nature (sans sucre)", "Thon (en boîte, eau)"),
    ("Müesli nature (sans sucre)", "Blanc de poulet (cuit)"),
    ("Müesli nature (sans sucre)", "Boeuf haché 5% MG"),
    ("Galettes de riz nature",     "Sardines (en boîte, huile)"),
    ("Galettes de riz nature",     "Maquereau (cuit)"),
    ("Pain complet",               "Sardines (en boîte, huile)"),   # sauf si utilisateur veut
    ("Pain complet",               "Maquereau (cuit)"),
    # Fruits sucrés → incompatibles avec poisson gras fort en goût
    ("Banane",   "Sardines (en boîte, huile)"),
    ("Banane",   "Maquereau (cuit)"),
    ("Mangue",   "Sardines (en boîte, huile)"),
    ("Mangue",   "Maquereau (cuit)"),
    # Yaourt / laitier sucré → pas avec poisson gras
    ("Yaourt grec 0%",    "Sardines (en boîte, huile)"),
    ("Yaourt grec 0%",    "Maquereau (cuit)"),
    ("Skyr 0%",           "Sardines (en boîte, huile)"),
    ("Skyr 0%",           "Maquereau (cuit)"),
    ("Fromage blanc 0%",  "Sardines (en boîte, huile)"),
    ("Fromage blanc 0%",  "Maquereau (cuit)"),
    ("Cottage cheese",    "Sardines (en boîte, huile)"),
    ("Cottage cheese",    "Maquereau (cuit)"),
    # Whey (goût sucré) → pas avec poisson gras
    ("EvoWhey HSN",   "Sardines (en boîte, huile)"),
    ("EvoWhey HSN",   "Maquereau (cuit)"),
    ("Whey protéine", "Sardines (en boîte, huile)"),
    ("Whey protéine", "Maquereau (cuit)"),
    # Beurre de cacahuète → pas avec poisson salé/gras
    ("Beurre de cacahuète", "Sardines (en boîte, huile)"),
    ("Beurre de cacahuète", "Maquereau (cuit)"),
    ("Beurre de cacahuète", "Thon (en boîte, eau)"),
    # Nouveaux aliments — incompatibilités logiques
    # Sucrants (confiture/miel/sirop) ↔ viandes/poissons/légumes
    ("Confiture (moyenne)",   "Blanc de poulet (cuit)"),
    ("Confiture (moyenne)",   "Saumon (cuit)"),
    ("Confiture (moyenne)",   "Boeuf haché 5% MG"),
    ("Confiture (moyenne)",   "Brocoli (cuit)"),
    ("Miel",                  "Saumon (cuit)"),
    ("Miel",                  "Sardines (en boîte, huile)"),
    ("Miel",                  "Maquereau (cuit)"),
    ("Sirop d'agave",         "Saumon (cuit)"),
    ("Sirop d'agave",         "Sardines (en boîte, huile)"),
    # Chocolat ↔ viandes/poissons
    ("Chocolat noir 70%",     "Blanc de poulet (cuit)"),
    ("Chocolat noir 70%",     "Saumon (cuit)"),
    ("Chocolat noir 70%",     "Boeuf haché 5% MG"),
    ("Chocolat noir 70%",     "Oeuf entier"),
    # Fromages durs ↔ poissons (culinairement bizarre)
    ("Emmental",              "Saumon (cuit)"),
    ("Emmental",              "Sardines (en boîte, huile)"),
    ("Emmental",              "Maquereau (cuit)"),
    ("Comté",                 "Saumon (cuit)"),
    ("Comté",                 "Sardines (en boîte, huile)"),
    ("Gruyère",               "Saumon (cuit)"),
    ("Gruyère",               "Sardines (en boîte, huile)"),
    # Jus d'orange ↔ poissons gras
    ("Jus d'orange (pur jus)", "Sardines (en boîte, huile)"),
    ("Jus d'orange (pur jus)", "Maquereau (cuit)"),
    # Pain blanc ↔ poissons gras (culinairement moins habituel)
    ("Pain blanc",            "Sardines (en boîte, huile)"),
    ("Pain blanc",            "Maquereau (cuit)"),
    # Beurre doux ↔ fruits : beurre fondu + fruit = bizarre
    ("Beurre doux",           "Banane"),
    ("Beurre doux",           "Pomme"),
    ("Beurre doux",           "Orange"),
    ("Beurre doux",           "Fraises"),
    ("Beurre doux",           "Myrtilles"),
    ("Beurre doux",           "Mangue"),
    ("Beurre doux",           "Kiwi"),
    ("Beurre doux",           "Ananas"),
    ("Beurre doux",           "Raisins"),
    ("Beurre doux",           "Poire"),
    ("Beurre doux",           "Pastèque"),
    # Beurre doux ↔ whey / caséine (shake + beurre = non)
    ("Beurre doux",           "Whey protéine"),
    ("Beurre doux",           "EvoWhey HSN"),
    ("Beurre doux",           "Caséine"),
    # Beurre doux ↔ poissons gras (culinairement seulement en sauce, pas en plan)
    ("Beurre doux",           "Sardines (en boîte, huile)"),
    ("Beurre doux",           "Maquereau (cuit)"),
    # Chocolat noir ↔ protéines animales
    ("Chocolat noir 70%",     "Banane"),
    ("Chocolat noir 70%",     "Orange"),
    ("Chocolat noir 70%",     "Kiwi"),
    ("Chocolat noir 70%",     "Mangue"),
    # Crème de riz / farine d'avoine ↔ viandes et poissons (post-WO = whey+crème de riz, pas avec poulet)
    ("Crème de riz HSN",      "Blanc de poulet (cuit)"),
    ("Crème de riz HSN",      "Saumon (cuit)"),
    ("Crème de riz HSN",      "Boeuf haché 5% MG"),
    ("Crème de riz HSN",      "Boeuf haché 15% MG"),
    ("Crème de riz HSN",      "Boeuf haché 20% MG"),
    ("Crème de riz HSN",      "Steak (rumsteck, cuit)"),
    ("Crème de riz HSN",      "Oeuf entier"),
    ("Farine d'avoine HSN",   "Blanc de poulet (cuit)"),
    ("Farine d'avoine HSN",   "Saumon (cuit)"),
    ("Farine d'avoine HSN",   "Boeuf haché 5% MG"),
    ("Farine d'avoine HSN",   "Boeuf haché 15% MG"),
    ("Farine d'avoine HSN",   "Steak (rumsteck, cuit)"),
    ("Farine d'avoine HSN",   "Oeuf entier"),
    # Huile d'olive ↔ laitiers sucrés (pas de cuisson dans un bowl de skyr)
    ("Huile d'olive",        "Skyr 0%"),
    ("Huile d'olive",        "Yaourt grec 0%"),
    ("Huile d'olive",        "Fromage blanc 0%"),
    ("Huile d'olive",        "Yaourt 0% nature"),
    ("Huile d'olive",        "Yaourt grec entier (5%)"),
    ("Huile d'olive",        "Fromage blanc 20%"),
    ("Huile d'olive",        "Cottage cheese"),
    ("Huile d'olive",        "Ricotta"),
    ("Huile d'olive",        "Whey protéine"),
    ("Huile d'olive",        "EvoWhey HSN"),
    ("Huile d'olive",        "Caséine"),
    ("Huile d'olive",        "Banane"),
    ("Huile d'olive",        "Pomme"),
    ("Huile d'olive",        "Fraises"),
    ("Huile d'olive",        "Myrtilles"),
    ("Huile d'olive",        "Orange"),
    ("Huile d'olive",        "Kiwi"),
    ("Huile d'olive",        "Mangue"),
    ("Huile d'olive",        "Raisins"),
    ("Huile d'olive",        "Flocons d'avoine"),
    ("Huile d'olive",        "Müesli nature (sans sucre)"),
    ("Huile d'olive",        "Galettes de riz nature"),
    ("Huile d'olive",        "Crème de riz HSN"),
    ("Huile d'olive",        "Farine d'avoine HSN"),
    ("Huile d'olive",        "Miel"),
    ("Huile d'olive",        "Confiture (moyenne)"),
    ("Huile d'olive",        "Sirop d'agave"),
    ("Huile d'olive",        "Chocolat noir 70%"),
    ("Huile d'olive",        "Chocolat au lait chaud"),
]
# Construire un set symétrique pour lookup O(1)
_INCOMPAT_SET = set()
for a,b in FOOD_INCOMPATIBLE:
    _INCOMPAT_SET.add((a,b))
    _INCOMPAT_SET.add((b,a))

def _is_compatible(food_a, food_b):
    """True si les deux aliments peuvent être dans le même repas."""
    return (food_a, food_b) not in _INCOMPAT_SET

def _filter_compatible(candidate, already_in_meal):
    """Retourne True si `candidate` est compatible avec tous les aliments déjà dans le repas."""
    return all(_is_compatible(candidate, existing) for existing in already_in_meal)



# ── Familles d'aliments (anti-répétition journalière) ─────────────────────────
# Si un aliment d'une famille est utilisé, tous les autres sont bloqués ce jour.
FOOD_SAME_FAMILY = {
    # Poudres protéinées : whey / evowhey / caséine = même effet, même goût de "shake"
    "EvoWhey HSN":      {"Whey protéine", "Caséine"},
    "Whey protéine":    {"EvoWhey HSN",   "Caséine"},
    "Caséine":          {"EvoWhey HSN",   "Whey protéine"},
    # Flocons / farine / crème de riz = même base céréalière chaude
    "Flocons d'avoine":     {"Farine d'avoine HSN", "Crème de riz HSN"},
    "Farine d'avoine HSN":  {"Flocons d'avoine",    "Crème de riz HSN"},
    "Crème de riz HSN":     {"Flocons d'avoine",    "Farine d'avoine HSN"},
    # Pâtes cuites / pâtes blanches / pâtes complètes = idem
    "Pâtes cuites":              {"Pâtes blanches (cuites)", "Pâtes complètes (cuites)"},
    "Pâtes blanches (cuites)":   {"Pâtes cuites",            "Pâtes complètes (cuites)"},
    "Pâtes complètes (cuites)":  {"Pâtes cuites",            "Pâtes blanches (cuites)"},
    # Riz cuit / riz brun = même base
    "Riz cuit":         {"Riz brun (cuit)"},
    "Riz brun (cuit)":  {"Riz cuit"},
    # Beurre de cacahuète / beurre d'amande = même usage (dans le skyr / sur pain)
    "Beurre de cacahuète": {"Beurre d'amande"},
    "Beurre d'amande":     {"Beurre de cacahuète"},
    # Blanc de poulet / blanc de dinde / dinde = même viande blanche
    "Blanc de poulet (cuit)":  {"Dinde (blanc cuit)", "Blanc de dinde (cuit)"},
    "Dinde (blanc cuit)":      {"Blanc de poulet (cuit)", "Blanc de dinde (cuit)"},
    "Blanc de dinde (cuit)":   {"Blanc de poulet (cuit)", "Dinde (blanc cuit)"},
}

def _generate_meal_plan(n_meals, selected_foods, cal_total, prot_total,
                         gluc_total, lip_total, day_offset=0):
    """
    Génère un plan alimentaire journalier avec :
    - Logique d'incompatibilité alimentaire (flocons ≠ sardines, etc.)
    - Variation par day_offset : chaque jour utilise une rotation différente
      des pools d'aliments disponibles → plans variés sur 7/30 jours
    - 4 passes de précision macro (prot → gluc → lip)
    """
    db  = FOOD_DB_EXT
    sel = set(selected_foods)

    # Suivi des aliments déjà utilisés dans la journée (toutes catégories)
    # → empêche de retrouver EvoWhey + flocons x2 dans la même journée
    _used_today: set = set()

    def _avail(cat, already_in_meal=None, offset=0, allow_repeat=False):
        """Retourne les aliments disponibles dans la catégorie.
        - Filtrés par incompatibilité dans le repas courant.
        - Filtrés par _used_today pour éviter la répétition dans la journée.
        - Mélange vraiment aléatoire à chaque appel.
        """
        candidates = [f for f in FOOD_CATS.get(cat, []) if f in sel and f in db]
        if already_in_meal:
            candidates = [f for f in candidates
                          if _filter_compatible(f, already_in_meal)]
        if not candidates:
            return []
        # Mélange vraiment aléatoire à chaque appel
        # (pas de seed déterministe → résultat différent à chaque génération)
        import random as _rnd2
        rotated = candidates[:]
        _rnd2.shuffle(rotated)

        # Filtre anti-répétition : exclure ce qui a déjà été utilisé aujourd'hui
        # SAUF catégories où la répétition est normale (légumes, lipides fixes, sucrants)
        REPEAT_OK_CATS = {"legume", "lipide_sain", "beurre_pain",
                          "sucrant_matin", "fromage_dur", "boisson_matin",
                          "huile_cuisson",    # l'huile peut revenir à chaque repas cuit
                          "supplement_lent",  # caséine = slot coucher uniquement
                          "laitier_lent",     # cottage/skyr lent = idem
                          "lipide_coucher"}   # noix au coucher = usage dédié
        if not allow_repeat and cat not in REPEAT_OK_CATS:
            fresh = [f for f in rotated if f not in _used_today]
            if fresh:
                return fresh
        return rotated

    def _macros(food, grams):
        k,p,g,l = db[food]
        r = grams/100.0
        return k*r, p*r, g*r, l*r

    def _g_for(food, target, macro_idx):
        """Calcule les grammes pour atteindre `target` en macro `macro_idx`.
        Applique le minimum anti-gaspillage : si la cible est trop basse
        pour justifier le minimum, retourne -1 (signal de skip).
        """
        val100 = db[food][macro_idx]
        if val100 <= 0: return 50
        raw = max(10, round(target / (val100/100.0)))
        cap = FOOD_MAX_PORTION.get(food, 300)
        mn  = FOOD_MIN_PORTION.get(food, 10)
        # Anti-gaspillage : si la cible ne justifie pas le minimum → signal skip
        if raw < mn * FOOD_MIN_SKIP_RATIO:
            return -1   # le générateur doit choisir un autre aliment
        return max(mn, min(cap, raw))

    # Offsets différents par catégorie pour plus de diversité
    # Jour 0 : prot=poulet, gluc=riz / Jour 1 : prot=dinde, gluc=pâtes / etc.
    off_prot = day_offset
    off_gluc = day_offset + 1   # décalé pour éviter toujours même glucide
    off_leg  = day_offset + 2
    off_lip  = day_offset + 3

    slots = MEAL_SLOTS.get(n_meals, MEAL_SLOTS[4])
    meals = []

    # ── PASSE 1 : protéines + glucides ────────────────────────────────────────
    for slot in slots:
        stype   = slot["type"]
        ratio   = slot["ratio"]
        t_prot  = prot_total * ratio
        t_gluc  = gluc_total * ratio

        raw_tpls = SLOT_TEMPLATES.get(stype, SLOT_TEMPLATES["collation"])
        # Rotation du point de départ des templates — seed combinant offset + slot type
        # (pas slots.index pour éviter la corrélation avec food selection)
        import random as _rnd3
        templates = raw_tpls[:]
        _rnd3.shuffle(templates)
        best_items = None

        for tpl in templates:
            items      = []
            rem_prot   = t_prot
            rem_gluc   = t_gluc
            used       = set()
            ok         = True
            _pending   = set()   # aliments candidats pour ce template — commit seulement si ok

            for cat, mode in tpl:
                # Offset adapté selon la catégorie fonctionnelle
                if cat in ("proteine_midi","proteine_maigre","proteine_grasse","oeuf"):
                    use_off = off_prot
                elif cat in ("glucide_midi","glucide_soir","glucide_matin",
                             "glucide_collation","fruit","pain_seulement"):
                    use_off = off_gluc
                elif cat == "legume":
                    use_off = off_leg
                elif cat in ("lipide_sain","lipide_matin","lipide_collation",
                             "lipide_coucher","beurre_pain","huile_cuisson"):
                    use_off = off_lip
                else:
                    use_off = day_offset

                already = [i["food"] for i in items]
                cands = [f for f in _avail(cat, already, use_off) if f not in used]

                if not cands:
                    if isinstance(mode, int): continue
                    ok = False; break

                food = cands[0]
                used.add(food)

                if isinstance(mode, int):
                    # Portion fixe du template — jamais sous le minimum anti-gaspillage
                    mn_fix = FOOD_MIN_PORTION.get(food, 0)
                    g = max(mn_fix, mode)
                elif mode == "prot":
                    g = _g_for(food, rem_prot, 1)
                    if g == -1:
                        # Cible trop basse pour justifier ce fruit/légume/yaourt
                        # → essayer le candidat suivant dans cands
                        cands_rest = [f for f in cands if f != food]
                        found = False
                        for alt in cands_rest:
                            g2 = _g_for(alt, rem_prot, 1)
                            if g2 != -1:
                                food = alt; g = g2; used.add(food)
                                found = True; break
                        if not found:
                            if not isinstance(mode, int): ok = False; break
                            continue
                    g = min(FOOD_MAX_PORTION.get(food, 280), g)
                elif mode == "prot_rest":
                    g = _g_for(food, rem_prot, 1)
                    if g == -1 or g < FOOD_MIN_PORTION.get(food, 10):
                        continue  # pas assez de marge → skip
                    g = min(FOOD_MAX_PORTION.get(food, 200), g)
                elif mode == "gluc":
                    g = _g_for(food, rem_gluc, 2)
                    if g == -1:
                        cands_rest = [f for f in cands if f != food]
                        found = False
                        for alt in cands_rest:
                            g2 = _g_for(alt, rem_gluc, 2)
                            if g2 != -1:
                                food = alt; g = g2; used.add(food)
                                found = True; break
                        if not found:
                            if not isinstance(mode, int): ok = False; break
                            continue
                    g = min(FOOD_MAX_PORTION.get(food, 260), g)
                else:
                    continue

                k,p,gc,l = _macros(food, g)
                items.append({"food":food,"g":g,"kcal":k,"p":p,"g_":gc,"l":l})
                _pending.add(food)   # accumuler — PAS encore dans _used_today
                _pending.update(FOOD_SAME_FAMILY.get(food, set()))
                rem_prot -= p
                rem_gluc -= gc

            if ok and items:
                # ✅ Template retenu → on commit dans _used_today
                _used_today.update(_pending)
                best_items = items
                break
            # ❌ Template abandonné → _pending est jeté, _used_today intact

        # Fallback ultime (pas de contrainte d'incompatibilité)
        if not best_items:
            # Fallback : d'abord des aliments non encore utilisés ce jour
            fallback_pool = [f for f in sel if f in db and f not in _used_today]
            if not fallback_pool:
                fallback_pool = [f for f in sel if f in db]  # tout si rien de frais
            for food in fallback_pool:
                g = max(50, _g_for(food, t_prot, 1))
                k,p,gc,l = _macros(food, g)
                best_items = [{"food":food,"g":g,"kcal":k,"p":p,"g_":gc,"l":l}]
                _used_today.add(food)
                _used_today.update(FOOD_SAME_FAMILY.get(food, set()))
                break

        best_items = best_items or []
        meals.append({"slot": slot, "type": stype, "items": best_items})

    # ── PASSE 1.5 : booster macro-conscient ─────────────────────────────────────
    # Avant d'ajouter un booster, on vérifie où on en est sur glucides et lipides.
    # Si glucides en déficit → booster glucidique en priorité.
    # Si lipides déjà en excès → on n'ajoute pas de lipides.
    GLUC_BOOSTERS_BY_SLOT = {
        "matin":     ["Flocons d'avoine", "Pain complet", "Pain blanc",
                      "Galettes de riz nature", "Crème de riz HSN",
                      "Müesli nature (sans sucre)", "Miel", "Confiture (moyenne)"],
        "midi":      ["Riz cuit", "Riz brun (cuit)", "Pâtes blanches (cuites)",
                      "Pâtes complètes (cuites)", "Patate douce (cuite)",
                      "Quinoa (cuit)", "Semoule (cuite)", "Boulgour (cuit)"],
        "soir":      ["Riz cuit", "Riz brun (cuit)", "Patate douce (cuite)",
                      "Quinoa (cuit)", "Pâtes complètes (cuites)", "Boulgour (cuit)"],
        "collation": ["Flocons d'avoine", "Crème de riz HSN", "Farine d'avoine HSN",
                      "Galettes de riz nature", "Banane"],
    }
    LIP_BOOSTERS_BY_SLOT = {
        "matin":     ["Beurre de cacahuète", "Beurre d'amande", "Beurre doux"],
        "midi":      ["Huile d'olive", "Avocat", "Amandes", "Noix",
                      "Beurre de cacahuète", "Cacahuètes", "Emmental", "Comté"],
        "soir":      ["Huile d'olive", "Avocat", "Amandes", "Noix", "Cacahuètes"],
        "collation": ["Amandes", "Noix", "Noix de cajou", "Cacahuètes",
                      "Beurre de cacahuète", "Beurre d'amande", "Chocolat noir 70%"],
    }

    # Calculer les totaux courants pour orienter le booster
    cur_gluc = sum(i["g_"] for m in meals for i in m["items"])
    cur_lip  = sum(i["l"]  for m in meals for i in m["items"])

    for m in meals:
        ratio_m   = m["slot"]["ratio"]
        t_cal_m   = cal_total * ratio_m
        got_cal_m = sum(i["kcal"] for i in m["items"])
        deficit_c = t_cal_m - got_cal_m
        stype_m   = m["type"]
        if deficit_c <= t_cal_m * 0.25 or stype_m == "coucher":
            continue

        already_foods = {i["food"] for i in m["items"]}
        # Pain présent au matin → beurre doux en premier lipide
        pain_present = stype_m == "matin" and any(
            f in already_foods for f in ("Pain blanc", "Pain complet"))

        # Décider quel type de booster selon les macros courantes
        gluc_pct = cur_gluc / gluc_total * 100 if gluc_total else 100
        lip_pct  = cur_lip  / lip_total  * 100 if lip_total  else 100

        # Glucides sous 85% de cible → booster glucidique en priorité
        if gluc_pct < 85 and stype_m in GLUC_BOOSTERS_BY_SLOT:
            boosters = GLUC_BOOSTERS_BY_SLOT[stype_m][:]
        # Lipides déjà au-dessus de 105% → pas de booster lipidique
        elif lip_pct > 105:
            boosters = GLUC_BOOSTERS_BY_SLOT.get(stype_m, [])[:]
        else:
            boosters = (["Beurre doux"] if pain_present else []) +                        LIP_BOOSTERS_BY_SLOT.get(stype_m, [])[:]

        import random as _r
        _r.shuffle(boosters)  # ordre aléatoire dans le type choisi
        for bst in boosters:
            if bst not in sel or bst not in db: continue
            if bst in already_foods: continue
            if not _filter_compatible(bst, list(already_foods)): continue
            k100, _, _, _ = db[bst]
            if k100 <= 0: continue
            g_bst_raw = max(10, round(deficit_c / (k100 / 100.0)))
            g_bst_mn  = FOOD_MIN_PORTION.get(bst, 10)
            g_bst     = min(FOOD_MAX_PORTION.get(bst, 40),
                            max(g_bst_mn, g_bst_raw))
            # Si le minimum dépasse 2× le déficit calorique → skip (gaspillage)
            if g_bst_mn > 0 and g_bst * (k100/100.0) > deficit_c * 2.5:
                continue
            k, p, gc, l = _macros(bst, g_bst)
            m["items"].append({"food": bst, "g": g_bst,
                                "kcal": k, "p": p, "g_": gc, "l": l})
            _used_today.add(bst)
            _used_today.update(FOOD_SAME_FAMILY.get(bst, set()))
            cur_gluc += gc
            cur_lip  += l
            break

    # ── PASSE 2 : correction protéines ───────────────────────────────────────
    got_prot = sum(i["p"] for m in meals for i in m["items"])
    if prot_total and abs(got_prot - prot_total) / prot_total * 100 > 5:
        delta_prot = prot_total - got_prot
        bm = max(meals, key=lambda m: max((i["p"] for i in m["items"]), default=0))
        mi = max(bm["items"], key=lambda i: i["p"], default=None)
        if mi:
            _, p100, _, _ = db[mi["food"]]
            if p100 > 0:
                raw_g = mi["g"] + round(delta_prot/(p100/100.0))
                mn_g  = FOOD_MIN_PORTION.get(mi["food"], 20)
                new_g = max(mn_g, min(FOOD_MAX_PORTION.get(mi["food"],300), raw_g))
                k,p,gc,l = _macros(mi["food"], new_g)
                mi.update({"g":new_g,"kcal":k,"p":p,"g_":gc,"l":l})

    # ── PASSE 3 : équilibrage glucides ────────────────────────────────────────
    # 3a. Trim si excès > 8%
    got_gluc = sum(i["g_"] for m in meals for i in m["items"])
    if gluc_total and (got_gluc - gluc_total) / gluc_total * 100 > 8:
        for m in meals:
            if m["type"] in ("midi","soir","matin"):
                gi = [i for i in m["items"] if any(i["food"] in FOOD_CATS.get(c,[])
                      for c in ("glucide_midi","glucide_soir","glucide_matin",
                                "glucide_collation","pain_seulement"))]
                if gi:
                    mg = max(gi, key=lambda x: x["g_"])
                    _, _, g100, _ = db[mg["food"]]
                    if g100 > 0:
                        mn_g  = FOOD_MIN_PORTION.get(mg["food"], 30)
                        new_g = max(mn_g, mg["g"] - round((got_gluc-gluc_total)/(g100/100.0)))
                        k,p,gc,l = _macros(mg["food"], new_g)
                        mg.update({"g":new_g,"kcal":k,"p":p,"g_":gc,"l":l})
                    break

    # 3b. Combler si déficit > 8% — augmenter la portion du plus grand glucide
    got_gluc = sum(i["g_"] for m in meals for i in m["items"])
    if gluc_total and (gluc_total - got_gluc) / gluc_total * 100 > 8:
        deficit_g = gluc_total - got_gluc
        # Chercher le repas midi ou soir avec glucide, augmenter sa portion
        for m in sorted(meals, key=lambda x: x["slot"]["ratio"], reverse=True):
            if m["type"] not in ("midi","soir","matin"): continue
            gi = [i for i in m["items"] if any(i["food"] in FOOD_CATS.get(c,[])
                  for c in ("glucide_midi","glucide_soir","glucide_matin"))]
            if gi:
                mg = max(gi, key=lambda x: x["g_"])
                _, _, g100, _ = db[mg["food"]]
                if g100 > 0:
                    add_g = round(deficit_g / (g100/100.0))
                    new_g = min(FOOD_MAX_PORTION.get(mg["food"],300), mg["g"] + add_g)
                    k,p,gc,l = _macros(mg["food"], new_g)
                    mg.update({"g":new_g,"kcal":k,"p":p,"g_":gc,"l":l})
                break

    # ── PASSE 4 : équilibrage lipides ─────────────────────────────────────────
    # 4a. Trim si excès > 10% — réduire les lipides rajoutés (huile, beurre...)
    got_lip = sum(i["l"] for m in meals for i in m["items"])
    if lip_total and (got_lip - lip_total) / lip_total * 100 > 10:
        excès_l = got_lip - lip_total
        lip_cats = ("lipide_sain","lipide_matin","lipide_collation",
                    "lipide_coucher","huile_cuisson","beurre_pain")
        for m in meals:
            for it in m["items"]:
                if any(it["food"] in FOOD_CATS.get(c,[]) for c in lip_cats):
                    _, _, _, l100 = db[it["food"]]
                    if l100 > 0:
                        reduce_g = min(it["g"] - FOOD_MIN_PORTION.get(it["food"], 5),
                                       round(excès_l / (l100/100.0)))
                        if reduce_g > 0:
                            new_g = max(FOOD_MIN_PORTION.get(it["food"], 5), it["g"] - reduce_g)
                            k,p,gc,l = _macros(it["food"], new_g)
                            it.update({"g":new_g,"kcal":k,"p":p,"g_":gc,"l":l})
                            excès_l -= (it["l"] - l)
                            if excès_l <= 2: break
            if excès_l <= 2: break

    # 4b. Combler si déficit > 5% — ajouter huile d'olive sur midi/soir
    got_lip = sum(i["l"] for m in meals for i in m["items"])
    deficit_lip = lip_total - got_lip
    if deficit_lip > lip_total * 0.05:
        lip_avail = _avail("lipide_sain")
        if lip_avail:
            lip_food = lip_avail[0]
            _, _, _, l100 = db[lip_food]
            if l100 > 0:
                mn_lip  = FOOD_MIN_PORTION.get(lip_food, 8)
                g_total = max(mn_lip, round(deficit_lip/(l100/100.0)))
                tslots  = [m for m in meals if m["type"] in ("midi","soir")]
                if not tslots:
                    tslots = [m for m in meals if m["type"] != "coucher"]
                if tslots:
                    g_base = g_total // len(tslots)
                    g_rest = g_total - g_base*(len(tslots)-1)
                    for idx, m in enumerate(tslots):
                        g = g_rest if idx == len(tslots)-1 else g_base
                        if g < 3: continue
                        k,p,gc,l = _macros(lip_food, g)
                        already = [it for it in m["items"] if it["food"] == lip_food]
                        if already:
                            ng = min(FOOD_MAX_PORTION.get(lip_food,40), already[0]["g"] + g)
                            k2,p2,gc2,l2 = _macros(lip_food, ng)
                            already[0].update({"g":ng,"kcal":k2,"p":p2,"g_":gc2,"l":l2})
                        else:
                            m["items"].append({"food":lip_food,"g":g,
                                                "kcal":k,"p":p,"g_":gc,"l":l})

    # ── PASSE 5 : précision protéines ±1% ────────────────────────────────────
    # La fourchette scientifique pour la musculation naturelle est 1.6–2.2 g/kg.
    # On vise exactement prot_total ±1% : ni plus (reins), ni moins (catabolisme).
    got_prot = sum(i["p"] for m in meals for i in m["items"])
    prot_err_pct = (got_prot - prot_total) / prot_total * 100 if prot_total else 0

    if abs(prot_err_pct) > 1.0:
        delta_p = prot_total - got_prot  # positif = déficit, négatif = excès
        # Trouver le plus grand item protéique hors coucher
        best_m, best_i = None, None
        for m in meals:
            if m["type"] == "coucher": continue
            for it in m["items"]:
                if best_i is None or it["p"] > best_i["p"]:
                    best_m, best_i = m, it
        if best_m and best_i:
            _, p100, _, _ = db[best_i["food"]]
            if p100 > 0:
                add_g  = round(delta_p / (p100 / 100.0))
                mn_p5  = FOOD_MIN_PORTION.get(best_i["food"], 20)
                new_g  = max(mn_p5, min(FOOD_MAX_PORTION.get(best_i["food"], 350),
                             best_i["g"] + add_g))
                k, p, gc, l = _macros(best_i["food"], new_g)
                best_i.update({"g": new_g, "kcal": k, "p": p, "g_": gc, "l": l})

    # ── PASSE 6 : calories à 100% — distribution multi-repas ─────────────────
    # Répartit l'écart calorique sur TOUS les repas glucidiques disponibles.
    # Converge en 2-3 itérations même pour des déficits de 500 kcal.
    gluc_cats = ("glucide_midi","glucide_soir","glucide_matin",
                 "glucide_collation","pain_seulement")
    lip_cats  = ("lipide_sain","lipide_matin","lipide_collation",
                 "lipide_coucher","huile_cuisson","beurre_pain")

    for _iteration in range(8):
        got_cal    = sum(i["kcal"] for m in meals for i in m["items"])
        delta_kcal = cal_total - got_cal
        if abs(delta_kcal / cal_total * 100) <= 1.0:
            break

        # Collecter tous les items glucidiques ajustables (hors coucher)
        gluc_items = []
        for m in meals:
            if m["type"] == "coucher": continue
            for it in m["items"]:
                if not any(it["food"] in FOOD_CATS.get(c, []) for c in gluc_cats):
                    continue
                cap = FOOD_MAX_PORTION.get(it["food"], 350)
                # Ajustable si pas encore au cap (déficit) ou au-dessus du min (excès)
                if delta_kcal > 0 and it["g"] < cap:
                    gluc_items.append(it)
                elif delta_kcal < 0 and it["g"] > max(25, FOOD_MIN_PORTION.get(it["food"], 25)):
                    gluc_items.append(it)

        if gluc_items:
            # Distribuer équitablement entre tous les repas glucidiques
            share = delta_kcal / len(gluc_items)
            for it in gluc_items:
                k100, _, _, _ = db[it["food"]]
                if k100 <= 0: continue
                cap = FOOD_MAX_PORTION.get(it["food"], 350)
                add_g  = round(share / (k100 / 100.0))
                mn_g6  = FOOD_MIN_PORTION.get(it["food"], 20)
                new_g  = max(mn_g6, min(cap, it["g"] + add_g))
                if new_g == it["g"]: continue
                k, p, gc, l = _macros(it["food"], new_g)
                it.update({"g": new_g, "kcal": k, "p": p, "g_": gc, "l": l})
        else:
            # Pas de glucide ajustable → lipides en dernier recours
            lip_items = []
            for m in meals:
                if m["type"] == "coucher": continue
                for it in m["items"]:
                    if any(it["food"] in FOOD_CATS.get(c, []) for c in lip_cats):
                        lip_items.append(it)
            if not lip_items: break
            share = delta_kcal / len(lip_items)
            for it in lip_items:
                k100, _, _, _ = db[it["food"]]
                if k100 <= 0: continue
                cap = FOOD_MAX_PORTION.get(it["food"], 50)
                add_g  = round(share / (k100 / 100.0))
                mn_l6  = FOOD_MIN_PORTION.get(it["food"], 8)
                new_g  = max(mn_l6, min(cap, it["g"] + add_g))
                if new_g == it["g"]: continue
                k, p, gc, l = _macros(it["food"], new_g)
                it.update({"g": new_g, "kcal": k, "p": p, "g_": gc, "l": l})

    # ── Passe 7 : filet de sécurité anti-gaspillage ─────────────────────────
    # Parcourt TOUS les items après les 6 passes de correction macro.
    # Tout item dont la portion est < FOOD_MIN_PORTION est soit :
    #   - monté exactement au minimum (si catégorie lipide/condiment/oléagineux)
    #   - supprimé proprement (si catégorie protéine/fruit/légume/laitier)
    # On recalcule les macros de l'item ajusté.
    BUMP_UP_CATS  = {"lipide_sain","lipide_matin","lipide_collation",
                     "lipide_coucher","huile_cuisson","beurre_pain",
                     "sucrant_matin","fromage_dur"}  # → monter au min
    REMOVE_CATS   = {"proteine_maigre","proteine_grasse","proteine_midi",
                     "fruit","legume","laitier","laitier_lent","oeuf"}  # → supprimer

    for m in meals:
        to_remove = []
        for it in m["items"]:
            f, g = it["food"], it["g"]
            mn = FOOD_MIN_PORTION.get(f, 0)
            if mn <= 0 or g >= mn * 0.97:
                continue  # OK
            # Violation détectée — décider de l'action
            in_bump = any(f in FOOD_CATS.get(c,[]) for c in BUMP_UP_CATS)
            if in_bump:
                # Monter au minimum et recalculer les macros
                k100,p100,g100,l100 = db[f]
                r = mn / 100.0
                it.update({"g": mn,
                           "kcal": round(k100*r,1), "p": round(p100*r,1),
                           "g_":  round(g100*r,1),  "l": round(l100*r,1)})
            else:
                to_remove.append(it)
        for it in to_remove:
            m["items"].remove(it)

    # ── Finaliser ─────────────────────────────────────────────────────────────
    result = []
    for m in meals:
        items = m["items"]
        result.append({
            "name":    m["slot"]["name"],
            "type":    m["type"],
            "items":   items,
            "tot_cal": sum(i["kcal"] for i in items),
            "tot_p":   sum(i["p"]    for i in items),
            "tot_g":   sum(i["g_"]   for i in items),
            "tot_l":   sum(i["l"]    for i in items),
        })
    return result


def _generate_multiday_plan(n_days, n_meals, selected_foods,
                              cal_total, prot_total, gluc_total, lip_total,
                              start_date=None):
    """
    Génère n_days plans alimentaires avec variation quotidienne garantie.
    Retourne une liste de dicts {date, label, plan}.
    """
    import datetime as _dt
    if start_date is None:
        start_date = _dt.date.today()
    DAY_FR = ["Lundi","Mardi","Mercredi","Jeudi","Vendredi","Samedi","Dimanche"]
    plans = []
    for i in range(n_days):
        date = start_date + _dt.timedelta(days=i)
        plan = _generate_meal_plan(n_meals, selected_foods,
                                    cal_total, prot_total, gluc_total, lip_total,
                                    day_offset=i)
        plans.append({
            "date":  date,
            "label": f"{DAY_FR[date.weekday()]} {date:%d/%m/%Y}",
            "plan":  plan,
        })
    return plans


def render_plan_card(parent_frame, app, plan, cal, prot, gluc, lip,
                     n_meals=4, adj_lbl="", date_lbl=None, show_pdf=True,
                     days=None):
    """
    Affiche un plan alimentaire dans un frame existant.
    - Si `days` est fourni (plan semaine/mois) : navigation par onglets jour
      avec scroll horizontal gauche/droite, identique au générateur.
    - Sinon : plan journalier simple.
    Callable depuis dashboard, nutrition_module, générateur.
    """
    # Vider le frame
    for w in parent_frame.winfo_children():
        w.destroy()

    # ── Helpers internes ─────────────────────────────────────────────────────
    def _render_macro_header(frame, cur_plan, cur_cal, cur_prot, cur_gluc,
                              cur_lip, cur_n_meals, cur_adj, cur_date_lbl,
                              pdf_plan=None):
        """En-tête macros + bouton PDF pour un plan donné."""
        tc = sum(m["tot_cal"] for m in cur_plan)
        tp = sum(m["tot_p"]   for m in cur_plan)
        tg = sum(m["tot_g"]   for m in cur_plan)
        tl = sum(m["tot_l"]   for m in cur_plan)

        sc = mk_card(frame)
        sc.pack(fill="x", pady=(0,10))
        title_txt = f"  📋  {cur_date_lbl or 'PLAN'} — {cur_n_meals} repas / {cur_adj}"
        mk_title(sc, title_txt).pack(anchor="w", padx=16, pady=(14,0))
        mk_sep(sc).pack(fill="x", padx=16, pady=(4,8))

        trow = ctk.CTkFrame(sc, fg_color="transparent")
        trow.pack(fill="x", padx=16, pady=(0,12))
        for label, got, tgt, unit in [
            ("🔥 Calories",  tc, cur_cal,  "kcal"),
            ("🥩 Protéines", tp, cur_prot, "g"),
            ("🍚 Glucides",  tg, cur_gluc, "g"),
            ("🥑 Lipides",   tl, cur_lip,  "g"),
        ]:
            pct  = (got/tgt*100) if tgt > 0 else 0
            diff = abs(pct-100)
            clr  = TH.SUCCESS if diff<=5 else (TH.ACCENT_GLOW if diff<=12 else TH.DANGER)
            col  = ctk.CTkFrame(trow, fg_color=TH.BG_CARD2, corner_radius=8)
            col.pack(side="left", expand=True, fill="x", padx=5, pady=4)
            mk_label(col, label,              size="small", color=TH.TEXT_MUTED).pack(pady=(8,2))
            mk_label(col, f"{got:.0f} {unit}", size="h3",   color=clr).pack()
            mk_label(col, f"cible {tgt:.0f} ({pct:.0f}%)",
                     size="small", color=TH.TEXT_MUTED).pack(pady=(0,8))

        if show_pdf and pdf_plan:
            pr = ctk.CTkFrame(sc, fg_color="transparent")
            pr.pack(fill="x", padx=16, pady=(0,10))
            def _epdf(p=pdf_plan):
                try:
                    from data import pdf_utils as _pu
                    _pu.export_meal_plan_pdf(app, p, ask_path=True)
                except Exception as ex:
                    from tkinter import messagebox as _mb
                    _mb.showerror("ERAGROK", f"PDF : {ex}")
            mk_btn(pr, "📄  Exporter PDF", _epdf,
                   color="#1a1a2e", hover="#252540",
                   width=150, height=TH.BTN_SM).pack(side="right")

    def _render_meals(frame, cur_plan):
        """Cartes repas détaillées pour un plan donné."""
        for meal in cur_plan:
            mc = mk_card(frame)
            mc.pack(fill="x", pady=(0,8))
            hdr = ctk.CTkFrame(mc, fg_color="transparent")
            hdr.pack(fill="x", padx=16, pady=(12,0))
            lh  = ctk.CTkFrame(hdr, fg_color="transparent")
            lh.pack(side="left", fill="x", expand=True)
            mk_label(lh, meal["name"].strip(), size="body", color=TH.ACCENT_GLOW).pack(anchor="w")
            mk_label(lh, SLOT_DESC.get(meal["type"],""),
                     size="small", color=TH.TEXT_MUTED).pack(anchor="w")
            mk_label(hdr,
                     f"{meal['tot_cal']:.0f} kcal\n"
                     f"{meal['tot_p']:.0f}P · {meal['tot_g']:.0f}G · {meal['tot_l']:.0f}L",
                     size="small", color=TH.TEXT_SUB).pack(side="right", anchor="e")
            mk_sep(mc).pack(fill="x", padx=16, pady=(6,4))

            if not meal["items"]:
                mk_label(mc, "  ⚠️  Aucun aliment pour ce repas.",
                         size="small", color=TH.DANGER).pack(padx=20, pady=(0,10))
                continue

            for item in meal["items"]:
                ir = ctk.CTkFrame(mc, fg_color="transparent")
                ir.pack(fill="x", padx=24, pady=2)
                ctk.CTkFrame(ir, fg_color=TH.ACCENT_GLOW,
                             width=6, height=6, corner_radius=3).pack(side="left", padx=(0,8))
                mk_label(ir, item["food"], size="body", color=TH.TEXT).pack(side="left")
                mk_label(ir,
                         f"{item['g']:.0f}g → {item['kcal']:.0f}kcal | "
                         f"{item['p']:.1f}P  {item['g_']:.1f}G  {item['l']:.1f}L",
                         size="body", color=TH.TEXT_MUTED).pack(side="right")
            ctk.CTkFrame(mc, fg_color="transparent", height=6).pack()

    # ══════════════════════════════════════════════════════════════════════════
    # CAS 1 : plan multi-jours → navigation par onglets
    # ══════════════════════════════════════════════════════════════════════════
    if days and len(days) > 1:
        n_days   = len(days)
        avg_cal  = sum(sum(m["tot_cal"] for m in d["plan"]) for d in days) / n_days
        avg_prot = sum(sum(m["tot_p"]   for m in d["plan"]) for d in days) / n_days
        avg_gluc = sum(sum(m["tot_g"]   for m in d["plan"]) for d in days) / n_days
        avg_lip  = sum(sum(m["tot_l"]   for m in d["plan"]) for d in days) / n_days

        # En-tête global moyennes
        mode_lbl = "Semaine" if n_days == 7 else f"{n_days} jours"
        hdr_card = mk_card(parent_frame)
        hdr_card.pack(fill="x", pady=(0,8))
        mk_title(hdr_card,
                 f"  📅  PLAN {mode_lbl.upper()} — {n_meals} repas/j — {adj_lbl}").pack(
            anchor="w", padx=16, pady=(14,0))
        mk_sep(hdr_card).pack(fill="x", padx=16, pady=(4,8))

        trow = ctk.CTkFrame(hdr_card, fg_color="transparent")
        trow.pack(fill="x", padx=16, pady=(0,8))
        for label, got, tgt, unit in [
            ("🔥 Cal. moy.",  avg_cal,  cal,  "kcal"),
            ("🥩 Prot. moy.", avg_prot, prot, "g"),
            ("🍚 Gluc. moy.", avg_gluc, gluc, "g"),
            ("🥑 Lip. moy.",  avg_lip,  lip,  "g"),
        ]:
            pct  = (got/tgt*100) if tgt > 0 else 0
            diff = abs(pct-100)
            clr  = TH.SUCCESS if diff<=5 else (TH.ACCENT_GLOW if diff<=12 else TH.DANGER)
            col  = ctk.CTkFrame(trow, fg_color=TH.BG_CARD2, corner_radius=8)
            col.pack(side="left", expand=True, fill="x", padx=5, pady=4)
            mk_label(col, label,              size="small", color=TH.TEXT_MUTED).pack(pady=(6,1))
            mk_label(col, f"{got:.0f} {unit}", size="body",  color=clr).pack()
            mk_label(col, f"/{tgt:.0f} ({pct:.0f}%)",
                     size="small", color=TH.TEXT_MUTED).pack(pady=(0,6))

        # Bouton PDF global
        if show_pdf:
            pr = ctk.CTkFrame(hdr_card, fg_color="transparent")
            pr.pack(fill="x", padx=16, pady=(0,10))
            def _epdf_multi(d=days):
                try:
                    from data import pdf_utils as _pu
                    _pu.export_multiday_plan_pdf(app, d, ask_path=True)
                except Exception as ex:
                    from tkinter import messagebox as _mb
                    _mb.showerror("ERAGROK", f"PDF : {ex}")
            mk_btn(pr, "📄  Exporter PDF complet", _epdf_multi,
                   color=TH.ACCENT, hover=TH.ACCENT_HOVER,
                   width=200, height=TH.BTN_SM).pack(side="right")

        # ── Barre d'onglets jours (scroll horizontal) ─────────────────────────
        tab_outer = ctk.CTkFrame(parent_frame, fg_color="transparent")
        tab_outer.pack(fill="x", pady=(0,6))
        tab_scroll = ctk.CTkScrollableFrame(tab_outer,
                                             fg_color=TH.BG_CARD2,
                                             height=48,
                                             orientation="horizontal",
                                             scrollbar_button_color=TH.BORDER,
                                             scrollbar_button_hover_color=TH.ACCENT)
        tab_scroll.pack(fill="x")

        # Zone affichage du jour sélectionné
        day_frame = ctk.CTkFrame(parent_frame, fg_color="transparent")
        day_frame.pack(fill="both", expand=True)

        tab_btns = []
        # ── Onglets Jour 1 … Jour N + Total ─────────────────────────────────
        # active_tab_var : -1 = Total, 0…n-1 = jour individuel
        active_tab_var = tk.IntVar(value=0)

        def _highlight_tabs(active_idx):
            """Met à jour couleurs de tous les onglets."""
            for i2, btn in enumerate(tab_btns):
                is_active = (i2 == active_idx + 1)  # +1 car [Total, J1, J2, ...]
                btn.configure(
                    fg_color   = TH.ACCENT    if is_active else TH.BG_CARD,
                    text_color = TH.TEXT      if is_active else TH.TEXT_MUTED,
                )
            # Le bouton Total est tab_btns[0]
            tab_btns[0].configure(
                fg_color   = TH.ACCENT    if active_idx == -1 else TH.BG_CARD,
                text_color = TH.TEXT      if active_idx == -1 else TH.TEXT_MUTED,
            )

        def _show_total():
            active_tab_var.set(-1)
            _highlight_tabs(-1)
            for w in day_frame.winfo_children(): w.destroy()
            # Résumé : stats moyennes sur tous les jours
            all_plans = [d["plan"] for d in days]
            avg_cal  = sum(sum(m["tot_cal"] for m in p) for p in all_plans) / n_days
            avg_prot = sum(sum(m["tot_p"]   for m in p) for p in all_plans) / n_days
            avg_gluc = sum(sum(m["tot_g"]   for m in p) for p in all_plans) / n_days
            avg_lip  = sum(sum(m["tot_l"]   for m in p) for p in all_plans) / n_days
            # Bloc résumé visuel
            sum_card = mk_card(day_frame)
            sum_card.pack(fill="x", pady=(0,10))
            mk_title(sum_card, f"  📊  RÉSUMÉ — {n_days} JOURS").pack(
                anchor="w", padx=16, pady=(14,4))
            mk_sep(sum_card).pack(fill="x", padx=16, pady=(0,8))
            trow = ctk.CTkFrame(sum_card, fg_color="transparent")
            trow.pack(fill="x", padx=16, pady=(0,10))
            for label, got, tgt, unit in [
                ("🔥 Cal. moy.",  avg_cal,  cal,  "kcal"),
                ("🥩 Prot. moy.", avg_prot, prot, "g"),
                ("🍚 Gluc. moy.", avg_gluc, gluc, "g"),
                ("🥑 Lip. moy.",  avg_lip,  lip,  "g"),
            ]:
                pct  = (got/tgt*100) if tgt > 0 else 0
                diff = abs(pct-100)
                clr  = TH.SUCCESS if diff<=5 else (TH.ACCENT_GLOW if diff<=12 else TH.DANGER)
                col  = ctk.CTkFrame(trow, fg_color=TH.BG_CARD2, corner_radius=8)
                col.pack(side="left", expand=True, fill="x", padx=5, pady=4)
                mk_label(col, label,              size="small", color=TH.TEXT_MUTED).pack(pady=(6,1))
                mk_label(col, f"{got:.0f} {unit}", size="body",  color=clr).pack()
                mk_label(col, f"/{tgt:.0f} ({pct:.0f}%)",
                         size="small", color=TH.TEXT_MUTED).pack(pady=(0,6))
            # Liste des jours avec leurs totaux
            for d in days:
                p = d["plan"]
                tc = sum(m["tot_cal"] for m in p)
                tp = sum(m["tot_p"]   for m in p)
                row = ctk.CTkFrame(day_frame, fg_color=TH.BG_CARD2, corner_radius=6)
                row.pack(fill="x", padx=4, pady=2)
                mk_label(row, d["label"], size="small", color=TH.TEXT_SUB,
                         width=160).pack(side="left", padx=10, pady=6)
                mk_label(row, f"{tc:.0f} kcal", size="small", color=TH.ACCENT_GLOW,
                         width=90).pack(side="left")
                mk_label(row, f"{tp:.0f}g prot", size="small", color=TH.TEXT_MUTED,
                         width=90).pack(side="left")

        def _show_day(day_idx):
            active_tab_var.set(day_idx)
            _highlight_tabs(day_idx)
            for w in day_frame.winfo_children(): w.destroy()
            d = days[day_idx]
            _render_macro_header(day_frame, d["plan"],
                                 cal, prot, gluc, lip,
                                 n_meals, adj_lbl, d["label"],
                                 pdf_plan=d["plan"])
            _render_meals(day_frame, d["plan"])

        # Bouton Total en premier
        btn_total = mk_btn(tab_scroll, "📊\nTotal",
                           _show_total,
                           color=TH.BG_CARD, hover=TH.BG_CARD2,
                           width=54, height=44)
        btn_total.pack(side="left", padx=(2,6), pady=2)
        tab_btns.append(btn_total)

        # Boutons Jour 1 … Jour N
        for i, d in enumerate(days):
            num  = d["date"].strftime("%d/%m")
            lbl  = f"J{i+1}\n{num}"
            btn  = mk_btn(tab_scroll, lbl,
                          lambda idx=i: _show_day(idx),
                          color=TH.BG_CARD, hover=TH.BG_CARD2,
                          width=52, height=44)
            btn.pack(side="left", padx=2, pady=2)
            tab_btns.append(btn)

        # Afficher le premier jour par défaut
        _show_day(0)
        return

    # ══════════════════════════════════════════════════════════════════════════
    # CAS 2 : plan 1 jour — affichage simple
    # ══════════════════════════════════════════════════════════════════════════
    if not plan:
        mk_label(parent_frame,
                 "  Aucun plan — génère un plan depuis le générateur.",
                 size="small", color=TH.TEXT_MUTED).pack(anchor="w", padx=16, pady=20)
        return

    _render_macro_header(parent_frame, plan, cal, prot, gluc, lip,
                         n_meals, adj_lbl, date_lbl, pdf_plan=plan)
    _render_meals(parent_frame, plan)



def _apply_budget_pass(plan: list, selected: list, budget_day: float, app) -> list:
    """
    Passe post-génération : ajuste le plan pour respecter le budget journalier.

    Stratégie :
      1. Calculer coût estimé du plan via prices_module
      2. Si coût <= budget → rien à faire
      3. Si dépassement → remplacer les items les plus chers par des alternatives
         de même catégorie macro (protéine/glucide/lipide) mais moins chers
      4. Réduire les portions des aliments onéreux si aucune alternative dispo
      5. Maxi 6 passes pour converger
    """
    import copy

    try:
        from data.prices_module import get_prices, compute_shopping_cost
        from data.features_module import FOOD_DB_EXT, FOOD_CATS, FOOD_INCOMPATIBLE
    except Exception:
        return plan   # pas de module prix → plan inchangé

    prices  = get_prices(app)

    def _day_cost(p):
        """Coût estimé d'un plan journée (liste de meals)."""
        total = 0.0
        for meal in p:
            for item in meal.get("items", []):
                food  = item.get("food", "")
                grams = item.get("g", item.get("grams", 0))   # "g" = clé standard
                pi    = prices.get(food)
                if not pi or not pi.get("prix_kg"): continue
                unite = pi.get("unite","kg")
                pxkg  = pi["prix_kg"]
                if unite == "unite":
                    n = max(1, round(grams / (60 if "Oeuf" in food else 35)))
                    total += n * pxkg
                else:
                    total += (grams / 1000) * pxkg
        return total

    # ── Construire index aliment → catégorie macro ────────────────────────────
    MACRO_CAT = {}   # food → "proteine" | "glucide" | "lipide" | "other"
    PROT_CATS = {"oeuf","proteine_maigre","proteine_grasse","laitier","laitier_lent","whey","supplement_lent"}
    GLUC_CATS = {"glucide_matin","glucide_midi","fruit"}
    LIP_CATS  = {"lipide_sain"}
    for cat, foods in FOOD_CATS.items():
        for f in foods:
            if cat in PROT_CATS:   MACRO_CAT[f] = "proteine"
            elif cat in GLUC_CATS: MACRO_CAT[f] = "glucide"
            elif cat in LIP_CATS:  MACRO_CAT[f] = "lipide"
            else:                  MACRO_CAT[f] = "other"

    # ── Classer les aliments sélectionnés par prix croissant par macro ────────
    def _sorted_by_price(macro: str) -> list:
        """Aliments selected de cette macro-catégorie, du moins au plus cher."""
        foods_macro = [f for f in selected if MACRO_CAT.get(f) == macro]
        def _px(f):
            pi = prices.get(f)
            if not pi: return 999
            # €/100g pour comparer
            pxkg = pi.get("prix_kg", 999)
            if pi.get("unite") == "unite":
                return pxkg * 0.6  # prix d'un oeuf ~60g
            return pxkg / 10
        return sorted(foods_macro, key=_px)

    # Pré-calculer alternatives moins chères par macro
    cheap_prot  = _sorted_by_price("proteine")
    cheap_gluc  = _sorted_by_price("glucide")
    cheap_lip   = _sorted_by_price("lipide")
    CHEAP_BY_MACRO = {"proteine": cheap_prot, "glucide": cheap_gluc,
                       "lipide": cheap_lip, "other": []}

    def _item_cost_per_g(food: str) -> float:
        pi = prices.get(food)
        if not pi or not pi.get("prix_kg"): return 0.0
        pxkg  = pi["prix_kg"]
        unite = pi.get("unite","kg")
        if unite == "unite":
            g_per_unit = 60 if "Oeuf" in food else 35
            return pxkg / g_per_unit
        return pxkg / 1000

    plan = copy.deepcopy(plan)

    for _pass in range(6):
        cost = _day_cost(plan)
        if cost <= budget_day * 1.05:   # tolérance 5%
            break

        overshoot = cost - budget_day
        if overshoot <= 0.10:
            break

        # Trouver l'item le plus cher du plan (hors coucher — on préserve protéine lente)
        most_expensive = None
        max_cost_item  = 0.0
        meal_idx = item_idx = -1

        for mi, meal in enumerate(plan):
            if meal.get("slot","") == "coucher":
                continue
            for ii, item in enumerate(meal.get("items",[])):
                food  = item.get("food","")
                grams = item.get("g", item.get("grams", 0))   # clé standard "g"
                ic    = _item_cost_per_g(food) * grams
                if ic > max_cost_item:
                    max_cost_item  = ic
                    most_expensive = item
                    meal_idx, item_idx = mi, ii

        if most_expensive is None or meal_idx < 0:
            break

        food_exp  = most_expensive["food"]
        grams_exp = most_expensive.get("g", most_expensive.get("grams", 100))
        macro_exp = MACRO_CAT.get(food_exp, "other")

        # Chercher alternative moins chère de même macro
        alternatives = [f for f in CHEAP_BY_MACRO.get(macro_exp, [])
                        if f != food_exp and f in selected]

        if alternatives:
            # Prendre la moins chère
            new_food  = alternatives[0]
            new_nutr  = FOOD_DB_EXT.get(new_food)
            if new_nutr:
                nk, np, ng, nl = new_nutr
                # Ajuster les grammes pour maintenir les protéines
                old_nutr = FOOD_DB_EXT.get(food_exp)
                if old_nutr and old_nutr[1] > 0 and np > 0:
                    # Conserver les protéines : new_g = old_g × (old_p / new_p)
                    new_grams = round(grams_exp * (old_nutr[1] / np) / 10) * 10
                    new_grams = max(50, min(new_grams, FOOD_MAX_PORTION.get(new_food, 300)))
                else:
                    new_grams = grams_exp
                # Recalculer macros item
                new_grams = max(30, new_grams)
                factor = new_grams / 100
                plan[meal_idx]["items"][item_idx] = {
                    "food": new_food,
                    "g":    new_grams,      # clé standard identique au générateur
                    "kcal": round(nk * factor, 1),
                    "p":    round(np * factor, 1),
                    "g_":   round(ng * factor, 1),  # glucides (g_ pour éviter clash avec g=grams)
                    "l":    round(nl * factor, 1),
                }
                # Recalculer totaux du repas
                meal = plan[meal_idx]
                meal["tot_cal"] = round(sum(it["kcal"] for it in meal["items"]))
                meal["tot_p"]   = round(sum(it["p"]    for it in meal["items"]), 1)
                meal["tot_g"]   = round(sum(it["g"]    for it in meal["items"]), 1)
                meal["tot_l"]   = round(sum(it["l"]    for it in meal["items"]), 1)
        else:
            # Aucune alternative → réduire la portion de 15%
            # mais jamais sous FOOD_MIN_PORTION — sinon supprimer l'aliment
            min_g     = FOOD_MIN_PORTION.get(food_exp, 10)
            new_grams = max(min_g, round(grams_exp * 0.85 / 10) * 10)
            old_nutr  = FOOD_DB_EXT.get(food_exp)
            if old_nutr:
                nk, np, ng, nl = old_nutr
                if new_grams < min_g or new_grams <= 0:
                    # Supprimer cet item plutôt que servir une portion ridicule
                    plan[meal_idx]["items"].pop(item_idx)
                else:
                    factor = new_grams / 100
                    plan[meal_idx]["items"][item_idx].update({
                        "g":    new_grams,
                        "kcal": round(nk * factor, 1),
                        "p":    round(np * factor, 1),
                        "g_":   round(ng * factor, 1),
                        "l":    round(nl * factor, 1),
                    })
                meal = plan[meal_idx]
                meal["tot_cal"] = round(sum(it["kcal"] for it in meal["items"]))
                meal["tot_p"]   = round(sum(it["p"]    for it in meal["items"]), 1)
                meal["tot_g"]   = round(sum(it["g"]    for it in meal["items"]), 1)
                meal["tot_l"]   = round(sum(it["l"]    for it in meal["items"]), 1)

    return plan


def show_meal_generator(app):
    """Générateur de plan — jour / semaine / mois, variation quotidienne garantie."""
    import datetime as _dt
    from data import utils, db as _db

    for w in app.content.winfo_children():
        w.destroy()

    from data.theme import screen_header, mk_scrollframe
    screen_header(app.content, "🍽  PLAN ALIMENTAIRE",
                  user_name=getattr(app, "selected_user_name", ""),
                  back_cmd=app.show_dashboard)

    outer = mk_scrollframe(app.content)
    outer.pack(fill="both", expand=True)

    body = ctk.CTkFrame(outer, fg_color="transparent")
    body.pack(fill="both", expand=True, padx=24, pady=20)
    body.columnconfigure(0, weight=0)
    body.columnconfigure(1, weight=1)

    # ══════════════════════════════════════════════════════════════════════════
    # PANNEAU GAUCHE — réglages
    # ══════════════════════════════════════════════════════════════════════════
    left = mk_card(body)
    left.grid(row=0, column=0, sticky="nsew", padx=(0, 14))

    mk_title(left, "  ⚙️  RÉGLAGES").pack(anchor="w", padx=16, pady=(14,6))
    mk_sep(left).pack(fill="x", padx=16, pady=(0,10))

    # ── Objectif (lecture seule) ──────────────────────────────────────────────
    ui  = getattr(app, "user_info", None) or {}
    obj = ui.get("objectif", "—")
    adj_label = getattr(app, "adjustment_var", None)
    adj_txt   = (adj_label.get() if adj_label else None) or ui.get("ajustement","Maintien (0%)")
    obj_frame = mk_card2(left)
    obj_frame.pack(fill="x", padx=12, pady=(0,10))
    mk_label(obj_frame, "  Objectif profil", size="small",
             color=TH.TEXT_MUTED).pack(anchor="w", padx=8, pady=(6,2))
    mk_label(obj_frame, f"  🎯  {obj}  —  {adj_txt}",
             size="body", color=TH.ACCENT_GLOW).pack(anchor="w", padx=8, pady=(0,6))

    # ── Nombre de repas / jour ────────────────────────────────────────────────
    mk_label(left, "Repas par jour", size="small",
             color=TH.TEXT_SUB).pack(anchor="w", padx=16, pady=(0,4))
    n_meals_var = tk.IntVar(value=4)
    n_frame = ctk.CTkFrame(left, fg_color="transparent")
    n_frame.pack(anchor="w", padx=16, pady=(0,10))
    for n in [3, 4, 5, 6]:
        ctk.CTkRadioButton(
            n_frame, text=str(n), value=n, variable=n_meals_var,
            fg_color=TH.ACCENT, hover_color=TH.ACCENT_HOVER,
            text_color=TH.TEXT, font=TH.F_SMALL,
        ).pack(side="left", padx=6)

    mk_sep(left).pack(fill="x", padx=16, pady=(0,8))

    # ── Mode de génération ────────────────────────────────────────────────────
    mk_label(left, "Mode de génération", size="small",
             color=TH.TEXT_SUB).pack(anchor="w", padx=16, pady=(0,4))
    gen_mode_var = tk.StringVar(value="jour")
    mode_frame   = ctk.CTkFrame(left, fg_color="transparent")
    mode_frame.pack(anchor="w", padx=16, pady=(0,8))
    for lbl, val in [("1 jour","jour"), ("Semaine (7j)","semaine"), ("Mois (30j)","mois")]:
        ctk.CTkRadioButton(
            mode_frame, text=lbl, value=val, variable=gen_mode_var,
            fg_color=TH.ACCENT, hover_color=TH.ACCENT_HOVER,
            text_color=TH.TEXT, font=TH.F_SMALL,
        ).pack(anchor="w", pady=2)

    # ── Budget hebdomadaire (optionnel) ──────────────────────────────────────
    mk_sep(left).pack(fill="x", padx=16, pady=(4,8))

    budget_header = ctk.CTkFrame(left, fg_color="transparent")
    budget_header.pack(fill="x", padx=16, pady=(0,4))
    mk_label(budget_header, "💰  Budget / semaine  ",
             size="small", color=TH.TEXT_SUB).pack(side="left")
    mk_label(budget_header, "optionnel",
             size="small", color=TH.TEXT_MUTED).pack(side="left")

    budget_frame = ctk.CTkFrame(left, fg_color=TH.BG_CARD2, corner_radius=8)
    budget_frame.pack(fill="x", padx=12, pady=(0,4))

    budget_inner = ctk.CTkFrame(budget_frame, fg_color="transparent")
    budget_inner.pack(fill="x", padx=10, pady=8)

    budget_var = tk.StringVar(value="")

    budget_entry = ctk.CTkEntry(
        budget_inner,
        textvariable=budget_var,
        placeholder_text="ex: 80",
        width=90, height=32,
        fg_color=TH.BG_INPUT,
        text_color=TH.TEXT,
        placeholder_text_color=TH.TEXT_MUTED,
        border_color=TH.BORDER,
        font=TH.F_BODY,
    )
    budget_entry.pack(side="left")
    mk_label(budget_inner, "  € / semaine",
             size="body", color=TH.ACCENT).pack(side="left", padx=(4,12))

    # Indicateur budget/jour recalculé dynamiquement
    budget_day_var = tk.StringVar(value="")
    budget_day_lbl = mk_label(budget_inner, "",
                              size="small", color=TH.TEXT_MUTED)
    budget_day_lbl.pack(side="left")

    def _update_budget_display(*_):
        raw = budget_var.get().strip().replace(",",".")
        try:
            b = float(raw)
            if b > 0:
                budget_day_var.set(f"≈ {b/7:.2f} €/j")
                budget_day_lbl.configure(text=f"≈ {b/7:.2f} €/j",
                                          text_color=TH.SUCCESS)
            else:
                budget_day_lbl.configure(text="", text_color=TH.TEXT_MUTED)
        except Exception:
            budget_day_lbl.configure(text="", text_color=TH.TEXT_MUTED)

    budget_var.trace_add("write", _update_budget_display)

    # Boutons rapides
    presets_row = ctk.CTkFrame(budget_frame, fg_color="transparent")
    presets_row.pack(fill="x", padx=10, pady=(0,8))
    for preset in [50, 70, 80, 100, 120]:
        def _set_preset(v=preset):
            budget_var.set(str(v))
        ctk.CTkButton(
            presets_row, text=f"{preset}€",
            command=_set_preset,
            fg_color=TH.BG_CARD, hover_color=TH.ACCENT,
            text_color=TH.TEXT_MUTED, font=TH.F_SMALL,
            width=44, height=24, corner_radius=6,
        ).pack(side="left", padx=2)
    def _clear_budget():
        budget_var.set("")
        budget_day_lbl.configure(text="")
    mk_btn(presets_row, "✕", _clear_budget,
           color=TH.BG_ROOT, hover=TH.GRAY,
           width=28, height=24).pack(side="right", padx=2)

    mk_sep(left).pack(fill="x", padx=16, pady=(4,8))

    # ── Date de début ─────────────────────────────────────────────────────────
    mk_label(left, "Date de début", size="small",
             color=TH.TEXT_SUB).pack(anchor="w", padx=16, pady=(0,4))
    date_row = ctk.CTkFrame(left, fg_color="transparent")
    date_row.pack(fill="x", padx=16, pady=(0,10))
    date_var = tk.StringVar(value=_dt.date.today().strftime("%d/%m/%Y"))
    date_entry = ctk.CTkEntry(date_row, textvariable=date_var,
                              width=120, height=30,
                              fg_color=TH.BG_INPUT, text_color=TH.TEXT,
                              border_color=TH.BORDER, font=TH.F_SMALL)
    date_entry.pack(side="left")
    mk_label(date_row, "  jj/mm/aaaa", size="small",
             color=TH.TEXT_MUTED).pack(side="left", padx=4)
    def _set_today():
        date_var.set(_dt.date.today().strftime("%d/%m/%Y"))
    mk_btn(date_row, "Auj.", _set_today,
           color=TH.GRAY, hover=TH.GRAY_HVR,
           width=50, height=28).pack(side="left", padx=4)

    mk_sep(left).pack(fill="x", padx=16, pady=(0,8))

    # ── Légende timing ────────────────────────────────────────────────────────
    legend = mk_card2(left)
    legend.pack(fill="x", padx=12, pady=(0,8))
    mk_label(legend, "  📌  Timing & compatibilité",
             size="small", color=TH.TEXT_MUTED).pack(anchor="w", padx=8, pady=(6,2))
    icons = {"matin":"🌅","midi":"☀️","collation":"🍎","soir":"🌙","coucher":"🌛"}
    for slot, desc in SLOT_DESC.items():
        r = ctk.CTkFrame(legend, fg_color="transparent")
        r.pack(fill="x", padx=8, pady=1)
        mk_label(r, f"{icons[slot]} {slot.capitalize()}",
                 size="small", color=TH.ACCENT_GLOW, width=90).pack(side="left")
        mk_label(r, desc, size="small", color=TH.TEXT_MUTED).pack(side="left", padx=4)
    mk_label(legend, "  ⚠️  Les aliments incompatibles sont\n"
                     "       automatiquement séparés.",
             size="small", color=TH.TEXT_MUTED).pack(anchor="w", padx=8, pady=(4,6))

    mk_sep(left).pack(fill="x", padx=16, pady=(0,8))

    # ── Sélection aliments ────────────────────────────────────────────────────
    mk_label(left, "Tes aliments disponibles", size="small",
             color=TH.TEXT_SUB).pack(anchor="w", padx=16, pady=(0,4))

    chk_vars    = {}
    foods_scroll = mk_scrollframe(left)
    foods_scroll.pack(fill="x", padx=8, pady=(0,8))
    foods_scroll.configure(height=340)

    DISPLAY_CATS = [
        ("🥚  Œufs",              ["oeuf"]),
        ("🥛  Laitiers",          ["laitier", "laitier_lent"]),
        ("💊  Suppléments",       ["whey", "supplement_lent"]),
        ("🍗  Protéines maigres", ["proteine_maigre"]),
        ("🥩  Protéines grasses", ["proteine_grasse"]),
        ("🥣  Glucides matin",    ["glucide_matin"]),
        ("🍚  Glucides repas",    ["glucide_midi"]),
        ("🍌  Fruits",            ["fruit"]),
        ("🥦  Légumes",           ["legume"]),
        ("🥑  Lipides sains",     ["lipide_sain"]),
    ]
    seen = set()
    for cat_lbl, cats in DISPLAY_CATS:
        foods_in = []
        for c in cats:
            for f in FOOD_CATS.get(c, []):
                if f not in seen and f in FOOD_DB_EXT:
                    foods_in.append(f); seen.add(f)
        if not foods_in: continue

        ch = ctk.CTkFrame(foods_scroll, fg_color=TH.BG_CARD2, corner_radius=4)
        ch.pack(fill="x", padx=8, pady=(5,1))
        mk_label(ch, cat_lbl, size="small",
                 color=TH.TEXT_MUTED).pack(anchor="w", padx=8, pady=3)

        for food in foods_in:
            k,p,g,l = FOOD_DB_EXT[food]
            var = tk.BooleanVar(value=False)
            chk_vars[food] = var
            rf = ctk.CTkFrame(foods_scroll, fg_color="transparent")
            rf.pack(fill="x", padx=8, pady=1)
            ctk.CTkCheckBox(
                rf, text=food, variable=var,
                fg_color=TH.ACCENT, hover_color=TH.ACCENT_HOVER,
                text_color=TH.TEXT, font=TH.F_SMALL,
                checkmark_color="#000", width=22, height=22,
            ).pack(side="left")
            mk_label(rf, f"{p:.0f}P/{g:.0f}G/{l:.0f}L",
                     size="small", color=TH.TEXT_MUTED).pack(side="right", padx=8)

    qrow = ctk.CTkFrame(left, fg_color="transparent")
    qrow.pack(fill="x", padx=12, pady=(2,0))
    mk_btn(qrow, "☑  Tout cocher",
           lambda: [v.set(True) for v in chk_vars.values()],
           color=TH.ACCENT, hover=TH.ACCENT_HOVER,
           width=130, height=TH.BTN_SM).pack(side="left", padx=4, pady=6)
    mk_btn(qrow, "Tout décocher",
           lambda: [v.set(False) for v in chk_vars.values()],
           color=TH.GRAY, hover=TH.GRAY_HVR,
           width=130, height=TH.BTN_SM).pack(side="right", padx=4, pady=6)

    mk_sep(left).pack(fill="x", padx=16, pady=(4,0))
    mk_btn(left, "⚡  GÉNÉRER",
           lambda: _run_gen(),
           color=TH.ACCENT, hover=TH.ACCENT_HOVER,
           width=240, height=TH.BTN_LG).pack(pady=(14, 4))

    # Zone bouton Accepter — visible uniquement après génération
    accept_zone = ctk.CTkFrame(left, fg_color="transparent")
    accept_zone.pack(fill="x", padx=16, pady=(0, 10))

    # ══════════════════════════════════════════════════════════════════════════
    # PANNEAU DROIT — résultats
    # ══════════════════════════════════════════════════════════════════════════
    right_scroll = mk_scrollframe(body)
    right_scroll.grid(row=0, column=1, sticky="nsew")

    result_frame = ctk.CTkFrame(right_scroll, fg_color="transparent")
    result_frame.pack(fill="both", expand=True)

    ph = mk_card(result_frame)
    ph.pack(fill="x", pady=(0,14))
    mk_label(ph, "  📌  Coche tes aliments → choisis le mode → GÉNÉRER.",
             size="body", color=TH.TEXT_MUTED).pack(padx=16, pady=24)

    # ── Helper : calcul macros depuis profil ──────────────────────────────────
    def _get_macros():
        try:
            dn    = ui.get("date_naissance","")
            age   = str(utils.age_depuis_naissance(dn) or ui.get("age") or "30")
            pv    = getattr(app, "poids_var", None)
            poids = (pv.get().strip() if pv else "") or str(ui.get("poids") or "80")
            nut   = utils.calculs_nutrition(poids, age, ui.get("sexe"),
                                             ui.get("objectif"), ui.get("taille"))
            av  = getattr(app, "adjustment_var", None)
            adj = utils.ADJUSTMENTS.get(
                (av.get() if av else "") or "Maintien (0%)", 0.0)
            cal  = (nut["tdee"]*(1+adj)) if nut else 2500
            obj_l = ui.get("objectif","").lower()
            if "masse"   in obj_l: cp, fp = 0.47, 0.23
            elif "perte" in obj_l: cp, fp = 0.37, 0.23
            else:                   cp, fp = 0.45, 0.25
            prot = nut["proteines"] if nut else cal*0.30/4
            gluc = (cal*cp)/4
            lip  = (cal*fp)/9
            return cal, prot, gluc, lip
        except Exception:
            return 2500, 180, 280, 70

    # ── Restaure dernier plan ─────────────────────────────────────────────────
    def _restore_last_plan():
        last = getattr(app, "_last_meal_plan", None)
        if not last: return
        try:
            if last.get("multiday"):
                _render_multiday(result_frame, last["days"],
                                 last["n_meals"], last["adj"],
                                 last["cal"], last["prot"], last["gluc"], last["lip"])
            else:
                plan = last["plan"]
                tc = sum(m["tot_cal"] for m in plan)
                tp = sum(m["tot_p"]   for m in plan)
                tg = sum(m["tot_g"]   for m in plan)
                tl = sum(m["tot_l"]   for m in plan)
                _render_plan(result_frame, plan, last["n_meals"], last["adj"],
                             tc, tp, tg, tl,
                             last["cal"], last["prot"], last["gluc"], last["lip"])
        except Exception:
            pass

    # ── Bouton Accepter conditionnel (affiché après génération) ─────────────
    def _show_accept_btn():
        """Affiche le bouton Accepter dans accept_zone après génération."""
        for w in accept_zone.winfo_children(): w.destroy()

        def _do_accept():
            lp = getattr(app, "_last_meal_plan", None)
            if lp: lp["accepted"] = True
            # Sauvegarder dans historique
            try:
                days_lp = lp.get("days") if lp else None
                plan_lp = lp.get("plan") if lp else None
                tc = tp = tg = tl = 0
                if plan_lp:
                    tc = sum(m["tot_cal"] for m in plan_lp)
                    tp = sum(m["tot_p"]   for m in plan_lp)
                    tg = sum(m["tot_g"]   for m in plan_lp)
                    tl = sum(m["tot_l"]   for m in plan_lp)
                elif days_lp:
                    n = len(days_lp)
                    tc = sum(sum(m["tot_cal"] for m in d["plan"]) for d in days_lp) / n
                    tp = sum(sum(m["tot_p"]   for m in d["plan"]) for d in days_lp) / n
                    tg = sum(sum(m["tot_g"]   for m in d["plan"]) for d in days_lp) / n
                    tl = sum(sum(m["tot_l"]   for m in d["plan"]) for d in days_lp) / n
                import datetime as _dt2
                ui2   = getattr(app, "user_info", None) or {}
                dn2   = ui2.get("date_naissance", "")
                age_s = str(utils.age_depuis_naissance(dn2) or ui2.get("age") or "")
                pv2   = getattr(app, "poids_var", None)
                pw    = pv2.get().strip().replace(",",".") if pv2 else str(ui2.get("poids",""))
                n_m   = lp.get("n_meals", 4) if lp else 4
                _db.nutrition_insert(app, _dt2.date.today().strftime("%d/%m/%Y"),
                    pw, age_s, str(round(tc)), str(round(tp)),
                    str(round(tg)), str(round(tl)),
                    f"Plan alimentaire — {n_m} repas")
                from tkinter import messagebox as _mb2
                _mb2.showinfo("ERAGROK", "✅ Plan accepté et enregistré.")
            except Exception as _ex:
                pass
            try:
                from data import nutrition_module as _nm
                _nm.show_nutrition_screen(app)
            except Exception: pass

        mk_btn(accept_zone, "✅  ACCEPTER LE PLAN",
               _do_accept,
               color=TH.SUCCESS, hover=TH.SUCCESS_HVR,
               width=240, height=TH.BTN_LG).pack()

    # ── Génération ───────────────────────────────────────────────────────────
    def _parse_budget() -> float | None:
        """Retourne le budget hebdo en € ou None si vide/invalide."""
        raw = budget_var.get().strip().replace(",", ".")
        try:
            b = float(raw)
            return b if b > 0 else None
        except Exception:
            return None

    def _run_gen():
        for w in result_frame.winfo_children(): w.destroy()

        selected = [f for f,v in chk_vars.items() if v.get()]
        if len(selected) < 2:
            e = mk_card(result_frame); e.pack(fill="x")
            mk_label(e, "  ⚠️  Sélectionne au moins 2 aliments.",
                     size="body", color=TH.DANGER).pack(padx=16, pady=20)
            return

        # Parse date de début
        try:
            start_date = _dt.datetime.strptime(date_var.get().strip(), "%d/%m/%Y").date()
        except Exception:
            start_date = _dt.date.today()

        n_meals  = n_meals_var.get()
        mode     = gen_mode_var.get()
        budget_w = _parse_budget()          # €/semaine ou None
        cal, prot, gluc, lip = _get_macros()

        if mode == "jour":
            import random as _rnd
            _day_off = _rnd.randint(0, 27)
            plan = _generate_meal_plan(n_meals, selected, cal, prot, gluc, lip,
                                        day_offset=_day_off)
            # Passe budget si activé (budget/7 pour un jour)
            if budget_w:
                budget_day = budget_w / 7
                plan = _apply_budget_pass(plan, selected, budget_day, app)
            app._last_meal_plan = {
                "plan": plan, "n_meals": n_meals, "cal": cal,
                "prot": prot, "gluc": gluc, "lip": lip,
                "adj": adj_txt, "multiday": False,
                "budget_w": budget_w,
            }
            tc = sum(m["tot_cal"] for m in plan)
            tp = sum(m["tot_p"]   for m in plan)
            tg = sum(m["tot_g"]   for m in plan)
            tl = sum(m["tot_l"]   for m in plan)
            _render_plan(result_frame, plan, n_meals, adj_txt,
                         tc, tp, tg, tl, cal, prot, gluc, lip,
                         budget_w=budget_w)
            _show_accept_btn()
        else:
            n_days = 7 if mode == "semaine" else 30
            prog_card = mk_card(result_frame)
            prog_card.pack(fill="x", pady=(0,8))
            prog_lbl = mk_label(prog_card,
                     f"  ⏳  Génération en cours — {n_days} jours...",
                     size="body", color=TH.ACCENT_GLOW)
            prog_lbl.pack(padx=16, pady=14)
            result_frame.update()

            days = _generate_multiday_plan(n_days, n_meals, selected,
                                            cal, prot, gluc, lip, start_date)
            # Passe budget jour par jour
            if budget_w:
                budget_day = budget_w / 7
                prog_lbl.configure(text="  💰  Optimisation budget en cours...")
                result_frame.update()
                for d in days:
                    d["plan"] = _apply_budget_pass(
                        d["plan"], selected, budget_day, app)

            app._last_meal_plan = {
                "days": days, "n_meals": n_meals, "cal": cal,
                "prot": prot, "gluc": gluc, "lip": lip,
                "adj": adj_txt, "multiday": True,
                "budget_w": budget_w,
            }
            _render_multiday(result_frame, days, n_meals, adj_txt,
                             cal, prot, gluc, lip, budget_w=budget_w)
            _show_accept_btn()

    # ── Render : 1 jour ──────────────────────────────────────────────────────
    def _render_plan(frame, plan, n_meals, adj_lbl,
                     tot_cal, tot_prot, tot_gluc, tot_lip,
                     cal, prot, gluc, lip, date_lbl=None, budget_w=None):
        for w in frame.winfo_children(): w.destroy()

        sc = mk_card(frame)
        sc.pack(fill="x", pady=(0,10))
        title_txt = f"  📋  {date_lbl or 'PLAN'} — {n_meals} repas / {adj_lbl}"
        mk_title(sc, title_txt).pack(anchor="w", padx=16, pady=(14,0))
        mk_sep(sc).pack(fill="x", padx=16, pady=(4,8))

        trow = ctk.CTkFrame(sc, fg_color="transparent")
        trow.pack(fill="x", padx=16, pady=(0,12))
        for label, got, tgt, unit in [
            ("🔥 Calories",  tot_cal,  cal,  "kcal"),
            ("🥩 Protéines", tot_prot, prot, "g"),
            ("🍚 Glucides",  tot_gluc, gluc, "g"),
            ("🥑 Lipides",   tot_lip,  lip,  "g"),
        ]:
            pct  = (got/tgt*100) if tgt > 0 else 0
            diff = abs(pct-100)
            clr  = TH.SUCCESS if diff<=5 else (TH.ACCENT_GLOW if diff<=12 else TH.DANGER)
            col  = ctk.CTkFrame(trow, fg_color=TH.BG_CARD2, corner_radius=8)
            col.pack(side="left", expand=True, fill="x", padx=5, pady=4)
            mk_label(col, label,            size="small", color=TH.TEXT_MUTED).pack(pady=(8,2))
            mk_label(col, f"{got:.0f} {unit}", size="h3", color=clr).pack()
            mk_label(col, f"cible {tgt:.0f} ({pct:.0f}%)",
                     size="small", color=TH.TEXT_MUTED).pack(pady=(0,8))

        # _save_plan défini ICI — avant d'être référencé dans pdf_row
        def _save_plan(p=plan, tc=tot_cal, tp=tot_prot, tg=tot_gluc, tl=tot_lip):
            try:
                today2 = _dt.date.today().strftime("%d/%m/%Y")
                ui2    = getattr(app, "user_info", None) or {}
                dn2    = ui2.get("date_naissance","")
                age_s  = str(utils.age_depuis_naissance(dn2) or ui2.get("age") or "")
                pv2    = getattr(app,"poids_var",None)
                pw     = pv2.get().strip() if pv2 else str(ui2.get("poids",""))
                _db.nutrition_insert(app, today2, pw, age_s,
                    str(round(tc)), str(round(tp)),
                    str(round(tg)), str(round(tl)),
                    f"Plan alimentaire — {n_meals} repas")
                from tkinter import messagebox as _mb
                _mb.showinfo("ERAGROK","✅ Plan enregistré dans l'historique nutrition.")
            except Exception as ex:
                from tkinter import messagebox as _mb
                _mb.showerror("ERAGROK", f"Erreur : {ex}")

        # ── Bilan budget (si activé) ──────────────────────────────────────────
        if budget_w:
            try:
                from data.prices_module import compute_shopping_cost
                _tmp_shop = {}
                for meal in plan:
                    for it in meal.get("items",[]):
                        f, g = it.get("food",""), it.get("grams",0)
                        if f not in _tmp_shop: _tmp_shop[f] = (g, "", "")
                        else: _tmp_shop[f] = (_tmp_shop[f][0]+g, "", "")
                # Simuler format shopping pour compute_shopping_cost
                fake_shopping = {"Repas": [(f, g, f"{g}g", "") for f,(g,_,__) in _tmp_shop.items()]}
                costs = compute_shopping_cost(fake_shopping, app)
                day_cost  = costs["total"]
                week_cost = day_cost * 7
                bgt_clr   = TH.SUCCESS if week_cost <= budget_w * 1.05 else (
                            TH.ACCENT_GLOW if week_cost <= budget_w * 1.20 else TH.DANGER)
                bgt_bar = ctk.CTkFrame(sc, fg_color=TH.BG_CARD2, corner_radius=8)
                bgt_bar.pack(fill="x", padx=16, pady=(0,8))
                bgt_inner = ctk.CTkFrame(bgt_bar, fg_color="transparent")
                bgt_inner.pack(fill="x", padx=12, pady=6)
                mk_label(bgt_inner, "💰  Budget estimé",
                         size="small", color=TH.TEXT_MUTED).pack(side="left")
                mk_label(bgt_inner,
                         f"  {day_cost:.2f} €/j  ·  {week_cost:.2f} €/sem",
                         size="body", color=bgt_clr).pack(side="left", padx=8)
                pct_bgt = (week_cost/budget_w*100) if budget_w > 0 else 0
                ok_str  = "✅" if week_cost <= budget_w*1.05 else ("⚠️" if week_cost <= budget_w*1.20 else "❌")
                mk_label(bgt_inner,
                         f"{ok_str}  {pct_bgt:.0f}% du budget ({budget_w:.0f} €/sem)",
                         size="small", color=bgt_clr).pack(side="right")

                # Avertissement si budget trop serré même après optimisation
                if week_cost > budget_w * 1.20:
                    warn = ctk.CTkFrame(sc, fg_color="#2a1010", corner_radius=8)
                    warn.pack(fill="x", padx=16, pady=(0,6))
                    warn_inner = ctk.CTkFrame(warn, fg_color="transparent")
                    warn_inner.pack(fill="x", padx=12, pady=8)
                    mk_label(warn_inner, "⚠️  Budget insuffisant",
                             size="small", color=TH.DANGER).pack(side="left")
                    mk_label(warn_inner,
                             f"  Avec ces aliments, le minimum estimé est {week_cost:.0f} €/sem.",
                             size="small", color=TH.TEXT_MUTED).pack(side="left", padx=4)
                    mk_label(warn_inner,
                             "Augmente le budget, décoche des aliments coûteux ou ajoute des alternatives moins chères.",
                             size="small", color=TH.TEXT_MUTED).pack(anchor="w", padx=0, pady=(2,0))
            except Exception:
                pass

        pdf_row = ctk.CTkFrame(sc, fg_color="transparent")
        pdf_row.pack(fill="x", padx=16, pady=(0,10))
        mk_btn(pdf_row, "💾  Enregistrer dans l'historique", _save_plan,
               color=TH.GRAY, hover=TH.GRAY_HVR,
               width=240, height=TH.BTN_SM).pack(side="left", padx=(0,8))

        def _show_shopping(p=plan):
            show_shopping_list(app, p, n_days=1)

        mk_btn(pdf_row, "🛒  Liste de courses",
               _show_shopping,
               color=TH.BG_CARD2, hover=TH.BG_CARD,
               width=180, height=TH.BTN_SM).pack(side="left")

        for meal in plan:
            mc = mk_card(frame)
            mc.pack(fill="x", pady=(0,8))
            hdr = ctk.CTkFrame(mc, fg_color="transparent")
            hdr.pack(fill="x", padx=16, pady=(12,0))
            lh  = ctk.CTkFrame(hdr, fg_color="transparent")
            lh.pack(side="left", fill="x", expand=True)
            mk_label(lh, meal["name"],  size="body",  color=TH.ACCENT_GLOW).pack(anchor="w")
            mk_label(lh, SLOT_DESC.get(meal["type"],""),
                     size="small", color=TH.TEXT_MUTED).pack(anchor="w")
            mk_label(hdr,
                     f"{meal['tot_cal']:.0f} kcal\n"
                     f"{meal['tot_p']:.0f}P · {meal['tot_g']:.0f}G · {meal['tot_l']:.0f}L",
                     size="small", color=TH.TEXT_SUB).pack(side="right", anchor="e")
            mk_sep(mc).pack(fill="x", padx=16, pady=(6,4))

            if not meal["items"]:
                mk_label(mc, "  ⚠️  Aucun aliment compatible — coche des aliments de cette catégorie.",
                         size="small", color=TH.DANGER).pack(padx=20, pady=(0,10))
                continue

            for item in meal["items"]:
                ir = ctk.CTkFrame(mc, fg_color="transparent")
                ir.pack(fill="x", padx=24, pady=2)
                ctk.CTkFrame(ir, fg_color=TH.ACCENT_GLOW,
                             width=6, height=6, corner_radius=3).pack(side="left", padx=(0,8))
                mk_label(ir, item["food"], size="body", color=TH.TEXT).pack(side="left")
                mk_label(ir,
                         f"{item['g']:.0f}g → {item['kcal']:.0f}kcal | "
                         f"{item['p']:.1f}P  {item['g_']:.1f}G  {item['l']:.1f}L",
                         size="body", color=TH.TEXT_MUTED).pack(side="right")
            ctk.CTkFrame(mc, fg_color="transparent", height=6).pack()

    # ── Render : multi-jours ─────────────────────────────────────────────────
    def _render_multiday(frame, days, n_meals, adj_lbl, cal, prot, gluc, lip, budget_w=None):
        for w in frame.winfo_children(): w.destroy()

        n_days = len(days)

        # ── En-tête récapitulatif ─────────────────────────────────────────────
        hdr_card = mk_card(frame)
        hdr_card.pack(fill="x", pady=(0,10))
        mode_lbl = "Semaine" if n_days == 7 else f"{n_days} jours"
        mk_title(hdr_card,
                 f"  📅  PLAN {mode_lbl.upper()} — {n_meals} repas/j — {adj_lbl}").pack(
            anchor="w", padx=16, pady=(14,0))
        mk_sep(hdr_card).pack(fill="x", padx=16, pady=(4,8))

        # Stats moyennes
        avg_cal  = sum(sum(m["tot_cal"] for m in d["plan"]) for d in days)/n_days
        avg_prot = sum(sum(m["tot_p"]   for m in d["plan"]) for d in days)/n_days
        avg_gluc = sum(sum(m["tot_g"]   for m in d["plan"]) for d in days)/n_days
        avg_lip  = sum(sum(m["tot_l"]   for m in d["plan"]) for d in days)/n_days
        trow = ctk.CTkFrame(hdr_card, fg_color="transparent")
        trow.pack(fill="x", padx=16, pady=(0,8))
        for label, got, tgt, unit in [
            ("🔥 Cal. moy.", avg_cal,  cal,  "kcal"),
            ("🥩 Prot. moy.", avg_prot, prot, "g"),
            ("🍚 Gluc. moy.", avg_gluc, gluc, "g"),
            ("🥑 Lip. moy.",  avg_lip,  lip,  "g"),
        ]:
            pct  = (got/tgt*100) if tgt > 0 else 0
            diff = abs(pct-100)
            clr  = TH.SUCCESS if diff<=5 else (TH.ACCENT_GLOW if diff<=12 else TH.DANGER)
            col  = ctk.CTkFrame(trow, fg_color=TH.BG_CARD2, corner_radius=8)
            col.pack(side="left", expand=True, fill="x", padx=5, pady=4)
            mk_label(col, label,              size="small", color=TH.TEXT_MUTED).pack(pady=(6,1))
            mk_label(col, f"{got:.0f} {unit}", size="body",  color=clr).pack()
            mk_label(col, f"/{tgt:.0f} ({pct:.0f}%)",
                     size="small", color=TH.TEXT_MUTED).pack(pady=(0,6))



        # ── Bilan budget multiday ────────────────────────────────────────────
        if budget_w:
            try:
                from data.prices_module import compute_shopping_cost
                # Coût moyen par jour sur toute la période
                day_costs = []
                for d in days:
                    fake_shop = {"Repas": [(it.get("food",""), it.get("grams",0), "", "")
                                           for meal in d["plan"]
                                           for it in meal.get("items",[])]}
                    day_costs.append(compute_shopping_cost(fake_shop, app)["total"])
                avg_day  = sum(day_costs)/len(day_costs) if day_costs else 0
                week_est = avg_day * 7
                bgt_clr  = TH.SUCCESS if week_est <= budget_w*1.05 else (
                           TH.ACCENT_GLOW if week_est <= budget_w*1.20 else TH.DANGER)
                bgt_bar = ctk.CTkFrame(hdr_card, fg_color=TH.BG_CARD2, corner_radius=8)
                bgt_bar.pack(fill="x", padx=16, pady=(0,10))
                bgt_inner = ctk.CTkFrame(bgt_bar, fg_color="transparent")
                bgt_inner.pack(fill="x", padx=12, pady=8)
                mk_label(bgt_inner, "💰  Budget estimé",
                         size="small", color=TH.TEXT_MUTED).pack(side="left")
                mk_label(bgt_inner,
                         f"  {avg_day:.2f} €/j · {week_est:.2f} €/sem",
                         size="body", color=bgt_clr).pack(side="left", padx=8)
                pct_b = (week_est/budget_w*100) if budget_w else 0
                ok_s  = "✅" if week_est<=budget_w*1.05 else ("⚠️" if week_est<=budget_w*1.20 else "❌")
                mk_label(bgt_inner,
                         f"{ok_s}  {pct_b:.0f}% du budget fixé ({budget_w:.0f} €/sem)",
                         size="small", color=bgt_clr).pack(side="right")

                if week_est > budget_w * 1.20:
                    warn = ctk.CTkFrame(hdr_card, fg_color="#2a1010", corner_radius=8)
                    warn.pack(fill="x", padx=16, pady=(0,8))
                    warn_r = ctk.CTkFrame(warn, fg_color="transparent")
                    warn_r.pack(fill="x", padx=12, pady=6)
                    mk_label(warn_r, "⚠️  Budget insuffisant pour ce plan",
                             size="small", color=TH.DANGER).pack(anchor="w")
                    mk_label(warn_r,
                             f"Minimum estimé : {week_est:.0f} €/sem  (budget : {budget_w:.0f} €)  "
                             f"— Décoche des aliments coûteux ou augmente le budget.",
                             size="small", color=TH.TEXT_MUTED).pack(anchor="w", pady=(2,0))
            except Exception:
                pass

        # ── Boutons actions semaine ───────────────────────────────────────────
        act_row = ctk.CTkFrame(frame, fg_color="transparent")
        act_row.pack(fill="x", padx=10, pady=(0, 6))

        def _show_shopping_multi(d=days, nd=n_days):
            show_shopping_list(app, d, n_days=nd)

        mk_btn(act_row, f"🛒  Liste de courses ({n_days}j)",
               _show_shopping_multi,
               color=TH.BG_CARD2, hover=TH.BG_CARD,
               width=220, height=TH.BTN_SM).pack(side="left", padx=(0, 8))

        # ── Navigation par onglets jour ───────────────────────────────────────
        tab_outer = ctk.CTkFrame(frame, fg_color="transparent")
        tab_outer.pack(fill="x", pady=(0,8))

        # Scroll horizontal d'onglets
        tab_scroll = ctk.CTkScrollableFrame(tab_outer, fg_color=TH.BG_CARD2,
                                             height=44, orientation="horizontal",
                                             scrollbar_button_color=TH.BORDER,
                                             scrollbar_button_hover_color=TH.ACCENT)
        tab_scroll.pack(fill="x")

        day_frame = ctk.CTkFrame(frame, fg_color="transparent")
        day_frame.pack(fill="both", expand=True)

        active_day_var = tk.IntVar(value=0)
        tab_btns = []

        def _show_day(idx):
            active_day_var.set(idx)
            # Mettre à jour couleurs onglets
            for i, btn in enumerate(tab_btns):
                btn.configure(
                    fg_color=TH.ACCENT if i==idx else TH.BG_CARD,
                    text_color=TH.TEXT if i==idx else TH.TEXT_MUTED,
                )
            # Afficher le plan du jour sélectionné dans day_frame
            for w in day_frame.winfo_children(): w.destroy()
            d    = days[idx]
            plan = d["plan"]
            tc   = sum(m["tot_cal"] for m in plan)
            tp   = sum(m["tot_p"]   for m in plan)
            tg   = sum(m["tot_g"]   for m in plan)
            tl   = sum(m["tot_l"]   for m in plan)
            _render_plan(day_frame, plan, n_meals, adj_lbl,
                         tc, tp, tg, tl, cal, prot, gluc, lip,
                         date_lbl=d["label"])

        DAY_SHORT = ["L","Ma","Me","J","V","S","D"]
        for i, d in enumerate(days):
            day_abbr = DAY_SHORT[d["date"].weekday()]
            day_num  = d["date"].strftime("%d")
            btn = mk_btn(tab_scroll,
                         f"{day_abbr}\n{day_num}",
                         lambda idx=i: _show_day(idx),
                         color=TH.BG_CARD, hover=TH.BG_CARD2,
                         width=42, height=40)
            btn.pack(side="left", padx=2, pady=2)
            tab_btns.append(btn)

        # Afficher le premier jour par défaut
        _show_day(0)

    try:
        app.root.after(100, _restore_last_plan)
    except Exception:
        pass

    return outer


# ══════════════════════════════════════════════════════════════════════════════
#  MODULE LISTE DE COURSES — conversions cuit/préparé → cru/sec/brut
# ══════════════════════════════════════════════════════════════════════════════

# Facteur de conversion : g_cuit × facteur = g_cru/sec à acheter
# ex: riz cuit 100g × 0.40 = 40g de riz sec
COOKED_TO_RAW = {
    # Céréales cuites → secs
    "Riz cuit":                   0.40,   # riz perd ~60% eau à la cuisson
    "Riz brun (cuit)":            0.40,
    "Pâtes blanches (cuites)":    0.43,   # pâtes ×2.3 à la cuisson
    "Pâtes complètes (cuites)":   0.43,
    "Pâtes cuites":               0.43,
    "Quinoa (cuit)":              0.38,
    "Boulgour (cuit)":            0.38,
    "Semoule (cuite)":            0.40,
    "Lentilles (cuites)":         0.42,
    "Pois chiches (cuits)":       0.42,
    "Haricots rouges (cuits)":    0.42,
    "Haricots blancs (cuits)":    0.42,
    "Edamame (cuit)":             0.90,   # peu de perte
    # Légumes cuits → crus (perte à la cuisson ~20-30%)
    "Brocoli (cuit)":             1.25,
    "Courgette (cuite)":          1.20,
    "Haricots verts (cuits)":     1.15,
    "Asperges (cuites)":          1.20,
    "Champignons (cuits)":        2.50,   # champignons perdent ~60% eau
    "Chou-fleur (cuit)":          1.25,
    "Épinards (crus)":            1.00,   # mangés crus — pas de conversion
    "Poivron (cru)":              1.00,
    "Tomate (crue)":              1.00,
    "Salade verte":               1.00,
    "Concombre (cru)":            1.00,
    # Viandes cuites → crues (perte eau + graisse ~25%)
    "Blanc de poulet (cuit)":     1.30,
    "Blanc de dinde (cuit)":      1.30,
    "Dinde (blanc cuit)":         1.30,
    "Boeuf haché 5% MG":          1.20,
    "Boeuf haché 15% MG":         1.20,
    "Boeuf haché 20% MG":         1.20,
    "Steak (rumsteck, cuit)":     1.30,
    "Escalope de veau (cuite)":   1.25,
    "Jambon blanc (dégraissé)":   1.00,   # prêt à l'emploi
    # Poissons cuits → crus (~25% perte)
    "Saumon (cuit)":              1.25,
    "Cabillaud (cuit)":           1.25,
    "Merlan (cuit)":              1.25,
    "Tilapia (cuit)":             1.25,
    "Filet de sole (cuit)":       1.25,
    "Maquereau (cuit)":           1.20,
    "Thon (en boîte, eau)":       1.00,   # conserve — pas de conversion
    "Sardines (en boîte, huile)": 1.00,
    "Crevettes (cuites)":         1.30,
    # Patate douce / pomme de terre cuites → crues (~20% perte)
    "Patate douce (cuite)":       1.25,
    "Patate douce violette (cuite)": 1.25,
    "Pomme de terre (cuite)":     1.20,
    # Tofu
    "Tofu ferme":                 1.00,   # poids identique
}

# Unités d'achat pratiques
# (seuil_grammes, unité_affichée, diviseur)
PURCHASE_UNIT = {
    # Liquides → litres
    "Lait écrémé":               ("L",    1000),
    "Lait entier":               ("L",    1000),
    "Lait de soja":              ("L",    1000),
    "Jus d'orange (pur jus)":    ("L",    1000),
    "Huile d'olive":             ("L",    1000),
    "Huile de coco":             ("L",    1000),
    # Œufs → unités (60g/oeuf)
    "Oeuf entier":               ("œufs", 60),
    "Blanc d'oeuf":              ("œufs", 35),  # blanc seul ~35g
    "Œuf dur entier":            ("œufs", 60),
    # Boîtes / conserves → boîtes (185g égoutté standard)
    "Thon (en boîte, eau)":      ("boîtes", 130),
    "Sardines (en boîte, huile)":("boîtes", 100),
}

# Catégories pour regrouper les courses
SHOPPING_CATEGORIES = {
    "🥩  Viandes & Poissons": [
        "Blanc de poulet (cuit)","Blanc de dinde (cuit)","Dinde (blanc cuit)",
        "Boeuf haché 5% MG","Boeuf haché 15% MG","Boeuf haché 20% MG",
        "Steak (rumsteck, cuit)","Escalope de veau (cuite)","Jambon blanc (dégraissé)",
        "Saumon (cuit)","Cabillaud (cuit)","Merlan (cuit)","Tilapia (cuit)",
        "Filet de sole (cuit)","Maquereau (cuit)","Crevettes (cuites)","Tofu ferme",
    ],
    "🐟  Conserves": [
        "Thon (en boîte, eau)","Sardines (en boîte, huile)",
    ],
    "🥚  Oeufs & Laitiers": [
        "Oeuf entier","Blanc d'oeuf","Œuf dur entier",
        "Skyr 0%","Fromage blanc 0%","Fromage blanc 20%","Yaourt grec 0%",
        "Yaourt grec entier (5%)","Yaourt 0% nature","Cottage cheese","Ricotta",
        "Lait écrémé","Lait entier","Lait de soja",
        "Emmental","Comté","Gruyère",
    ],
    "🌾  Céréales & Féculents (sec)": [
        "Riz cuit","Riz brun (cuit)","Pâtes blanches (cuites)","Pâtes complètes (cuites)",
        "Quinoa (cuit)","Boulgour (cuit)","Semoule (cuite)","Flocons d'avoine",
        "Farine d'avoine HSN","Crème de riz HSN","Pain complet","Pain blanc",
        "Galettes de riz nature","Müesli nature (sans sucre)",
        "Patate douce (cuite)","Patate douce violette (cuite)","Pomme de terre (cuite)",
    ],
    "🥦  Légumes": [
        "Brocoli (cuit)","Épinards (crus)","Courgette (cuite)","Haricots verts (cuits)",
        "Asperges (cuites)","Poivron (cru)","Tomate (crue)","Salade verte",
        "Champignons (cuits)","Chou-fleur (cuit)","Concombre (cru)",
    ],
    "🫘  Légumineuses (sec)": [
        "Lentilles (cuites)","Pois chiches (cuits)","Haricots rouges (cuits)",
        "Haricots blancs (cuits)","Edamame (cuit)",
    ],
    "🍌  Fruits": [
        "Banane","Pomme","Orange","Kiwi","Fraises","Myrtilles","Mangue",
        "Ananas","Poire","Pastèque","Raisins","Avocat",
    ],
    "🥑  Matières grasses & Oléagineux": [
        "Huile d'olive","Huile de coco","Beurre doux","Beurre de cacahuète",
        "Beurre d'amande","Amandes","Noix","Noix de cajou","Cacahuètes",
        "Graines de chia","Graines de lin","Tahini (purée sésame)",
        "Chocolat noir 70%","Cacao pur",
    ],
    "🍯  Sucrants & Condiments": [
        "Miel","Confiture (moyenne)","Sirop d'agave",
    ],
    "💊  Suppléments": [
        "EvoWhey HSN","Whey protéine","Caséine",
        "Chocolat au lait chaud","Jus d'orange (pur jus)",
    ],
}


def compute_shopping_list(plans_or_plan):
    """
    Calcule la liste de courses à partir d'un plan jour ou semaine.
    plans_or_plan : soit un plan journée (list de meals),
                    soit une list de {date, label, plan}.
    Retourne un dict ordonné par catégorie :
      {cat_name: [(food, qty_raw, unit, label_str), ...]}
    """
    # Agréger les grammes totaux par aliment
    totals = {}  # food → grammes cuits/préparés totaux

    # Détecter si c'est un plan multiday ou un plan jour
    if plans_or_plan and isinstance(plans_or_plan[0], dict):
        first = plans_or_plan[0]
        if "plan" in first:
            # Multiday : liste de {date, label, plan}
            all_meals = [m for day in plans_or_plan for m in day["plan"]]
        else:
            # Jour : liste de meals directement
            all_meals = plans_or_plan
    else:
        all_meals = plans_or_plan or []

    for meal in all_meals:
        for item in meal.get("items", []):
            food  = item.get("food","")
            grams = item.get("g", item.get("grams", 0))   # robustesse clés
            if not food: continue
            totals[food] = totals.get(food, 0) + grams

    # Convertir cuit → cru et formater
    result = {}
    food_to_cat = {}
    for cat, foods in SHOPPING_CATEGORIES.items():
        for f in foods:
            food_to_cat[f] = cat

    for food, g_cooked in totals.items():
        # Conversion cuit→cru
        factor  = COOKED_TO_RAW.get(food, 1.0)
        g_raw   = g_cooked * factor

        # Unité d'achat
        if food in PURCHASE_UNIT:
            unit, divisor = PURCHASE_UNIT[food]
            qty = g_raw / divisor
            if unit in ("L",):
                label = f"{qty:.2f} L" if qty < 1 else f"{qty:.1f} L"
            elif unit == "œufs":
                qty = max(1, round(qty))
                label = f"{qty} œuf{'s' if qty > 1 else ''}"
            elif unit == "boîtes":
                qty = max(1, round(qty))
                label = f"{qty} boîte{'s' if qty > 1 else ''}"
            else:
                label = f"{qty:.1f} {unit}"
        elif g_raw >= 1000:
            label = f"{g_raw/1000:.2f} kg"
        elif g_raw >= 100:
            label = f"{g_raw:.0f} g"
        else:
            label = f"{g_raw:.0f} g"

        # Annotation cuit→cru si conversion significative
        if factor != 1.0 and abs(factor - 1.0) > 0.05:
            note = f"(cuit: {g_cooked:.0f}g)"
        else:
            note = ""

        cat = food_to_cat.get(food, "🛒  Autres")
        if cat not in result:
            result[cat] = []
        result[cat].append((food, g_raw, label, note))

    # ── Agrégation spéciale : tous les œufs regroupés ──────────────────────────
    # Oeuf entier=60g, Blanc d'oeuf=35g, Œuf dur entier=60g → total en œufs
    EGG_FORMS = {
        "Oeuf entier":    60,
        "Blanc d'oeuf":   35,   # 3 blancs = ~1 œuf complet côté achat
        "Œuf dur entier": 60,
    }
    egg_totals_g   = {}   # {food: g_raw}
    egg_totals_cnt = {}   # {food: nb_oeufs}
    egg_cat = None
    for food in list(EGG_FORMS.keys()):
        cat = food_to_cat.get(food)
        for c in result:
            found = [(i, it) for i, it in enumerate(result[c]) if it[0] == food]
            if found:
                idx, it = found[0]
                g_raw = it[1]
                nb    = max(1, round(g_raw / EGG_FORMS[food]))
                egg_totals_g[food]   = g_raw
                egg_totals_cnt[food] = nb
                egg_cat = c
                result[c].pop(idx)
                break

    if egg_totals_cnt:
        total_oeufs = sum(egg_totals_cnt.values())
        # Ligne agrégée
        detail_parts = []
        for food, nb in egg_totals_cnt.items():
            lbl_food = food.replace("Oeuf entier","entiers")                           .replace("Blanc d'oeuf","blancs")                           .replace("Œuf dur entier","durs")
            detail_parts.append(f"{nb} {lbl_food}")
        detail = "dont " + ", ".join(detail_parts)
        cat_oeufs = egg_cat or "🥚  Oeufs & Laitiers"
        if cat_oeufs not in result:
            result[cat_oeufs] = []
        result[cat_oeufs].insert(
            0,
            ("🥚 Œufs (total)", total_oeufs * 60, f"{total_oeufs} œufs", detail)
        )

    # ── Trier chaque catégorie par quantité décroissante ─────────────────────
    for cat in result:
        # Garder la ligne agrégée œufs en tête si présente
        eggs_row = [it for it in result[cat] if it[0] == "🥚 Œufs (total)"]
        others   = [it for it in result[cat] if it[0] != "🥚 Œufs (total)"]
        others.sort(key=lambda x: x[1], reverse=True)
        result[cat] = eggs_row + others

    # Réordonner selon SHOPPING_CATEGORIES
    ordered = {}
    for cat in SHOPPING_CATEGORIES:
        if cat in result:
            ordered[cat] = result[cat]
    for cat in result:
        if cat not in ordered:
            ordered[cat] = result[cat]

    return ordered


def _render_shopping_content(scroll, shopping, period_lbl, app=None):
    """Render shopping list items into a scroll frame (réutilisé par semaine/mois)."""
    from data.theme import TH, mk_card, mk_label, mk_sep

    for w in scroll.winfo_children(): w.destroy()
    if not shopping:
        mk_label(scroll, "  Aucun aliment pour cette période.",
                 size="body", color=TH.TEXT_MUTED).pack(anchor="w", padx=16, pady=20)
        return

    # ── Calcul des coûts si app disponible ────────────────────────────────────
    costs = None
    if app:
        try:
            from data.prices_module import compute_shopping_cost
            costs = compute_shopping_cost(shopping, app)
        except Exception:
            pass

    total_items = sum(len(v) for v in shopping.values())
    # Ligne résumé
    summary_row = ctk.CTkFrame(scroll, fg_color="transparent")
    summary_row.pack(fill="x", padx=16, pady=(8,4))
    mk_label(summary_row, f"  {total_items} aliments — {period_lbl}",
             size="small", color=TH.TEXT_MUTED).pack(side="left")
    if costs and costs["total"] > 0:
        n_f, n_t = costs["nb_prices_found"], costs["nb_total"]
        coverage  = f"{n_f}/{n_t}"
        cost_lbl  = f"≈ {costs['total']:.2f} €  ({coverage} prix)"
        mk_label(summary_row, cost_lbl,
                 size="body", color=TH.SUCCESS).pack(side="right")

    for cat, items in shopping.items():
        if not items: continue
        card = mk_card(scroll)
        card.pack(fill="x", padx=10, pady=(0, 6))
        cat_hdr = ctk.CTkFrame(card, fg_color=TH.BG_CARD2, corner_radius=8)
        cat_hdr.pack(fill="x", padx=8, pady=(8, 4))
        mk_label(cat_hdr, f"  {cat}", size="h3", color=TH.ACCENT_GLOW).pack(
            side="left", padx=10, pady=6)
        # Coût catégorie
        cat_cost = costs["by_cat"].get(cat, 0) if costs else 0
        info_str = f"{len(items)} art."
        if cat_cost > 0:
            info_str += f"  ≈ {cat_cost:.2f} €"
        mk_label(cat_hdr, info_str,
                 size="small", color=TH.TEXT_MUTED).pack(side="right", padx=10)

        for food, g_raw, label, note in items:
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=2)
            ctk.CTkFrame(row, fg_color=TH.TEXT_MUTED,
                         width=5, height=5, corner_radius=3).pack(
                side="left", padx=(4, 10), pady=6)
            mk_label(row, food, size="body", color=TH.TEXT).pack(side="left")
            if note:
                mk_label(row, f"  {note}", size="small",
                         color=TH.TEXT_MUTED).pack(side="left")
            # Coût item à droite de la quantité
            item_cost = costs["by_item"].get(food, 0) if costs else 0
            if item_cost > 0:
                mk_label(row, f"≈ {item_cost:.2f} €",
                         size="small", color=TH.TEXT_MUTED).pack(side="right", padx=(0,4))
            mk_label(row, label, size="body", color=TH.ACCENT).pack(side="right", padx=8)
        mk_sep(card).pack(fill="x", padx=12, pady=(6, 8))

    # Bandeau total en bas du scroll
    if costs and costs["total"] > 0:
        total_bar = ctk.CTkFrame(scroll, fg_color=TH.BG_CARD2, corner_radius=8)
        total_bar.pack(fill="x", padx=10, pady=(4, 10))
        mk_label(total_bar, "  TOTAL ESTIMÉ",
                 size="small", color=TH.TEXT_MUTED).pack(side="left", padx=16, pady=10)
        src_lbl = "Open Food Facts + prix marché France 2025"
        mk_label(total_bar, src_lbl,
                 size="small", color=TH.TEXT_MUTED).pack(side="left", padx=4)
        mk_label(total_bar, f"≈ {costs['total']:.2f} €",
                 size="h2", color=TH.SUCCESS).pack(side="right", padx=16)


def show_shopping_list(app, plans_or_plan, n_days=1):
    """Affiche la liste de courses avec navigation par semaine et mois."""
    import datetime as _dt
    from data.theme import TH, mk_card, mk_label, mk_btn, mk_sep, mk_scrollframe

    # ── Construire les tranches selon le type de plan ─────────────────────────
    # Normaliser en liste de {label, days_list}
    # days_list = liste de {date, plan} pour ce segment
    if isinstance(plans_or_plan, list) and plans_or_plan and "plan" in plans_or_plan[0]:
        all_days = plans_or_plan          # multiday list
    else:
        # Plan journée — simuler un seul jour
        today = _dt.date.today()
        all_days = [{"date": today, "label": today.strftime("%d/%m/%Y"),
                     "plan": plans_or_plan}]

    n_days = len(all_days)

    # Découper en semaines (7 jours max par tranche)
    def _slice_days(days_list, start, count):
        return days_list[start:start+count]

    segments = []  # [(tab_label, days_slice)]

    if n_days == 1:
        # Plan journée : un seul onglet
        d0 = all_days[0]["date"] if hasattr(all_days[0].get("date", None), "strftime") else _dt.date.today()
        segments.append((f"📅\n{d0.strftime('%d/%m')}", all_days))
    else:
        # Découper en semaines (même pour 7j : Sem. 1 + Total)
        n_full_weeks = n_days // 7
        leftover     = n_days % 7
        for w in range(n_full_weeks):
            sl = _slice_days(all_days, w * 7, 7)
            d0 = sl[0]["date"]  if hasattr(sl[0].get("date", None),  "strftime") else _dt.date.today()
            d1 = sl[-1]["date"] if hasattr(sl[-1].get("date", None), "strftime") else d0
            segments.append((f"Sem. {w+1}\n{d0.strftime('%d/%m')}–{d1.strftime('%d/%m')}", sl))
        if leftover:
            sl = _slice_days(all_days, n_full_weeks * 7, leftover)
            d0 = sl[0]["date"]  if hasattr(sl[0].get("date", None),  "strftime") else _dt.date.today()
            d1 = sl[-1]["date"] if hasattr(sl[-1].get("date", None), "strftime") else d0
            segments.append((f"Sem. {n_full_weeks+1}\n{d0.strftime('%d/%m')}–{d1.strftime('%d/%m')}", sl))
        # Onglet total : "Semaine" si 7j, "Mois entier" si 30j
        total_lbl = "Mois\nentier" if n_days >= 28 else f"Total\n{n_days}j"
        segments.append((total_lbl, all_days))

    if not segments:
        from tkinter import messagebox as _mb
        _mb.showinfo("ERAGROK", "Aucun aliment dans le plan.")
        return

    # ── Fenêtre ───────────────────────────────────────────────────────────────
    dlg = ctk.CTkToplevel(app.root)
    dlg.title("🛒  Liste de courses")
    dlg.geometry("640x760")
    dlg.resizable(True, True)
    dlg.grab_set()
    try: dlg.iconbitmap("")
    except Exception: pass

    # En-tête fixe
    hdr = ctk.CTkFrame(dlg, fg_color=TH.BG_CARD, corner_radius=0)
    hdr.pack(fill="x", side="top")
    mk_label(hdr, "🛒  LISTE DE COURSES",
             size="h2", color=TH.ACCENT).pack(side="left", padx=20, pady=12)
    mk_label(hdr, "Quantités brutes à acheter",
             size="small", color=TH.TEXT_MUTED).pack(side="right", padx=20)

    # Navigation onglets semaines — packée avant content pour garder la place
    nav_outer = ctk.CTkFrame(dlg, fg_color=TH.BG_CARD2, corner_radius=0)
    nav_outer.pack(fill="x", side="top")
    nav_scroll = ctk.CTkScrollableFrame(nav_outer, fg_color="transparent",
                                         height=72, orientation="horizontal",
                                         scrollbar_button_color=TH.BORDER,
                                         scrollbar_button_hover_color=TH.ACCENT)
    nav_scroll.pack(fill="x", padx=8, pady=6)

    # !! Barre boutons packée AVANT content_scroll (sinon expand=True l'écrase)
    btn_bar = ctk.CTkFrame(dlg, fg_color=TH.BG_ROOT, corner_radius=0)
    btn_bar.pack(fill="x", side="bottom")

    # Zone contenu scroll — en dernier pour prendre l'espace restant
    content_scroll = mk_scrollframe(dlg)
    content_scroll.pack(fill="both", expand=True, side="top")

    # État courant
    _state = {"seg_idx": 0, "nav_btns": []}

    def _select_segment(idx):
        _state["seg_idx"] = idx
        lbl, days_slice = segments[idx]
        lbl_clean = lbl.replace("\n", " ").strip()

        # Recalculer courses pour ce segment
        shopping = compute_shopping_list(days_slice)
        nd = len(days_slice)
        period = f"{nd} jour{'s' if nd > 1 else ''}"
        if lbl.startswith("Mois"):
            period = f"mois complet ({nd} jours)"
        _render_shopping_content(content_scroll, shopping, period, app=app)

        # Mettre à jour couleurs onglets
        for i, btn in enumerate(_state["nav_btns"]):
            btn.configure(
                fg_color   = TH.ACCENT    if i == idx else TH.BG_CARD,
                text_color = "#000"       if i == idx else TH.TEXT_MUTED,
            )

        # Mettre à jour bouton PDF label
        _state["pdf_days"] = days_slice
        _state["pdf_lbl"]  = lbl_clean

    # Créer les onglets
    for i, (lbl, days_slice) in enumerate(segments):
        is_month = lbl.startswith("Mois")
        fg  = TH.ACCENT   if i == 0 else TH.BG_CARD
        txt = "#000"      if i == 0 else TH.TEXT_MUTED
        w   = 70 if is_month else 58
        btn = ctk.CTkButton(
            nav_scroll, text=lbl, command=lambda idx=i: _select_segment(idx),
            fg_color=fg, text_color=txt, hover_color=TH.BG_CARD2,
            font=TH.F_SMALL, width=w, height=52, corner_radius=10)
        btn.pack(side="left", padx=4, pady=4)
        _state["nav_btns"].append(btn)

    # Actions PDF / Imprimer
    def _export_pdf():
        days_slice = _state.get("pdf_days", all_days)
        lbl        = _state.get("pdf_lbl", "liste_courses")
        try:
            from data import pdf_utils as _pu
            shopping = compute_shopping_list(days_slice)
            _pu.export_shopping_pdf(app, shopping, lbl, ask_path=True)
        except Exception as ex:
            from tkinter import messagebox as _mb
            _mb.showerror("ERAGROK", f"Erreur PDF : {ex}")

    def _print_list():
        days_slice = _state.get("pdf_days", all_days)
        lbl        = _state.get("pdf_lbl", "liste_courses")
        try:
            from data import pdf_utils as _pu
            shopping = compute_shopping_list(days_slice)
            _pu.export_shopping_pdf(app, shopping, lbl, ask_path=False, print_after=True)
        except Exception as ex:
            from tkinter import messagebox as _mb
            _mb.showerror("ERAGROK", f"Erreur impression : {ex}")

    mk_btn(btn_bar, "📄  Exporter PDF", _export_pdf,
           color=TH.ACCENT, hover=TH.ACCENT_HOVER,
           width=160, height=TH.BTN_SM).pack(side="left", padx=(12,4), pady=8)
    mk_btn(btn_bar, "🖨  Imprimer",    _print_list,
           color="#1a1a2e", hover="#252540",
           width=140, height=TH.BTN_SM).pack(side="left", padx=4, pady=8)
    mk_btn(btn_bar, "✕  Fermer", dlg.destroy,
           color=TH.GRAY, hover=TH.GRAY_HVR,
           width=120, height=TH.BTN_SM).pack(side="right", padx=12, pady=8)

    # Afficher premier onglet
    _select_segment(0)

