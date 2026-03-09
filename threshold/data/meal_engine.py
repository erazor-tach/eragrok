# data/meal_engine.py — THRESHOLD · Moteur nutritionnel
# ─────────────────────────────────────────────────────────────────────────────
# Extrait d'ERAGROK features_module.py — logique pure sans UI.
# Contient :
#   • FOOD_DB, FOOD_DB_EXT — base nutritionnelle (kcal, prot, gluc, lip / 100g)
#   • FOOD_CATS, SLOT_TEMPLATES, MEAL_SLOTS — catégories et templates repas
#   • FOOD_MIN_PORTION, FOOD_MAX_PORTION — bornes anti-gaspillage
#   • FOOD_INCOMPATIBLE, FOOD_SAME_FAMILY — matrices de compatibilité
#   • FOOD_FIBER — fibres alimentaires (g/100g)
#   • _generate_meal_plan() — générateur 7+2 passes
#   • _generate_multiday_plan() — générateur multiday
#   • compute_diversity_score() — score de diversité
#   • compute_shopping_list() — liste de courses avec conversions cuit/cru
# ─────────────────────────────────────────────────────────────────────────────
import datetime

FOOD_DB = {
    # (kcal/100g, prot/100g, gluc/100g, lip/100g)
    "Blanc de poulet (cuit)":     (165, 31,  0,   3.6),
    "Blanc de dinde (cuit)":      (135, 29,  0,   2.5),
    "Boeuf haché 5% MG":          (152, 26,  0,   5.0),
    "Saumon (cuit)":              (208, 20,  0,  13.0),
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
    "Flocons d'avoine":           (367, 13.5, 58.7,  7.0),
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

    food_var  = tk.StringVar(value=sorted(FOOD_DB_EXT.keys())[0])
    grams_var = tk.StringVar(value="150")

    mk_label(top, "Aliment :", size="small", color=TH.TEXT_SUB).pack(side="left",padx=(0,6))
    cb = mk_combo(top, sorted(FOOD_DB_EXT.keys()), width=260)
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
            vals = FOOD_DB_EXT.get(food)
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
        if food in FOOD_DB_EXT and grams > 0:
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
    "Yaourt 0% nature":          ( 43,  4.3,  5.7,  0.1),
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
    "Jambon blanc (dégraissé)":  (107, 17.5,  1.5,  3.5),
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
    "Pomme de terre (cuite)":    ( 80,  1.9, 17.5,  0.1),
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
    "Poivron (cru)":             ( 27,  1.0,  5.2,  0.2),
    "Tomate (crue)":             ( 18,  0.9,  3.9,  0.2),
    "Salade verte":              ( 15,  1.4,  2.3,  0.3),
    "Champignons (cuits)":       ( 28,  3.1,  4.0,  0.3),
    "Chou-fleur (cuit)":         ( 23,  2.3,  3.8,  0.2),
    "Concombre (cru)":           ( 12,  0.6,  2.2,  0.1),
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
    "Emmental":                  (370, 27.5,  0.5, 29.0),
    "Comté":                     (415, 27.0,  0.3, 34.0),
    "Gruyère":                   (413, 27.0,  0.4, 33.0),

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


# ── Constante par défaut pour les aliments non listés dans FOOD_MAX_PORTION ──
# Utilisée PARTOUT dans les .get() du générateur pour éviter des caps incohérents.
FOOD_MAX_DEFAULT = 300

# ── Portions maximales réalistes par aliment (g ou ml) ───────────────────────
# Empêche des quantités immangables (ex: 600g de riz, 400g de blanc d'oeuf).
# Un aliment NON listé ici recevra FOOD_MAX_DEFAULT (300g).
#
# Philosophie :
#   "satiété"  → au-delà = écœurement / pas ingérable en un repas
#   "densité"  → aliment très calorique → cap bas pour ne pas exploser les macros
#   "cuisson"  → portion raisonnable dans une assiette / un bol
#   "produit"  → conditionné en portions standard (pot, sachet, filet)
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
    # ── Légumes (portion max d'accompagnement par repas) ────────────────────
    "Brocoli (cuit)":            250,   # gros accompagnement
    "Courgette (cuite)":         250,
    "Haricots verts (cuits)":    250,
    "Asperges (cuites)":         200,   # ~10 asperges
    "Champignons (cuits)":       200,
    "Chou-fleur (cuit)":         250,
    "Poivron (cru)":             200,   # ~1.5 poivrons
    "Tomate (crue)":             250,   # ~2 tomates
    "Salade verte":              150,   # saladier raisonnable
    "Concombre (cru)":           250,
    "Épinards (crus)":           150,   # volume important, poids faible
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


# ── Fibres alimentaires (g / 100g) ──────────────────────────────────────────
# Données ANSES / USDA.  Aliments absents = 0g par défaut.
# Calculées à l'affichage (pas dans le moteur) → zéro risque sur les 7 passes.
FOOD_FIBER = {
    # Protéines animales → toutes 0g (pas de fibres)
    # Glucides cuits
    "Riz cuit":                    0.4,
    "Riz brun (cuit)":             1.8,
    "Pâtes cuites":                1.8,
    "Pâtes blanches (cuites)":     1.8,
    "Pâtes complètes (cuites)":    4.5,
    "Patate douce (cuite)":        3.0,
    "Patate douce violette (cuite)": 3.0,
    "Pomme de terre (cuite)":      2.2,
    "Quinoa (cuit)":               2.8,
    "Lentilles (cuites)":          7.9,
    "Pois chiches (cuits)":        7.6,
    "Haricots rouges (cuits)":     6.4,
    "Haricots blancs (cuits)":     6.3,
    "Boulgour (cuit)":             4.5,
    "Semoule (cuite)":             1.4,
    "Edamame (cuit)":              5.2,
    # Glucides secs / poudres
    "Flocons d'avoine":           10.6,
    "Pain complet":                6.8,
    "Pain blanc":                  2.7,
    "Müesli nature (sans sucre)":  7.5,
    "Galettes de riz nature":      1.7,
    "Crème de riz HSN":            0.5,
    "Farine d'avoine HSN":         8.5,
    # Fruits
    "Banane":                      2.6,
    "Pomme":                       2.4,
    "Orange":                      2.3,
    "Kiwi":                        3.0,
    "Fraises":                     2.0,
    "Myrtilles":                   2.4,
    "Mangue":                      1.6,
    "Ananas":                      1.4,
    "Poire":                       3.1,
    "Pastèque":                    0.4,
    "Raisins":                     0.9,
    # Légumes
    "Brocoli (cuit)":              3.3,
    "Épinards (crus)":             2.2,
    "Courgette (cuite)":           1.1,
    "Haricots verts (cuits)":      3.4,
    "Asperges (cuites)":           2.1,
    "Poivron (cru)":               1.7,
    "Tomate (crue)":               1.2,
    "Salade verte":                1.3,
    "Champignons (cuits)":         2.2,
    "Chou-fleur (cuit)":           2.9,
    "Concombre (cru)":             0.5,
    # Lipides / oléagineux
    "Avocat":                      6.7,
    "Amandes":                    12.5,
    "Noix":                        6.7,
    "Noix de cajou":               3.3,
    "Cacahuètes":                  8.5,
    "Beurre de cacahuète":         6.3,
    "Beurre d'amande":             6.0,
    "Graines de chia":            34.4,
    "Graines de lin":             27.3,
    "Tahini (purée sésame)":       9.3,
    "Chocolat noir 70%":          11.0,
    "Chocolat noir 85%":          12.5,
    "Cacao pur en poudre":        33.2,
    # Laitiers / poudres / viandes → 0g (défaut)
    # Tofu / protéines végétales
    "Tofu ferme":                  0.9,
}

def _fiber_for(food: str, grams: float) -> float:
    """Retourne les fibres (g) pour une portion donnée."""
    return FOOD_FIBER.get(food, 0.0) * grams / 100.0# ── Catégories fonctionnelles (utilisées par les templates) ───────────────────
FOOD_CATS = {
    "oeuf":             ["Oeuf entier", "Blanc d'oeuf", "Œuf dur entier"],
    "glucide_matin":    ["Flocons d'avoine", "Müesli nature (sans sucre)",
                         "Galettes de riz nature"],
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
    # Portions lipides réduites pour contrôler l'excès (lipides cachés dans prot)
    "matin": [
        [("oeuf","prot"),          ("glucide_matin","gluc"), ("huile_cuisson",8),  ("fruit",120), ("laitier","prot_rest")],
        [("oeuf","prot"),          ("glucide_matin","gluc"), ("huile_cuisson",8),  ("fruit",120)],
        [("laitier","prot"),       ("glucide_matin","gluc"), ("lipide_matin",15),  ("fruit",120)],
        [("pain_seulement","gluc"),("beurre_pain",10),       ("oeuf","prot"),       ("fromage_dur",25)],
        [("pain_seulement","gluc"),("beurre_pain",10),       ("laitier","prot")],
        [("pain_seulement","gluc"),("beurre_pain",10),       ("sucrant_matin",20), ("laitier","prot")],
        [("pain_seulement","gluc"),("beurre_pain",10),       ("sucrant_matin",20), ("oeuf","prot")],
        [("pain_seulement","gluc"),("beurre_pain",10),       ("fromage_dur",25),   ("fruit",120)],
        [("oeuf","prot"),          ("glucide_matin","gluc"), ("huile_cuisson",8),  ("sucrant_matin",20)],
        [("laitier","prot"),       ("glucide_matin","gluc"), ("fromage_dur",25),   ("fruit",100)],
        [("oeuf","prot"),          ("pain_seulement","gluc"),("huile_cuisson",8),  ("fromage_dur",25)],
        [("laitier","prot"),       ("glucide_matin","gluc")],
        [("laitier","prot"),       ("glucide_matin","gluc"), ("boisson_matin",200)],
        # Templates sans lipide ajouté (pour diluer l'excès global)
        [("oeuf","prot"),          ("glucide_matin","gluc"), ("fruit",130)],
        [("laitier","prot"),       ("glucide_matin","gluc"), ("fruit",130)],
    ],
    # ── MIDI ──────────────────────────────────────────────────────────────────
    "midi": [
        [("proteine_midi","prot"), ("glucide_midi","gluc"),  ("legume",150), ("huile_cuisson",8)],
        [("proteine_midi","prot"), ("glucide_midi","gluc"),  ("legume",150), ("lipide_sain",10)],
        [("proteine_midi","prot"), ("glucide_midi","gluc"),  ("legume",150), ("fromage_dur",20)],
        [("proteine_midi","prot"), ("glucide_midi","gluc"),  ("legume",150)],
        # Template sans lipide ajouté
        [("proteine_midi","prot"), ("glucide_midi","gluc"),  ("legume",180)],
    ],
    # ── COLLATION ─────────────────────────────────────────────────────────────
    "collation": [
        [("whey","prot"),          ("glucide_collation","gluc")],
        [("laitier","prot"),       ("glucide_collation","gluc"), ("lipide_collation",15)],
        [("laitier","prot"),       ("lipide_collation",20),      ("fruit",130)],
        [("laitier","prot"),       ("fruit",130)],
        [("whey","prot")],
        [("fromage_dur",30),       ("fruit",150)],
        [("laitier","prot"),       ("lipide_collation",20)],
        # Templates légers sans lipide
        [("laitier","prot"),       ("glucide_collation","gluc")],
        [("whey","prot"),          ("fruit",130)],
    ],
    # ── SOIR ──────────────────────────────────────────────────────────────────
    "soir": [
        [("proteine_maigre","prot"), ("glucide_soir","gluc"), ("legume",180), ("huile_cuisson",8)],
        [("proteine_maigre","prot"), ("glucide_soir","gluc"), ("legume",150), ("lipide_sain",10)],
        [("proteine_grasse","prot"), ("glucide_soir","gluc"), ("legume",180)],
        [("proteine_grasse","prot"), ("legume",200)],
        [("proteine_maigre","prot"), ("legume",200), ("huile_cuisson",8)],
        [("proteine_maigre","prot"), ("glucide_soir","gluc"), ("legume",150), ("fromage_dur",20)],
        # Template sans lipide ajouté
        [("proteine_maigre","prot"), ("glucide_soir","gluc"), ("legume",180)],
    ],
    # ── AVANT COUCHER ─────────────────────────────────────────────────────────
    "coucher": [
        [("supplement_lent","prot")],
        [("laitier_lent","prot"),    ("lipide_coucher",15)],
        [("laitier_lent","prot"),    ("lipide_coucher",15)],
        [("laitier","prot"),         ("lipide_coucher",15)],
        [("supplement_lent","prot")],
        [("laitier_lent","prot")],
        [("supplement_lent","prot"), ("lipide_coucher",15)],
        [("laitier","prot")],
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


def _food_swap_alternatives(food: str, meal_items: list, selected_foods: set = None) -> list:
    """
    Retourne les alternatives de remplacement pour `food` dans un repas.
    - Même(s) catégorie(s) FOOD_CATS que l'aliment original
    - Compatibles avec les autres items du repas
    - Filtrées par selected_foods si fourni
    Retourne [(food_name, kcal/100, prot/100, gluc/100, lip/100), ...]
    """
    # Trouver les catégories de l'aliment
    food_cats = [cat for cat, foods in FOOD_CATS.items() if food in foods]
    if not food_cats:
        return []

    # Collecter les candidats de toutes les catégories partagées
    candidates = set()
    for cat in food_cats:
        for f in FOOD_CATS.get(cat, []):
            if f != food and f in FOOD_DB_EXT:
                candidates.add(f)

    # Filtrer par sélection utilisateur
    if selected_foods:
        candidates = {f for f in candidates if f in selected_foods}

    # Filtrer par compatibilité avec les autres items du repas
    other_foods = [it["food"] for it in meal_items if it["food"] != food]
    result = []
    for c in sorted(candidates):
        if _filter_compatible(c, other_foods):
            k, p, g, l = FOOD_DB_EXT[c]
            result.append((c, k, p, g, l))
    return result
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
        cap = FOOD_MAX_PORTION.get(food, FOOD_MAX_DEFAULT)
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
                    # Portion fixe du template — bornée entre min et max
                    mn_fix = FOOD_MIN_PORTION.get(food, 0)
                    mx_fix = FOOD_MAX_PORTION.get(food, FOOD_MAX_DEFAULT)
                    g = max(mn_fix, min(mx_fix, mode))
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
                    g = min(FOOD_MAX_PORTION.get(food, FOOD_MAX_DEFAULT), g)
                elif mode == "prot_rest":
                    g = _g_for(food, rem_prot, 1)
                    if g == -1 or g < FOOD_MIN_PORTION.get(food, 10):
                        continue  # pas assez de marge → skip
                    g = min(FOOD_MAX_PORTION.get(food, FOOD_MAX_DEFAULT), g)
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
                    g = min(FOOD_MAX_PORTION.get(food, FOOD_MAX_DEFAULT), g)
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

        # ── Anti-doublon féculents & légumes : si déjà présent dans le repas,
        #    augmenter la portion existante au lieu d'en ajouter un deuxième.
        STARCH_CATS = {"glucide_midi", "glucide_soir", "glucide_matin",
                       "glucide_collation", "pain_seulement"}
        VEGGIE_CATS = {"legume"}
        existing_starch = None
        existing_veggie = None
        for it in m["items"]:
            if any(it["food"] in FOOD_CATS.get(c, []) for c in STARCH_CATS):
                existing_starch = it
            if any(it["food"] in FOOD_CATS.get(c, []) for c in VEGGIE_CATS):
                existing_veggie = it

        if existing_starch and any(bst in FOOD_CATS.get(c, [])
                                    for bst in boosters
                                    for c in STARCH_CATS):
            # Essayer d'augmenter le féculent existant d'abord
            es_food = existing_starch["food"]
            es_cap  = FOOD_MAX_PORTION.get(es_food, FOOD_MAX_DEFAULT)
            k100_es = db[es_food][0]
            if existing_starch["g"] < es_cap and k100_es > 0:
                add_g = min(es_cap - existing_starch["g"],
                            max(20, round(deficit_c / (k100_es / 100.0))))
                if add_g >= 15:
                    old_gc = existing_starch["g_"]
                    new_g = existing_starch["g"] + add_g
                    k, p, gc, l = _macros(es_food, new_g)
                    existing_starch.update({"g": new_g, "kcal": k, "p": p, "g_": gc, "l": l})
                    cur_gluc += (gc - old_gc)
                    continue  # boosté via l'existant → pas besoin d'ajouter

        for bst in boosters:
            if bst not in sel or bst not in db: continue
            if bst in already_foods: continue
            if not _filter_compatible(bst, list(already_foods)): continue
            # Anti-doublon : pas de 2ème féculent ou 2ème légume si déjà présent
            if existing_starch and any(bst in FOOD_CATS.get(c, []) for c in STARCH_CATS):
                continue
            if existing_veggie and any(bst in FOOD_CATS.get(c, []) for c in VEGGIE_CATS):
                continue
            k100, _, _, _ = db[bst]
            if k100 <= 0: continue
            g_bst_raw = max(10, round(deficit_c / (k100 / 100.0)))
            g_bst_mn  = FOOD_MIN_PORTION.get(bst, 10)
            g_bst     = min(FOOD_MAX_PORTION.get(bst, FOOD_MAX_DEFAULT),
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
        # Collecter TOUS les items protéiques triés par quantité de protéines (desc)
        prot_items = sorted(
            [i for m in meals for i in m["items"] if db[i["food"]][1] > 5],
            key=lambda i: i["p"], reverse=True)
        for pi in prot_items:
            if abs(delta_prot) < 2:
                break
            _, p100, _, _ = db[pi["food"]]
            if p100 <= 0:
                continue
            raw_g = pi["g"] + round(delta_prot / (p100 / 100.0))
            mn_g  = FOOD_MIN_PORTION.get(pi["food"], 20)
            new_g = max(mn_g, min(FOOD_MAX_PORTION.get(pi["food"], FOOD_MAX_DEFAULT), raw_g))
            if new_g == pi["g"]:
                continue
            old_p = pi["p"]
            k, p, gc, l = _macros(pi["food"], new_g)
            pi.update({"g": new_g, "kcal": k, "p": p, "g_": gc, "l": l})
            delta_prot -= (p - old_p)  # réduire le delta restant

    # ── PASSE 3 : équilibrage glucides ────────────────────────────────────────
    # 3a. Trim si excès > 3%
    got_gluc = sum(i["g_"] for m in meals for i in m["items"])
    if gluc_total and (got_gluc - gluc_total) / gluc_total * 100 > 3:
        excess_g = got_gluc - gluc_total
        gluc_items = sorted(
            [i for m in meals if m["type"] in ("midi","soir","matin")
             for i in m["items"]
             if any(i["food"] in FOOD_CATS.get(c,[])
                    for c in ("glucide_midi","glucide_soir","glucide_matin",
                              "glucide_collation","pain_seulement"))],
            key=lambda x: x["g_"], reverse=True)
        for gi in gluc_items:
            if excess_g < 2:
                break
            _, _, g100, _ = db[gi["food"]]
            if g100 <= 0:
                continue
            mn_g  = FOOD_MIN_PORTION.get(gi["food"], 30)
            reduce = min(gi["g"] - mn_g, round(excess_g / (g100 / 100.0)))
            if reduce <= 0:
                continue
            new_g = max(mn_g, gi["g"] - reduce)
            old_gc = gi["g_"]
            k, p, gc, l = _macros(gi["food"], new_g)
            gi.update({"g": new_g, "kcal": k, "p": p, "g_": gc, "l": l})
            excess_g -= (old_gc - gc)

    # 3b. Combler si déficit > 3% — augmenter les portions glucidiques
    got_gluc = sum(i["g_"] for m in meals for i in m["items"])
    if gluc_total and (gluc_total - got_gluc) / gluc_total * 100 > 3:
        deficit_g = gluc_total - got_gluc
        gluc_items = sorted(
            [i for m in sorted(meals, key=lambda x: x["slot"]["ratio"], reverse=True)
             if m["type"] in ("midi","soir","matin")
             for i in m["items"]
             if any(i["food"] in FOOD_CATS.get(c,[])
                    for c in ("glucide_midi","glucide_soir","glucide_matin"))],
            key=lambda x: x["g_"], reverse=True)
        for gi in gluc_items:
            if deficit_g < 2:
                break
            _, _, g100, _ = db[gi["food"]]
            if g100 <= 0:
                continue
            cap = FOOD_MAX_PORTION.get(gi["food"], FOOD_MAX_DEFAULT)
            add_g = min(cap - gi["g"], round(deficit_g / (g100 / 100.0)))
            if add_g <= 0:
                continue
            new_g = min(cap, gi["g"] + add_g)
            old_gc = gi["g_"]
            k, p, gc, l = _macros(gi["food"], new_g)
            gi.update({"g": new_g, "kcal": k, "p": p, "g_": gc, "l": l})
            deficit_g -= (gc - old_gc)

    # ── PASSE 4 : équilibrage lipides ─────────────────────────────────────────
    # 4a. Trim si excès > 3% — réduire les lipides rajoutés (huile, beurre...)
    got_lip = sum(i["l"] for m in meals for i in m["items"])
    if lip_total and (got_lip - lip_total) / lip_total * 100 > 3:
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

    # 4b. Combler si déficit > 3% — ajouter huile d'olive sur midi/soir
    got_lip = sum(i["l"] for m in meals for i in m["items"])
    deficit_lip = lip_total - got_lip
    if deficit_lip > lip_total * 0.03:
        lip_avail = _avail("lipide_sain")
        if lip_avail:
            # Filtrer les lipides compatibles avec au moins un repas cible
            tslots = [m for m in meals if m["type"] in ("midi","soir")]
            if not tslots:
                tslots = [m for m in meals if m["type"] != "coucher"]
            lip_food = None
            for lf_cand in lip_avail:
                # Vérifier que ce lipide est compatible avec au moins un repas
                ok_slot = False
                for m in tslots:
                    existing = [it["food"] for it in m["items"]]
                    if _filter_compatible(lf_cand, existing):
                        ok_slot = True
                        break
                if ok_slot:
                    lip_food = lf_cand
                    break
            if not lip_food:
                lip_food = lip_avail[0]  # fallback si tout est incompatible

            _, _, _, l100 = db[lip_food]
            if l100 > 0:
                mn_lip  = FOOD_MIN_PORTION.get(lip_food, 8)
                g_total = max(mn_lip, round(deficit_lip/(l100/100.0)))
                if tslots:
                    g_base = g_total // len(tslots)
                    g_rest = g_total - g_base*(len(tslots)-1)
                    for idx, m in enumerate(tslots):
                        g = g_rest if idx == len(tslots)-1 else g_base
                        if g < 3: continue
                        # Vérifier incompatibilité avant injection
                        existing = [it["food"] for it in m["items"]]
                        if not _filter_compatible(lip_food, existing):
                            continue
                        k,p,gc,l = _macros(lip_food, g)
                        already = [it for it in m["items"] if it["food"] == lip_food]
                        if already:
                            ng = min(FOOD_MAX_PORTION.get(lip_food, FOOD_MAX_DEFAULT), already[0]["g"] + g)
                            k2,p2,gc2,l2 = _macros(lip_food, ng)
                            already[0].update({"g":ng,"kcal":k2,"p":p2,"g_":gc2,"l":l2})
                        else:
                            m["items"].append({"food":lip_food,"g":g,
                                                "kcal":k,"p":p,"g_":gc,"l":l})

    # ── PASSE 5 : précision protéines ±1% ────────────────────────────────────
    # La fourchette scientifique pour la musculation naturelle est 1.6–2.2 g/kg.
    # On vise exactement prot_total ±1% : ni plus (reins), ni moins (catabolisme).
    # Itératif sur tous les items protéiques (hors coucher) jusqu'à convergence.
    got_prot = sum(i["p"] for m in meals for i in m["items"])
    prot_err_pct = (got_prot - prot_total) / prot_total * 100 if prot_total else 0

    if abs(prot_err_pct) > 1.0:
        delta_p = prot_total - got_prot  # positif = déficit, négatif = excès
        # Collecter tous les items protéiques hors coucher, triés par protéine (desc)
        prot5_items = sorted(
            [it for m in meals if m["type"] != "coucher"
             for it in m["items"] if db[it["food"]][1] > 5],
            key=lambda x: x["p"], reverse=True)
        for p5i in prot5_items:
            if abs(delta_p) < 1:
                break
            _, p100, _, _ = db[p5i["food"]]
            if p100 <= 0:
                continue
            add_g = round(delta_p / (p100 / 100.0))
            mn_p5 = FOOD_MIN_PORTION.get(p5i["food"], 20)
            new_g = max(mn_p5, min(FOOD_MAX_PORTION.get(p5i["food"], FOOD_MAX_DEFAULT),
                                    p5i["g"] + add_g))
            if new_g == p5i["g"]:
                continue
            old_p = p5i["p"]
            k, p, gc, l = _macros(p5i["food"], new_g)
            p5i.update({"g": new_g, "kcal": k, "p": p, "g_": gc, "l": l})
            delta_p -= (p - old_p)

    # ── PASSE 5b : injection protéique d'urgence ──────────────────────────────
    # Si après passe 5, les protéines sont encore > 8% en dessous de la cible,
    # on ajoute un scoop de whey/oeuf dans le repas le plus déficitaire.
    got_prot5 = sum(i["p"] for m in meals for i in m["items"])
    deficit_p5 = prot_total - got_prot5
    if deficit_p5 > prot_total * 0.08:
        # Trouver un repas hors coucher avec de la place calorique
        target_meal = None
        for m in meals:
            if m["type"] == "coucher":
                continue
            m_cal = sum(i["kcal"] for i in m["items"])
            target_cal = cal_total * m["slot"]["ratio"]
            if m_cal < target_cal * 1.15:  # pas déjà saturé
                if target_meal is None or m_cal < sum(i["kcal"] for i in target_meal["items"]):
                    target_meal = m
        if target_meal:
            # Chercher la meilleure source : whey > oeuf > protéine maigre
            EMERGENCY_PROT = [
                ("whey", ["EvoWhey HSN", "Whey protéine"]),
                ("oeuf", ["Oeuf entier", "Blanc d'oeuf"]),
                ("proteine_maigre", ["Blanc de poulet (cuit)", "Thon (en boîte, eau)",
                                      "Blanc de dinde (cuit)"]),
            ]
            existing_foods = {i["food"] for i in target_meal["items"]}
            for _, candidates in EMERGENCY_PROT:
                for c in candidates:
                    if c not in sel or c not in db:
                        continue
                    if c in existing_foods:
                        # Augmenter la portion existante
                        for it in target_meal["items"]:
                            if it["food"] == c:
                                _, cp100, _, _ = db[c]
                                if cp100 <= 0:
                                    break
                                add = round(deficit_p5 / (cp100 / 100.0))
                                mn = FOOD_MIN_PORTION.get(c, 20)
                                mx = FOOD_MAX_PORTION.get(c, FOOD_MAX_DEFAULT)
                                new_g = max(mn, min(mx, it["g"] + add))
                                if new_g > it["g"]:
                                    k2, p2, gc2, l2 = _macros(c, new_g)
                                    it.update({"g": new_g, "kcal": k2, "p": p2, "g_": gc2, "l": l2})
                                    deficit_p5 = 0
                                break
                        if deficit_p5 <= 0:
                            break
                        continue
                    if not _filter_compatible(c, list(existing_foods)):
                        continue
                    _, cp100, _, _ = db[c]
                    if cp100 <= 0:
                        continue
                    g_need = round(deficit_p5 / (cp100 / 100.0))
                    mn = FOOD_MIN_PORTION.get(c, 20)
                    mx = FOOD_MAX_PORTION.get(c, FOOD_MAX_DEFAULT)
                    g_add = max(mn, min(mx, g_need))
                    k2, p2, gc2, l2 = _macros(c, g_add)
                    target_meal["items"].append({
                        "food": c, "g": g_add,
                        "kcal": k2, "p": p2, "g_": gc2, "l": l2})
                    _used_today.add(c)
                    deficit_p5 = 0
                    break
                if deficit_p5 <= 0:
                    break

    # ── PASSE 6a : rééquilibrage glucides / lipides ────────────────────────────
    # Les protéines (oeufs, fromage, viande grasse) apportent des lipides "cachés".
    # Stratégie : trim les lipides excédentaires → libère des calories →
    #             réinjecter ces calories en glucides (1g lip = 9kcal → 2.25g gluc).
    gluc_cats = ("glucide_midi","glucide_soir","glucide_matin",
                 "glucide_collation","pain_seulement")
    lip_cats  = ("lipide_sain","lipide_matin","lipide_collation",
                 "lipide_coucher","huile_cuisson","beurre_pain")
    LIP_TRIM_PRIORITY = [
        ("huile_cuisson", 0.5),   ("beurre_pain",   0.6),
        ("lipide_sain",   0.7),   ("lipide_matin",  0.7),
        ("lipide_collation", 0.7),("lipide_coucher", 0.7),
        ("fromage_dur",   0.8),
    ]

    for _rebal in range(6):
        cur_g = sum(i["g_"] for m in meals for i in m["items"])
        cur_l = sum(i["l"]  for m in meals for i in m["items"])
        g_err = (cur_g - gluc_total) / gluc_total * 100 if gluc_total else 0
        l_err = (cur_l - lip_total)  / lip_total  * 100 if lip_total  else 0
        if abs(g_err) <= 5 and abs(l_err) <= 5:
            break

        freed_kcal = 0.0
        # Phase A : trim items des catégories lipides pures (PAS les protéines)
        if l_err > 5:
            excess_lip_g = cur_l - lip_total
            for cat_name, _ in LIP_TRIM_PRIORITY:
                if excess_lip_g <= 1: break
                for m in meals:
                    if m["type"] == "coucher": continue
                    for it in m["items"]:
                        if it["food"] not in FOOD_CATS.get(cat_name, []): continue
                        _, _, _, l100 = db[it["food"]]
                        if l100 <= 0: continue
                        mn = FOOD_MIN_PORTION.get(it["food"], 5)
                        can_trim_g = it["g"] - mn
                        if can_trim_g <= 1: continue
                        needed_g = round(excess_lip_g / (l100 / 100.0))
                        trim_g = min(can_trim_g, needed_g)
                        old_l, old_kcal = it["l"], it["kcal"]
                        new_g = max(mn, it["g"] - trim_g)
                        k, p, gc, l = _macros(it["food"], new_g)
                        it.update({"g": new_g, "kcal": k, "p": p, "g_": gc, "l": l})
                        excess_lip_g -= (old_l - l)
                        freed_kcal += (old_kcal - k)

        # Phase B : réinjecter en glucides
        cur_g2 = sum(i["g_"] for m in meals for i in m["items"])
        g_deficit = gluc_total - cur_g2
        if g_deficit > 2:
            cur_cal = sum(i["kcal"] for m in meals for i in m["items"])
            cal_room = cal_total - cur_cal + freed_kcal
            max_gluc_add_g = cal_room / 4 if cal_room > 0 else 0
            gluc_to_add = min(g_deficit, max_gluc_add_g)
            if gluc_to_add > 2:
                _g_items = sorted(
                    [it for m in meals if m["type"] != "coucher"
                     for it in m["items"]
                     if any(it["food"] in FOOD_CATS.get(c, []) for c in gluc_cats)],
                    key=lambda x: x["g_"], reverse=True)
                if _g_items:
                    share_g = gluc_to_add / len(_g_items)
                    for gi in _g_items:
                        if share_g < 1: break
                        _, _, g100, _ = db[gi["food"]]
                        if g100 <= 0: continue
                        cap = FOOD_MAX_PORTION.get(gi["food"], FOOD_MAX_DEFAULT)
                        add = min(cap - gi["g"], round(share_g / (g100 / 100.0)))
                        if add <= 0: continue
                        new_g = min(cap, gi["g"] + add)
                        k, p, gc, l = _macros(gi["food"], new_g)
                        gi.update({"g": new_g, "kcal": k, "p": p, "g_": gc, "l": l})

    # ── PASSE 6b : calories à 100% — distribution multi-repas ─────────────────
    # Répartit l'écart calorique sur TOUS les repas glucidiques disponibles.
    # Converge en 2-3 itérations même pour des déficits de 500 kcal.

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
                cap = FOOD_MAX_PORTION.get(it["food"], FOOD_MAX_DEFAULT)
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
                cap = FOOD_MAX_PORTION.get(it["food"], FOOD_MAX_DEFAULT)
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
                cap = FOOD_MAX_PORTION.get(it["food"], FOOD_MAX_DEFAULT)
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


def compute_diversity_score(days: list) -> dict:
    """
    Analyse la diversité d'un plan multiday.
    Retourne {score, unique, total, streak_alerts, rating}.
    - score : ratio aliments uniques / slots totaux (0-100)
    - streak_alerts : protéine principale identique 3+ jours d'affilée
    - rating : "excellent" | "bon" | "moyen" | "faible"
    """
    all_foods = []          # liste de tous les aliments (avec doublons)
    unique_foods = set()
    main_prots = []         # protéine principale par jour (la + grosse en prot)

    for d in days:
        day_foods = []
        best_prot_food, best_prot_val = "", 0
        for meal in d.get("plan", []):
            for item in meal.get("items", []):
                food = item.get("food", "")
                if not food:
                    continue
                day_foods.append(food)
                unique_foods.add(food)
                if item.get("p", 0) > best_prot_val:
                    best_prot_val = item["p"]
                    best_prot_food = food
        all_foods.extend(day_foods)
        main_prots.append(best_prot_food)

    total = len(all_foods)
    unique = len(unique_foods)
    score = (unique / total * 100) if total > 0 else 0

    # Détecter les streaks de protéine principale ≥ 3 jours
    streak_alerts = []
    if len(main_prots) >= 3:
        cur_food, cur_start, cur_len = main_prots[0], 0, 1
        for i in range(1, len(main_prots)):
            if main_prots[i] == cur_food:
                cur_len += 1
            else:
                if cur_len >= 3:
                    streak_alerts.append((cur_food, cur_start + 1, cur_start + cur_len, cur_len))
                cur_food, cur_start, cur_len = main_prots[i], i, 1
        if cur_len >= 3:
            streak_alerts.append((cur_food, cur_start + 1, cur_start + cur_len, cur_len))

    # Rating global
    penalty = len(streak_alerts) * 5
    adj_score = max(0, score - penalty)
    if adj_score >= 60:
        rating = "excellent"
    elif adj_score >= 45:
        rating = "bon"
    elif adj_score >= 30:
        rating = "moyen"
    else:
        rating = "faible"

    return {
        "score": round(adj_score, 1),
        "unique": unique,
        "total": total,
        "streak_alerts": streak_alerts,
        "rating": rating,
    }


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
