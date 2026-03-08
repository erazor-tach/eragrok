# data/nutrition_module.py — ERAGROK  ·  Dark Bodybuilding
import os, math, csv, calendar as pycal, datetime
import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
from tkcalendar import Calendar
from data import utils
from data import db as _db
try:
    from data import features_module as _feat
except Exception:
    _feat = None
from data.theme import (
    TH, mk_btn, mk_card, mk_card2, mk_entry, mk_combo,
    mk_textbox, mk_label, mk_title, mk_sep, mk_badge,
    mk_scrollframe, screen_header, apply_treeview_style,
)

# matplotlib optionnel (courbe poids uniquement)
try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
except Exception:
    plt = FigureCanvasTkAgg = None
# PDF centralisé
try:
    from data import pdf_utils as _pdf
    _PDF_OK = True
except ImportError:
    _PDF_OK = False


# ── Helpers ───────────────────────────────────────────────────────────────────
def _d2s(d): return d.strftime("%d/%m/%Y")

def _parse(s):
    for fmt in ["%d/%m/%Y", "%Y-%m-%d", "%m/%d/%Y"]:
        try: return datetime.datetime.strptime(str(s).strip(), fmt).date()
        except Exception: pass
    return None

def _last_entries(app, fname, n=1):
    if not getattr(app, "current_user", None): return []
    try:
        rows = _db.nutrition_get_last_n(app, n)
        return [" | ".join([r.get("date",""), r.get("poids",""), r.get("calories",""),
                            r.get("proteines",""), r.get("glucides",""), r.get("lipides",""),
                            r.get("note","")]) for r in rows]
    except Exception: return []

def _sort_tree(app, col):
    """Tri du treeview historique par colonne (clic en-tête)."""
    if not hasattr(app, "nutrition_tree"): return
    items = [(app.nutrition_tree.set(iid, col), iid)
             for iid in app.nutrition_tree.get_children("")]
    rev = getattr(app, "_tree_sort_rev", {})
    ascending = not rev.get(col, False)
    items.sort(reverse=not ascending)
    for idx, (_, iid) in enumerate(items):
        app.nutrition_tree.move(iid, "", idx)
    rev[col] = not ascending
    app._tree_sort_rev = rev


def _refresh_tree(app, fichier):
    if not hasattr(app, "nutrition_tree"): return
    for r in app.nutrition_tree.get_children():
        app.nutrition_tree.delete(r)
    rows_data = _db.nutrition_get_all(app)
    if not rows_data: return
    try:
        for _rowdict in rows_data:
            _row_id = _rowdict.get("id", None)
            app.nutrition_tree.insert("", "end",
                iid=str(_row_id) if _row_id else "",
                values=(
                    _rowdict.get("date", ""),
                    _rowdict.get("poids", ""),
                    _rowdict.get("calories", ""),
                    _rowdict.get("note", ""),
                ))
    except Exception: pass


# ── Calculs ───────────────────────────────────────────────────────────────────
def _update_calc(app):
    try:
        poids = app.poids_var.get().strip().replace(",", ".")
        if not poids: return
        ui = getattr(app, "user_info", None)
        if not ui: return
        # Âge calculé dynamiquement depuis date_naissance
        dn  = ui.get("date_naissance", "")
        age = str(utils.age_depuis_naissance(dn) or ui.get("age") or "")
        if not age: return
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
                text=f"🔥  {cal:.0f} kcal  (TDEE {nut['tdee']:.0f} kcal | ajust. {adj*100:+.0f}%)")
        if getattr(app, "proteines_label", None):
            app.proteines_label.configure(text=f"🥩  {nut['proteines']:.0f} g")
        if getattr(app, "glucides_label",  None):
            app.glucides_label.configure(text=f"🍚  {g:.0f} g")
        if getattr(app, "lipides_label",   None):
            app.lipides_label.configure(text=f"🥑  {l:.0f} g")
        app._last_cal = int(round(cal))
        # ── Redessiner la jauge IMC si le poids a changé ─────────────────────
        try:
            p = float(poids)
            t = float(ui.get("taille", 0))
            if p > 0 and t > 0:
                imc_v, _ = utils.calculer_imc(p, t)
                gf = getattr(app, "_imc_frame", None)
                if gf and gf.winfo_exists():
                    _imc_gauge(gf, imc_v, p, t)
        except Exception:
            pass
        # ── Redessiner le camembert macros ────────────────────────────────────
        try:
            pf = getattr(app, "_macro_pie_frame", None)
            if pf and pf.winfo_exists() and _feat:
                for w in pf.winfo_children(): w.destroy()
                pie = _feat.render_macro_pie(
                    pf, cal,
                    nut.get("proteines", 0),
                    (cal * (0.45 if "perte" not in ui.get("objectif","").lower() else 0.37)) / 4,
                    (cal * (0.25 if "perte" not in ui.get("objectif","").lower() else 0.23)) / 9,
                    app=app,
                )
                if pie:
                    pie.pack()
        except Exception:
            pass
    except Exception: pass


def _save_nutrition(app):
    if not getattr(app, "current_user", None):
        messagebox.showerror("ERAGROK", "Sélectionne un élève."); return
    sel = {datetime.date.today()}
    poids = app.poids_var.get().strip().replace(",", ".")
    age   = app.age_var.get().strip()
    note  = ""
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
    for d in sorted(sel):
        try:
            _db.nutrition_insert(app, _d2s(d), poids, age, c,
                                  f"{p:.0f}", f"{g:.0f}", f"{l:.0f}", note)
        except Exception as e:
            messagebox.showerror("ERAGROK", str(e)); return
    messagebox.showinfo("ERAGROK",
                        f"✔  Nutrition sauvegardée pour {len(sel)} date(s).")
    _refresh_tree(app, "")


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
    if not sel:
        messagebox.showinfo("ERAGROK", "Sélectionne au moins une ligne.")
        return
    n = len(sel)
    msg = f"Supprimer {n} ligne(s) ?" if n > 1 else "Supprimer la ligne ?"
    if not messagebox.askyesno("Confirmer", msg): return
    try:
        for iid in sel:
            try:
                _db.nutrition_delete_by_id(app, int(iid))
            except Exception:
                # Fallback par date si l'iid n'est pas un entier
                vals = app.nutrition_tree.item(iid, "values")
                if vals:
                    _db.nutrition_delete_by_date(app, vals[0])
        _refresh_tree(app, "")
    except Exception as e:
        messagebox.showerror("ERAGROK", str(e))


def _delete_all(app):
    rows = app.nutrition_tree.get_children()
    if not rows:
        messagebox.showinfo("ERAGROK", "L'historique est déjà vide.")
        return
    n = len(rows)
    msg_all = f"Supprimer TOUTES les {n} entrees ?\nCette action est irreversible."
    if not messagebox.askyesno("Confirmer", msg_all):
        return
    try:
        _db.nutrition_delete_all(app)
        _refresh_tree(app, "")
        messagebox.showinfo("ERAGROK", f"✅ {n} entrées supprimées.")
    except Exception as e:
        messagebox.showerror("ERAGROK", str(e))


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


# ── Jauge IMC — barre horizontale pleine largeur ─────────────────────────────
def _imc_gauge(parent, imc, poids, taille):
    """
    Jauge IMC redessinée : barre horizontale pleine largeur.
    Design :
      • Grande valeur IMC + catégorie colorée en haut
      • Barre colorée 7 zones pleine largeur avec étiquettes au-dessus
      • Curseur triangle + halo sous la barre à la position exacte
      • Message différentiel + poids cibles en bas
    Aucune dépendance externe.
    """
    for w in parent.winfo_children():
        w.destroy()

    # ── Dimensions ─────────────────────────────────────────────────────────────
    W, H = 640, 195
    PAD  = 28          # marge gauche/droite
    BAR_Y    = 90      # y haut de la barre
    BAR_H    = 26      # hauteur barre
    LABEL_Y  = BAR_Y - 14   # y des étiquettes zone (au-dessus)
    CURSOR_Y = BAR_Y + BAR_H + 14  # y pointe du triangle curseur

    BG = TH.BG_CARD2

    cv = tk.Canvas(parent, width=W, height=H, bg=BG, highlightthickness=0)
    cv.pack(anchor="center", padx=8, pady=6)

    # ── Zones (IMC_MIN → IMC_MAX) ──────────────────────────────────────────────
    ZONES = [
        (0.0,  16.0, "#1d4ed8", "Dénutrition"),
        (16.0, 18.5, "#60a5fa", "Maigreur"),
        (18.5, 25.0, "#22c55e", "Normal"),
        (25.0, 30.0, "#f59e0b", "Surpoids"),
        (30.0, 35.0, "#f97316", "Obésité I"),
        (35.0, 40.0, "#ef4444", "Obésité II"),
        (40.0, 45.0, "#7f1d1d", "Obésité III"),
    ]
    IMC_MIN = 0.0
    IMC_MAX = 45.0
    BAR_W   = W - 2 * PAD  # largeur utile de la barre

    def imc_to_x(v):
        """Convertit une valeur IMC en coordonnée X pixel."""
        ratio = max(0.0, min(1.0, (v - IMC_MIN) / (IMC_MAX - IMC_MIN)))
        return PAD + ratio * BAR_W

    # ── Fond barre (arrondi simulé par rectangle + deux ovales) ───────────────
    r = BAR_H // 2
    cv.create_rectangle(PAD + r, BAR_Y, W - PAD - r, BAR_Y + BAR_H,
                        fill="#222222", outline="")
    cv.create_oval(PAD, BAR_Y, PAD + 2*r, BAR_Y + BAR_H,
                   fill="#222222", outline="")
    cv.create_oval(W - PAD - 2*r, BAR_Y, W - PAD, BAR_Y + BAR_H,
                   fill="#222222", outline="")

    # ── Segments colorés ───────────────────────────────────────────────────────
    for i, (lo, hi, col, lbl) in enumerate(ZONES):
        x0 = imc_to_x(lo)
        x1 = imc_to_x(hi)
        mid_x = (x0 + x1) / 2
        # Rectangle de la zone
        cv.create_rectangle(x0, BAR_Y, x1, BAR_Y + BAR_H, fill=col, outline="")

        # Séparateur vertical entre zones (sauf bords)
        if i > 0:
            cv.create_line(x0, BAR_Y + 2, x0, BAR_Y + BAR_H - 2,
                           fill="#1a1a1a",
                           width=1)

        # Étiquette de zone AU-DESSUS de la barre
        seg_w = x1 - x0
        short = lbl.split()[0]  # premier mot seulement
        if seg_w > 28:
            font_size = 7 if seg_w < 46 else 8
            cv.create_text(mid_x, LABEL_Y, text=short,
                           fill=col, font=("Inter", font_size, "bold"),
                           anchor="center")

        # Valeur IMC min de chaque zone en bas de barre (sauf 0)
        if lo > 0:
            tick_x = imc_to_x(lo)
            cv.create_line(tick_x, BAR_Y + BAR_H, tick_x, BAR_Y + BAR_H + 5,
                           fill="#555555", width=1)
            cv.create_text(tick_x, BAR_Y + BAR_H + 13,
                           text=str(lo).rstrip("0").rstrip("."),
                           fill="#666666", font=("Inter", 7), anchor="center")

    # Bords arrondis par-dessus
    cv.create_arc(PAD, BAR_Y, PAD + 2*r, BAR_Y + BAR_H,
                  start=90, extent=180, fill=ZONES[0][2], outline="", style="pieslice")
    cv.create_arc(W - PAD - 2*r, BAR_Y, W - PAD, BAR_Y + BAR_H,
                  start=270, extent=180, fill=ZONES[-1][2], outline="", style="pieslice")

    # ── Curseur (triangle + halo) à la position IMC ───────────────────────────
    zone_col = "#aaaaaa"
    zone_lbl = "—"
    imc_display = imc

    if imc is not None:
        # Trouver la zone
        for lo, hi, col, lbl in ZONES:
            if lo <= imc < hi:
                zone_col = col
                zone_lbl = lbl
                break
        else:
            zone_col = ZONES[-1][2]
            zone_lbl = ZONES[-1][3]

        cx_cur = imc_to_x(max(IMC_MIN, min(IMC_MAX - 0.01, imc)))

        # Halo coloré derrière le triangle
        cv.create_oval(cx_cur - 10, CURSOR_Y - 10,
                       cx_cur + 10, CURSOR_Y + 10,
                       fill=zone_col, outline="", stipple="gray50")

        # Triangle curseur (pointe vers le haut)
        TRI = 8
        cv.create_polygon(
            cx_cur,       BAR_Y + BAR_H + 3,
            cx_cur - TRI, CURSOR_Y + TRI,
            cx_cur + TRI, CURSOR_Y + TRI,
            fill=zone_col, outline=BG, width=2,
        )

        # Ligne verticale du curseur sur la barre
        cv.create_line(cx_cur, BAR_Y, cx_cur, BAR_Y + BAR_H,
                       fill="white", width=2)

    # ── Grande valeur IMC + catégorie (en haut) ────────────────────────────────
    if imc is not None:
        # Gros chiffre IMC
        cv.create_text(W // 2, 22,
                       text=f"{imc:.1f}",
                       fill=zone_col,
                       font=("Inter", 32, "bold"),
                       anchor="center")
        # Label IMC en petit à gauche du chiffre
        cv.create_text(W // 2 - 64, 22,
                       text="IMC",
                       fill="#666666",
                       font=("Inter", 11, "bold"),
                       anchor="center")
        # Catégorie
        cv.create_text(W // 2, 50,
                       text=zone_lbl,
                       fill=zone_col,
                       font=("Inter", 12, "bold"),
                       anchor="center")
    else:
        cv.create_text(W // 2, 30,
                       text="IMC  —",
                       fill="#555555",
                       font=("Inter", 22, "bold"),
                       anchor="center")
        cv.create_text(W // 2, 52,
                       text="Renseigne poids et taille",
                       fill="#444444",
                       font=("Inter", 9),
                       anchor="center")

    # ── Message différentiel + poids cibles (en bas) ──────────────────────────
    if imc is not None and poids and taille:
        try:
            tm   = float(taille) / 100
            p    = float(poids)
            p_lo = round(18.5 * tm ** 2, 1)
            p_hi = round(25.0 * tm ** 2, 1)
            p_id = round(22.0 * tm ** 2, 1)

            if p < p_lo:
                diff_txt = f"↑  +{p_lo - p:.1f} kg pour atteindre IMC 18.5"
                diff_col = "#60a5fa"
            elif p > p_hi:
                diff_txt = f"↓  −{p - p_hi:.1f} kg pour atteindre IMC 25"
                diff_col = "#f59e0b"
            else:
                diff_txt = f"✓  Dans la zone normale"
                diff_col = "#22c55e"

            cv.create_text(W // 2, H - 32,
                           text=diff_txt,
                           fill=diff_col,
                           font=("Inter", 9, "bold"),
                           anchor="center")
            cv.create_text(W // 2, H - 14,
                           text=f"Normal : {p_lo} – {p_hi} kg     Idéal : {p_id} kg",
                           fill="#555555",
                           font=("Inter", 8),
                           anchor="center")
        except Exception:
            pass


# ════════════════════════════════════════════════════════════════════════════
#  DASHBOARD
# ════════════════════════════════════════════════════════════════════════════
def _read_last_cycle(app):
    """Lit la dernière entrée de cycle depuis SQLite."""
    if not getattr(app, "current_user", None): return None
    try:
        row = _db.cycle_get_active(app)
        if not row: return None
        return {
            "debut":    row.get("debut", "—"),
            "fin":      row.get("fin_estimee", "—"),
            "longueur": row.get("longueur_sem", "—"),
            "produits": row.get("produits_doses", ""),
            "note":     row.get("note", ""),
        }
    except Exception: return None


def _render_cycle_card_inline(parent, app):
    """
    Contenu cycle hormonal injecté dans un frame déjà existant
    (sans créer de mk_card ni de titre — appelé depuis render_dashboard).
    """
    try:
        from data import cycle_module as _cm
        PRODUCT_INFO = _cm.PRODUCT_INFO
    except Exception:
        PRODUCT_INFO = {}
    cycle = _read_last_cycle(app)
    _draw_cycle_body(parent, cycle, PRODUCT_INFO, show_buttons=True, app=app)


def _draw_cycle_body(c, cycle, PRODUCT_INFO, show_buttons=False, app=None):
    """Corps partagé du rendu cycle — utilisé par inline + carte standalone."""
    if not cycle:
        mk_label(c, "  Aucun cycle enregistré.",
                 size="small", color=TH.TEXT_MUTED).pack(anchor="w", padx=16, pady=(0, 8))
        return

    # ── Ligne dates ───────────────────────────────────────────────────────────
    dr = ctk.CTkFrame(c, fg_color=TH.BG_CARD2, corner_radius=8)
    dr.pack(fill="x", padx=16, pady=(0, 8))
    dr_inner = ctk.CTkFrame(dr, fg_color="transparent")
    dr_inner.pack(fill="x", padx=12, pady=8)
    for lbl, val, col in [
        ("📅 Début",    cycle["debut"],               TH.TEXT),
        ("🏁 Fin est.", cycle["fin"],                  TH.ACCENT_GLOW),
        ("⏱ Durée",    f"{cycle['longueur']} sem.",   TH.TEXT_SUB),
    ]:
        cell = ctk.CTkFrame(dr_inner, fg_color="transparent")
        cell.pack(side="left", padx=14)
        mk_label(cell, lbl,         size="small", color=TH.TEXT_MUTED).pack(anchor="w")
        mk_label(cell, val or "—",  size="body",  color=col).pack(anchor="w")

    # ── Produits + infos ──────────────────────────────────────────────────────
    if cycle["produits"]:
        mk_label(c, "  Produits du stack :", size="small",
                 color=TH.TEXT_ACCENT).pack(anchor="w", padx=16, pady=(4, 4))
        entries = [p.strip() for p in cycle["produits"].split("|") if p.strip()]
        dang_scores = []
        for entry in entries:
            parts     = entry.split(":", 1)
            prod_name = parts[0].strip()
            prod_dose = parts[1].strip() if len(parts) > 1 else ""
            info      = PRODUCT_INFO.get(prod_name, {})
            dang      = info.get("dangerosite", "")
            stars     = dang.count("★")
            dang_scores.append(stars)
            dang_col  = {0:"#555555",1:"#22c55e",2:"#84cc16",
                         3:"#f59e0b",4:"#ef4444",5:"#7f1d1d"}.get(stars, TH.TEXT_SUB)
            row = ctk.CTkFrame(c, fg_color=TH.BG_CARD2, corner_radius=6)
            row.pack(fill="x", padx=16, pady=2)
            top = ctk.CTkFrame(row, fg_color="transparent")
            top.pack(fill="x", padx=10, pady=(6, 2))
            mk_label(top, f"• {prod_name}", size="small", color=TH.TEXT).pack(side="left")
            if prod_dose:
                mk_badge(top, prod_dose,
                         color=TH.ACCENT_DIM,
                         text_color=TH.ACCENT_GLOW).pack(side="left", padx=8)
            if info:
                det = ctk.CTkFrame(row, fg_color="transparent")
                det.pack(fill="x", padx=20, pady=(0, 6))
                utilite  = info.get("utilite",  "")
                demi_vie = info.get("demi_vie", "")
                notes_p  = info.get("notes",    "")
                dose_ref = info.get("dose_min", "")
                if utilite or demi_vie:
                    rl = ctk.CTkFrame(det, fg_color="transparent")
                    rl.pack(fill="x")
                    if utilite:
                        mk_label(rl, f"🎯 {utilite}",  size="small",
                                 color=TH.TEXT_SUB).pack(side="left", padx=(0,16))
                    if demi_vie:
                        mk_label(rl, f"⏲ {demi_vie}", size="small",
                                 color=TH.TEXT_MUTED).pack(side="left")
                rl2 = ctk.CTkFrame(det, fg_color="transparent")
                rl2.pack(fill="x", pady=(2,0))
                if dose_ref:
                    mk_label(rl2, f"💊 Réf: {dose_ref}", size="small",
                             color=TH.TEXT_MUTED).pack(side="left", padx=(0,12))
                if dang:
                    mk_label(rl2, f"⚠ {dang}", size="small",
                             color=dang_col).pack(side="left")
                if notes_p:
                    mk_label(row, f"    ⚡ {notes_p}", size="small",
                             color="#cc8800").pack(anchor="w", padx=20, pady=(0,6))
        if dang_scores:
            max_dang = max(dang_scores)
            risk_txt = {0:"—",1:"✅ Faible",2:"✅ Modéré",
                        3:"⚠️  Élevé",4:"🔴 Très élevé",5:"🔴 Extrême"}.get(max_dang,"—")
            risk_col = {0:"#555",1:"#22c55e",2:"#84cc16",
                        3:"#f59e0b",4:"#ef4444",5:"#7f1d1d"}.get(max_dang,TH.TEXT_SUB)
            rr = ctk.CTkFrame(c, fg_color="transparent")
            rr.pack(fill="x", padx=16, pady=(6,4))
            mk_label(rr, "Risque stack :", size="small",
                     color=TH.TEXT_MUTED, width=100).pack(side="left")
            mk_label(rr, risk_txt, size="body", color=risk_col).pack(side="left")

    # ── Note utilisateur ──────────────────────────────────────────────────────
    if cycle.get("note"):
        note_f = ctk.CTkFrame(c, fg_color=TH.BG_CARD2, corner_radius=6)
        note_f.pack(fill="x", padx=16, pady=(4,10))
        mk_label(note_f,
                 f"📝  {cycle['note'][:120]}{'…' if len(cycle['note'])>120 else ''}",
                 size="small", color=TH.TEXT_SUB).pack(anchor="w", padx=12, pady=6)

    # ── Boutons Ouvrir / PDF ──────────────────────────────────────────────────
    if show_buttons and app:
        br = ctk.CTkFrame(c, fg_color="transparent")
        br.pack(anchor="w", padx=14, pady=(0,14))
        mk_btn(br, "Ouvrir",
               lambda: __import__("data.cycle_module")
                       .cycle_module.show_cycle_disclaimer(app),
               color=TH.WARNING, hover=TH.WARNING_HVR,
               width=100, height=TH.BTN_SM).pack(side="left", padx=3)
        mk_btn(br, "📄 PDF Cycle",
               lambda: _do_cycle_pdf_export(app),
               color=TH.ACCENT, hover=TH.ACCENT_HOVER,
               width=110, height=TH.BTN_SM).pack(side="left", padx=3)


def _render_cycle_card(parent, app):
    """
    Carte cycle dashboard — version détaillée :
    • Dates début/fin + longueur
    • Produits avec dose, utilité, dangérosité, demi-vie, notes produit
    • Risques agrégés (danger max du stack)
    • Note utilisateur
    """
    try:
        from data import cycle_module as _cm
        PRODUCT_INFO = _cm.PRODUCT_INFO
    except Exception:
        PRODUCT_INFO = {}

    cycle = _read_last_cycle(app)

    c = mk_card(parent)
    c.pack(fill="x", pady=(0, 14))
    mk_title(c, "  💉  CYCLE HORMONAL").pack(anchor="w", padx=16, pady=(14, 6))
    mk_sep(c).pack(fill="x", padx=16, pady=(0, 10))

    _draw_cycle_body(c, cycle, PRODUCT_INFO, show_buttons=True, app=app)


def _do_cycle_pdf_export(app):
    """Exporte le PDF cycle en demandant le chemin."""
    try:
        from data import pdf_utils
        pdf_utils.export_cycle_pdf(app, ask_path=True)
    except ImportError:
        from tkinter import messagebox
        messagebox.showerror("ERAGROK", "pdf_utils.py manquant dans data/")


def render_dashboard(app):
    """
    Dashboard principal ERAGROK — architecture 2 colonnes.
    Ordre :
      1. Carte PROFIL & MACROS  (full width)
      2. Ligne 2 cols : Graphique poids (60%) | Cycle hormonal (40%)
      3. Timeline cycle         (full width)
      4. Plan alimentaire       (full width)
      5. Semaines en cours / suivante (2 cols, sans section cycle)
    """
    # ── Nettoyer les canvases matplotlib AVANT de détruire les widgets ─────────
    # (évite bgerror check_dpi_scaling / update après navigation)
    for _c, _f in getattr(app, "_mpl_canvases", []):
        try:
            from data.features_module import _cancel_mpl
            _cancel_mpl(_c, _f)
        except Exception:
            pass
    app._mpl_canvases = []
    for w in app.content.winfo_children(): w.destroy()

    screen_header(app.content, "🏠  DASHBOARD",
                  user_name=app.selected_user_name)
    scroll = mk_scrollframe(app.content)
    scroll.pack(fill="both", expand=True)

    # ── Variables StringVar ───────────────────────────────────────────────────
    for attr in ["poids_var", "age_var", "adjustment_var"]:
        if not hasattr(app, attr): setattr(app, attr, tk.StringVar())

    dp = ""
    last = _last_entries(app, "nutrition.csv", 1)
    if last:
        try: dp = last[0].split(" | ")[1]
        except Exception: pass
    if not dp and getattr(app, "user_info", None):
        p = app.user_info.get("poids")
        if p is not None:
            dp = str(int(float(p))) if float(p).is_integer() else str(p)
    app.poids_var.set(dp)
    dadj = app.user_info.get("ajustement", "Maintien (0%)") if app.user_info else "Maintien (0%)"
    if dadj not in utils.ADJUSTMENTS: dadj = "Maintien (0%)"
    app.adjustment_var.set(dadj)

    # ═════════════════════════════════════════════════════════════════════════
    # SECTION 1 — PROFIL & MACROS
    # ═════════════════════════════════════════════════════════════════════════
    nc = mk_card(scroll)
    nc.pack(fill="x", padx=0, pady=(0, 14))
    mk_title(nc, "  👤  PROFIL & MACROS DU JOUR").pack(
        anchor="w", padx=16, pady=(14, 6))
    mk_sep(nc).pack(fill="x", padx=16, pady=(0, 10))

    # ── Ligne inputs ──────────────────────────────────────────────────────────
    ir_wrap = ctk.CTkFrame(nc, fg_color="transparent")
    ir_wrap.pack(anchor="center", pady=(0, 8))
    ir = ctk.CTkFrame(ir_wrap, fg_color="transparent")
    ir.pack(anchor="center")

    cc_p = ctk.CTkFrame(ir, fg_color="transparent")
    cc_p.pack(side="left", padx=(0, 16))
    mk_label(cc_p, "Poids (kg)", size="small",
             color=TH.TEXT_SUB).pack(anchor="center", pady=(0, 4))
    e_p = mk_entry(cc_p, width=100)
    e_p.configure(textvariable=app.poids_var); e_p.pack()

    mc2 = ctk.CTkFrame(ir, fg_color="transparent")
    mc2.pack(side="left")
    mk_label(mc2, "Ajustement", size="small",
             color=TH.TEXT_SUB).pack(anchor="center", pady=(0, 4))
    acb = mk_combo(mc2, list(utils.ADJUSTMENTS.keys()), width=300,
                   command=lambda v: _update_calc(app))
    acb.configure(variable=app.adjustment_var); acb.pack()

    # ── Macros + camembert ────────────────────────────────────────────────────
    rrow = ctk.CTkFrame(nc, fg_color="transparent")
    rrow.pack(anchor="center", pady=(0, 8))

    def _macro_col(parent, label, color):
        col = ctk.CTkFrame(parent, fg_color="transparent")
        col.pack(side="left", padx=20)
        mk_label(col, label, size="small", color=TH.TEXT_MUTED).pack(anchor="center")
        lbl = ctk.CTkLabel(col, text="—", font=TH.F_H3, text_color=color)
        lbl.pack(anchor="center", pady=(2, 0))
        return lbl

    app.calories_label  = _macro_col(rrow, "🔥  Calories",  TH.ACCENT_GLOW)
    app.proteines_label = _macro_col(rrow, "🥩  Protéines", "#4aaa4a")
    app.glucides_label  = _macro_col(rrow, "🍚  Glucides",  "#3b82f6")
    app.lipides_label   = _macro_col(rrow, "🥑  Lipides",   "#a855f7")
    app._macro_pie_frame = ctk.CTkFrame(rrow, fg_color="transparent")
    app._macro_pie_frame.pack(side="left", padx=12)

    # ── IMC + métriques ───────────────────────────────────────────────────────
    imc_val = poids_val = taille_val = None
    imc_cat = ("—", TH.TEXT)
    if getattr(app, "user_info", None):
        try:
            poids_val  = float(dp or app.user_info.get("poids", 0))
            taille_val = float(app.user_info.get("taille", 0))
            imc_val, imc_cat = utils.calculer_imc(poids_val, taille_val)
        except Exception: pass

    hg = ctk.CTkFrame(nc, fg_color="transparent")
    hg.pack(fill="x", padx=16, pady=(0, 8))

    met = ctk.CTkFrame(hg, fg_color="transparent")
    met.pack(side="left", padx=(0, 20), pady=6, anchor="n")
    def mrow(lbl, val, col=TH.TEXT):
        r = ctk.CTkFrame(met, fg_color="transparent")
        r.pack(anchor="w", pady=5)
        mk_label(r, lbl,  size="small", color=TH.TEXT_SUB, width=100).pack(side="left")
        mk_label(r, val,  size="body",  color=col).pack(side="left")
    mrow("⚖️  Poids", f"{poids_val:.1f} kg" if poids_val else "—")
    mrow("📏  IMC",
         f"{imc_val:.1f} — {imc_cat[0]}" if imc_val else "—",
         col=TH.ACCENT_GLOW)

    gf = mk_card2(hg)
    gf.pack(side="left", fill="both", expand=True, pady=6)
    _imc_gauge(gf, imc_val, poids_val, taille_val)
    app._imc_frame = gf

    # ── Alerte PCT ────────────────────────────────────────────────────────────
    try:
        msg, col = _feat.get_pct_alert(app) if _feat else (None, None)
        if msg:
            pct_alert = ctk.CTkFrame(nc, fg_color="#0a0d2b", corner_radius=6)
            pct_alert.pack(fill="x", padx=16, pady=(0, 10))
            mk_label(pct_alert, f"  {msg}", size="small",
                     color=col).pack(anchor="w", padx=10, pady=6)
    except Exception: pass

    # ── Traces poids / ajustement ─────────────────────────────────────────────
    try:
        for _tid in getattr(app, "_calc_trace_ids", []):
            try: app.poids_var.trace_remove("write", _tid)
            except Exception: pass
            try: app.adjustment_var.trace_remove("write", _tid)
            except Exception: pass
        app._calc_trace_ids = []
        _tid1 = app.poids_var.trace_add("write",      lambda *a: _update_calc(app))
        _tid2 = app.adjustment_var.trace_add("write", lambda *a: _update_calc(app))
        app._calc_trace_ids = [_tid1, _tid2]
    except Exception: pass
    _update_calc(app)

    # ═════════════════════════════════════════════════════════════════════════
    # SECTION 2 — 2 colonnes : Graphique poids (g) | Cycle hormonal (d)
    # ═════════════════════════════════════════════════════════════════════════
    row2 = ctk.CTkFrame(scroll, fg_color="transparent")
    row2.pack(fill="x", padx=0, pady=(0, 14))
    row2.columnconfigure(0, weight=3)   # 60 %
    row2.columnconfigure(1, weight=2)   # 40 %

    # ── Graphique poids ───────────────────────────────────────────────────────
    chart_card = mk_card(row2)
    chart_card.grid(row=0, column=0, sticky="nsew", padx=(0, 7))
    mk_title(chart_card, "  📈  ÉVOLUTION DU POIDS").pack(
        anchor="w", padx=16, pady=(14, 4))
    mk_sep(chart_card).pack(fill="x", padx=16, pady=(0, 8))
    if _feat:
        try: _feat.render_weight_chart(chart_card, app)
        except Exception: pass

    # ── Cycle hormonal ────────────────────────────────────────────────────────
    cycle_card = mk_card(row2)
    cycle_card.grid(row=0, column=1, sticky="nsew", padx=(7, 0))
    mk_title(cycle_card, "  💉  CYCLE HORMONAL").pack(
        anchor="w", padx=16, pady=(14, 6))
    mk_sep(cycle_card).pack(fill="x", padx=16, pady=(0, 10))
    try:
        _render_cycle_card_inline(cycle_card, app)
    except Exception: pass

    # ═════════════════════════════════════════════════════════════════════════
    # SECTION 3 — Timeline cycle
    # ═════════════════════════════════════════════════════════════════════════
    if _feat:
        try: _feat.render_cycle_timeline(scroll, app)
        except Exception: pass

    # ═════════════════════════════════════════════════════════════════════════
    # SECTION 4 — Plan alimentaire
    # ═════════════════════════════════════════════════════════════════════════
    if _feat:
        plan_card = mk_card(scroll)
        plan_card.pack(fill="x", padx=0, pady=(0, 14))

        pc_hdr = ctk.CTkFrame(plan_card, fg_color="transparent")
        pc_hdr.pack(fill="x", padx=16, pady=(14, 6))
        mk_title(pc_hdr, "  🍽  PLAN ALIMENTAIRE DU JOUR").pack(side="left")
        mk_sep(plan_card).pack(fill="x", padx=16, pady=(0, 8))

        last_plan  = getattr(app, "_last_meal_plan", None)
        _plan_data = None
        _cal = _prot = _gluc = _lip = 0
        _n_meals = 4
        _adj = ""
        if last_plan:
            _plan_data = (last_plan.get("plan") or
                          (last_plan["days"][0]["plan"] if last_plan.get("days") else None))
            _cal     = last_plan.get("cal",    2500)
            _prot    = last_plan.get("prot",   180)
            _gluc    = last_plan.get("gluc",   280)
            _lip     = last_plan.get("lip",    70)
            _n_meals = last_plan.get("n_meals", 4)
            _adj     = last_plan.get("adj",    "")
        _accepted = last_plan.get("accepted", False) if last_plan else False

        if _plan_data:
            badge_row = ctk.CTkFrame(plan_card, fg_color="transparent")
            badge_row.pack(fill="x", padx=16, pady=(0, 6))
            if _accepted:
                b = ctk.CTkFrame(badge_row, fg_color=TH.SUCCESS, corner_radius=4)
                b.pack(side="left")
                mk_label(b, "  ✅  Plan accepté  ", size="small",
                         color="#000").pack(padx=4, pady=2)

            else:
                mk_label(badge_row, "⏳  Plan généré — pas encore accepté",
                         size="small", color=TH.ACCENT_GLOW).pack(side="left")
                def _accept_and_goto_nutrition():
                    lp = getattr(app, "_last_meal_plan", None)
                    if lp: lp["accepted"] = True
                    show_nutrition_screen(app)
                mk_btn(badge_row, "✅  Accepter",
                       _accept_and_goto_nutrition,
                       color=TH.SUCCESS, hover=TH.SUCCESS_HVR,
                       width=110, height=TH.BTN_SM).pack(side="right")

            plan_scroll = mk_scrollframe(plan_card)
            plan_scroll.pack(fill="x", padx=8, pady=(0, 12))
            plan_scroll.configure(height=920)
            plan_inner = ctk.CTkFrame(plan_scroll, fg_color="transparent")
            plan_inner.pack(fill="both", expand=True)
            _days = last_plan.get("days") if last_plan else None
            _feat.render_plan_card(plan_inner, app, _plan_data,
                                   _cal, _prot, _gluc, _lip,
                                   n_meals=_n_meals, adj_lbl=_adj,
                                   show_pdf=False, days=_days)  # PDF dans cc_hdr
        else:
            pr = ctk.CTkFrame(plan_card, fg_color="transparent")
            pr.pack(fill="x", padx=16, pady=12)
            mk_label(pr, "Aucun plan — génère un plan depuis le générateur.",
                     size="small", color=TH.TEXT_MUTED).pack(side="left")
            mk_btn(pr, "⚡  Générer",
                   lambda: _feat.show_meal_generator(app),
                   color=TH.ACCENT, hover=TH.ACCENT_HOVER,
                   width=120, height=TH.BTN_SM).pack(side="right")

    # ═════════════════════════════════════════════════════════════════════════
    # SECTION 5 — Semaines (sans section cycle — déjà en section 2)
    # ═════════════════════════════════════════════════════════════════════════
    _render_week_view(app, scroll)




def _render_week_view(app, parent):
    """
    Affiche deux cartes côte à côte sous le dashboard principal :
      • Semaine EN COURS  (lundi→dimanche de la semaine courante)
      • Semaine SUIVANTE  (lundi→dimanche de la semaine prochaine)
    Chaque carte résume : entraînement planifié, nutrition moyenne, phase cycle.
    """
    import datetime as _dt

    today = _dt.date.today()
    # Lundi de la semaine courante
    monday_cur  = today - _dt.timedelta(days=today.weekday())
    monday_next = monday_cur + _dt.timedelta(weeks=1)

    wk_frame = ctk.CTkFrame(parent, fg_color="transparent")
    wk_frame.pack(fill="x", padx=24, pady=(0, 20))
    wk_frame.columnconfigure(0, weight=1)
    wk_frame.columnconfigure(1, weight=1)

    for col_idx, (monday, label) in enumerate([
        (monday_cur,  "SEMAINE EN COURS"),
        (monday_next, "SEMAINE SUIVANTE"),
    ]):
        sunday = monday + _dt.timedelta(days=6)
        date_range = f"{monday:%d/%m} → {sunday:%d/%m/%Y}"

        card = mk_card(wk_frame)
        card.grid(row=0, column=col_idx, sticky="nsew",
                  padx=(0, 10) if col_idx == 0 else (10, 0))

        # En-tête carte
        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.pack(fill="x", padx=16, pady=(14, 4))
        mk_title(hdr, f"  📅  {label}").pack(side="left")
        mk_label(hdr, date_range, size="small",
                 color=TH.TEXT_MUTED).pack(side="right")
        mk_sep(card).pack(fill="x", padx=16, pady=(0, 10))

        # ── Nutrition ──
        _render_week_nutrition(card, app, monday, sunday)
        # ── Entraînements ──
        _render_week_training(card, app, monday, sunday)
        # Cycle affiché dans la section 2 du dashboard — pas répété ici

        ctk.CTkFrame(card, fg_color="transparent", height=10).pack()


def _week_dates(monday, sunday):
    """Génère la liste des dates de la semaine."""
    import datetime as _dt
    d, out = monday, []
    while d <= sunday:
        out.append(d)
        d += _dt.timedelta(days=1)
    return out


def _parse_date_flex(s):
    """Parse souple de date — retourne datetime.date ou None."""
    import datetime as _dt
    if not s:
        return None
    s = str(s).strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y"):
        try:
            return _dt.datetime.strptime(s, fmt).date()
        except Exception:
            pass
    return None


def _render_week_training(card, app, monday, sunday):
    """
    Lit planning.csv et affiche pour chaque jour de la semaine :
      - Date + jour
      - Type d'entraînement (Programme)
      - Partie du corps / catégorie (Groupes / Types)
      - Technique + reps + charge (Line)
    """
    import os, csv as _csv
    week_dates = set(_week_dates(monday, sunday))
    DAY_FR = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]

    # planning.csv : [Date, Groupes, Programme, Types, Note, Line]
    sessions = []  # liste de dicts
    try:
        for r in _db.planning_get_all(app):
            d = _parse_date_flex(r.get("date",""))
            if d and d in week_dates:
                sessions.append({
                    "date":    d,
                    "groupes": r.get("groupes","").strip(),
                    "prog":    r.get("programme","").strip(),
                    "types":   r.get("types","").strip(),
                    "line":    r.get("line","").strip(),
                })
    except Exception:
        pass

    # Fallback entrainement.csv : [Date, Groupes musculaires, Programme, Note]
    if not sessions:
        fpath2 = os.path.join(utils.USERS_DIR, getattr(app, "current_user", ""), "entrainement.csv")
        if os.path.exists(fpath2):
            try:
                with open(fpath2, "r", newline="", encoding="utf-8") as f:
                    reader = _csv.reader(f)
                    next(reader, [])
                    for row in reader:
                        if not row: continue
                        d = _parse_date_flex(row[0])
                        if d and d in week_dates:
                            sessions.append({
                                "date":   d,
                                "groupes": row[1].strip() if len(row) > 1 else "",
                                "prog":   row[2].strip() if len(row) > 2 else "",
                                "types":  "",
                                "line":   row[3].strip() if len(row) > 3 else "",
                            })
            except Exception:
                pass

    mk_label(card, "🏋  Entraînement", size="small",
             color=TH.TEXT_ACCENT).pack(anchor="w", padx=16, pady=(0, 4))

    if not sessions:
        mk_label(card, "   Aucune séance planifiée",
                 size="small", color=TH.TEXT_MUTED).pack(anchor="w", padx=16)
        mk_sep(card).pack(fill="x", padx=16, pady=(8, 6))
        return

    # Grouper par jour de semaine : {date: {groupes, progs, techniques[]}}
    import re as _re
    from collections import defaultdict
    import datetime as _dt_t
    days_map = defaultdict(lambda: {"groupes": set(), "progs": set(), "lines": []})
    for s in sessions:
        d = s["date"]
        if s["groupes"]: days_map[d]["groupes"].add(s["groupes"])
        if s["prog"]:    days_map[d]["progs"].add(s["prog"])
        if s["line"]:
            clean = _re.sub(r"\s*\([A-Z0-9_]+\)\s*$", "", s["line"]).strip()
            if clean and clean not in days_map[d]["lines"]:
                days_map[d]["lines"].append(clean)

    # Afficher tous les jours Lun→Dim avec séance ou repos
    monday_date = monday  # lundi de la semaine
    for wd in range(7):
        d = monday_date + _dt_t.timedelta(days=wd)
        day_str = f"{DAY_FR[wd]} {d:%d/%m}"

        row_f = ctk.CTkFrame(card, fg_color=TH.BG_CARD2, corner_radius=6)
        row_f.pack(fill="x", padx=16, pady=2)

        l1 = ctk.CTkFrame(row_f, fg_color="transparent")
        l1.pack(fill="x", padx=10, pady=(4, 2))

        # Jour + date
        mk_label(l1, day_str, size="small",
                 color=TH.ACCENT_GLOW, width=68).pack(side="left")

        if d in days_map:
            info_d = days_map[d]
            # Muscles / groupes
            muscles = " · ".join(sorted(info_d["groupes"]))
            if muscles:
                mk_label(l1, f"💪 {muscles}", size="small",
                         color=TH.TEXT_SUB).pack(side="left", padx=(6, 0))
            # Programme badge
            for pg in sorted(info_d["progs"]):
                mk_badge(l1, pg, color=TH.ACCENT_DIM,
                         text_color=TH.ACCENT_GLOW).pack(side="left", padx=4)
            # Techniques (2 max pour compacité)
            techs = info_d["lines"][:2]
            if techs:
                l2 = ctk.CTkFrame(row_f, fg_color="transparent")
                l2.pack(fill="x", padx=12, pady=(0, 4))
                for t in techs:
                    mk_label(l2, f"  🔧 {t[:60]}{'…' if len(t)>60 else ''}",
                             size="small", color=TH.TEXT_MUTED).pack(anchor="w")
                if len(info_d["lines"]) > 2:
                    mk_label(l2, f"  + {len(info_d['lines'])-2} exercice(s)…",
                             size="small", color=TH.TEXT_MUTED).pack(anchor="w")
            else:
                ctk.CTkFrame(row_f, fg_color="transparent", height=3).pack()
        else:
            # Pas de séance planifiée ce jour
            mk_label(l1, "Repos", size="small", color=TH.TEXT_MUTED).pack(side="left", padx=6)
            ctk.CTkFrame(row_f, fg_color="transparent", height=3).pack()

    mk_sep(card).pack(fill="x", padx=16, pady=(8, 6))


def _render_week_nutrition(card, app, monday, sunday):
    """Lit nutrition.csv et affiche les moyennes calories/macros de la semaine."""
    import os, csv as _csv
    week_dates = set(_week_dates(monday, sunday))
    rows_week = []
    try:
        nut_rows = _db.nutrition_get_all(app)
        for r in nut_rows:
            d = _parse_date_flex(r.get("date",""))
            if d and d in week_dates:
                # Reproduire le format liste [date,poids,age,cal,prot,gluc,lip,note]
                rows_week.append([
                    r.get("date",""), r.get("poids",""), r.get("age",""),
                    r.get("calories",""), r.get("proteines",""),
                    r.get("glucides",""), r.get("lipides",""), r.get("note",""),
                ])
    except Exception:
        pass

    sub = ctk.CTkFrame(card, fg_color="transparent")
    sub.pack(fill="x", padx=16, pady=(0, 6))
    mk_label(sub, "🍎  Nutrition", size="small",
             color=TH.TEXT_ACCENT).pack(anchor="w")

    if rows_week:
        # Calculer moyennes  [Date, Poids, Age, Calories, Protéines, Glucides, Lipides, Note]
        def _avg(col):
            vals = []
            for r in rows_week:
                try:
                    v = float(r[col]) if len(r) > col and r[col].strip() else None
                    if v: vals.append(v)
                except Exception:
                    pass
            return sum(vals)/len(vals) if vals else None

        cal  = _avg(3); prot = _avg(4); gluc = _avg(5); lip = _avg(6)
        # Poids moyen
        pw = []
        for r in rows_week:
            try:
                v = float(r[1]) if len(r)>1 and r[1].strip() else None
                if v: pw.append(v)
            except Exception: pass
        poids_moy = sum(pw)/len(pw) if pw else None

        stats_row = ctk.CTkFrame(card, fg_color=TH.BG_CARD2, corner_radius=6)
        stats_row.pack(fill="x", padx=16, pady=2)
        n = len(rows_week)
        jours_txt = f"{n} jour{'s' if n > 1 else ''} enregistré{'s' if n > 1 else ''}"
        mk_label(stats_row, jours_txt, size="small",
                 color=TH.TEXT_SUB).pack(anchor="w", padx=8, pady=(4,2))
        for lbl, val, unit, col in [
            ("⚖️  Poids moy.",   poids_moy, "kg",   TH.TEXT),
            ("🔥  Calories moy.",cal,        "kcal", TH.ACCENT_GLOW),
            ("🥩  Prot. moy.",   prot,       "g",    "#22c55e"),
            ("🍚  Gluc. moy.",   gluc,       "g",    "#3b82f6"),
            ("🥑  Lip. moy.",    lip,        "g",    "#f59e0b"),
        ]:
            if val is None:
                continue
            rw = ctk.CTkFrame(stats_row, fg_color="transparent")
            rw.pack(fill="x", padx=8, pady=1)
            mk_label(rw, lbl, size="small", color=TH.TEXT_SUB,
                     width=120).pack(side="left")
            mk_label(rw, f"{val:.0f} {unit}", size="small",
                     color=col).pack(side="left")
    else:
        # Semaine future ou sans données → afficher les macros cibles du profil
        import datetime as _dtnow
        today_chk = _dtnow.date.today()
        if monday > today_chk:
            # Calculer macros cibles depuis le profil
            try:
                from data import utils as _utw
                ui_w = getattr(app, "user_info", {}) or {}
                dn_w = ui_w.get("date_naissance", "")
                age_w = str(_utw.age_depuis_naissance(dn_w) or ui_w.get("age") or "30")
                pv_w  = getattr(app, "poids_var", None)
                poids_w = (pv_w.get().strip() if pv_w else "") or str(ui_w.get("poids") or "80")
                nut_w = _utw.calculs_nutrition(
                    poids_w, age_w, ui_w.get("sexe"), ui_w.get("objectif"), ui_w.get("taille"))
                av_w  = getattr(app, "adjustment_var", None)
                adj_w = _utw.ADJUSTMENTS.get(
                    (av_w.get() if av_w else "") or "Maintien (0%)", 0.0)
                cal_w  = (nut_w["tdee"] * (1 + adj_w)) if nut_w else 2500
                obj_w  = ui_w.get("objectif", "").lower()
                if "masse"   in obj_w: cp_w, fp_w = 0.47, 0.23
                elif "perte" in obj_w: cp_w, fp_w = 0.37, 0.23
                else:                   cp_w, fp_w = 0.45, 0.25
                prot_w = nut_w["proteines"] if nut_w else cal_w * 0.30 / 4
                gluc_w = (cal_w * cp_w) / 4
                lip_w  = (cal_w * fp_w) / 9

                proj = ctk.CTkFrame(card, fg_color=TH.BG_CARD2, corner_radius=6)
                proj.pack(fill="x", padx=16, pady=2)
                mk_label(proj, "Objectifs nutritionnels cibles", size="small",
                         color=TH.TEXT_SUB).pack(anchor="w", padx=8, pady=(4, 2))
                for lbl_w, val_w, unit_w, col_w in [
                    ("🔥  Calories cible",  cal_w,  "kcal", TH.ACCENT_GLOW),
                    ("🥩  Protéines cible", prot_w, "g",    "#22c55e"),
                    ("🍚  Glucides cible",  gluc_w, "g",    "#3b82f6"),
                    ("🥑  Lipides cible",   lip_w,  "g",    "#f59e0b"),
                ]:
                    rw_w = ctk.CTkFrame(proj, fg_color="transparent")
                    rw_w.pack(fill="x", padx=8, pady=1)
                    mk_label(rw_w, lbl_w, size="small",
                             color=TH.TEXT_SUB, width=120).pack(side="left")
                    mk_label(rw_w, f"{val_w:.0f} {unit_w}", size="small",
                             color=col_w).pack(side="left")
            except Exception:
                mk_label(card, "   Semaine à venir — aucune donnée",
                         size="small", color=TH.TEXT_MUTED).pack(anchor="w", padx=16)
        else:
            mk_label(card, "   Aucune entrée nutrition cette semaine",
                     size="small", color=TH.TEXT_MUTED).pack(anchor="w", padx=16)

    mk_sep(card).pack(fill="x", padx=16, pady=(8, 6))


def _render_week_cycle(card, app, monday, sunday):
    """
    Affiche le cycle actif pour la semaine :
    - Phase + numéro de semaine calculé depuis la date de début
    - Chaque produit sur sa propre ligne : nom, DOSAGE en badge, 
      utilité, demi-vie, dangerosité étoiles, notes risque
    - Risque global du stack
    """
    import os, csv as _csv, datetime as _dt

    try:
        from data import cycle_module as _cm
        PINFO = _cm.PRODUCT_INFO
    except Exception:
        PINFO = {}

    # Lire le dernier cycle sauvegardé
    cycle_row = None
    try:
        _last = _db.cycle_get_active(app)
        if _last:
            cycle_row = [
                _last.get("debut",""), _last.get("fin_estimee",""),
                _last.get("longueur_sem","12"), _last.get("produits_doses",""),
                _last.get("note",""),
            ]
    except Exception:
        pass

    # En-tête
    mk_label(card, "💉  Cycle hormonal", size="small",
             color=TH.TEXT_ACCENT).pack(anchor="w", padx=16, pady=(0, 4))

    if cycle_row is None:
        mk_label(card, "   Aucun cycle enregistré.",
                 size="small", color=TH.TEXT_MUTED).pack(anchor="w", padx=16, pady=(0, 6))
        mk_sep(card).pack(fill="x", padx=16, pady=(4, 6))
        return

    # Colonnes : [0]=Début [1]=Fin est. [2]=Longueur(sem) [3]=Produits & doses [4]=Note
    debut_str  = cycle_row[0] if len(cycle_row) > 0 else ""
    fin_str    = cycle_row[1] if len(cycle_row) > 1 else ""
    longueur_s = cycle_row[2] if len(cycle_row) > 2 else "12"
    produits_s = cycle_row[3] if len(cycle_row) > 3 else ""
    note_s     = cycle_row[4] if len(cycle_row) > 4 else ""

    debut_date = _parse_date_flex(debut_str)
    try:
        n_weeks = int(longueur_s.strip())
    except Exception:
        n_weeks = 12

    # Calculer la semaine N dans le cycle
    phase = "—"
    phase_col = TH.TEXT_MUTED
    week_label = "—"
    cycle_actif = False
    washout_w = 2

    if debut_date:
        debut_monday = debut_date - _dt.timedelta(days=debut_date.weekday())
        delta_weeks  = (monday - debut_monday).days // 7
        if delta_weeks < 0:
            jours = (debut_date - monday).days
            phase = "AVANT CYCLE"
            phase_col = TH.TEXT_MUTED
            week_label = f"Début dans {jours}j"
        elif delta_weeks < n_weeks:
            phase = "CYCLE"
            phase_col = "#22c55e"
            week_label = f"S{delta_weeks+1} / {n_weeks}"
            cycle_actif = True
        elif delta_weeks < n_weeks + washout_w:
            phase = "WASHOUT"
            phase_col = "#f59e0b"
            week_label = f"Wash-out S{delta_weeks-n_weeks+1}/{washout_w}"
            cycle_actif = True
        else:
            phase = "TERMINÉ"
            phase_col = TH.TEXT_MUTED
            week_label = f"Fin : {fin_str}"

    # Bannière phase
    banner = ctk.CTkFrame(card, fg_color=TH.BG_CARD2, corner_radius=7)
    banner.pack(fill="x", padx=16, pady=(0, 6))
    brow = ctk.CTkFrame(banner, fg_color="transparent")
    brow.pack(fill="x", padx=10, pady=6)

    phase_bg = {"CYCLE":"#0d2b0d", "WASHOUT":"#2b1f00",
                "PCT":"#0a0d2b", "AVANT CYCLE":"#1a1a28",
                "TERMINÉ":"#1a1a1a"}.get(phase, TH.BG_CARD2)
    badge_f = ctk.CTkFrame(brow, fg_color=phase_bg, corner_radius=5)
    badge_f.pack(side="left", padx=(0, 10))
    mk_label(badge_f, f"  {phase}  ", size="small",
             color=phase_col).pack(padx=2, pady=3)
    mk_label(brow, week_label, size="small", color=TH.TEXT).pack(side="left")
    if debut_str:
        mk_label(brow, f"Début : {debut_str}", size="small",
                 color=TH.TEXT_MUTED).pack(side="right")

    # Produits avec tous les détails
    # Calculer la date de début PCT pour filtrer Clomid/Nolvadex
    _pct_start = None
    if debut_date:
        import datetime as _dt2
        _pct_start = debut_date + _dt2.timedelta(weeks=n_weeks + washout_w)

    # Produits PCT à masquer pendant le cycle actif (visibles seulement dès J-14)
    _PCT_NAMES = {"Clomiphene (Clomid)", "Tamoxifen (Nolvadex)"}

    def _show_this_product(entry_raw):
        """
        Retourne True si cet entry (brut depuis produits_s) doit être affiché.
        Règles :
         - [PCT]... → jamais (sauf si dans les 14 jours du PCT)
         - nom brut dans _PCT_NAMES → jamais (sauf si dans les 14 jours)
         - _J+... dans le nom → toujours filtré (clé de dose PCT)
        """
        pname = entry_raw.split(":")[0].strip()
        # Entrée taggée [PCT] ou clé composée
        if pname.startswith("[PCT]") or "_J+" in pname:
            if _pct_start is None:
                return False
            import datetime as _dt3
            days_before_pct = (_pct_start - monday).days
            return days_before_pct <= 14
        # Nom brut PCT
        if pname in _PCT_NAMES:
            if _pct_start is None:
                return False
            import datetime as _dt3
            days_before_pct = (_pct_start - monday).days
            return days_before_pct <= 14
        return True  # produit normal → toujours visible

    if not produits_s and (cycle_actif or phase == "AVANT CYCLE"):
        nf = ctk.CTkFrame(card, fg_color=TH.BG_CARD2, corner_radius=6)
        nf.pack(fill="x", padx=16, pady=2)
        mk_label(nf, "  Aucun produit renseigné — ouvre Cycle hormonal pour compléter.",
                 size="small", color=TH.TEXT_MUTED).pack(anchor="w", padx=10, pady=5)
    if produits_s and (cycle_actif or phase == "AVANT CYCLE"):
        entries = [p.strip() for p in produits_s.split("|") if p.strip()]
        # Filtrer les produits PCT selon la proximité de la date PCT
        entries = [e for e in entries if _show_this_product(e)]
        dang_scores = []

        for entry in entries:
            parts     = entry.split(":", 1)
            prod_name = parts[0].strip()
            prod_dose = parts[1].strip() if len(parts) > 1 else ""
            info      = PINFO.get(prod_name, {})

            dang_str = info.get("dangerosite", "")
            stars    = dang_str.count("★")
            dang_scores.append(stars if stars else 0)
            dang_col = {1:"#22c55e", 2:"#84cc16", 3:"#f59e0b",
                        4:"#ef4444", 5:"#7f1d1d"}.get(stars, TH.TEXT_SUB)

            row_f = ctk.CTkFrame(card, fg_color=TH.BG_CARD2, corner_radius=6)
            row_f.pack(fill="x", padx=16, pady=2)

            # Ligne 1 : nom + DOSAGE badge orange + étoiles danger
            l1 = ctk.CTkFrame(row_f, fg_color="transparent")
            l1.pack(fill="x", padx=10, pady=(5, 1))
            mk_label(l1, prod_name, size="small",
                     color=TH.TEXT).pack(side="left")
            if prod_dose:
                # Dose saisie par l'utilisateur → badge orange vif
                mk_badge(l1, f"💉 {prod_dose} mg/sem",
                         color=TH.ACCENT_DIM,
                         text_color=TH.ACCENT_GLOW).pack(side="left", padx=6)
            if info.get("dose_min") and info.get("dose_max"):
                mk_badge(l1, f"réf {info['dose_min']}–{info['dose_max']}",
                         color="#1a2a1a",
                         text_color=TH.TEXT_MUTED).pack(side="left", padx=2)
            elif info.get("dose_min"):
                mk_badge(l1, f"réf {info['dose_min']}",
                         color="#1a2a1a",
                         text_color=TH.TEXT_MUTED).pack(side="left", padx=2)
            if dang_str:
                mk_label(l1, dang_str, size="small",
                         color=dang_col).pack(side="right", padx=4)

            if info:
                utilite  = info.get("utilite", "")
                demi_vie = info.get("demi_vie", "")
                notes_p  = info.get("notes", "")

                # Ligne 2 : utilité + demi-vie
                if utilite or demi_vie:
                    l2 = ctk.CTkFrame(row_f, fg_color="transparent")
                    l2.pack(fill="x", padx=14, pady=(0, 1))
                    if utilite:
                        mk_label(l2, f"🎯 {utilite}", size="small",
                                 color=TH.TEXT_SUB).pack(side="left", padx=(0, 12))
                    if demi_vie:
                        mk_label(l2, f"⏲ {demi_vie}", size="small",
                                 color=TH.TEXT_MUTED).pack(side="left")

                # Ligne 3 : notes risques
                if notes_p:
                    l3 = ctk.CTkFrame(row_f, fg_color="transparent")
                    l3.pack(fill="x", padx=14, pady=(0, 5))
                    mk_label(l3, f"⚡ {notes_p}", size="small",
                             color="#cc8800").pack(side="left")
                else:
                    ctk.CTkFrame(row_f, fg_color="transparent", height=3).pack()
            else:
                ctk.CTkFrame(row_f, fg_color="transparent", height=4).pack()

        # Risque global
        if dang_scores and any(s > 0 for s in dang_scores):
            max_d   = max(dang_scores)
            risk_tx = {1:"✅ Faible", 2:"✅ Modéré", 3:"⚠️  Élevé",
                       4:"🔴 Très élevé", 5:"🔴 Extrême"}.get(max_d, "—")
            risk_cl = {1:"#22c55e", 2:"#84cc16", 3:"#f59e0b",
                       4:"#ef4444", 5:"#7f1d1d"}.get(max_d, TH.TEXT_MUTED)
            rr = ctk.CTkFrame(card, fg_color="transparent")
            rr.pack(fill="x", padx=16, pady=(5, 2))
            mk_label(rr, "Risque stack :", size="small",
                     color=TH.TEXT_MUTED, width=95).pack(side="left")
            mk_label(rr, risk_tx, size="small", color=risk_cl).pack(side="left")

        # Note utilisateur
        if note_s:
            nf = ctk.CTkFrame(card, fg_color=TH.BG_CARD2, corner_radius=6)
            nf.pack(fill="x", padx=16, pady=(3, 2))
            mk_label(nf,
                     f"📝 {note_s[:90]}{'…' if len(note_s)>90 else ''}",
                     size="small", color=TH.TEXT_SUB).pack(
                anchor="w", padx=10, pady=4)

    elif phase == "WASHOUT":
        wf = ctk.CTkFrame(card, fg_color=TH.BG_CARD2, corner_radius=6)
        wf.pack(fill="x", padx=16, pady=2)
        mk_label(wf, "  🚫  Arrêt de tous les produits du cycle",
                 size="small", color="#f59e0b").pack(anchor="w", padx=10, pady=6)

    # Avertissement PCT imminent (J-14 → J-7 → J)
    if _pct_start and phase in ("CYCLE", "WASHOUT"):
        import datetime as _dt4
        days_left = (_pct_start - monday).days
        if 0 < days_left <= 14:
            pct_f = ctk.CTkFrame(card, fg_color="#0a0d2b", corner_radius=6)
            pct_f.pack(fill="x", padx=16, pady=(4, 2))
            if days_left <= 7:
                msg = f"⚠️  PCT dans {days_left}j — Prépare Clomid & Nolvadex"
                col = "#ef4444"
            else:
                msg = f"📋  PCT dans {days_left}j — Anticiper la commande PCT"
                col = "#f59e0b"
            mk_label(pct_f, f"  {msg}", size="small",
                     color=col).pack(anchor="w", padx=10, pady=5)
        elif days_left <= 0 and phase == "WASHOUT":
            pct_f = ctk.CTkFrame(card, fg_color="#0a0d2b", corner_radius=6)
            pct_f.pack(fill="x", padx=16, pady=(4, 2))
            mk_label(pct_f, "  💊  PCT EN COURS — Clomid + Nolvadex",
                     size="small", color="#a855f7").pack(anchor="w", padx=10, pady=5)

    mk_sep(card).pack(fill="x", padx=16, pady=(8, 6))

# ════════════════════════════════════════════════════════════════════════════
#  ÉCRAN NUTRITION
# ════════════════════════════════════════════════════════════════════════════
def show_nutrition_screen(app):
    # ── Nettoyer les canvases matplotlib AVANT de détruire les widgets ─────────
    # (évite bgerror check_dpi_scaling / update après navigation)
    for _c, _f in getattr(app, "_mpl_canvases", []):
        try:
            from data.features_module import _cancel_mpl
            _cancel_mpl(_c, _f)
        except Exception:
            pass
    app._mpl_canvases = []
    for w in app.content.winfo_children(): w.destroy()

    screen_header(app.content, "🍎  NUTRITION",
                  user_name=app.selected_user_name,
                  back_cmd=app.show_dashboard)
    scroll = mk_scrollframe(app.content)
    scroll.pack(fill="both", expand=True)

    # ── Layout full-width (plus de colonne gauche) ──────────────────────────
    right = ctk.CTkFrame(scroll, fg_color="transparent")
    right.pack(fill="both", expand=True, padx=24, pady=20)

    for attr in ["poids_var", "age_var", "adjustment_var"]:
        if not hasattr(app, attr): setattr(app, attr, tk.StringVar())

    dp = ""
    if getattr(app, "user_info", None):
        p = app.user_info.get("poids")
        if p is not None: dp = str(int(float(p))) if float(p).is_integer() else str(p)
    app.poids_var.set(dp)
    dadj = app.user_info.get("ajustement", "Maintien (0%)") if app.user_info else "Maintien (0%)"
    if dadj not in utils.ADJUSTMENTS: dadj = "Maintien (0%)"
    app.adjustment_var.set(dadj)

    # ── Fonctions PDF (définies avant le cadre) ───────────────────────────────
    def _export_nutr_pdf():
        """Export PDF unique : historique nutrition + plan alimentaire."""
        try:
            from data import pdf_utils
            pdf_utils.export_nutrition_full_pdf(app, ask_path=True)
        except Exception as e:
            from tkinter import messagebox as _mb
            _mb.showerror("ERAGROK", f"Erreur PDF : {e}")

    # ── Calculateur repas (défini avant le cadre) ─────────────────────────────
    def _open_meal_calc_screen():
        def _apply(cal, prot, gluc, lip):
            try:
                import datetime as _dtmc, data.utils as _utmc
                ui  = getattr(app,"user_info",{}) or {}
                dn  = ui.get("date_naissance","")
                age = str(_utmc.age_depuis_naissance(dn) or ui.get("age") or "")
                p   = app.poids_var.get().strip().replace(",",".") or str(ui.get("poids",""))
                today_s = _dtmc.date.today().strftime("%d/%m/%Y")
                _db.nutrition_insert(app, today_s, p, age,
                    str(round(cal)), str(round(prot)),
                    str(round(gluc)), str(round(lip)), "calculateur repas")
                from tkinter import messagebox as _mb
                _mb.showinfo("ERAGROK", "✅ Repas enregistré.")
            except Exception:
                pass
        if _feat: _feat.show_meal_calculator(app, on_apply=_apply)

    # ── Cadre CALCULS NUTRITIONNELS ───────────────────────────────────────────
    cc = mk_card(right)
    cc.pack(fill="x", pady=(0, 14))

    # En-tête titre + boutons actions (gauche→droite : Plan alim | Calculateur | Exporter PDF | Sauvegarder)
    cc_hdr = ctk.CTkFrame(cc, fg_color="transparent")
    cc_hdr.pack(fill="x", padx=16, pady=(14, 6))
    mk_title(cc_hdr, "  📊  CALCULS NUTRITIONNELS").pack(side="left")

    # Boutons — ordre d'affichage G→D (pack side=right du plus à droite au plus à gauche)
    mk_btn(cc_hdr, "💾  Sauvegarder",
           lambda: _save_nutrition(app),
           color=TH.SUCCESS, hover=TH.SUCCESS_HVR,
           width=150, height=TH.BTN_SM).pack(side="right", padx=(4, 0))
    mk_btn(cc_hdr, "🍽  Calculateur",
           _open_meal_calc_screen,
           color="#1a2a3a", hover="#223344",
           width=140, height=TH.BTN_SM).pack(side="right", padx=4)
    mk_btn(cc_hdr, "📤  Exporter PDF",
           _export_nutr_pdf,
           color="#1a1a2e", hover="#252540",
           width=140, height=TH.BTN_SM).pack(side="right", padx=4)
    def _show_shopping_nutr():
        lp = getattr(app, "_last_meal_plan", None)
        if not lp or not _feat:
            from tkinter import messagebox as _mb
            _mb.showinfo("ERAGROK", "Aucun plan accepté — génère et accepte un plan d'abord.")
            return
        days = lp.get("days")
        plan = days if days else lp.get("plan", [])
        nd   = len(days) if days else 1
        _feat.show_shopping_list(app, plan, n_days=nd)
    mk_btn(cc_hdr, "🛒  Liste de courses",
           _show_shopping_nutr,
           color=TH.BG_CARD2, hover=TH.BG_CARD,
           width=170, height=TH.BTN_SM).pack(side="right", padx=4)
    mk_btn(cc_hdr, "📋  Plan alimentaire",
           lambda: _feat.show_meal_generator(app) if _feat else None,
           color="#0e2a1a", hover="#14381f",
           width=160, height=TH.BTN_SM).pack(side="right", padx=4)

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
        for _tid in getattr(app, "_calc_trace_ids", []):
            try: app.poids_var.trace_remove("write", _tid)
            except Exception: pass
            try: app.adjustment_var.trace_remove("write", _tid)
            except Exception: pass
        app._calc_trace_ids = []
        _tid1 = app.poids_var.trace_add("write",      lambda *a: _update_calc(app))
        _tid2 = app.adjustment_var.trace_add("write", lambda *a: _update_calc(app))
        app._calc_trace_ids = [_tid1, _tid2]
    except Exception: pass

    # cadre note et save_row supprimés — boutons intégrés dans cc_hdr ci-dessus
    if not hasattr(app, "nutrition_note_text"):
        app.nutrition_note_text = None   # compat _save_nutrition

    # ── Plan alimentaire — rendu identique au générateur ─────────────────────
    if _feat:
        pc = mk_card(right)
        pc.pack(fill="x", pady=(0, 14))

        # En-tête avec titre + bouton générateur
        pc_hdr = ctk.CTkFrame(pc, fg_color="transparent")
        pc_hdr.pack(fill="x", padx=16, pady=(14,6))
        mk_title(pc_hdr, "  🍽  PLAN ALIMENTAIRE").pack(side="left")
        mk_sep(pc).pack(fill="x", padx=16, pady=(0,8))

        last_plan = getattr(app, "_last_meal_plan", None)
        _plan_data = None
        _cal = _prot = _gluc = _lip = 0
        if last_plan:
            if last_plan.get("plan"):
                _plan_data = last_plan["plan"]
            elif last_plan.get("days"):
                _plan_data = last_plan["days"][0]["plan"]
            _cal  = last_plan.get("cal",  2500)
            _prot = last_plan.get("prot", 180)
            _gluc = last_plan.get("gluc", 280)
            _lip  = last_plan.get("lip",  70)
            _n_meals = last_plan.get("n_meals", 4)
            _adj  = last_plan.get("adj", "")
        accepted = last_plan.get("accepted", False) if last_plan else False

        if _plan_data:
            # Badge accepté ou bouton accepter
            if accepted:
                badge_r = ctk.CTkFrame(pc, fg_color="transparent")
                badge_r.pack(fill="x", padx=16, pady=(0,6))
                b = ctk.CTkFrame(badge_r, fg_color=TH.SUCCESS, corner_radius=4)
                b.pack(side="left")
                mk_label(b, "  ✅  Plan accepté  ", size="small",
                         color="#000").pack(padx=4, pady=2)
            else:
                accept_r = ctk.CTkFrame(pc, fg_color="transparent")
                accept_r.pack(fill="x", padx=16, pady=(0,6))
                mk_label(accept_r, "⏳  Plan généré — pas encore accepté.",
                         size="small", color=TH.ACCENT_GLOW).pack(side="left")
                def _accept_plan():
                    lp = getattr(app, "_last_meal_plan", None)
                    if lp: lp["accepted"] = True
                    show_nutrition_screen(app)
                mk_btn(accept_r, "✅  Accepter",
                       _accept_plan,
                       color=TH.SUCCESS, hover=TH.SUCCESS_HVR,
                       width=110, height=TH.BTN_SM).pack(side="right")

            # Zone scrollable avec rendu complet identique au générateur
            plan_scroll = mk_scrollframe(pc)
            plan_scroll.pack(fill="x", padx=8, pady=(0,12))
            plan_scroll.configure(height=1000)
            plan_inner = ctk.CTkFrame(plan_scroll, fg_color="transparent")
            plan_inner.pack(fill="both", expand=True)
            _days = last_plan.get("days") if last_plan else None
            _feat.render_plan_card(plan_inner, app, _plan_data,
                                   _cal, _prot, _gluc, _lip,
                                   n_meals=_n_meals, adj_lbl=_adj,
                                   show_pdf=False, days=_days)  # PDF dans cc_hdr
        else:
            mk_label(pc, "  Aucun plan — génère un plan depuis le générateur.",
                     size="small", color=TH.TEXT_MUTED).pack(
                anchor="w", padx=16, pady=(0,14))

    # historique
    hc = mk_card(right)
    hc.pack(fill="x", pady=(0, 14))
    mk_title(hc, "  HISTORIQUE NUTRITION").pack(
        anchor="w", padx=16, pady=(14, 6))
    mk_sep(hc).pack(fill="x", padx=16, pady=(0, 8))

    apply_treeview_style("Nutr")
    tree_frame = ctk.CTkFrame(hc, fg_color="transparent")
    tree_frame.pack(fill="x", padx=16, pady=(0, 4))

    app.nutrition_tree = ttk.Treeview(
        tree_frame, columns=("Date", "Poids", "Calories", "Note"),
        show="headings", selectmode="extended", style="Nutr.Treeview",
        height=8)   # ~8 lignes visibles — scroll pour le reste
    for col, w in [("Date", 120), ("Poids", 80),
                   ("Calories", 100), ("Note", 340)]:
        app.nutrition_tree.heading(col, text=col,
            command=lambda c=col: _sort_tree(app, c))
        app.nutrition_tree.column(col, width=w,
                                   anchor="center" if col != "Note" else "w")

    vsb = ttk.Scrollbar(tree_frame, orient="vertical",
                         command=app.nutrition_tree.yview)
    app.nutrition_tree.configure(yscrollcommand=vsb.set)
    vsb.pack(side="right", fill="y")
    app.nutrition_tree.pack(side="left", fill="both", expand=True)
    app.nutrition_tree.bind("<Double-1>", lambda e: _edit_selected(app))

    # Info multi-sélection
    mk_label(hc, "  Maj+clic ou Ctrl+clic pour sélection multiple",
             size="small", color=TH.TEXT_MUTED).pack(anchor="w", padx=16, pady=(0,6))

    ar = ctk.CTkFrame(hc, fg_color="transparent")
    ar.pack(fill="x", padx=14, pady=(0, 14))
    mk_btn(ar, "✏  Modifier",  lambda: _edit_selected(app),
           color=TH.GRAY, hover=TH.GRAY_HVR,
           width=120, height=TH.BTN_SM).pack(side="left", padx=4)
    mk_btn(ar, "🗑  Supprimer", lambda: _delete_selected(app),
           color=TH.DANGER, hover=TH.DANGER_HVR,
           width=120, height=TH.BTN_SM).pack(side="left", padx=4)
    mk_btn(ar, "🗑  Tout supprimer", lambda: _delete_all(app),
           color="#5a0000", hover="#7a0000",
           width=150, height=TH.BTN_SM).pack(side="right", padx=4)

    f = os.path.join(utils.USERS_DIR, app.current_user, "nutrition.csv") if app.current_user else None
    if f: _refresh_tree(app, f)
    _update_calc(app)

    # ── Détection modification + confirmation avant fermeture ─────────────────
    app._nutr_dirty = False  # devient True dès qu'un champ est modifié

    def _mark_dirty(*_):
        app._nutr_dirty = True

    def _on_close():
        if getattr(app, "_nutr_dirty", False):
            from tkinter import messagebox as _mb
            ans = _mb.askyesnocancel(
                "ERAGROK — Modifications non sauvegardées",
                "Tu as modifié des champs nutritionnels.\n"
                "Veux-tu sauvegarder avant de quitter ?")
            if ans is True:          # Oui → sauvegarder puis fermer
                _save_nutrition(app)
                app.root.destroy()
            elif ans is False:       # Non → fermer sans sauvegarder
                app.root.destroy()
            # ans is None → Annuler, on ne ferme pas
        else:
            app.root.destroy()

    # Lier les champs poids + ajustement à _mark_dirty
    try:
        for _tid in getattr(app, "_dirty_trace_ids", []):
            try: app.poids_var.trace_remove("write", _tid)
            except Exception: pass
        _dt1 = app.poids_var.trace_add("write", _mark_dirty)
        _dt2 = app.adjustment_var.trace_add("write", _mark_dirty)
        app._dirty_trace_ids = [_dt1, _dt2]
    except Exception: pass

    app.root.protocol("WM_DELETE_WINDOW", _on_close)


def _clear_sel(app):
    app.selected_dates = set()
    if hasattr(app, "sel_label"): app.sel_label.configure(text="Sélection : (aucune)")
    f = os.path.join(utils.USERS_DIR, app.current_user, "nutrition.csv") if app.current_user else None
    if f: _refresh_tree(app, f)
