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
        # Supprimer les bgerror "check_dpi_scaling" / "update" de CustomTkinter
        # Ces erreurs sont bénignes : callbacks after() qui survivent à la navigation
        def _silent_callback_exception(exc, val, tb):
            import traceback
            msg = str(val)
            if any(x in msg for x in ("check_dpi_scaling", "application has been destroyed",
                                       "invalid command name")):
                return  # ignorer silencieusement — erreur CTk cosmétique connue
            traceback.print_exception(exc, val, tb)  # afficher les vraies erreurs
        root.report_callback_exception = _silent_callback_exception
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
        # Auto-login si un seul profil existe
        _users = utils.list_users()
        if len(_users) == 1:
            _info = utils.get_user_info(_users[0])
            if _info:
                self.current_user       = _info.get("folder",
                                            _users[0].lower().replace(" ", "_"))
                self.selected_user_name = _users[0]
                self.user_info          = _info
                try: self.poids_var.set(str(_info.get("poids", "")))
                except: pass
                try: self.age_var.set(str(_info.get("age", "")))
                except: pass
                adj = _info.get("ajustement", "Maintien (0%)")
                try: self.adjustment_var.set(
                    adj if adj in utils.ADJUSTMENTS else "Maintien (0%)")
                except: pass
                self._build_sidebar()
                self.sidebar.pack(side="left", fill="y")
                self.content.pack(side="right", fill="both", expand=True)
                self.show_dashboard()

                # Prix alimentaires — charger défauts + MAJ OFF si besoin (background)
                def _init_prices(s=self):
                    try:
                        from data.prices_module import ensure_prices_loaded
                        ensure_prices_loaded(s)
                    except Exception as _pe:
                        import logging; logging.getLogger("eragrok").debug("prices init: %s", _pe)
                root.after(2000, _init_prices)  # délai 2s pour laisser l'UI charger
                return
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
        # Ligne 1 : Nom (pleine largeur)
        name_cell = ctk.CTkFrame(grid, fg_color="transparent")
        name_cell.grid(row=0, column=0, columnspan=2, sticky="ew", padx=12, pady=8)
        mk_label(name_cell, "Nom / Prénom", size="small",
                 color=TH.TEXT_SUB).pack(anchor="w", pady=(0, 4))
        e_name = mk_entry(name_cell, width=600, placeholder="Ex : Rudy Martin")
        e_name.pack(anchor="w", fill="x")
        self.form_entries["name"] = e_name

        # Ligne 2 : Date de naissance (3 menus) + Taille
        dob_cell = ctk.CTkFrame(grid, fg_color="transparent")
        dob_cell.grid(row=1, column=0, sticky="ew", padx=12, pady=8)
        mk_label(dob_cell, "Date de naissance", size="small",
                 color=TH.TEXT_SUB).pack(anchor="w", pady=(0, 4))
        dob_row = ctk.CTkFrame(dob_cell, fg_color="transparent")
        dob_row.pack(anchor="w")
        JOURS  = [str(j).zfill(2) for j in range(1, 32)]
        MOIS   = ["01 Janvier","02 Février","03 Mars","04 Avril","05 Mai","06 Juin",
                  "07 Juillet","08 Août","09 Septembre","10 Octobre","11 Novembre","12 Décembre"]
        ANNEES = [str(y) for y in range(2026, 1939, -1)]
        self.dob_jour_var  = tk.StringVar(value="01")
        self.dob_mois_var  = tk.StringVar(value="01 Janvier")
        self.dob_annee_var = tk.StringVar(value=str(2001))
        for var, vals, w, lbl2 in [
            (self.dob_jour_var,  JOURS,  70,  "Jour"),
            (self.dob_mois_var,  MOIS,  170,  "Mois"),
            (self.dob_annee_var, ANNEES, 90,  "Année"),
        ]:
            sub = ctk.CTkFrame(dob_row, fg_color="transparent")
            sub.pack(side="left", padx=(0, 8))
            mk_label(sub, lbl2, size="small", color=TH.TEXT_MUTED).pack(anchor="w", pady=(0,2))
            cb = mk_combo(sub, vals, width=w)
            cb.configure(variable=var)
            cb.pack()

        taille_cell = ctk.CTkFrame(grid, fg_color="transparent")
        taille_cell.grid(row=1, column=1, sticky="ew", padx=12, pady=8)
        mk_label(taille_cell, "Taille (cm)", size="small",
                 color=TH.TEXT_SUB).pack(anchor="w", pady=(0, 4))
        e_taille = mk_entry(taille_cell, width=300, placeholder="Ex : 180")
        e_taille.pack(anchor="w", fill="x")
        self.form_entries["taille"] = e_taille

        # Ligne 3 : Poids
        poids_cell = ctk.CTkFrame(grid, fg_color="transparent")
        poids_cell.grid(row=2, column=0, sticky="ew", padx=12, pady=8)
        mk_label(poids_cell, "Poids (kg)", size="small",
                 color=TH.TEXT_SUB).pack(anchor="w", pady=(0, 4))
        e_poids = mk_entry(poids_cell, width=300, placeholder="Ex : 85")
        e_poids.pack(anchor="w", fill="x")
        self.form_entries["poids"] = e_poids

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

    def _get_dob_str(self):
        """Retourne la date de naissance au format JJ/MM/AAAA depuis les 3 menus."""
        j = getattr(self, "dob_jour_var", None)
        m = getattr(self, "dob_mois_var", None)
        a = getattr(self, "dob_annee_var", None)
        if not j or not m or not a:
            return ""
        mois_num = (m.get() or "01")[:2]
        return f"{j.get().zfill(2)}/{mois_num}/{a.get()}"

    def _set_dob_vars(self, dob_str):
        """Remplit les 3 menus depuis une date JJ/MM/AAAA."""
        if not dob_str or "/" not in dob_str:
            return
        parts = dob_str.split("/")
        if len(parts) != 3:
            return
        j, m_num, a = parts
        MOIS_MAP = {"01":"01 Janvier","02":"02 Février","03":"03 Mars",
                    "04":"04 Avril","05":"05 Mai","06":"06 Juin",
                    "07":"07 Juillet","08":"08 Août","09":"09 Septembre",
                    "10":"10 Octobre","11":"11 Novembre","12":"12 Décembre"}
        try:
            self.dob_jour_var.set(j.zfill(2))
            self.dob_mois_var.set(MOIS_MAP.get(m_num.zfill(2), "01 Janvier"))
            self.dob_annee_var.set(a)
        except Exception:
            pass

    def _load_for_edit(self):
        if not self.user_combobox:
            return
        sel = self.user_combobox.get()
        if not sel:
            messagebox.showinfo("ERAGROK", "Sélectionne un profil."); return
        info = utils.get_user_info(sel)
        if not info:
            messagebox.showerror("ERAGROK", "Profil introuvable."); return
        for k in ["name", "taille", "poids"]:
            if k in self.form_entries:
                self.form_entries[k].delete(0, tk.END)
                self.form_entries[k].insert(0, str(info.get(k, "") or ""))
        self._set_dob_vars(info.get("date_naissance", ""))
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
        try:
            self.dob_jour_var.set("01")
            self.dob_mois_var.set("01 Janvier")
            import datetime as _dt2
            self.dob_annee_var.set(str(_dt2.date.today().year - 25))
        except Exception:
            pass
        self.form_sexe.set("Homme")
        self.form_adj.set("Maintien (0%)")
        self._editing_user = None
        self._update_form_mode()

    def _create_or_modify(self):
        name      = self.form_entries["name"].get().strip()
        taille    = self.form_entries["taille"].get().strip()
        poids     = self.form_entries.get("poids", type("",(),{"get":lambda s:""})()).get().strip()
        sexe      = self.form_sexe.get()
        ajust     = self.form_adj.get()
        objectif  = utils.ajustement_to_objectif(ajust)
        dob       = self._get_dob_str()
        age       = str(utils.age_depuis_naissance(dob) or "")
        if not name:
            messagebox.showerror("ERAGROK", "Le nom est obligatoire."); return
        if not dob or len(dob) != 10:
            messagebox.showerror("ERAGROK", "Sélectionne une date de naissance valide."); return
        if self._editing_user:
            ok = utils.update_user(self._editing_user, name, dob, sexe,
                                    taille, poids, objectif, ajust, date_naissance=dob)
            if ok:
                messagebox.showinfo("ERAGROK", f"✔ Profil '{name}' mis à jour.")
                self.show_user_selection_screen()
            else:
                messagebox.showerror("ERAGROK", "Mise à jour échouée.")
        else:
            ok, msg = utils.add_user(name, dob, sexe, taille, poids,
                                      objectif, ajust, date_naissance=dob)
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

        # Prix alimentaires — charger défauts + MAJ OFF si besoin (background)
        def _init_prices():
            try:
                from data.prices_module import ensure_prices_loaded
                ensure_prices_loaded(self)
            except Exception as _pe:
                import logging; logging.getLogger("eragrok").debug("prices init: %s", _pe)
        root.after(2000, _init_prices)   # délai 2s pour laisser l'UI charger

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
        app  = EragrokApp(root)

        def _on_close():
            """Fermeture propre : annuler les after() CTk AVANT destroy()."""
            try:
                # 1. Annuler les canvases matplotlib pendants
                from data.features_module import _cancel_mpl
                for item in getattr(app, "_mpl_canvases", []):
                    try:
                        c, f = item if isinstance(item, tuple) else (item, None)
                        _cancel_mpl(c, f)
                    except Exception:
                        pass
                app._mpl_canvases = []
            except Exception:
                pass
            try:
                root.quit()       # arrêter mainloop proprement
            except Exception:
                pass
            try:
                root.destroy()    # détruire la fenêtre
            except Exception:
                pass
            sys.exit(0)           # fermer la console Windows

        root.protocol("WM_DELETE_WINDOW", _on_close)
        root.mainloop()
    except Exception:
        logging.exception("Fatal error")
        sys.exit(1)


if __name__ == "__main__":
    main()
