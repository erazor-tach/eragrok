# data/prices_module.py — ERAGROK · Estimateur prix liste de courses
# ─────────────────────────────────────────────────────────────────────────────
# Sources :
#   1. Prix par défaut hardcodés (marché France 2025, grandes surfaces)
#   2. Open Food Facts API (https://world.openfoodfacts.org) — mise à jour hebdo
#   3. Prix manuels saisis par l'utilisateur (priorité max)
#
# Mise à jour auto :
#   • Si table vide → chargement des défauts + tentative OFF
#   • Si dernière MAJ > 7 jours → tentative OFF en thread background
# ─────────────────────────────────────────────────────────────────────────────

import datetime
import threading
import logging

log = logging.getLogger("eragrok.prices")

# ─────────────────────────────────────────────────────────────────────────────
# BASE PRIX PAR DÉFAUT  (€/kg sauf mention)
# Sources : relevés Leclerc / Carrefour / Intermarché France 2025
# ─────────────────────────────────────────────────────────────────────────────
DEFAULT_PRICES = {
    # food                              prix_kg  unite  barcode_OFF (pour MAJ auto)
    # ── Protéines animales ────────────────────────────────────────────────────
    "Blanc de poulet (cuit)":          (11.50, "kg",  ""),   # ~8.80€/kg cru × 1.30
    "Blanc de dinde (cuit)":           (10.20, "kg",  ""),
    "Dinde (blanc cuit)":              (10.20, "kg",  ""),
    "Boeuf haché 5% MG":               (13.50, "kg",  ""),
    "Boeuf haché 15% MG":              (10.90, "kg",  ""),
    "Boeuf haché 20% MG":              ( 9.50, "kg",  ""),
    "Steak (rumsteck, cuit)":          (18.00, "kg",  ""),
    "Escalope de veau (cuite)":        (19.50, "kg",  ""),
    "Jambon blanc (dégraissé)":        (14.20, "kg",  ""),
    "Saumon (cuit)":                   (22.00, "kg",  ""),
    "Cabillaud (cuit)":                (17.80, "kg",  ""),
    "Merlan (cuit)":                   (10.50, "kg",  ""),
    "Tilapia (cuit)":                  (10.00, "kg",  ""),
    "Filet de sole (cuit)":            (16.50, "kg",  ""),
    "Maquereau (cuit)":                ( 8.50, "kg",  ""),
    "Crevettes (cuites)":              (18.00, "kg",  ""),
    "Thon (en boîte, eau)":            (14.00, "kg",  "3017804040025"),
    "Sardines (en boîte, huile)":      ( 9.00, "kg",  ""),
    "Tofu ferme":                      ( 8.50, "kg",  ""),
    # ── Œufs ──────────────────────────────────────────────────────────────────
    "Oeuf entier":                     ( 0.30, "unite", ""),  # ~0.30€/oeuf
    "Blanc d'oeuf":                    ( 0.30, "unite", ""),
    "Œuf dur entier":                  ( 0.30, "unite", ""),
    # ── Laitiers ──────────────────────────────────────────────────────────────
    "Skyr 0%":                         ( 5.80, "kg",  ""),
    "Fromage blanc 0%":                ( 3.20, "kg",  ""),
    "Fromage blanc 20%":               ( 3.50, "kg",  ""),
    "Yaourt grec 0%":                  ( 4.50, "kg",  ""),
    "Yaourt grec entier (5%)":         ( 5.20, "kg",  ""),
    "Yaourt 0% nature":                ( 2.80, "kg",  ""),
    "Cottage cheese":                  ( 6.50, "kg",  ""),
    "Ricotta":                         ( 7.00, "kg",  ""),
    "Lait écrémé":                     ( 1.10, "L",   ""),
    "Lait entier":                     ( 1.30, "L",   ""),
    "Lait de soja":                    ( 2.20, "L",   ""),
    "Emmental":                        (10.50, "kg",  ""),
    "Comté":                           (16.00, "kg",  ""),
    "Gruyère":                         (11.00, "kg",  ""),
    # ── Céréales / Féculents (prix sec) ───────────────────────────────────────
    "Riz cuit":                        ( 1.80, "kg",  ""),   # riz sec ~1.80€/kg
    "Riz brun (cuit)":                 ( 2.20, "kg",  ""),
    "Pâtes blanches (cuites)":         ( 1.60, "kg",  ""),   # pâtes sèches ~1.60€/kg
    "Pâtes complètes (cuites)":        ( 2.00, "kg",  ""),
    "Pâtes cuites":                    ( 1.60, "kg",  ""),
    "Quinoa (cuit)":                   ( 6.50, "kg",  ""),
    "Boulgour (cuit)":                 ( 3.50, "kg",  ""),
    "Semoule (cuite)":                 ( 2.20, "kg",  ""),
    "Flocons d'avoine":                ( 2.50, "kg",  "3017804061142"),
    "Farine d'avoine HSN":             ( 5.90, "kg",  ""),
    "Crème de riz HSN":                ( 5.50, "kg",  ""),
    "Müesli nature (sans sucre)":      ( 4.80, "kg",  ""),
    "Galettes de riz nature":          ( 5.00, "kg",  ""),
    "Pain complet":                    ( 4.20, "kg",  ""),
    "Pain blanc":                      ( 3.80, "kg",  ""),
    "Patate douce (cuite)":            ( 3.50, "kg",  ""),
    "Patate douce violette (cuite)":   ( 5.50, "kg",  ""),
    "Pomme de terre (cuite)":          ( 1.80, "kg",  ""),
    # ── Légumes ───────────────────────────────────────────────────────────────
    "Brocoli (cuit)":                  ( 3.50, "kg",  ""),
    "Épinards (crus)":                 ( 4.00, "kg",  ""),
    "Courgette (cuite)":               ( 2.20, "kg",  ""),
    "Haricots verts (cuits)":          ( 3.80, "kg",  ""),
    "Asperges (cuites)":               ( 8.50, "kg",  ""),
    "Poivron (cru)":                   ( 3.50, "kg",  ""),
    "Tomate (crue)":                   ( 2.80, "kg",  ""),
    "Salade verte":                    ( 2.00, "kg",  ""),
    "Champignons (cuits)":             ( 4.50, "kg",  ""),
    "Chou-fleur (cuit)":               ( 2.50, "kg",  ""),
    "Concombre (cru)":                 ( 1.80, "kg",  ""),
    # ── Légumineuses ──────────────────────────────────────────────────────────
    "Lentilles (cuites)":              ( 2.50, "kg",  ""),
    "Pois chiches (cuits)":            ( 2.80, "kg",  ""),
    "Haricots rouges (cuits)":         ( 2.20, "kg",  ""),
    "Haricots blancs (cuits)":         ( 2.20, "kg",  ""),
    "Edamame (cuit)":                  ( 5.50, "kg",  ""),
    # ── Fruits ────────────────────────────────────────────────────────────────
    "Banane":                          ( 2.20, "kg",  ""),
    "Pomme":                           ( 2.80, "kg",  ""),
    "Orange":                          ( 2.50, "kg",  ""),
    "Kiwi":                            ( 4.50, "kg",  ""),
    "Fraises":                         ( 6.50, "kg",  ""),
    "Myrtilles":                       (12.00, "kg",  ""),
    "Mangue":                          ( 5.00, "kg",  ""),
    "Avocat":                          ( 5.00, "kg",  ""),
    "Ananas":                          ( 3.00, "kg",  ""),
    "Poire":                           ( 3.20, "kg",  ""),
    "Pastèque":                        ( 1.20, "kg",  ""),
    "Raisins":                         ( 4.50, "kg",  ""),
    # ── Matières grasses ──────────────────────────────────────────────────────
    "Huile d'olive":                   ( 8.50, "L",   ""),
    "Huile de coco":                   (10.00, "L",   ""),
    "Beurre doux":                     ( 8.50, "kg",  ""),
    "Beurre de cacahuète":             ( 8.00, "kg",  ""),
    "Beurre d'amande":                 (14.00, "kg",  ""),
    "Amandes":                         (12.00, "kg",  ""),
    "Noix":                            (14.00, "kg",  ""),
    "Noix de cajou":                   (16.00, "kg",  ""),
    "Cacahuètes":                      ( 6.00, "kg",  ""),
    "Chocolat noir 70%":               (10.00, "kg",  ""),
    # ── Sucrants ──────────────────────────────────────────────────────────────
    "Miel":                            ( 9.50, "kg",  ""),
    "Confiture (moyenne)":             ( 5.00, "kg",  ""),
    "Sirop d'agave":                   (12.00, "kg",  ""),
    # ── Suppléments ───────────────────────────────────────────────────────────
    "EvoWhey HSN":                     (24.00, "kg",  ""),  # ~24€/kg (1kg sachet)
    "Whey protéine":                   (25.00, "kg",  ""),
    "Caséine":                         (28.00, "kg",  ""),
}

# Barcodes Open Food Facts pour les produits recherchables
OFF_BARCODES = {food: bc for food, (_, _, bc) in DEFAULT_PRICES.items() if len(DEFAULT_PRICES[food]) > 2 and DEFAULT_PRICES[food][2]}

# Termes de recherche OFF pour les produits sans barcode fixe
OFF_SEARCH_TERMS = {
    "Skyr 0%":               "skyr nature 0%",
    "Fromage blanc 0%":      "fromage blanc 0% matière grasse",
    "Yaourt grec 0%":        "yaourt grec 0%",
    "Flocons d'avoine":      "flocons d'avoine",
    "Beurre de cacahuète":   "beurre de cacahuète",
    "Amandes":               "amandes entières",
    "Noix":                  "cerneaux noix",
    "Lait écrémé":           "lait écrémé UHT",
    "Lait entier":           "lait entier UHT",
    "Huile d'olive":         "huile d'olive vierge extra",
    "Pain complet":          "pain complet de mie",
    "Riz cuit":              "riz long grain blanc",
    "Pâtes blanches (cuites)": "pâtes spaghetti",
    "Patate douce (cuite)":  "patate douce",
    "Saumon (cuit)":         "filet saumon atlantique",
    "Blanc de poulet (cuit)":"filet poulet",
    "Thon (en boîte, eau)":  "thon naturel conserve",
}

UPDATE_INTERVAL_DAYS = 7


def _should_update(app) -> bool:
    """True si table vide ou dernière MAJ > 7 jours."""
    try:
        from data import db as _db
        if _db.prices_count(app) == 0:
            return True
        last = _db.prices_last_update(app)
        if not last:
            return True
        last_dt = datetime.date.fromisoformat(last)
        return (datetime.date.today() - last_dt).days >= UPDATE_INTERVAL_DAYS
    except Exception:
        return False


def load_defaults(app) -> None:
    """Charge les prix par défaut en DB (ne remplace pas les prix manuels)."""
    try:
        from data import db as _db
        today = datetime.date.today().isoformat()
        existing = _db.prices_get_all(app)
        for food, vals in DEFAULT_PRICES.items():
            prix_kg, unite = vals[0], vals[1]
            ex = existing.get(food)
            # Ne pas écraser un prix manuel
            if ex and ex.get("source") == "manual":
                continue
            # Ne pas écraser un prix OFF récent
            if ex and ex.get("source") == "openfoodfacts":
                continue
            _db.prices_upsert(app, food, prix_kg, unite, "default", today)
        log.info("Prix par défaut chargés (%d aliments)", len(DEFAULT_PRICES))
    except Exception as e:
        log.warning("load_defaults failed: %s", e)


def _fetch_off_price(search_term: str) -> float | None:
    """
    Interroge Open Food Facts pour trouver un prix moyen (€/kg).
    Retourne None si pas de données ou erreur réseau.
    """
    try:
        import urllib.request, urllib.parse, json
        # Recherche par terme
        q = urllib.parse.quote(search_term)
        url = (f"https://world.openfoodfacts.org/cgi/search.pl"
               f"?search_terms={q}&search_simple=1&action=process"
               f"&json=1&page_size=5&fields=product_name,price_data,ecoscore_data,countries_tags")
        req = urllib.request.Request(url, headers={"User-Agent": "ERAGROK/1.0 (+https://eragrok.app)"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())

        products = data.get("products", [])
        prices = []
        for p in products:
            # Filtrer France uniquement
            countries = p.get("countries_tags", [])
            if countries and "en:france" not in countries:
                continue
            pd = p.get("price_data") or {}
            avg = pd.get("price_per_kg") or pd.get("prices_count")
            if isinstance(avg, (int, float)) and avg > 0:
                prices.append(float(avg))

        if prices:
            # Médiane pour éviter les outliers
            prices.sort()
            mid = len(prices) // 2
            return prices[mid]
        return None
    except Exception as e:
        log.debug("OFF fetch failed for '%s': %s", search_term, e)
        return None


def update_prices_from_off(app, on_progress=None, on_done=None) -> None:
    """
    Mise à jour des prix via Open Food Facts en thread background.
    on_progress(food, current, total) — callback optionnel
    on_done(n_updated, n_failed)     — callback optionnel
    """
    def _worker():
        from data import db as _db
        today     = datetime.date.today().isoformat()
        n_updated = 0
        n_failed  = 0
        foods     = list(OFF_SEARCH_TERMS.items())
        total     = len(foods)

        for i, (food, term) in enumerate(foods):
            if on_progress:
                try: on_progress(food, i+1, total)
                except Exception: pass
            price = _fetch_off_price(term)
            if price and 0.5 < price < 200:  # sanity check
                _db.prices_upsert(app, food, round(price, 2),
                                  DEFAULT_PRICES.get(food, (0,"kg"))[1],
                                  "openfoodfacts", today)
                n_updated += 1
                log.info("OFF prix %s : %.2f €/kg", food, price)
            else:
                n_failed += 1

        log.info("MAJ OFF terminée : %d mis à jour, %d inchangés", n_updated, n_failed)
        if on_done:
            try: on_done(n_updated, n_failed)
            except Exception: pass

    t = threading.Thread(target=_worker, daemon=True, name="prices_off_update")
    t.start()


def ensure_prices_loaded(app, force_off=False) -> None:
    """
    Point d'entrée principal — appelé au démarrage de l'app.
    1. Si table vide → load_defaults synchrone
    2. Si MAJ > 7j ou force_off → update OFF en background
    """
    try:
        from data import db as _db
        if _db.prices_count(app) == 0:
            log.info("Table food_prices vide — chargement des prix par défaut")
            load_defaults(app)

        if force_off or _should_update(app):
            log.info("MAJ prix Open Food Facts (background)...")
            update_prices_from_off(app)
    except Exception as e:
        log.warning("ensure_prices_loaded: %s", e)


def get_prices(app) -> dict:
    """
    Retourne {food: {prix_kg, unite, source}} depuis la DB.
    Fallback sur DEFAULT_PRICES si DB vide ou erreur.
    """
    try:
        from data import db as _db
        db_prices = _db.prices_get_all(app)
        if db_prices:
            return db_prices
    except Exception:
        pass
    # Fallback
    return {food: {"prix_kg": vals[0], "unite": vals[1], "source": "default"}
            for food, vals in DEFAULT_PRICES.items()}


def compute_shopping_cost(shopping: dict, app) -> dict:
    """
    Calcule l'estimation du coût à partir de la liste de courses.
    shopping : dict retourné par compute_shopping_list()
    Retourne :
      {
        "total":    float,          # coût total estimé €
        "by_cat":   {cat: float},   # coût par catégorie
        "by_item":  {food: float},  # coût par aliment
        "currency": "€",
        "nb_prices_found": int,     # combien d'aliments ont un prix
        "nb_total": int,
      }
    """
    prices   = get_prices(app)
    by_cat   = {}
    by_item  = {}
    n_found  = 0
    n_total  = 0

    for cat, items in shopping.items():
        cat_total = 0.0
        for food, g_raw, label, note in items:
            if food.startswith("🥚"):
                # Ligne agrégée œufs — sauter (les lignes individuelles sont absentes)
                # Estimer via quantité en g_raw (total grammes)
                price_info = prices.get("Oeuf entier") or {"prix_kg": 5.0, "unite": "unite"}
                n_total += 1
                # g_raw ici = nb_oeufs * 60g — on convertit en nb oeufs
                n_oeufs = round(g_raw / 60)
                cout = n_oeufs * (price_info.get("prix_kg", 0.30) if price_info.get("unite") == "unite"
                                  else price_info.get("prix_kg", 5.0) * (g_raw / 1000))
                by_item[food]  = round(cout, 2)
                cat_total     += cout
                n_found       += 1
                continue

            price_info = prices.get(food)
            n_total += 1
            if not price_info:
                by_item[food] = 0.0
                continue

            prix_kg = price_info.get("prix_kg", 0)
            unite   = price_info.get("unite", "kg")
            if not prix_kg:
                by_item[food] = 0.0
                continue

            n_found += 1
            if unite == "unite":
                # g_raw = nb unités × poids moyen
                n_units = round(g_raw / 60) if food in ("Oeuf entier","Œuf dur entier") else round(g_raw / 35)
                cout = max(1, n_units) * prix_kg
            elif unite == "L":
                cout = (g_raw / 1000) * prix_kg
            else:  # kg
                cout = (g_raw / 1000) * prix_kg

            by_item[food]  = round(cout, 2)
            cat_total     += cout

        by_cat[cat] = round(cat_total, 2)

    return {
        "total":            round(sum(by_cat.values()), 2),
        "by_cat":           by_cat,
        "by_item":          by_item,
        "currency":         "€",
        "nb_prices_found":  n_found,
        "nb_total":         n_total,
    }
