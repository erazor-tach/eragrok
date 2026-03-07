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
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    MPL_OK = True
except Exception:
    MPL_OK = False

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
    if len(weights_s) >= 2:
        import numpy as np
        x_num = matplotlib.dates.date2num(list(dates_s))
        z = np.polyfit(x_num, weights_s, 1)
        p = np.poly1d(z)
        trend_dates = [dates_s[0], dates_s[-1]]
        ax.plot(trend_dates, p(matplotlib.dates.date2num(trend_dates)),
                "--", color="#818aaa", linewidth=1, alpha=0.6, label="tendance")

    fig.tight_layout(pad=0.5)

    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="x", padx=12, pady=(0, 10))
    plt.close(fig)
    return frame


# ══════════════════════════════════════════════════════════════════════════════
#  CAMEMBERT MACROS
# ══════════════════════════════════════════════════════════════════════════════
def render_macro_pie(parent, cal, prot, gluc, lip):
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

    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas.draw()
    canvas.get_tk_widget().pack()
    plt.close(fig)
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
}

# ── Catégories fonctionnelles (utilisées par les templates) ───────────────────
FOOD_CATS = {
    "oeuf":             ["Oeuf entier", "Blanc d'oeuf", "Œuf dur entier"],
    "glucide_matin":    ["Flocons d'avoine", "Pain complet",
                         "Müesli nature (sans sucre)", "Galettes de riz nature"],
    "glucide_midi":     ["Riz cuit", "Riz brun (cuit)", "Pâtes blanches (cuites)",
                         "Pâtes complètes (cuites)", "Patate douce (cuite)",
                         "Pomme de terre (cuite)", "Quinoa (cuit)",
                         "Lentilles (cuites)", "Pois chiches (cuits)",
                         "Haricots rouges (cuits)", "Boulgour (cuit)",
                         "Patate douce violette (cuite)"],
    "glucide_soir":     ["Riz cuit", "Riz brun (cuit)", "Patate douce (cuite)",
                         "Quinoa (cuit)", "Pâtes complètes (cuites)",
                         "Boulgour (cuit)", "Lentilles (cuites)"],
    "fruit":            ["Banane", "Pomme", "Orange", "Kiwi", "Fraises",
                         "Myrtilles", "Mangue", "Ananas", "Poire",
                         "Pastèque", "Raisins"],
    "legume":           ["Brocoli (cuit)", "Épinards (crus)", "Courgette (cuite)",
                         "Haricots verts (cuits)", "Asperges (cuites)",
                         "Poivron (cru)", "Tomate (crue)", "Salade verte",
                         "Champignons (cuits)", "Chou-fleur (cuit)",
                         "Concombre (cru)"],
    "lipide_sain":      ["Huile d'olive", "Avocat", "Amandes",
                         "Beurre de cacahuète", "Noix", "Noix de cajou",
                         "Graines de chia", "Graines de lin",
                         "Tahini (purée sésame)", "Huile de coco"],
    "laitier":          ["Skyr 0%", "Fromage blanc 0%", "Yaourt grec 0%",
                         "Cottage cheese", "Lait écrémé", "Fromage blanc 20%",
                         "Yaourt 0% nature", "Ricotta"],
    "laitier_lent":     ["Cottage cheese", "Skyr 0%", "Fromage blanc 0%"],
    "whey":             ["EvoWhey HSN", "Whey protéine"],
    "supplement_lent":  ["Caséine"],
    "proteine_maigre":  ["Blanc de poulet (cuit)", "Dinde (blanc cuit)",
                         "Thon (en boîte, eau)", "Cabillaud (cuit)",
                         "Merlan (cuit)", "Tilapia (cuit)",
                         "Crevettes (cuites)", "Filet de sole (cuit)",
                         "Escalope de veau (cuite)", "Blanc de dinde (cuit)",
                         "Jambon blanc (dégraissé)"],
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
                         "Blanc d'oeuf", "Jambon blanc (dégraissé)"],
}

# ── Templates de repas par slot ───────────────────────────────────────────────
# Chaque template = liste de (cat, macro_mode)
#  macro_mode :
#    "prot"  → calculer g pour atteindre t_prot du slot
#    "gluc"  → calculer g pour atteindre t_gluc du slot
#    int     → portion fixe (légumes, lipides de base)
SLOT_TEMPLATES = {
    "matin": [
        [("oeuf","prot"),        ("glucide_matin","gluc"), ("fruit",120), ("laitier","prot_rest")],
        [("laitier","prot"),     ("glucide_matin","gluc"), ("fruit",120), ("whey","prot_rest")],
        [("whey","prot"),        ("glucide_matin","gluc"), ("fruit",100)],
        [("oeuf","prot"),        ("glucide_matin","gluc")],
    ],
    "midi": [
        [("proteine_midi","prot"),  ("glucide_midi","gluc"), ("legume",150)],
        [("proteine_midi","prot"),  ("glucide_midi","gluc")],
    ],
    "collation": [
        [("laitier","prot"),     ("fruit",130)],
        [("whey","prot"),        ("fruit",120)],
        [("laitier","prot")],
        [("whey","prot")],
    ],
    "soir": [
        [("proteine_maigre","prot"), ("legume",180), ("glucide_soir","gluc")],
        [("proteine_maigre","prot"), ("legume",200)],
    ],
    "coucher": [
        [("supplement_lent","prot")],
        [("laitier_lent","prot")],
        [("laitier","prot")],
    ],
}

SLOT_DESC = {
    "matin":     "Œufs / laitiers / flocons / fruits / whey",
    "midi":      "Repas principal — grasses OK — glucides complets",
    "collation": "Laitier ou whey — fruit léger",
    "soir":      "Protéines maigres uniquement — légumes",
    "coucher":   "Protéines lentes (caséine/cottage) — zéro glucide",
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

    def _avail(cat, already_in_meal=None, offset=0):
        """Retourne les aliments disponibles dans la catégorie, filtrés par incompatibilité,
        avec rotation basée sur day_offset pour la variation journalière."""
        candidates = [f for f in FOOD_CATS.get(cat,[]) if f in sel and f in db]
        if already_in_meal:
            candidates = [f for f in candidates
                          if _filter_compatible(f, already_in_meal)]
        if not candidates:
            return []
        # Rotation : décaler le point de départ selon day_offset
        n = len(candidates)
        start = (offset % n) if n > 0 else 0
        return candidates[start:] + candidates[:start]

    def _macros(food, grams):
        k,p,g,l = db[food]
        r = grams/100.0
        return k*r, p*r, g*r, l*r

    def _g_for(food, target, macro_idx):
        val100 = db[food][macro_idx]
        if val100 <= 0: return 50
        return max(10, round(target / (val100/100.0)))

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

        templates = SLOT_TEMPLATES.get(stype, SLOT_TEMPLATES["collation"])
        best_items = None

        for tpl in templates:
            items      = []
            rem_prot   = t_prot
            rem_gluc   = t_gluc
            used       = set()
            ok         = True

            for cat, mode in tpl:
                # Offset adapté selon la catégorie fonctionnelle
                if cat in ("proteine_midi","proteine_maigre","proteine_grasse","oeuf"):
                    use_off = off_prot
                elif cat in ("glucide_midi","glucide_soir","glucide_matin","fruit"):
                    use_off = off_gluc
                elif cat == "legume":
                    use_off = off_leg
                elif cat == "lipide_sain":
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
                    g = mode
                elif mode == "prot":
                    g = min(500, _g_for(food, rem_prot, 1))
                elif mode == "prot_rest":
                    if rem_prot > 5:
                        g = min(300, _g_for(food, rem_prot, 1))
                    else:
                        continue
                elif mode == "gluc":
                    g = min(400, _g_for(food, rem_gluc, 2))
                else:
                    continue

                k,p,gc,l = _macros(food, g)
                items.append({"food":food,"g":g,"kcal":k,"p":p,"g_":gc,"l":l})
                rem_prot -= p
                rem_gluc -= gc

            if ok and items:
                best_items = items
                break

        # Fallback ultime (pas de contrainte d'incompatibilité)
        if not best_items:
            for food in sel:
                if food in db:
                    g = max(50, _g_for(food, t_prot, 1))
                    k,p,gc,l = _macros(food, g)
                    best_items = [{"food":food,"g":g,"kcal":k,"p":p,"g_":gc,"l":l}]
                    break

        best_items = best_items or []
        meals.append({"slot": slot, "type": stype, "items": best_items})

    # ── PASSE 2 : micro-correction protéines ─────────────────────────────────
    got_prot = sum(i["p"] for m in meals for i in m["items"])
    if prot_total and abs(got_prot - prot_total) / prot_total * 100 > 5:
        delta_prot = prot_total - got_prot
        bm = max(meals, key=lambda m: max((i["p"] for i in m["items"]), default=0))
        mi = max(bm["items"], key=lambda i: i["p"], default=None)
        if mi:
            _, p100, _, _ = db[mi["food"]]
            if p100 > 0:
                new_g = max(20, mi["g"] + round(delta_prot/(p100/100.0)))
                k,p,gc,l = _macros(mi["food"], new_g)
                mi.update({"g":new_g,"kcal":k,"p":p,"g_":gc,"l":l})

    # ── PASSE 3 : trim glucides excédentaires ────────────────────────────────
    got_gluc = sum(i["g_"] for m in meals for i in m["items"])
    if gluc_total and (got_gluc - gluc_total)/gluc_total*100 > 5:
        for m in meals:
            if m["type"] in ("midi","soir","matin"):
                gi = [i for i in m["items"] if any(i["food"] in FOOD_CATS.get(c,[])
                      for c in ("glucide_midi","glucide_soir","glucide_matin"))]
                if gi:
                    mg = max(gi, key=lambda x: x["g_"])
                    _, _, g100, _ = db[mg["food"]]
                    if g100 > 0:
                        new_g = max(30, mg["g"] - round((got_gluc-gluc_total)/(g100/100.0)))
                        k,p,gc,l = _macros(mg["food"], new_g)
                        mg.update({"g":new_g,"kcal":k,"p":p,"g_":gc,"l":l})
                    break

    # ── PASSE 4 : combler déficit lipidique ───────────────────────────────────
    got_lip = sum(i["l"] for m in meals for i in m["items"])
    deficit_lip = lip_total - got_lip
    if deficit_lip > 2:
        lip_avail = _avail("lipide_sain", offset=off_lip)
        if lip_avail:
            lip_food = lip_avail[0]
            _, _, _, l100 = db[lip_food]
            if l100 > 0:
                g_total = round(deficit_lip/(l100/100.0))
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
                            ng = already[0]["g"] + g
                            k2,p2,gc2,l2 = _macros(lip_food, ng)
                            already[0].update({"g":ng,"kcal":k2,"p":p2,"g_":gc2,"l":l2})
                        else:
                            m["items"].append({"food":lip_food,"g":g,
                                                "kcal":k,"p":p,"g_":gc,"l":l})

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
    mk_btn(qrow, "Tout décocher",
           lambda: [v.set(False) for v in chk_vars.values()],
           color=TH.GRAY, hover=TH.GRAY_HVR,
           width=130, height=TH.BTN_SM).pack(side="right", padx=4, pady=6)

    mk_sep(left).pack(fill="x", padx=16, pady=(4,0))
    mk_btn(left, "⚡  GÉNÉRER",
           lambda: _run_gen(),
           color=TH.ACCENT, hover=TH.ACCENT_HOVER,
           width=240, height=TH.BTN_LG).pack(pady=14)

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

    # ── Génération ───────────────────────────────────────────────────────────
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

        n_meals = n_meals_var.get()
        mode    = gen_mode_var.get()
        cal, prot, gluc, lip = _get_macros()

        if mode == "jour":
            plan = _generate_meal_plan(n_meals, selected, cal, prot, gluc, lip,
                                        day_offset=0)
            app._last_meal_plan = {
                "plan": plan, "n_meals": n_meals, "cal": cal,
                "prot": prot, "gluc": gluc, "lip": lip,
                "adj": adj_txt, "multiday": False,
            }
            tc = sum(m["tot_cal"] for m in plan)
            tp = sum(m["tot_p"]   for m in plan)
            tg = sum(m["tot_g"]   for m in plan)
            tl = sum(m["tot_l"]   for m in plan)
            _render_plan(result_frame, plan, n_meals, adj_txt,
                         tc, tp, tg, tl, cal, prot, gluc, lip)
        else:
            n_days = 7 if mode == "semaine" else 30
            # Barre de progression
            prog_card = mk_card(result_frame)
            prog_card.pack(fill="x", pady=(0,8))
            mk_label(prog_card,
                     f"  ⏳  Génération en cours — {n_days} jours...",
                     size="body", color=TH.ACCENT_GLOW).pack(padx=16, pady=14)
            result_frame.update()

            days = _generate_multiday_plan(n_days, n_meals, selected,
                                            cal, prot, gluc, lip, start_date)
            app._last_meal_plan = {
                "days": days, "n_meals": n_meals, "cal": cal,
                "prot": prot, "gluc": gluc, "lip": lip,
                "adj": adj_txt, "multiday": True,
            }
            _render_multiday(result_frame, days, n_meals, adj_txt,
                             cal, prot, gluc, lip)

    # ── Render : 1 jour ──────────────────────────────────────────────────────
    def _render_plan(frame, plan, n_meals, adj_lbl,
                     tot_cal, tot_prot, tot_gluc, tot_lip,
                     cal, prot, gluc, lip, date_lbl=None):
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

        pdf_row = ctk.CTkFrame(sc, fg_color="transparent")
        pdf_row.pack(fill="x", padx=16, pady=(0,10))
        def _export_pdf(p=plan):
            try:
                from data import pdf_utils as _pu
                _pu.export_meal_plan_pdf(app, p, ask_path=True)
            except Exception as ex:
                from tkinter import messagebox as _mb
                _mb.showerror("ERAGROK", f"Erreur PDF : {ex}")
        mk_btn(pdf_row, "📄  Exporter PDF", _export_pdf,
               color="#1a1a2e", hover="#252540",
               width=160, height=TH.BTN_SM).pack(side="right")

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
                mk_label(ir, item["food"], size="small", color=TH.TEXT).pack(side="left")
                mk_label(ir,
                         f"{item['g']:.0f}g → {item['kcal']:.0f}kcal | "
                         f"{item['p']:.1f}P  {item['g_']:.1f}G  {item['l']:.1f}L",
                         size="small", color=TH.TEXT_MUTED).pack(side="right")
            ctk.CTkFrame(mc, fg_color="transparent", height=6).pack()

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

        sr = ctk.CTkFrame(frame, fg_color="transparent")
        sr.pack(fill="x", pady=8)
        mk_btn(sr, "💾  Enregistrer dans l'historique", _save_plan,
               color=TH.SUCCESS, hover=TH.SUCCESS_HVR,
               width=270, height=TH.BTN_LG).pack(side="right", padx=4)

    # ── Render : multi-jours ─────────────────────────────────────────────────
    def _render_multiday(frame, days, n_meals, adj_lbl, cal, prot, gluc, lip):
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

        # Bouton PDF global
        pr = ctk.CTkFrame(hdr_card, fg_color="transparent")
        pr.pack(fill="x", padx=16, pady=(0,10))
        def _export_multi_pdf():
            try:
                from data import pdf_utils as _pu
                _pu.export_multiday_plan_pdf(app, days, ask_path=True)
            except Exception as ex:
                from tkinter import messagebox as _mb
                _mb.showerror("ERAGROK", f"Erreur PDF : {ex}")
        mk_btn(pr, "📄  Exporter PDF complet", _export_multi_pdf,
               color=TH.ACCENT, hover=TH.ACCENT_HOVER,
               width=200, height=TH.BTN_SM).pack(side="right")

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
