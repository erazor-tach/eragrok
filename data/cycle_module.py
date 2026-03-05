# data/cycle_module.py — ERAGROK  ·  Dark Bodybuilding
import os, csv
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk
import customtkinter as ctk
from tkcalendar import Calendar
from data import utils
from data.theme import (
    TH, mk_btn, mk_card, mk_card2, mk_entry,
    mk_textbox, mk_label, mk_title, mk_sep,
    mk_scrollframe, screen_header, apply_treeview_style,
)


def _user_dir(app):
    d = os.path.join(utils.USERS_DIR, app.current_user)
    Path(d).mkdir(parents=True, exist_ok=True)
    return d


# ── Disclaimer ────────────────────────────────────────────────────────────────
def show_cycle_disclaimer(app):
    if getattr(app, "cycle_disclaimer_shown", False):
        show_cycle_screen(app); return

    dlg = ctk.CTkToplevel(app.root)
    dlg.title("Avertissement — Cycle hormonal")
    dlg.geometry("660x440")
    dlg.configure(fg_color=TH.BG_CARD)
    dlg.grab_set(); dlg.focus_set()

    ctk.CTkLabel(dlg, text="⚠️  AVERTISSEMENT MÉDICAL",
                 font=TH.F_H2, text_color=TH.WARNING).pack(
        anchor="w", padx=28, pady=(22, 8))
    mk_sep(dlg).pack(fill="x", padx=28, pady=(0, 14))

    txt = (
        "Les produits anabolisants et hormones (testostérone, hCG, etc.) peuvent "
        "provoquer des effets secondaires graves et irréversibles : troubles "
        "cardiaques, déséquilibres hormonaux, atteintes hépatiques.\n\n"
        "Consultez impérativement un médecin avant toute utilisation.\n\n"
        "En cliquant sur « ACCEPTER » vous reconnaissez avoir été informé(e) de "
        "ces risques et vous assumez l'entière responsabilité de l'usage de ces "
        "informations à titre strictement personnel."
    )
    tb = mk_textbox(dlg, height=180)
    tb.pack(padx=28, pady=(0, 4))
    tb.insert("1.0", txt)
    tb.configure(state="disabled")

    row = ctk.CTkFrame(dlg, fg_color="transparent")
    row.pack(pady=18)
    mk_btn(row, "✅  ACCEPTER",
           lambda: (_accept(dlg, app)),
           color=TH.SUCCESS, hover=TH.SUCCESS_HVR,
           width=160, height=TH.BTN_LG).pack(side="left", padx=16)
    mk_btn(row, "❌  REFUSER", dlg.destroy,
           color=TH.DANGER, hover=TH.DANGER_HVR,
           width=160, height=TH.BTN_LG).pack(side="left", padx=16)


def _accept(dlg, app):
    dlg.destroy()
    app.cycle_disclaimer_shown = True
    show_cycle_screen(app)


# ── Écran Cycle ───────────────────────────────────────────────────────────────
def show_cycle_screen(app):
    for w in app.content.winfo_children():
        w.destroy()

    screen_header(app.content, "💉  CYCLE HORMONAL",
                  user_name=app.selected_user_name,
                  back_cmd=app.show_dashboard)

    scroll = mk_scrollframe(app.content)
    scroll.pack(fill="both", expand=True)

    cols = ctk.CTkFrame(scroll, fg_color="transparent")
    cols.pack(fill="both", expand=True, padx=28, pady=20)
    cols.columnconfigure(0, weight=0)
    cols.columnconfigure(1, weight=1)

    # ── Calendrier ──
    left = mk_card(cols)
    left.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
    mk_title(left, "  DATE DE LA PRISE").pack(anchor="w", padx=16, pady=(14, 6))
    mk_sep(left).pack(fill="x", padx=16, pady=(0, 10))

    _cal_style = dict(
        background=TH.BG_CARD2, foreground=TH.TEXT,
        selectbackground=TH.ACCENT, selectforeground=TH.TEXT,
        bordercolor=TH.BORDER,
        headersbackground=TH.BG_CARD, headersforeground=TH.TEXT_SUB,
        normalforeground=TH.TEXT, weekendforeground=TH.ACCENT_GLOW,
        font=("Inter", 10), headersfont=("Inter", 10, "bold"),
    )
    app.cycle_date_entry = Calendar(left, selectmode="day", **_cal_style)
    app.cycle_date_entry.pack(padx=16, pady=(0, 16))

    # ── Saisie ──
    right = ctk.CTkFrame(cols, fg_color="transparent")
    right.grid(row=0, column=1, sticky="nsew")

    data_card = mk_card(right)
    data_card.pack(fill="x", pady=(0, 14))
    mk_title(data_card, "  DONNÉES DU CYCLE").pack(
        anchor="w", padx=16, pady=(14, 6))
    mk_sep(data_card).pack(fill="x", padx=16, pady=(0, 12))

    app.cycle_entries = {}
    for display, key, unit, ph in [
        ("Dose testostérone", "Dose testo (mg/sem)", "mg/sem", "Ex : 250"),
        ("hCG",               "hCG (UI/sem)",         "UI/sem",  "Ex : 500"),
        ("Phase",             "Phase (blast/cruise)",  "",        "blast / cruise"),
    ]:
        r = ctk.CTkFrame(data_card, fg_color="transparent")
        r.pack(fill="x", padx=16, pady=6)
        mk_label(r, f"{display} :", size="small",
                 color=TH.TEXT_SUB, width=180).pack(side="left")
        e = mk_entry(r, width=190, placeholder=ph)
        e.pack(side="left", padx=8)
        if unit:
            mk_label(r, unit, size="small",
                     color=TH.TEXT_MUTED).pack(side="left")
        app.cycle_entries[key] = e

    # Note
    note_card = mk_card(right)
    note_card.pack(fill="x", pady=(0, 14))
    mk_title(note_card, "  NOTES / OBSERVATIONS").pack(
        anchor="w", padx=16, pady=(14, 6))
    mk_sep(note_card).pack(fill="x", padx=16, pady=(0, 10))
    app.cycle_note_text = mk_textbox(note_card, height=100)
    app.cycle_note_text.pack(fill="x", padx=16, pady=(0, 14))

    mk_btn(right, "💾  SAUVEGARDER LE CYCLE",
           lambda: _save(app),
           color=TH.SUCCESS, hover=TH.SUCCESS_HVR,
           width=280, height=TH.BTN_LG).pack(anchor="e", pady=(0, 14))

    # Historique
    hist_card = mk_card(right)
    hist_card.pack(fill="both", expand=True)
    mk_title(hist_card, "  HISTORIQUE (5 dernières)").pack(
        anchor="w", padx=16, pady=(14, 6))
    mk_sep(hist_card).pack(fill="x", padx=16, pady=(0, 8))

    apply_treeview_style("Cycle")
    cols_t = ("Date", "Testo mg/sem", "hCG UI/sem", "Phase", "Note")
    app.cycle_tree = ttk.Treeview(
        hist_card, columns=cols_t, show="headings",
        height=5, selectmode="browse", style="Cycle.Treeview")
    for c in cols_t:
        app.cycle_tree.heading(c, text=c)
        app.cycle_tree.column(c, width=110, anchor="center")
    app.cycle_tree.column("Note", width=200, anchor="w")
    app.cycle_tree.pack(fill="both", expand=True, padx=16, pady=(0, 14))

    _refresh(app)


def _refresh(app):
    if not hasattr(app, "cycle_tree"): return
    for r in app.cycle_tree.get_children():
        app.cycle_tree.delete(r)
    fichier = os.path.join(utils.USERS_DIR, app.current_user, "cycle.csv")
    if not os.path.exists(fichier): return
    try:
        with open(fichier, "r", newline="", encoding="utf-8") as f:
            rows = list(csv.reader(f))
        for row in reversed(rows[1:][-5:]):
            while len(row) < 5: row.append("")
            app.cycle_tree.insert("", "end", values=tuple(row[:5]))
    except Exception:
        pass


def _save(app):
    if not getattr(app, "current_user", None):
        messagebox.showerror("ERAGROK", "Sélectionne un élève."); return
    try:
        date  = app.cycle_date_entry.get_date()
        testo = app.cycle_entries["Dose testo (mg/sem)"].get().strip() or "0"
        hcg   = app.cycle_entries["hCG (UI/sem)"].get().strip() or "0"
        phase = app.cycle_entries["Phase (blast/cruise)"].get().strip()
        note  = app.cycle_note_text.get("1.0", "end").strip()
        d     = _user_dir(app)
        fichier = os.path.join(d, "cycle.csv")
        if not os.path.exists(fichier):
            with open(fichier, "w", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow(
                    ["Date", "Dose testo (mg/sem)", "hCG (UI/sem)",
                     "Phase (blast/cruise)", "Note"])
        with open(fichier, "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([date, testo, hcg, phase, note])
        for e in app.cycle_entries.values():
            e.delete(0, tk.END)
        app.cycle_note_text.delete("1.0", "end")
        _refresh(app)
        messagebox.showinfo("ERAGROK", f"✔  Cycle du {date} sauvegardé.")
    except Exception as e:
        messagebox.showerror("ERAGROK", str(e))
