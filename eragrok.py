# eragrok.py
# Point d'entrée principal — UI complète
# Convention current_user : toujours le folder_name (lowercase + underscores)
# Convention selected_user_name : toujours le nom d'affichage (tel que saisi)

import os, sys, traceback, logging
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

SCRIPT_DIR = Path(__file__).resolve().parent
os.chdir(SCRIPT_DIR)

LOG_FILE = SCRIPT_DIR / "run_output.txt"
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8"),
    ],
)
logging.info("Lancement eragrok.py (cwd: %s)", SCRIPT_DIR)

try:
    from data import utils
    from data import entrainement_module
    from data import nutrition_module
    from data import cycle_module
    from data import weight_chart
except Exception:
    logging.exception("Erreur import data modules")
    traceback.print_exc()
    try:
        tk.Tk().withdraw()
        messagebox.showerror("Erreur", "Impossible d'importer les modules data. Voir run_output.txt")
    except Exception:
        pass
    sys.exit(1)

required = [
    "ensure_users_dir", "list_users", "get_user_info",
    "add_user", "update_user", "delete_user",
    "calculs_nutrition", "calculer_imc", "ajustement_to_objectif",
    "get_current_user_folder", "get_user_dir", "to_folder_name",
]
missing = [f for f in required if not hasattr(utils, f)]
if missing:
    logging.error("Fonctions manquantes dans data.utils: %s", missing)
    try:
        tk.Tk().withdraw()
        messagebox.showerror("Erreur", f"Fonctions manquantes dans data.utils:\n{missing}")
    except Exception:
        pass
    sys.exit(1)


class EragrokApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ERAGROK - Coach")
        self.root.geometry("1280x880")
        self.root.configure(bg="#f3f4f6")

        # ── État utilisateur ─────────────────────────────────────────────────
        # current_user       : folder_name  (ex: "rudy")         ← source de vérité
        # selected_user_name : display_name (ex: "Rudy")
        # user_info          : dict complet (depuis utils.get_user_info)
        self.current_user       = ""
        self.selected_user_name = ""
        self.user_info          = None

        # ── Vars partagées ───────────────────────────────────────────────────
        self.poids_var      = tk.StringVar()
        self.age_var        = tk.StringVar()
        self.adjustment_var = tk.StringVar()
        self.groupes_vars   = {}

        # ── Frames ───────────────────────────────────────────────────────────
        self.sidebar = tk.Frame(root, bg="#0f172a", width=260)
        self.content = tk.Frame(root, bg="#f3f4f6")

        utils.ensure_users_dir()
        self.show_user_selection_screen()

    # ══════════════════════════════════════════════════════════════════════════
    #  SÉLECTION / CRÉATION / MODIFICATION DE PROFIL
    # ══════════════════════════════════════════════════════════════════════════

    def show_user_selection_screen(self):
        self.sidebar.pack_forget()
        for w in self.content.winfo_children():
            w.destroy()
        self.content.pack(side="right", fill="both", expand=True)

        header = tk.Frame(self.content, bg="#f3f4f6"); header.pack(fill="x", pady=18)
        tk.Label(header, text="ERAGROK", font=("Inter", 28, "bold"),
                 bg="#f3f4f6", fg="#0f172a").pack(side="left", padx=24)
        tk.Label(header, text="Choisis, crée ou modifie un profil",
                 font=("Inter", 12), bg="#f3f4f6").pack(side="left", padx=12)

        users = utils.list_users()
        frame = tk.Frame(self.content, bg="#f3f4f6")
        frame.pack(pady=8, padx=24, fill="x")

        if not users:
            tk.Label(frame, text="Aucun profil enregistré.",
                     font=("Helvetica", 13), fg="orange", bg="#f3f4f6").pack(pady=6)
            self.user_combobox = None
        else:
            tk.Label(frame, text="Profil existant :", font=("Helvetica", 13),
                     bg="#f3f4f6").pack(side="left", padx=6)
            self.user_combobox = ttk.Combobox(frame, values=users,
                                               state="readonly", width=36,
                                               font=("Helvetica", 12))
            self.user_combobox.pack(side="left", padx=6)
            self.user_combobox.bind("<<ComboboxSelected>>", self._on_combobox_selected)
            ttk.Button(frame, text="Sélectionner",
                       command=self.on_user_selected).pack(side="left", padx=6)
            ttk.Button(frame, text="Effacer sélection",
                       command=self._clear_selection).pack(side="left", padx=6)
            ttk.Button(frame, text="Supprimer",
                       command=self.on_delete_profile).pack(side="left", padx=6)

        # ── Formulaire Créer / Modifier ──────────────────────────────────────
        cf = tk.Frame(self.content, bg="#ffffff"); cf.pack(pady=12, padx=24, fill="x")
        cf.configure(padx=12, pady=12)
        tk.Label(cf, text="Créer / Modifier un profil",
                 font=("Inter", 14, "bold"), bg="#ffffff").pack(anchor="w", pady=(0, 8))

        ff = tk.Frame(cf, bg="#ffffff"); ff.pack(fill="x")
        self.form_entries = {}
        for i, (lbl, key) in enumerate([
            ("Nom / Prénom", "name"), ("Age", "age"),
            ("Taille (cm)", "taille"), ("Poids (kg)", "poids"),
        ]):
            row = tk.Frame(ff, bg="#ffffff"); row.grid(row=i, column=0, sticky="w", pady=6)
            tk.Label(row, text=f"{lbl} :", font=("Helvetica", 11),
                     bg="#ffffff", width=16, anchor="w").pack(side="left", padx=6)
            e = ttk.Entry(row, width=34); e.pack(side="left", padx=6)
            self.form_entries[key] = e

        row = tk.Frame(ff, bg="#ffffff"); row.grid(row=4, column=0, pady=6)
        tk.Label(row, text="Sexe :", font=("Helvetica", 11),
                 bg="#ffffff", width=16, anchor="w").pack(side="left", padx=6)
        self.form_sexe = ttk.Combobox(row, values=["Homme", "Femme"],
                                       state="readonly", width=32)
        self.form_sexe.pack(side="left", padx=6)

        row3 = tk.Frame(ff, bg="#ffffff"); row3.grid(row=5, column=0, pady=6)
        tk.Label(row3, text="Approche calorique :", font=("Helvetica", 11),
                 bg="#ffffff", width=16, anchor="w").pack(side="left", padx=6)
        self.form_ajustement = ttk.Combobox(
            row3, values=list(utils.ADJUSTMENTS.keys()),
            state="readonly", width=32)
        self.form_ajustement.pack(side="left", padx=6)
        self.form_ajustement.set("Maintien (0%)")

        bf = tk.Frame(cf, bg="#ffffff"); bf.pack(pady=12, anchor="e")
        self.create_modify_button = ttk.Button(
            bf, text="Créer cet élève",
            command=self._create_or_modify_handler, width=24)
        self.create_modify_button.pack(side="left", padx=6)
        ttk.Button(bf, text="Rafraîchir la liste",
                   command=self.show_user_selection_screen).pack(side="left", padx=6)

        self._set_form_to_create_mode()

    def _on_combobox_selected(self, event=None):
        if not self.user_combobox:
            return
        selected = self.user_combobox.get()
        if not selected:
            self._set_form_to_create_mode()
            return
        info = utils.get_user_info(selected)
        if not info:
            messagebox.showerror("Grok", "Impossible de récupérer les infos du profil")
            return
        self.form_entries["name"].delete(0, tk.END)
        self.form_entries["name"].insert(0, info.get("name", ""))
        self.form_entries["age"].delete(0, tk.END)
        self.form_entries["age"].insert(0, str(info.get("age", "") or ""))
        self.form_entries["taille"].delete(0, tk.END)
        self.form_entries["taille"].insert(0, str(info.get("taille", "") or ""))
        self.form_entries["poids"].delete(0, tk.END)
        self.form_entries["poids"].insert(0, str(info.get("poids", "") or ""))
        self.form_sexe.set(info.get("sexe", "") or "")
        self.form_ajustement.set(info.get("ajustement", "Maintien (0%)") or "Maintien (0%)")
        self.create_modify_button.config(text="Modifier le profil",
                                          command=self._create_or_modify_handler)

    def _set_form_to_create_mode(self):
        for e in self.form_entries.values():
            e.delete(0, tk.END)
        self.form_sexe.set("")
        self.form_ajustement.set("Maintien (0%)")
        self.create_modify_button.config(text="Créer cet élève",
                                          command=self._create_or_modify_handler)

    def _create_or_modify_handler(self):
        selected  = self.user_combobox.get() if getattr(self, "user_combobox", None) else ""
        name      = self.form_entries["name"].get().strip()
        age       = self.form_entries["age"].get().strip()
        taille    = self.form_entries["taille"].get().strip()
        poids     = self.form_entries["poids"].get().strip()
        sexe      = self.form_sexe.get()
        ajustement = self.form_ajustement.get() or "Maintien (0%)"

        if not all([name, age, sexe, taille]):
            messagebox.showerror("Grok", "Tous les champs sauf Poids sont obligatoires")
            return

        # Validation basique des champs numériques
        try:
            int(age)
            int(taille)
            if poids:
                float(poids)
        except ValueError:
            messagebox.showerror("Grok", "Age et Taille doivent être des nombres entiers.\nPoids doit être un nombre décimal.")
            return

        objectif = utils.ajustement_to_objectif(ajustement)

        if selected:
            if name != selected and name in utils.list_users():
                messagebox.showerror("Grok", "Un profil avec ce nom existe déjà")
                return
            ok = utils.update_user(selected, name, age, sexe, taille, poids, objectif, ajustement)
            if ok:
                messagebox.showinfo("Grok", f"Profil '{selected}' mis à jour.")
                self.show_user_selection_screen()
            else:
                messagebox.showerror("Grok", "Impossible de mettre à jour le profil")
        else:
            ok, msg = utils.add_user(name, age, sexe, taille, poids, objectif, ajustement)
            if ok:
                messagebox.showinfo("Grok", msg)
                self._set_user(name)
                self.sidebar.pack(side="left", fill="y")
                self.create_sidebar()
                self.show_dashboard()
            else:
                messagebox.showerror("Grok", msg)

    def _clear_selection(self):
        if getattr(self, "user_combobox", None):
            self.user_combobox.set("")
        self._set_form_to_create_mode()

    def on_user_selected(self):
        if not getattr(self, "user_combobox", None):
            messagebox.showwarning("Grok", "Aucun profil à sélectionner")
            return
        selected = self.user_combobox.get()
        if not selected:
            return
        self._set_user(selected)
        self.sidebar.pack(side="left", fill="y")
        self.create_sidebar()
        self.show_dashboard()

    def on_delete_profile(self):
        if not getattr(self, "user_combobox", None):
            messagebox.showwarning("Grok", "Aucun profil à supprimer")
            return
        selected = self.user_combobox.get()
        if not selected:
            messagebox.showwarning("Grok", "Sélectionne un profil à supprimer")
            return
        if not messagebox.askyesno(
            "Grok",
            f"Supprimer le profil '{selected}' et tous ses fichiers ?\nCette action est irréversible."
        ):
            return
        if utils.delete_user(selected):
            messagebox.showinfo("Grok", f"Profil '{selected}' supprimé.")
            self.show_user_selection_screen()
        else:
            messagebox.showerror("Grok", "Impossible de supprimer le profil")

    # ── Méthode centrale de sélection d'utilisateur ──────────────────────────

    def _set_user(self, display_name: str):
        """
        Source unique pour initialiser current_user + selected_user_name + user_info.
        Toujours appeler cette méthode plutôt que de modifier les attributs directement.
        """
        self.selected_user_name = display_name
        self.current_user       = utils.to_folder_name(display_name)
        self.user_info          = utils.get_user_info(display_name) or {}

    # ══════════════════════════════════════════════════════════════════════════
    #  SIDEBAR
    # ══════════════════════════════════════════════════════════════════════════

    def create_sidebar(self):
        for w in self.sidebar.winfo_children():
            w.destroy()
        tk.Label(self.sidebar, text="ERAGROK",
                 font=("Helvetica", 20, "bold"),
                 bg="#0f172a", fg="white").pack(pady=24, padx=10)
        boutons = [
            ("🏠 Dashboard",        self.show_dashboard),
            ("🏋️ Entraînement",     lambda: entrainement_module.show_entrainement_screen(self)),
            ("🍎 Nutrition",         lambda: nutrition_module.show_nutrition_screen(self)),
            ("📈 Évolution poids",   lambda: weight_chart.show_weight_chart(self)),
            ("👥 Gérer profils",     self.show_user_selection_screen),
            ("💉 Cycle hormonal",    lambda: cycle_module.show_cycle_disclaimer(self)),
            ("📁 Exporter CSV",      lambda: messagebox.showinfo("Export", "Export CSV (placeholder)")),
            ("🚪 Quitter",           self.root.quit),
        ]
        for texte, cmd in boutons:
            ttk.Button(self.sidebar, text=texte, command=cmd, width=24).pack(
                pady=8, padx=10, fill="x")

    # ══════════════════════════════════════════════════════════════════════════
    #  DASHBOARD
    # ══════════════════════════════════════════════════════════════════════════

    def show_dashboard(self):
        for w in self.content.winfo_children():
            w.destroy()
        if not self.current_user:
            tk.Label(self.content, text="Aucun profil sélectionné",
                     font=("Helvetica", 20), bg="#f3f4f6").pack(pady=120)
            return
        try:
            nutrition_module.render_dashboard(self)
        except Exception:
            logging.exception("Erreur rendu dashboard")
            traceback.print_exc()
            messagebox.showerror("Erreur", "Impossible d'afficher le dashboard. Voir run_output.txt")


def main():
    try:
        root = tk.Tk()
        app  = EragrokApp(root)
        root.mainloop()
    except Exception:
        logging.exception("Exception non gérée")
        traceback.print_exc()
        try:
            tk.Tk().withdraw()
            messagebox.showerror("Erreur critique", "Voir run_output.txt")
        except Exception:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()
