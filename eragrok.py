import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from tkcalendar import Calendar
import datetime
import csv
import os
import random

try:
    import pandas as pd
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
except ImportError:
    pd = None
    plt = None

print("[DEBUG] Début du script – imports OK")

if pd is None or plt is None:
    print("ERREUR : Pandas et/ou Matplotlib manquants")
    print("Installe-les : pip install pandas matplotlib")
    messagebox.showerror("Libs manquantes", "Installe pandas et matplotlib :\npip install pandas matplotlib")
    exit(1)

print("[DEBUG] Pandas & Matplotlib chargés")

MESSAGES_GROK = [
    "LIGHT WEIGHT BABY ! – Ronnie Coleman",
    "YEAH BUDDY ! KEEP PUMPING !",
    "Ain't nothin' but a peanut !",
    "The mind is the limit. – Arnold",
    "Train insane or remain the same. – Dorian Yates",
    "Douleur aujourd'hui = gainz demain 💉",
    "Pas de jours off pour les vrais. LET'S GO.",
    "Respire. Focus. Domine.",
    "Chaque rep est une promesse à ton futur toi.",
    "Le pump arrive quand la douleur part.",
    "Tu n’es pas ici pour être moyen. PROUVE-LE."
]

FICHIER_USERS = "eragrok_users.csv"

def initialiser_users():
    if not os.path.exists(FICHIER_USERS):
        with open(FICHIER_USERS, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Name", "Age", "Sexe", "Taille (cm)", "Objectif"])
        print("[VERBOSE] Créé users.csv")

initialiser_users()

def get_users():
    if not os.path.exists(FICHIER_USERS):
        return []

    with open(FICHIER_USERS, 'r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader, None)  # Skip header
        return [row[1] for row in reader if len(row) > 1]

def add_user(name, age, sexe, taille, objectif):
    users = get_users()
    if name in users:
        messagebox.showerror("Erreur", "Ce nom existe déjà")
        return False

    id = len(users) + 1
    row = [id, name, age, sexe, taille, objectif]
    with open(FICHIER_USERS, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(row)

    prefix = name.lower().replace(" ", "_") + "_"
    fichiers = [
        (prefix + "entrainement.csv", ["Date", "Groupes musculaires", "Type entrainement", "Note"]),
        (prefix + "nutrition.csv", ["Date", "Prénom", "Calories estimees", "Proteines (g)", "Glucides (g)", "Lipides (g)", "Note", "Poids (kg)"]),
        (prefix + "cycle.csv", ["Date", "Dose testo (mg/sem)", "hCG (UI/sem)", "Phase (blast/cruise)", "Note"])
    ]
    for fichier, headers in fichiers:
        if not os.path.exists(fichier):
            with open(fichier, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(headers)

    print(f"[VERBOSE] User ajouté : {name}")
    return True

myofib_options = [
    "Force lourde (1–5 reps | 3–5 min | Force max, recrutement neuronal)",
    "Forced Repetitions (1-5 reps | 3-5 min | Max effort with assistance)",
    "Negatives (eccentric 1-5 reps | 3-5 min | Strength in eccentric phase)",
    "Maximal Effort Method (1-3 reps | 3-5 min | Max strength)",
    "Isometric (hold 5-10s | 2-3 min | Static strength)",
    "Dynamic Effort Method (3-5 reps explosive | 1-2 min | Speed-strength)",
    "Powerbuilding (5–10 reps | 2 min | Force + esthétique)",
    "Force-hypertrophie (4–8 reps | 2–3 min | Force + volume)",
    "Cluster sets (3–5 reps × mini-séries | 15–30s intra | Volume élevé avec charges lourdes)",
    "Poliquin cluster (5 reps | 15-20s | Strength)",
    "Miller intensive cluster (2-4 reps | 45-60s | Intensive)",
    "Mentzer cluster (5-6 reps | 30-45s | Heavy)",
    "Top Set With a Back Off Set (heavy top set + lighter back off | 3-5 min | Strength + volume)",
    "Reverse Pyramid (heavy start decreasing | 2-3 min | Strength)"
]

sarco_options = [
    "Drop sets (10–20 reps | sans repos | Épuisement musculaire)",
    "Giant sets / trisets (12–20 reps | 30–60s intra | Métabolique intense)",
    "Supersets (8-15 reps | no rest | Compound + isolation)",
    "Pre-Exhaustion (8-12 reps | no rest | Isolation followed by compound)",
    "Rest-pause (12–20 reps | 10–15s intra | Volume élevé)",
    "High-rep finisher (20–30+ reps | 30–60s | Endurance + brûlure)",
    "BFR (Blood Flow Restriction) (20–30 reps légers | 30s intra | Hypertrophie avec peu de charge)",
    "Burnout set (max reps to failure | short rest | Muscle burn)",
    "Pyramid set (increasing 8-15 reps | 60-90s | Progressive overload)",
    "Compound Sets (same muscle group | no rest | Volume intensification)",
    "Interset (mini-sets within set | short rest | Volume accumulation)",
    "Straight Set (8-15 reps | 60-90s | Basic hypertrophy)",
    "Lengthened Partials (partial reps in stretch | 60-90s | Hypertrophie in lengthened)",
    "Pause set (pause in rep | 2-3 min | Strength in sticking point)",
    "Explosive set (8-12 reps explosive | 60-90s | Power hypertrophy)",
    "Rest-pause-technical elimination (failure + downgrade | 20-30s | Exhaustion)",
    "Miller extensive cluster (5-6 reps | 30-45s | Extensive)",
    "Max Stim training (single reps with limited rest | limited rest | Effective for bodybuilding)",
    "Partials (partial reps | 2-3 min | Strength in specific range)",
    "Isometric pre/post fatigue (isometric + reps | short rest | Fatigue)"
]

class EragrokApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ERAGROK - COACH EDITION")
        self.root.geometry("1200x800")

        self.sidebar = tk.Frame(root, bg="#1f2937", width=250)
        self.content = tk.Frame(root, bg="#f9fafb")

        self.current_user = None
        self.current_prefix = ""
        self.selected_user_name = ""

        self.myofib_var = tk.StringVar()
        self.sarco_var = tk.StringVar()
        self.groupes_vars = {}
        self.note_text = None
        self.calendar = None
        self.date_entry = None
        self.prenom_var = tk.StringVar()
        self.poids_var = tk.StringVar()
        self.taille_var = tk.StringVar()
        self.age_var = tk.StringVar()
        self.sexe_var = tk.StringVar(value="Homme")
        self.objectif_var = tk.StringVar(value="Maintien")
        self.macros_entries = {}
        self.nutrition_note_text = None
        self.nutrition_history = None
        self.graph_frame = None
        self.calc_table = None

        self.cycle_disclaimer_shown = False

        # Démarrage sur écran de sélection/création d'élève
        self.show_user_selection_screen()

        print("[DEBUG] App prête")

    def show_user_selection_screen(self):
        self.sidebar.pack_forget()
        for widget in self.content.winfo_children():
            widget.destroy()

        self.content.pack(side='right', fill='both', expand=True)

        tk.Label(self.content, text="ERAGROK - Coach Edition", font=("Helvetica", 32, "bold"), bg="#f9fafb", fg="#1f2937").pack(pady=40)

        tk.Label(self.content, text="Choisis ou crée un élève pour commencer", font=("Helvetica", 18), bg="#f9fafb").pack(pady=10)

        users = get_users()

        frame = tk.Frame(self.content, bg="#f9fafb")
        frame.pack(pady=30)

        if not users:
            tk.Label(frame, text="Aucun élève enregistré pour le moment.", font=("Helvetica", 14), fg="orange", bg="#f9fafb").pack(pady=10)
            tk.Label(frame, text="Crée ton premier élève ci-dessous :", font=("Helvetica", 14), bg="#f9fafb").pack(pady=5)
        else:
            tk.Label(frame, text="Élève existant :", font=("Helvetica", 14), bg="#f9fafb").pack(side='left', padx=10)

            self.user_combobox = ttk.Combobox(frame, values=users, state="readonly", width=40, font=("Helvetica", 14))
            self.user_combobox.pack(side='left', padx=10)

            ttk.Button(frame, text="Sélectionner cet élève", command=self.on_user_selected).pack(side='left', padx=10)

        # Formulaire création (toujours visible)
        create_frame = tk.Frame(self.content, bg="#f9fafb")
        create_frame.pack(pady=20, padx=50, fill='x')

        tk.Label(create_frame, text="Créer un nouvel élève :", font=("Helvetica", 16, "bold"), bg="#f9fafb").pack(pady=10)

        form_frame = tk.Frame(create_frame, bg="#f9fafb")
        form_frame.pack()

        entries = {}

        champs = [
            ("Nom / Prénom", "name"),
            ("Age", "age"),
            ("Taille (cm)", "taille")
        ]

        for label_text, key in champs:
            row = tk.Frame(form_frame, bg="#f9fafb")
            row.pack(fill='x', pady=8)

            tk.Label(row, text=label_text + " :", font=("Helvetica", 12), bg="#f9fafb").pack(side='left', padx=10)
            entry = ttk.Entry(row, width=30)
            entry.pack(side='left', padx=10)
            entries[key] = entry

        tk.Label(form_frame, text="Sexe :", font=("Helvetica", 12), bg="#f9fafb").pack(side='left', padx=10)
        sexe_combo = ttk.Combobox(form_frame, values=["Homme", "Femme"], state="readonly", width=27)
        sexe_combo.pack(side='left', padx=10)
        entries["sexe"] = sexe_combo

        tk.Label(form_frame, text="Objectif :", font=("Helvetica", 12), bg="#f9fafb").pack(side='left', padx=10)
        obj_combo = ttk.Combobox(form_frame, values=["Gain de masse", "Perte de poids", "Maintien"], state="readonly", width=27)
        obj_combo.pack(side='left', padx=10)
        entries["objectif"] = obj_combo

        def save_new_user():
            name = entries["name"].get().strip()
            age = entries["age"].get().strip()
            sexe = entries["sexe"].get()
            taille = entries["taille"].get().strip()
            objectif = entries["objectif"].get()

            if not all([name, age, sexe, taille, objectif]):
                messagebox.showerror("Erreur", "Tous les champs sont obligatoires")
                return

            if add_user(name, age, sexe, taille, objectif):
                self.current_user = name.lower().replace(" ", "_")
                self.current_prefix = self.current_user + "_"
                self.selected_user_name = name
                self.sidebar = tk.Frame(self.root, bg="#1f2937", width=250)
                self.sidebar.pack(side='left', fill='y')
                self.create_sidebar()
                self.show_dashboard()

        ttk.Button(create_frame, text="Créer cet élève", command=save_new_user, width=30).pack(pady=20)

        ttk.Button(self.content, text="Rafraîchir la liste", command=self.show_user_selection_screen, width=30).pack(pady=10)

    def on_user_selected(self):
        selected = self.user_combobox.get()
        if not selected:
            messagebox.showwarning("Attention", "Sélectionne un élève")
            return

        self.current_user = selected.lower().replace(" ", "_")
        self.current_prefix = self.current_user + "_"
        self.selected_user_name = selected
        print(f"[DEBUG] Élève sélectionné : {selected}")

        self.sidebar = tk.Frame(self.root, bg="#1f2937", width=250)
        self.sidebar.pack(side='left', fill='y')
        self.create_sidebar()

        self.show_dashboard()

    def create_sidebar(self):
        tk.Label(self.sidebar, text="ERAGROK", font=("Helvetica", 20, "bold"), bg="#1f2937", fg="white").pack(pady=30, padx=10)

        boutons = [
            ("🏠 Dashboard", self.show_dashboard),
            ("🏋️ Entraînement", self.show_entrainement_frame),
            ("🍎 Nutrition", self.show_nutrition_frame),
            ("💉 Cycle hormonal", self.show_cycle_disclaimer),
            ("📊 Analyse & Stats", self.analyser_entrainements),
            ("📁 Exporter CSV", self.exporter_tous),
            ("🚪 Quitter", self.root.quit)
        ]

        for texte, cmd in boutons:
            btn = ttk.Button(self.sidebar, text=texte, command=cmd, width=20)
            btn.pack(pady=10, padx=10, fill='x')

    def show_dashboard(self):
        for widget in self.content.winfo_children():
            widget.destroy()

        if self.current_user is None:
            tk.Label(self.content, text="Aucun élève sélectionné", font=("Helvetica", 20), bg="#f9fafb").pack(pady=100)
            return

        title_frame = tk.Frame(self.content, bg="#f9fafb")
        title_frame.pack(fill='x', pady=10, padx=20)

        tk.Label(title_frame, text=f"Élève : {self.selected_user_name}", font=("Helvetica", 24, "bold"), bg="#f9fafb", fg="#1f2937").pack(side='left')

        ttk.Button(title_frame, text="Changer d'élève", command=self.show_user_selection_screen).pack(side='right', padx=10)

        main_frame = tk.Frame(self.content, bg="#f9fafb")
        main_frame.pack(fill='both', expand=True, padx=20, pady=10)

        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)

        metrics_frame = tk.Frame(main_frame, bg="#dbeafe", bd=2, relief="groove", padx=10, pady=10)
        metrics_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5, rowspan=2)

        tk.Label(metrics_frame, text="📊 Metrics Nutrition", font=("Helvetica", 16, "bold"), bg="#dbeafe").pack(pady=10)

        fichier_nut = self.current_prefix + "nutrition.csv"
        if not os.path.exists(fichier_nut):
            tk.Label(metrics_frame, text="Pas de données nutrition – ajoute une entrée ! 💪", bg="#dbeafe").pack(pady=20)
        else:
            df = pd.read_csv(fichier_nut, on_bad_lines='skip')
            if df.empty:
                tk.Label(metrics_frame, text="Pas de données nutrition – ajoute une entrée ! 💪", bg="#dbeafe").pack(pady=20)
            else:
                last_row = df.iloc[-1]
                poids = float(last_row.get('Poids (kg)', 0))
                taille = float(last_row.get('Taille (cm)', 180)) / 100
                imc = poids / (taille ** 2) if taille > 0 else 0
                tk.Label(metrics_frame, text=f"IMC actuel : {imc:.1f}", bg="#dbeafe").pack(pady=5)

                df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
                df = df.dropna(subset=['Date']).sort_values('Date')
                df['Poids (kg)'] = pd.to_numeric(df['Poids (kg)'], errors='coerce')

                for days in [7, 30]:
                    recent = df[df['Date'] > datetime.datetime.now() - datetime.timedelta(days=days)]
                    if len(recent) > 1:
                        trend = recent['Poids (kg)'].iloc[-1] - recent['Poids (kg)'].iloc[0]
                        tk.Label(metrics_frame, text=f"Tendance {days}j : {trend:+.1f} kg", bg="#dbeafe").pack(pady=5)
                    else:
                        tk.Label(metrics_frame, text=f"Pas assez de données pour tendance {days}j", bg="#dbeafe").pack(pady=5)

                recent7 = df[df['Date'] > datetime.datetime.now() - datetime.timedelta(days=7)]
                recent7['Calories estimees'] = pd.to_numeric(recent7['Calories estimees'], errors='coerce').fillna(0)
                if len(recent7) > 0:
                    avg_cal = recent7['Calories estimees'].mean()
                    bmr_est = 2500
                    delta = avg_cal - bmr_est
                    status = "déficit" if delta < 0 else "surplus"
                    tk.Label(metrics_frame, text=f"{status.capitalize()} moyen : {abs(delta):.0f} kcal/j", bg="#dbeafe").pack(pady=5)
                else:
                    tk.Label(metrics_frame, text="Pas de données calories", bg="#dbeafe").pack(pady=5)

        training_frame = tk.Frame(main_frame, bg="#dcfce7", bd=2, relief="groove", padx=10, pady=10)
        training_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        tk.Label(training_frame, text="🏋️ Entraînements semaine", font=("Helvetica", 16, "bold"), bg="#dcfce7").pack(pady=10)

        fichier_train = self.current_prefix + "entrainement.csv"
        if not os.path.exists(fichier_train):
            tk.Label(training_frame, text="Pas d'entraînement cette semaine", bg="#dcfce7").pack(pady=20)
        else:
            df = pd.read_csv(fichier_train, on_bad_lines='skip')
            if df.empty:
                tk.Label(training_frame, text="Pas d'entraînement cette semaine", bg="#dcfce7").pack(pady=20)
            else:
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
                week_start = datetime.datetime.now() - datetime.timedelta(days=7)
                week_df = df[df['Date'] >= week_start]
                if week_df.empty:
                    tk.Label(training_frame, text="Aucun entraînement cette semaine", bg="#dcfce7").pack(pady=20)
                else:
                    tree = ttk.Treeview(training_frame, columns=("Date", "Groupes", "Type"), show="headings")
                    tree.heading("Date", text="Date")
                    tree.heading("Groupes", text="Groupes")
                    tree.heading("Type", text="Type")
                    for _, row in week_df.iterrows():
                        tree.insert("", "end", values=(row['Date'].strftime("%d/%m"), row.get('Groupes musculaires', 'N/A'), row.get('Type entrainement', 'N/A')))
                    tree.pack(fill='both', expand=True)

        cycle_frame = tk.Frame(main_frame, bg="#fee2e2", bd=2, relief="groove", padx=10, pady=10)
        cycle_frame.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)

        tk.Label(cycle_frame, text="💉 Cycle semaine", font=("Helvetica", 16, "bold"), bg="#fee2e2").pack(pady=10)

        fichier_cycle = self.current_prefix + "cycle.csv"
        if not os.path.exists(fichier_cycle):
            tk.Label(cycle_frame, text="Pas de cycle cette semaine", bg="#fee2e2").pack(pady=20)
        else:
            df = pd.read_csv(fichier_cycle, on_bad_lines='skip')
            if df.empty:
                tk.Label(cycle_frame, text="Pas de cycle cette semaine", bg="#fee2e2").pack(pady=20)
            else:
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
                week_df = df[df['Date'] >= week_start]
                if week_df.empty:
                    tk.Label(cycle_frame, text="Aucun cycle cette semaine", bg="#fee2e2").pack(pady=20)
                else:
                    tree = ttk.Treeview(cycle_frame, columns=("Date", "Testo", "hCG", "Phase"), show="headings")
                    tree.heading("Date", text="Date")
                    tree.heading("Testo", text="Testo")
                    tree.heading("hCG", text="hCG")
                    tree.heading("Phase", text="Phase")
                    for _, row in week_df.iterrows():
                        tree.insert("", "end", values=(row['Date'].strftime("%d/%m"), row.get('Dose testo (mg/sem)', 'N/A'), row.get('hCG (UI/sem)', 'N/A'), row.get('Phase (blast/cruise)', 'N/A')))
                    tree.pack(fill='both', expand=True)

        self.root.update()
        self.root.lift()

    def show_entrainement_frame(self):
        for widget in self.content.winfo_children():
            widget.destroy()

        tk.Label(self.content, text=f"ENTRAÎNEMENT - Élève : {self.selected_user_name}", font=("Helvetica", 28, "bold"), bg="#f9fafb", fg="#1f2937").pack(pady=20)

        cal_frame = tk.Frame(self.content, bg="#f9fafb")
        cal_frame.pack(pady=10, fill='x')

        self.calendar = Calendar(cal_frame, selectmode='day', year=2026, month=2, day=20, background='white', foreground='black', selectbackground='#2563eb')
        self.calendar.pack(side='left', padx=20)

        tk.Label(self.content, text="Groupes musculaires :", font=("Helvetica", 14, "bold"), bg="#f9fafb", fg="#1f2937").pack(pady=15, anchor='w', padx=20)

        groupes_frame = tk.Frame(self.content, bg="#f9fafb")
        groupes_frame.pack(anchor='w', padx=40)

        self.groupes_vars = {}
        groupes = ["Pecs", "Dos", "Cuisses", "Épaules", "Bras", "Full body", "Alpha body"]
        for groupe in groupes:
            var = tk.BooleanVar()
            chk = tk.Checkbutton(groupes_frame, text=groupe, variable=var, bg="#f9fafb", fg="#1f2937", selectcolor="#2563eb")
            chk.pack(anchor='w')
            self.groupes_vars[groupe] = var

        tk.Label(self.content, text="Type d'entraînement principal :", font=("Helvetica", 14, "bold"), bg="#f9fafb", fg="#1f2937").pack(pady=15, anchor='w', padx=20)

        type_frame = tk.Frame(self.content, bg="#f9fafb")
        type_frame.pack(anchor='w', padx=40)

        tk.Label(type_frame, text="Myofibrillaire (force)", font=("Helvetica", 12, "bold"), bg="#f9fafb", fg="#1f2937").grid(row=0, column=0, sticky='w', padx=10)
        self.myofib_var.set("")
        ttk.Combobox(type_frame, textvariable=self.myofib_var, values=myofib_options, state="readonly", width=60).grid(row=1, column=0, padx=10, pady=5)

        tk.Label(type_frame, text="Sarcoplasmique (volume)", font=("Helvetica", 12, "bold"), bg="#f9fafb", fg="#1f2937").grid(row=0, column=1, sticky='w', padx=10)
        self.sarco_var.set("")
        ttk.Combobox(type_frame, textvariable=self.sarco_var, values=sarco_options, state="readonly", width=60).grid(row=1, column=1, padx=10, pady=5)

        tk.Label(self.content, text="Note / commentaire :", font=("Helvetica", 14, "bold"), bg="#f9fafb", fg="#1f2937").pack(pady=15, anchor='w', padx=20)

        self.note_text = tk.Text(self.content, height=6, width=80, bg="white", fg="black")
        self.note_text.pack(padx=20, pady=5)

        btn_frame = tk.Frame(self.content, bg="#f9fafb")
        btn_frame.pack(pady=20)

        ttk.Button(btn_frame, text="SAUVEGARDER ENTRAÎNEMENT", command=self.sauvegarder_entrainement).pack(side='left', padx=10)
        ttk.Button(btn_frame, text="Retour Dashboard", command=self.show_dashboard).pack(side='left', padx=10)

    def sauvegarder_entrainement(self):
        if self.current_user is None:
            messagebox.showerror("Erreur", "Sélectionne un élève d'abord")
            return

        try:
            date = self.calendar.get_date()
            groupes = [g for g, v in self.groupes_vars.items() if v.get()]
            groupes_str = ", ".join(groupes) if groupes else "Aucun"
            type_str = ""
            if self.myofib_var.get():
                type_str += "Myofibrillaire: " + self.myofib_var.get()
            if self.sarco_var.get():
                type_str += " | Sarcoplasmique: " + self.sarco_var.get()
            note = self.note_text.get("1.0", tk.END).strip()

            fichier = self.current_prefix + "entrainement.csv"
            with open(fichier, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([date, groupes_str, type_str, note])

            messagebox.showinfo("Succès", "Entraînement sauvegardé ! 💪")
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

    def show_nutrition_frame(self):
        for widget in self.content.winfo_children():
            widget.destroy()

        tk.Label(self.content, text=f"NUTRITION - Élève : {self.selected_user_name}", font=("Helvetica", 28, "bold"), bg="#f9fafb", fg="#1f2937").pack(pady=20)

        date_frame = tk.Frame(self.content, bg="#f9fafb")
        date_frame.pack(pady=10, fill='x', padx=20)

        tk.Label(date_frame, text="Date du jour :", font=("Helvetica", 14, "bold"), bg="#f9fafb").pack(side='left', padx=10)
        self.date_entry = Calendar(date_frame, selectmode='day', year=datetime.date.today().year, month=datetime.date.today().month, day=datetime.date.today().day, background='white', foreground='black', selectbackground='#2563eb')
        self.date_entry.pack(side='left', padx=10)

        calc_frame = tk.Frame(self.content, bg="#f9fafb")
        calc_frame.pack(pady=20, padx=40, fill='x')

        self.prenom_var = tk.StringVar()
        tk.Label(calc_frame, text="Prénom :", font=("Helvetica", 12), bg="#f9fafb", fg="#1f2937").pack(side='left', padx=10)
        ttk.Entry(calc_frame, textvariable=self.prenom_var, width=15).pack(side='left', padx=5)

        self.poids_var = tk.StringVar()
        tk.Label(calc_frame, text="Poids (kg) :", font=("Helvetica", 12), bg="#f9fafb", fg="#1f2937").pack(side='left', padx=10)
        ttk.Entry(calc_frame, textvariable=self.poids_var, width=10).pack(side='left', padx=5)

        self.taille_var = tk.StringVar()
        tk.Label(calc_frame, text="Taille (cm) :", font=("Helvetica", 12), bg="#f9fafb", fg="#1f2937").pack(side='left', padx=10)
        ttk.Entry(calc_frame, textvariable=self.taille_var, width=10).pack(side='left', padx=5)

        self.age_var = tk.StringVar()
        tk.Label(calc_frame, text="Age :", font=("Helvetica", 12), bg="#f9fafb", fg="#1f2937").pack(side='left', padx=10)
        ttk.Entry(calc_frame, textvariable=self.age_var, width=10).pack(side='left', padx=5)

        self.sexe_var = tk.StringVar(value="Homme")
        tk.Label(calc_frame, text="Sexe :", font=("Helvetica", 12), bg="#f9fafb", fg="#1f2937").pack(side='left', padx=10)
        ttk.Combobox(calc_frame, textvariable=self.sexe_var, values=["Homme", "Femme"], state="readonly", width=10).pack(side='left', padx=5)

        self.objectif_var = tk.StringVar(value="Maintien")
        tk.Label(calc_frame, text="Objectif :", font=("Helvetica", 12), bg="#f9fafb", fg="#1f2937").pack(side='left', padx=10)
        ttk.Combobox(calc_frame, textvariable=self.objectif_var, values=["Gain de masse", "Perte de poids", "Maintien"], state="readonly", width=15).pack(side='left', padx=5)

        ttk.Button(self.content, text="Calculer IMC / BMR / Macros", command=self.calculer_nutrition).pack(pady=10)

        self.calc_table = ttk.Treeview(self.content, columns=("Métrique", "Valeur"), show="headings")
        self.calc_table.heading("Métrique", text="Métrique")
        self.calc_table.heading("Valeur", text="Valeur")
        self.calc_table.pack(pady=10, padx=20, fill='x')

        tk.Label(self.content, text="Macros saisies (optionnel)", font=("Helvetica", 14, "bold"), bg="#f9fafb", fg="#1f2937").pack(pady=15, anchor='w', padx=20)

        macros_frame = tk.Frame(self.content, bg="#f9fafb")
        macros_frame.pack(pady=10, padx=40, fill='x')

        self.macros_entries = {}
        macros_champs = ["Calories estimées", "Protéines (g)", "Glucides (g)", "Lipides (g)"]
        for champ in macros_champs:
            row = tk.Frame(macros_frame, bg="#f9fafb")
            row.pack(fill='x', pady=8)

            tk.Label(row, text=f"{champ} :", font=("Helvetica", 12), bg="#f9fafb", fg="#1f2937").pack(side='left', padx=10)
            entry = ttk.Entry(row, width=15)
            entry.pack(side='left', padx=5)
            self.macros_entries[champ] = entry

        tk.Label(self.content, text="Note / ressenti / repas spéciaux :", font=("Helvetica", 14, "bold"), bg="#f9fafb", fg="#1f2937").pack(pady=15, anchor='w', padx=20)

        self.nutrition_note_text = tk.Text(self.content, height=6, width=80, bg="white", fg="black")
        self.nutrition_note_text.pack(padx=20, pady=5)

        btn_frame = tk.Frame(self.content, bg="#f9fafb")
        btn_frame.pack(pady=30)

        ttk.Button(btn_frame, text="SAUVEGARDER NUTRITION", command=self.sauvegarder_nutrition).pack(side='left', padx=20)
        ttk.Button(btn_frame, text="Retour Dashboard", command=self.show_dashboard).pack(side='left', padx=20)

        tk.Label(self.content, text="Historique entrées (clic pour graphs)", font=("Helvetica", 14, "bold"), bg="#f9fafb", fg="#1f2937").pack(pady=15, anchor='w', padx=20)

        self.nutrition_history = tk.Listbox(self.content, height=10, width=100)
        self.nutrition_history.pack(padx=20, pady=5)
        self.nutrition_history.bind('<<ListboxSelect>>', self.show_nutrition_graphs)

        self.load_nutrition_history()

        self.graph_frame = tk.Frame(self.content, bg="#f9fafb")
        self.graph_frame.pack(pady=20, fill='both', expand=True)

    def load_nutrition_history(self):
        self.nutrition_history.delete(0, tk.END)
        if self.current_user is None:
            return
        fichier = self.current_prefix + "nutrition.csv"
        if os.path.exists(fichier):
            with open(fichier, 'r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader, None)
                for row in reader:
                    if len(row) >= 8:
                        display = f"{row[0]} | {row[1]} | Cal: {row[2]} | Poids: {row[7]} kg"
                        self.nutrition_history.insert(tk.END, display)

    def show_nutrition_graphs(self, event):
        if self.current_user is None:
            return

        selection = self.nutrition_history.curselection()
        if not selection:
            return

        selected = self.nutrition_history.get(selection[0])
        date_str = selected.split(" | ")[0].strip()
        date = self.parse_date(date_str)
        if not date:
            return

        try:
            fichier = self.current_prefix + "nutrition.csv"
            df = pd.read_csv(fichier, on_bad_lines='skip')
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            df = df.dropna(subset=['Date'])
            df['Date'] = df['Date'].dt.date
            df = df.sort_values('Date')

            for widget in self.graph_frame.winfo_children():
                widget.destroy()

            fig1 = plt.Figure(figsize=(6, 4))
            ax1 = fig1.add_subplot(111)
            ax1.plot(df['Date'], df['Poids (kg)'], marker='o', color='blue')
            ax1.set_title("Historique Poids")
            ax1.grid(True)
            canvas1 = FigureCanvasTkAgg(fig1, master=self.graph_frame)
            canvas1.draw()
            canvas1.get_tk_widget().pack(side='left', padx=20)

            selected_row = df[df['Date'] == date]
            if selected_row.empty:
                return

            poids = float(selected_row['Poids (kg)'].values[0])
            taille = float(self.taille_var.get() or 180) / 100
            imc = poids / (taille ** 2)

            tranches = {
                'Sous-poids': max(0, min(18.5, imc)),
                'Normal': max(0, min(6.4, imc - 18.5)),
                'Surpoids': max(0, min(5, imc - 25)),
                'Obésité': max(0, imc - 30)
            }

            fig2 = plt.Figure(figsize=(6, 4))
            ax2 = fig2.add_subplot(111)
            ax2.pie(tranches.values(), labels=tranches.keys(), autopct='%1.1f%%', colors=['yellow', 'green', 'orange', 'red'])
            ax2.set_title(f"IMC : {imc:.1f}")
            canvas2 = FigureCanvasTkAgg(fig2, master=self.graph_frame)
            canvas2.draw()
            canvas2.get_tk_widget().pack(side='left', padx=20)

        except Exception as e:
            messagebox.showerror("Erreur", str(e))

    def calculer_nutrition(self):
        try:
            poids = float(self.poids_var.get() or 0)
            taille = float(self.taille_var.get() or 0) / 100
            age = float(self.age_var.get() or 0)
            sexe = self.sexe_var.get()
            objectif = self.objectif_var.get()

            if poids <= 0 or taille <= 0 or age <= 0:
                messagebox.showerror("Erreur", "Poids, taille et age doivent être positifs.")
                return

            imc = poids / (taille ** 2)
            imc_categ = "Sous-poids" if imc < 18.5 else "Normal" if imc < 25 else "Surpoids" if imc < 30 else "Obésité"

            if sexe == "Homme":
                bmr = 10 * poids + 6.25 * (taille * 100) - 5 * age + 5
            else:
                bmr = 10 * poids + 6.25 * (taille * 100) - 5 * age - 161

            activity_factor = 1.55
            bmr_daily = bmr * activity_factor
            if objectif == "Gain de masse":
                calories = bmr_daily * 1.2
            elif objectif == "Perte de poids":
                calories = bmr_daily * 0.8
            else:
                calories = bmr_daily * 1.0

            protein = 2 * poids
            carbs = (0.5 if objectif == "Gain de masse" else 0.4 if objectif == "Maintien" else 0.3) * calories / 4
            lip = (0.3 if objectif == "Gain de masse" else 0.3 if objectif == "Maintien" else 0.4) * calories / 9

            for item in self.calc_table.get_children():
                self.calc_table.delete(item)

            self.calc_table.insert("", "end", values=("IMC", f"{imc:.1f} ({imc_categ})"))
            self.calc_table.insert("", "end", values=("BMR", f"{bmr:.0f} kcal"))
            self.calc_table.insert("", "end", values=("Calories/j", f"{calories:.0f} kcal"))
            self.calc_table.insert("", "end", values=("Protéines", f"{protein:.0f} g"))
            self.calc_table.insert("", "end", values=("Glucides", f"{carbs:.0f} g"))
            self.calc_table.insert("", "end", values=("Lipides", f"{lip:.0f} g"))

        except ValueError:
            messagebox.showerror("Erreur", "Valeurs numériques invalides")

    def sauvegarder_nutrition(self):
        if self.current_user is None:
            messagebox.showerror("Erreur", "Sélectionne un élève d'abord")
            return

        try:
            date = self.date_entry.get_date()
            prenom = self.prenom_var.get().strip()
            if not prenom:
                messagebox.showerror("Erreur", "Prénom requis")
                return

            calories = self.macros_entries["Calories estimées"].get().strip() or "0"
            proteines = self.macros_entries["Protéines (g)"].get().strip() or "0"
            glucides = self.macros_entries["Glucides (g)"].get().strip() or "0"
            lipides = self.macros_entries["Lipides (g)"].get().strip() or "0"
            note = self.nutrition_note_text.get("1.0", tk.END).strip()

            row = [date, prenom, calories, proteines, glucides, lipides, note, self.poids_var.get().strip() or "0"]

            fichier = self.current_prefix + "nutrition.csv"
            with open(fichier, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(row)

            messagebox.showinfo("Succès", "Sauvegardé ! 💪")
            self.load_nutrition_history()

        except Exception as e:
            messagebox.showerror("Erreur save", str(e))

    def show_cycle_disclaimer(self):
        if not self.cycle_disclaimer_shown:
            disclaimer_text = (
                "AVERTISSEMENT IMPORTANT\n\n"
                "Les produits anabolisants et hormones (testostérone, hCG, etc.) peuvent causer des effets secondaires graves : risques cardiovasculaires, hépatiques, endocriniens, psychologiques et autres complications potentiellement mortelles.\n\n"
                "Leur utilisation sans supervision médicale est illégale dans de nombreux pays et peut entraîner des poursuites pénales.\n\n"
                "Cette application est un outil de suivi personnel fictif et éducatif. Elle ne fournit aucun conseil médical, pharmacologique ou thérapeutique.\n\n"
                "Nous dégageons toute responsabilité en cas d'utilisation inappropriée, de dommages à la santé, de problèmes légaux ou autres conséquences.\n\n"
                "Consultez toujours un médecin avant tout usage de substances anabolisantes.\n\n"
                "En cliquant sur 'Accepter', vous confirmez avoir lu et compris ce disclaimer et assumez l'entière responsabilité de vos actions."
            )

            fenetre = tk.Toplevel(self.root)
            fenetre.title("Avertissement - Cycle hormonal")
            fenetre.geometry("600x400")
            fenetre.configure(bg="#f9fafb")

            scrolled_text = scrolledtext.ScrolledText(fenetre, wrap=tk.WORD, width=70, height=15, font=("Helvetica", 10))
            scrolled_text.insert(tk.INSERT, disclaimer_text)
            scrolled_text.config(state=tk.DISABLED)
            scrolled_text.pack(pady=10, padx=10)

            button_frame = tk.Frame(fenetre, bg="#f9fafb")
            button_frame.pack(pady=10)

            def accept():
                fenetre.destroy()
                self.cycle_disclaimer_shown = True
                self.show_cycle_frame()

            ttk.Button(button_frame, text="ACCEPTER", command=accept).pack(side=tk.LEFT, padx=20)
            ttk.Button(button_frame, text="REFUSER", command=fenetre.destroy).pack(side=tk.LEFT, padx=20)
        else:
            self.show_cycle_frame()

    def show_cycle_frame(self):
        for widget in self.content.winfo_children():
            widget.destroy()

        tk.Label(self.content, text=f"CYCLE HORMONAL - Élève : {self.selected_user_name}", font=("Helvetica", 28, "bold"), bg="#f9fafb", fg="#1f2937").pack(pady=20)

        date_frame = tk.Frame(self.content, bg="#f9fafb")
        date_frame.pack(pady=10, fill='x', padx=20)

        tk.Label(date_frame, text="Date :", font=("Helvetica", 14, "bold"), bg="#f9fafb").pack(side='left', padx=10)
        date_entry = Calendar(date_frame, selectmode='day', year=datetime.date.today().year, month=datetime.date.today().month, day=datetime.date.today().day, background='white', foreground='black', selectbackground='#2563eb')
        date_entry.pack(side='left', padx=10)

        champs_frame = tk.Frame(self.content, bg="#f9fafb")
        champs_frame.pack(pady=20, padx=40, fill='x')

        champs = [
            ("Dose testo (mg/sem)", "mg/sem"),
            ("hCG (UI/sem)", "UI/sem"),
            ("Phase (blast/cruise)", "")
        ]

        entries = {}
        for label_text, unit in champs:
            row = tk.Frame(champs_frame, bg="#f9fafb")
            row.pack(fill='x', pady=8)

            tk.Label(row, text=f"{label_text} :", font=("Helvetica", 12), bg="#f9fafb", fg="#1f2937").pack(side='left', padx=10)
            entry = ttk.Entry(row, width=20)
            entry.pack(side='left', padx=5)
            tk.Label(row, text=unit, font=("Helvetica", 12), bg="#f9fafb").pack(side='left', padx=5)
            entries[label_text] = entry

        tk.Label(self.content, text="Note :", font=("Helvetica", 14, "bold"), bg="#f9fafb", fg="#1f2937").pack(pady=15, anchor='w', padx=20)

        note_text = tk.Text(self.content, height=6, width=80, bg="white", fg="black")
        note_text.pack(padx=20, pady=5)

        btn_frame = tk.Frame(self.content, bg="#f9fafb")
        btn_frame.pack(pady=30)

        def sauvegarder():
            try:
                date = date_entry.get_date()
                dose_testo = entries["Dose testo (mg/sem)"].get().strip() or "0"
                hcg = entries["hCG (UI/sem)"].get().strip() or "0"
                phase = entries["Phase (blast/cruise)"].get().strip()
                note = note_text.get("1.0", tk.END).strip()

                fichier = self.current_prefix + "cycle.csv"
                row = [date, dose_testo, hcg, phase, note]
                with open(fichier, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(row)

                messagebox.showinfo("Succès", "Cycle sauvegardé")
            except Exception as e:
                messagebox.showerror("Erreur", str(e))

        ttk.Button(btn_frame, text="SAUVEGARDER", command=sauvegarder).pack(side='left', padx=20)
        ttk.Button(btn_frame, text="Retour Dashboard", command=self.show_dashboard).pack(side='left', padx=20)

    def analyser_entrainements(self):
        messagebox.showinfo("Analyse", "Fonction en développement")

    def exporter_tous(self):
        messagebox.showinfo("Export", "En développement")

if __name__ == "__main__":
    print("[DEBUG] Lancement main")
    root = tk.Tk()
    app = EragrokApp(root)
    root.mainloop()