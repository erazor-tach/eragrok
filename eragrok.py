# eragrok.py — ERAGROK  ·  Dark Bodybuilding
import os, sys, traceback, logging
from pathlib import Path
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

SCRIPT_DIR = Path(__file__).resolve().parent
os.chdir(SCRIPT_DIR)
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(SCRIPT_DIR / "run_output.txt", mode="a", encoding="utf-8"),
    ],
)

try:
    from data import utils, pdf_utils, entrainement_module, nutrition_module, cycle_module
    from data.theme import (
        TH, mk_btn, mk_ghost_btn, mk_card, mk_card2,
        mk_entry, mk_combo, mk_label, mk_title, mk_sep,
        mk_badge, mk_scrollframe,
        apply_root_style, hero_header, screen_header,
    )
except Exception:
    logging.exception("Import error")
    traceback.print_exc()
    try:
        tk.Tk().withdraw()
        messagebox.showerror("Erreur", "Import échoué.\nVoir run_output.txt")
    except Exception:
        pass
    sys.exit(1)

for _f in ["ensure_users_dir","list_users","get_user_info","add_user",
           "update_user","delete_user","calculs_nutrition","calculer_imc",
           "ajustement_to_objectif"]:
    if not hasattr(utils, _f):
        logging.error("data.utils manque : %s", _f); sys.exit(1)


class EragrokApp:
    def __init__(self, root):
        self.root = root
        apply_root_style(root, "ERAGROK — Coach Bodybuilding")

        self.current_user       = None
        self.selected_user_name = ""
        self.user_info          = None
        self._editing_user      = None
        self.poids_var          = tk.StringVar()
        self.age_var            = tk.StringVar()
        self.adjustment_var     = tk.StringVar()
        self.groupes_vars       = {}

        self.sidebar = ctk.CTkFrame(root, fg_color=TH.BG_SIDEBAR,
                                     width=252, corner_radius=0)
        self.content = ctk.CTkFrame(root, fg_color=TH.BG_ROOT,
                                     corner_radius=0)
        utils.ensure_users_dir()
        self.show_user_selection_screen()

    # ── Écran sélection profil ─────────────────────────────────────────
    def show_user_selection_screen(self):
        # Si un utilisateur est déjà connecté, garder la sidebar visible
        already_logged = bool(getattr(self, "current_user", None))
        if not already_logged:
            self.sidebar.pack_forget()
        for w in self.content.winfo_children():
            w.destroy()
        self.content.pack(side="right", fill="both", expand=True)

        # Bouton retour (uniquement quand sidebar présente)
        if already_logged:
            top_bar = ctk.CTkFrame(self.content, fg_color=TH.BG_SIDEBAR,
                                   corner_radius=0, height=44)
            top_bar.pack(fill="x", side="top")
            top_bar.pack_propagate(False)
            mk_btn(top_bar, "←  Retour au Dashboard",
                   self.show_dashboard,
                   color=TH.GRAY, hover=TH.GRAY_HVR,
                   width=220, height=34).pack(side="left", padx=14, pady=5)

        hero_header(self.content)
        scroll = mk_scrollframe(self.content)
        scroll.pack(fill="both", expand=True)

        # — Sélection profil existant —
        sel = mk_card(scroll)
        sel.pack(fill="x", padx=32, pady=(28, 0))
        mk_title(sel, "  SÉLECTIONNER UN PROFIL").pack(
            anchor="w", padx=20, pady=(16, 6))
        mk_sep(sel).pack(fill="x", padx=20, pady=(0, 12))

        row = ctk.CTkFrame(sel, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=(0, 18))

        users = utils.list_users()
        if not users:
            mk_label(row, "Aucun profil — crée le premier ci-dessous.",
                     color=TH.TEXT_MUTED).pack(anchor="w")
            self.user_combobox = None
        else:
            self.user_combobox = mk_combo(row, users, width=340,
                                          command=lambda v: None)
            self.user_combobox.pack(side="left", padx=(0, 10))
            for txt, cmd, col, hov in [
                ("▶  OUVRIR",    self.on_user_selected,   TH.ACCENT,  TH.ACCENT_HOVER),
                ("✎  Modifier",  self._load_for_edit,     TH.GRAY,    TH.GRAY_HVR),
                ("✕  Supprimer", self.on_delete_profile,  TH.DANGER,  TH.DANGER_HVR),
            ]:
                mk_btn(row, txt, cmd, color=col, hover=hov,
                       width=128).pack(side="left", padx=4)

        # — Formulaire créer / modifier —
        form = mk_card(scroll)
        form.pack(fill="x", padx=32, pady=18)

        self._form_title = ctk.CTkLabel(
            form, text="CRÉER UN NOUVEAU PROFIL",
            font=TH.F_H3, text_color=TH.TEXT_ACCENT, anchor="w")
        self._form_title.pack(anchor="w", padx=20, pady=(16, 6))
        mk_sep(form).pack(fill="x", padx=20, pady=(0, 14))

        grid = ctk.CTkFrame(form, fg_color="transparent")
        grid.pack(fill="x", padx=20)
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

        self.form_entries = {}
        fields = [
            ("Nom / Prénom", "name",   "Ex : Rudy Martin"),
            ("Age",          "age",    "Ex : 28"),
            ("Taille (cm)",  "taille", "Ex : 180"),
            ("Poids (kg)",   "poids",  "Ex : 85"),
        ]
        for i, (lbl, key, ph) in enumerate(fields):
            cell = ctk.CTkFrame(grid, fg_color="transparent")
            cell.grid(row=i // 2, column=i % 2,
                      sticky="ew", padx=12, pady=8)
            mk_label(cell, lbl, size="small",
                     color=TH.TEXT_SUB).pack(anchor="w", pady=(0, 4))
            e = mk_entry(cell, width=300, placeholder=ph)
            e.pack(anchor="w", fill="x")
            self.form_entries[key] = e

        row2 = ctk.CTkFrame(form, fg_color="transparent")
        row2.pack(fill="x", padx=20, pady=(0, 8))
        for lbl, attr, vals, default, w in [
            ("Sexe",               "form_sexe",
             ["Homme", "Femme"],                 "Homme",        200),
            ("Approche calorique", "form_adj",
             list(utils.ADJUSTMENTS.keys()),      "Maintien (0%)", 370),
        ]:
            c = ctk.CTkFrame(row2, fg_color="transparent")
            c.pack(side="left", padx=12, pady=8)
            mk_label(c, lbl, size="small",
                     color=TH.TEXT_SUB).pack(anchor="w", pady=(0, 4))
            cb = mk_combo(c, vals, width=w)
            cb.set(default)
            cb.pack(anchor="w")
            setattr(self, attr, cb)

        brow = ctk.CTkFrame(form, fg_color="transparent")
        brow.pack(anchor="e", padx=20, pady=18)
        self._form_btn = mk_btn(
            brow, "＋  CRÉER CE PROFIL", self._create_or_modify,
            color=TH.SUCCESS, hover=TH.SUCCESS_HVR,
            width=220, height=TH.BTN_LG)
        self._form_btn.pack(side="left", padx=6)
        mk_btn(brow, "↺  Réinitialiser", self._clear_form,
               color=TH.GRAY, hover=TH.GRAY_HVR,
               width=160, height=TH.BTN_LG).pack(side="left", padx=6)

        self._editing_user = None
        self._update_form_mode()

    # ── Helpers formulaire ─────────────────────────────────────────────
    def _load_for_edit(self):
        if not self.user_combobox:
            return
        sel = self.user_combobox.get()
        if not sel:
            messagebox.showinfo("ERAGROK", "Sélectionne un profil."); return
        info = utils.get_user_info(sel)
        if not info:
            messagebox.showerror("ERAGROK", "Profil introuvable."); return
        for k in ["name", "age", "taille", "poids"]:
            self.form_entries[k].delete(0, tk.END)
            self.form_entries[k].insert(0, str(info.get(k, "") or ""))
        if info.get("sexe") in ["Homme", "Femme"]:
            self.form_sexe.set(info["sexe"])
        adj = info.get("ajustement", "Maintien (0%)")
        if adj in utils.ADJUSTMENTS:
            self.form_adj.set(adj)
        self._editing_user = sel
        self._update_form_mode()

    def _update_form_mode(self):
        editing = getattr(self, "_editing_user", None)
        if editing:
            self._form_title.configure(
                text=f"MODIFIER — {editing.upper()}")
            self._form_btn.configure(
                text=f"✔  ENREGISTRER '{editing}'",
                fg_color=TH.ACCENT, hover_color=TH.ACCENT_HOVER)
        else:
            self._form_title.configure(text="CRÉER UN NOUVEAU PROFIL")
            self._form_btn.configure(
                text="＋  CRÉER CE PROFIL",
                fg_color=TH.SUCCESS, hover_color=TH.SUCCESS_HVR)

    def _clear_form(self):
        if self.user_combobox:
            self.user_combobox.set("")
        for e in self.form_entries.values():
            e.delete(0, tk.END)
        self.form_sexe.set("Homme")
        self.form_adj.set("Maintien (0%)")
        self._editing_user = None
        self._update_form_mode()

    def _create_or_modify(self):
        name      = self.form_entries["name"].get().strip()
        age       = self.form_entries["age"].get().strip()
        taille    = self.form_entries["taille"].get().strip()
        poids     = self.form_entries["poids"].get().strip()
        sexe      = self.form_sexe.get()
        ajust     = self.form_adj.get()
        objectif  = utils.ajustement_to_objectif(ajust)
        if not name:
            messagebox.showerror("ERAGROK", "Le nom est obligatoire."); return
        if self._editing_user:
            ok = utils.update_user(self._editing_user, name, age, sexe,
                                    taille, poids, objectif, ajust)
            if ok:
                messagebox.showinfo("ERAGROK", f"✔ Profil '{name}' mis à jour.")
                self.show_user_selection_screen()
            else:
                messagebox.showerror("ERAGROK", "Mise à jour échouée.")
        else:
            ok, msg = utils.add_user(name, age, sexe, taille, poids,
                                      objectif, ajust)
            if ok:
                # Auto-connexion immédiate sur le nouveau profil
                info2 = utils.get_user_info(name)
                if info2:
                    self.current_user       = info2.get("folder",
                                                name.lower().replace(" ", "_"))
                    self.selected_user_name = name
                    self.user_info          = info2
                    self.poids_var.set(str(info2.get("poids", "")))
                    self.age_var.set(str(info2.get("age", "")))
                    adj2 = info2.get("ajustement", "Maintien (0%)")
                    self.adjustment_var.set(
                        adj2 if adj2 in utils.ADJUSTMENTS else "Maintien (0%)")
                    self.content.pack_forget()
                    self._build_sidebar()
                    self.sidebar.pack(side="left", fill="y")
                    self.content.pack(side="right", fill="both", expand=True)
                    self.show_dashboard()
                else:
                    messagebox.showinfo("ERAGROK", f"✔ Profil '{name}' créé.")
                    self.show_user_selection_screen()
            else:
                messagebox.showerror("ERAGROK", msg)

    def on_user_selected(self):
        if not self.user_combobox:
            messagebox.showinfo("ERAGROK", "Aucun profil disponible."); return
        sel = self.user_combobox.get()
        if not sel:
            messagebox.showinfo("ERAGROK", "Sélectionne un profil."); return
        info = utils.get_user_info(sel)
        if not info:
            messagebox.showerror("ERAGROK", "Profil introuvable."); return
        self.current_user       = info.get("folder",
                                            sel.lower().replace(" ", "_"))
        self.selected_user_name = sel
        self.user_info          = info
        self.poids_var.set(str(info.get("poids", "")))
        self.age_var.set(str(info.get("age", "")))
        adj = info.get("ajustement", "Maintien (0%)")
        self.adjustment_var.set(
            adj if adj in utils.ADJUSTMENTS else "Maintien (0%)")
        self.content.pack_forget()
        self._build_sidebar()
        self.sidebar.pack(side="left", fill="y")
        self.content.pack(side="right", fill="both", expand=True)
        self.show_dashboard()

    def on_delete_profile(self):
        if not self.user_combobox: return
        sel = self.user_combobox.get()
        if not sel:
            messagebox.showinfo("ERAGROK", "Sélectionne un profil."); return
        if not messagebox.askyesno(
                "Confirmer", f"Supprimer '{sel}' ?\nIrréversible."): return
        if utils.delete_user(sel):
            messagebox.showinfo("ERAGROK", f"✔ '{sel}' supprimé.")
            self.show_user_selection_screen()
        else:
            messagebox.showerror("ERAGROK", "Suppression échouée.")

    # ── Sidebar ────────────────────────────────────────────────────────
    def _build_sidebar(self):
        for w in self.sidebar.winfo_children():
            w.destroy()

        # logo
        logo = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo.pack(fill="x", padx=14, pady=(22, 6))
        ctk.CTkLabel(logo, text="⚡ ERAGROK",
                     font=("Inter", 20, "bold"),
                     text_color=TH.ACCENT).pack(anchor="w")
        ctk.CTkLabel(logo, text=self.selected_user_name.upper(),
                     font=TH.F_SMALL,
                     text_color=TH.TEXT_MUTED).pack(anchor="w")

        mk_sep(self.sidebar).pack(fill="x", padx=14, pady=(10, 16))

        for icon, label, cmd in [
            ("🏠", "Dashboard",      self.show_dashboard),
            ("🏋", "Entraînement",   lambda: entrainement_module
                                         .show_entrainement_screen(self)),
            ("🍎", "Nutrition",      lambda: nutrition_module
                                         .show_nutrition_screen(self)),
            ("👥", "Gérer profils",  self.show_user_selection_screen),
            ("💉", "Cycle hormonal", lambda: cycle_module
                                         .show_cycle_disclaimer(self)),
            ("📄", "Exporter PDF",   lambda: pdf_utils.export_unified_pdf(self)),
        ]:
            mk_ghost_btn(
                self.sidebar, f"  {icon}   {label}", cmd,
                width=224, height=44).pack(fill="x", padx=10, pady=2)

        mk_sep(self.sidebar).pack(fill="x", padx=14,
                                   pady=12, side="bottom")
        mk_btn(self.sidebar, "🚪  Quitter", self.root.quit,
               color=TH.DANGER, hover=TH.DANGER_HVR,
               width=224, height=40).pack(
            side="bottom", padx=14, pady=(0, 14))

    # ── Dashboard ──────────────────────────────────────────────────────
    def show_dashboard(self):
        for w in self.content.winfo_children():
            w.destroy()
        if not self.current_user:
            mk_label(self.content, "Aucun profil sélectionné",
                     size="h2", color=TH.TEXT_MUTED).pack(pady=120)
            return
        try:
            nutrition_module.render_dashboard(self)
        except Exception:
            logging.exception("Dashboard error")
            messagebox.showerror(
                "Erreur",
                "Impossible d'afficher le dashboard.\nVoir run_output.txt")


def main():
    try:
        root = ctk.CTk()
        EragrokApp(root)
        root.mainloop()
    except Exception:
        logging.exception("Fatal error")
        sys.exit(1)


if __name__ == "__main__":
    main()
