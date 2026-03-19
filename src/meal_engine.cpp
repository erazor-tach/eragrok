// meal_engine.cpp — Moteur génération plans alimentaires THRESHOLD
// ─────────────────────────────────────────────────────────────────────────────
// Port complet de Python _generate_meal_plan() — algorithme 7 passes
// ─────────────────────────────────────────────────────────────────────────────
#include "meal_engine.h"
#include "food_data.h"
#include "utils.h"
#include <algorithm>
#include <cmath>
#include <numeric>

namespace threshold {

// ═════════════════════════════════════════════════════════════════════════════
//  FOOD CATALOG (inchangé — chargement des ~100 aliments)
// ═════════════════════════════════════════════════════════════════════════════
void FoodCatalog::add(const std::string& nom, const std::string& cat,
                      float kcal, float prot, float gluc, float lip, float fib,
                      float pmin, float pmax, float cook) {
    FoodData d;
    d.kcal_100g = kcal; d.prot_100g = prot; d.gluc_100g = gluc;
    d.lip_100g = lip; d.fibres_100g = fib; d.categorie = cat;
    d.portion_min = pmin; d.portion_max = pmax; d.cooked_to_raw = cook;
    catalog_[nom] = d;
    categories_[cat].push_back(nom);
}

void FoodCatalog::load_default_catalog() {
    // Protéines animales
    add("Blanc de poulet (cuit)",     "Protéines animales", 165,31.0,0.0,3.6,0, 80,250,1.0);
    add("Blanc de dinde (cuit)",      "Protéines animales", 135,29.0,0.0,2.5,0, 80,250,1.0);
    add("Boeuf haché 5% MG",         "Protéines animales", 152,26.0,0.0,5.0,0, 80,250,1.0);
    add("Boeuf haché 15% MG",        "Protéines animales", 215,22.0,0.0,14.0,0, 80,220,1.0);
    add("Boeuf haché 20% MG",        "Protéines animales", 254,20.0,0.0,19.0,0, 80,200,1.0);
    add("Saumon (cuit)",             "Protéines animales", 208,20.0,0.0,13.0,0, 100,220,1.0);
    add("Thon (en boîte, eau)",      "Protéines animales", 116,26.0,0.0,1.0,0, 60,200,1.0);
    add("Cabillaud (cuit)",          "Protéines animales",  82,18.0,0.0,0.7,0, 100,250,1.0);
    add("Crevettes (cuites)",        "Protéines animales",  99,21.0,0.3,1.1,0, 80,200,1.0);
    add("Steak (rumsteck, cuit)",    "Protéines animales", 185,29.0,0.0,7.0,0, 120,250,1.0);
    add("Maquereau (cuit)",          "Protéines animales", 230,19.0,0.0,16.0,0, 80,200,1.0);
    add("Sardines (en boîte, huile)","Protéines animales", 208,24.6,0.0,11.5,0, 75,150,1.0);
    add("Jambon blanc (dégraissé)",  "Protéines animales",  97,17.0,1.0,2.5,0, 40,150,1.0);
    // Protéines végétales
    add("Tofu ferme",                "Protéines végétales",  76,8.1,1.9,4.2,0.3, 80,250,1.0);
    add("Edamame (cuit)",            "Protéines végétales", 121,11.9,8.9,5.2,5.2, 60,200,1.0);
    add("Lentilles (cuites)",        "Protéines végétales", 116,9.0,20.1,0.4,7.9, 80,250,2.0);
    add("Pois chiches (cuits)",      "Protéines végétales", 164,8.9,27.4,2.6,7.6, 80,250,2.0);
    add("Haricots rouges (cuits)",   "Protéines végétales", 127,8.7,22.8,0.5,6.4, 80,250,2.0);
    add("Haricots blancs (cuits)",   "Protéines végétales", 139,9.7,25.4,0.5,6.3, 80,250,2.0);
    // Œufs & laitiers
    add("Oeuf entier",               "Œufs & laitiers", 155,13.0,1.1,11.0,0, 55,240,1.0);
    add("Blanc d'oeuf",              "Œufs & laitiers",  52,11.0,0.7,0.2,0, 30,280,1.0);
    add("Fromage blanc 0%",          "Œufs & laitiers",  45,8.0,4.0,0.1,0, 100,200,1.0);
    add("Yaourt grec 0%",            "Œufs & laitiers",  59,10.0,3.6,0.4,0, 125,200,1.0);
    add("Yaourt grec entier (5%)",   "Œufs & laitiers", 100,9.0,3.6,5.0,0, 125,200,1.0);
    add("Skyr 0%",                   "Œufs & laitiers",  57,10.0,4.0,0.1,0, 125,200,1.0);
    add("Cottage cheese",            "Œufs & laitiers",  98,11.1,3.4,4.3,0, 100,200,1.0);
    add("Lait écrémé",               "Œufs & laitiers",  35,3.5,5.0,0.1,0, 100,300,1.0);
    add("Lait entier",               "Œufs & laitiers",  61,3.2,4.7,3.3,0, 100,300,1.0);
    add("Ricotta",                   "Œufs & laitiers", 174,7.3,3.0,13.0,0, 80,150,1.0);
    add("Emmental",                  "Œufs & laitiers", 379,28.5,0.4,29.0,0, 20,50,1.0);
    add("Comté",                     "Œufs & laitiers", 413,27.0,0.0,34.0,0, 25,50,1.0);
    // Suppléments
    add("Whey protéine",             "Suppléments", 380,80.0,8.0,5.0,0, 25,50,1.0);
    add("EvoWhey HSN",               "Suppléments", 380,76.0,7.0,6.0,0, 25,50,1.0);
    add("Caséine",                   "Suppléments", 370,78.0,9.0,3.0,0, 25,50,1.0);
    // Glucides
    add("Riz cuit",                  "Glucides", 130,2.7,28.0,0.3,0.4, 80,280,2.5);
    add("Riz brun (cuit)",           "Glucides", 123,2.7,25.6,1.0,1.8, 80,280,2.5);
    add("Pâtes cuites",              "Glucides", 131,5.0,26.0,1.1,1.8, 80,250,2.5);
    add("Pâtes complètes (cuites)",  "Glucides", 124,5.3,23.2,1.0,3.5, 80,250,2.5);
    add("Flocons d'avoine",          "Glucides", 367,13.5,58.7,7.0,10.0, 30,100,1.0);
    add("Pain complet",              "Glucides", 247,9.0,45.0,3.5,6.5, 30,100,1.0);
    add("Pain blanc",                "Glucides", 265,8.0,52.0,1.6,2.7, 30,100,1.0);
    add("Patate douce (cuite)",      "Glucides",  90,2.0,21.0,0.1,3.3, 80,250,1.0);
    add("Pomme de terre (cuite)",    "Glucides",  87,1.9,20.1,0.1,1.8, 80,300,1.0);
    add("Quinoa (cuit)",             "Glucides", 120,4.4,22.0,1.9,2.8, 80,250,2.5);
    add("Boulgour (cuit)",           "Glucides",  83,3.1,18.6,0.2,4.5, 80,250,2.5);
    add("Semoule (cuite)",           "Glucides", 120,3.8,23.2,0.2,1.4, 80,250,2.5);
    add("Galettes de riz nature",    "Glucides", 387,7.3,81.5,2.8,2.4, 10,60,1.0);
    add("Banane",                    "Glucides",  89,1.1,23.0,0.3,2.6, 100,200,1.0);
    // Fruits
    add("Pomme","Fruits",52,0.3,14.0,0.2,2.4,100,200,1.0);
    add("Orange","Fruits",47,0.9,11.8,0.1,2.4,120,200,1.0);
    add("Kiwi","Fruits",61,1.1,14.7,0.5,3.0,60,150,1.0);
    add("Fraises","Fruits",32,0.7,7.7,0.3,2.0,80,200,1.0);
    add("Myrtilles","Fruits",57,0.7,14.5,0.3,2.4,60,150,1.0);
    add("Mangue","Fruits",60,0.8,15.0,0.4,1.6,150,200,1.0);
    add("Ananas","Fruits",50,0.5,13.1,0.1,1.4,100,200,1.0);
    add("Pastèque","Fruits",30,0.6,7.6,0.2,0.4,150,300,1.0);
    // Légumes
    add("Brocoli (cuit)","Légumes",35,2.4,7.0,0.4,3.3,80,250,1.0);
    add("Épinards (crus)","Légumes",23,2.9,3.6,0.4,2.2,30,150,1.0);
    add("Courgette (cuite)","Légumes",17,1.2,3.6,0.1,1.0,80,250,1.0);
    add("Haricots verts (cuits)","Légumes",35,1.9,7.9,0.1,3.4,70,250,1.0);
    add("Asperges (cuites)","Légumes",20,2.4,3.7,0.1,2.1,60,200,1.0);
    add("Poivron (cru)","Légumes",31,1.0,6.0,0.3,2.1,80,200,1.0);
    add("Tomate (crue)","Légumes",18,0.9,3.9,0.2,1.2,80,250,1.0);
    add("Salade verte","Légumes",15,1.4,2.4,0.2,1.3,60,150,1.0);
    add("Champignons (cuits)","Légumes",28,2.2,5.3,0.1,2.0,60,200,1.0);
    add("Chou-fleur (cuit)","Légumes",23,1.9,4.1,0.3,2.3,80,250,1.0);
    add("Concombre (cru)","Légumes",15,0.7,3.1,0.1,0.5,100,250,1.0);
    // Lipides
    add("Huile d'olive","Lipides",884,0.0,0.0,100.0,0,8,25,1.0);
    add("Avocat","Lipides",160,2.0,9.0,15.0,6.7,80,150,1.0);
    add("Amandes","Lipides",579,21.0,22.0,49.0,12.5,15,40,1.0);
    add("Noix","Lipides",654,15.2,13.7,65.0,6.7,15,40,1.0);
    add("Noix de cajou","Lipides",553,18.2,30.2,43.9,3.3,15,40,1.0);
    add("Beurre de cacahuète","Lipides",588,25.0,20.0,50.0,6.0,15,40,1.0);
    add("Beurre d'amande","Lipides",614,21.1,19.0,56.0,7.0,15,35,1.0);
    add("Graines de chia","Lipides",490,17.0,42.0,31.0,34.4,10,30,1.0);
    add("Graines de lin","Lipides",534,18.3,28.9,42.2,27.3,10,30,1.0);
    add("Beurre doux","Lipides",717,0.6,0.5,81.0,0,10,25,1.0);
    add("Chocolat noir 70%","Lipides",598,7.8,45.9,42.6,10.9,15,40,1.0);
    // Divers
    add("Miel","Divers",304,0.3,82.0,0.0,0.2,10,25,1.0);
    add("Confiture (moyenne)","Divers",250,0.5,65.0,0.1,1.0,15,30,1.0);
    add("Cacao pur en poudre","Divers",228,20.0,10.0,13.7,33.2,8,15,1.0);
}

const FoodData* FoodCatalog::get(const std::string& nom) const {
    auto it = catalog_.find(nom);
    return (it != catalog_.end()) ? &it->second : nullptr;
}
std::vector<std::string> FoodCatalog::get_category(const std::string& cat) const {
    auto it = categories_.find(cat);
    return (it != categories_.end()) ? it->second : std::vector<std::string>{};
}
std::vector<std::string> FoodCatalog::get_category_names() const {
    std::vector<std::string> r;
    for (auto& p : categories_) r.push_back(p.first);
    return r;
}
std::vector<std::string> FoodCatalog::get_all_names() const {
    std::vector<std::string> r;
    for (auto& p : catalog_) r.push_back(p.first);
    return r;
}
bool FoodCatalog::exists(const std::string& nom) const {
    return catalog_.find(nom) != catalog_.end();
}
void FoodCatalog::add_custom_food(const std::string& nom, const FoodData& data) {
    catalog_[nom] = data;
    categories_[data.categorie].push_back(nom);
}

// ═════════════════════════════════════════════════════════════════════════════
//  MEAL GENERATOR — helpers internes
// ═════════════════════════════════════════════════════════════════════════════
MealGenerator::MealGenerator(const FoodCatalog& catalog)
    : catalog_(catalog) {
    std::random_device rd;
    rng_.seed(rd());
}

// Helper : calcul macros pour une portion
static void calc_macros(const FoodData& fd, float grams,
                        float& kcal, float& prot, float& gluc, float& lip) {
    float r = grams / 100.0f;
    kcal = fd.kcal_100g * r; prot = fd.prot_100g * r;
    gluc = fd.gluc_100g * r; lip  = fd.lip_100g  * r;
}

// Helper : grammes pour atteindre target en macro_idx (0=kcal,1=prot,2=gluc,3=lip)
// Retourne -1 si cible trop basse pour justifier le minimum (signal skip)
static float g_for(const FoodData& fd, const std::string& food, float target, int macro_idx) {
    float val100 = 0;
    switch (macro_idx) {
        case 0: val100 = fd.kcal_100g; break;
        case 1: val100 = fd.prot_100g; break;
        case 2: val100 = fd.gluc_100g; break;
        case 3: val100 = fd.lip_100g;  break;
    }
    if (val100 <= 0) return 50;
    float raw = std::max(10.0f, std::round(target / (val100 / 100.0f)));
    auto it_mx = FOOD_MAX_PORTION.find(food);
    float cap = (it_mx != FOOD_MAX_PORTION.end()) ? it_mx->second : FOOD_MAX_DEFAULT;
    auto it_mn = FOOD_MIN_PORTION.find(food);
    float mn = (it_mn != FOOD_MIN_PORTION.end()) ? it_mn->second : 10.0f;
    if (raw < mn * FOOD_MIN_SKIP_RATIO) return -1;  // signal skip
    return std::max(mn, std::min(cap, raw));
}

// Structure interne pour un item de repas pendant la génération
struct GenItem {
    std::string food;
    float g, kcal, prot, gluc, lip;
};

// Catégories où la répétition journalière est acceptable
static const std::set<std::string> REPEAT_OK_CATS = {
    "legume","lipide_sain","beurre_pain","sucrant_matin","fromage_dur",
    "huile_cuisson","supplement_lent","laitier_lent","lipide_coucher"
};

// ═════════════════════════════════════════════════════════════════════════════
//  PASSE 1 : Génération templates + PASSE 1.5 : Boost calorique
// ═════════════════════════════════════════════════════════════════════════════
PlanJournalier MealGenerator::generate_day(int n_repas,
                                           const std::vector<std::string>& available,
                                           const Macros& targets,
                                           int day_offset) {
    PlanJournalier plan;
    plan.date = date_iso_today();
    plan.label = "Plan généré";

    std::set<std::string> sel(available.begin(), available.end());
    std::set<std::string> used_today;
    float cal_total = targets.kcal, prot_total = targets.proteines;
    float gluc_total = targets.glucides, lip_total = targets.lipides;

    auto it_slots = MEAL_SLOTS.find(n_repas);
    if (it_slots == MEAL_SLOTS.end()) it_slots = MEAL_SLOTS.find(4);
    const auto& slots = it_slots->second;

    // Helper : aliments disponibles dans une catégorie
    auto avail = [&](const std::string& cat, const std::vector<std::string>& already) {
        auto it_c = FOOD_CATS.find(cat);
        if (it_c == FOOD_CATS.end()) return std::vector<std::string>{};
        std::vector<std::string> cands;
        for (auto& f : it_c->second) {
            if (sel.count(f) && catalog_.exists(f) && filter_compatible(f, already))
                cands.push_back(f);
        }
        std::shuffle(cands.begin(), cands.end(), rng_);
        // Filtre anti-répétition
        if (REPEAT_OK_CATS.find(cat) == REPEAT_OK_CATS.end()) {
            std::vector<std::string> fresh;
            for (auto& f : cands) if (!used_today.count(f)) fresh.push_back(f);
            if (!fresh.empty()) return fresh;
        }
        return cands;
    };

    // Structures internes pour les repas en cours de génération
    struct MealGen { SlotDef slot; std::string type; std::vector<GenItem> items; };
    std::vector<MealGen> meals;

    // ── PASSE 1 : templates ──────────────────────────────────────────────────
    for (auto& slot : slots) {
        float ratio = slot.ratio;
        float t_prot = prot_total * ratio;
        float t_gluc = gluc_total * ratio;
        auto it_t = SLOT_TEMPLATES.find(slot.type);
        if (it_t == SLOT_TEMPLATES.end()) it_t = SLOT_TEMPLATES.find("collation");
        auto templates = it_t->second;
        std::shuffle(templates.begin(), templates.end(), rng_);
        std::vector<GenItem> best_items;

        for (auto& tpl : templates) {
            std::vector<GenItem> items;
            float rem_prot = t_prot, rem_gluc = t_gluc;
            std::set<std::string> used;
            std::set<std::string> pending;
            bool ok = true;

            for (auto& ti : tpl) {
                std::vector<std::string> already;
                for (auto& i : items) already.push_back(i.food);
                auto cands = avail(ti.cat, already);
                // Remove already used in this template
                std::vector<std::string> filtered;
                for (auto& c : cands) if (!used.count(c)) filtered.push_back(c);
                if (filtered.empty()) {
                    if (ti.fixed_g > 0) continue; // optional fixed portion
                    ok = false; break;
                }
                std::string food = filtered[0];
                used.insert(food);
                const FoodData* fd = catalog_.get(food);
                if (!fd) { ok = false; break; }
                float g = 0;

                if (ti.fixed_g > 0) {
                    // Portion fixe bornée entre min et max
                    auto mn_it = FOOD_MIN_PORTION.find(food);
                    auto mx_it = FOOD_MAX_PORTION.find(food);
                    float mn_fix = (mn_it != FOOD_MIN_PORTION.end()) ? mn_it->second : 0;
                    float mx_fix = (mx_it != FOOD_MAX_PORTION.end()) ? mx_it->second : FOOD_MAX_DEFAULT;
                    g = std::max(mn_fix, std::min(mx_fix, (float)ti.fixed_g));
                } else if (ti.mode == "prot") {
                    g = g_for(*fd, food, rem_prot, 1);
                    if (g < 0) { // skip signal — essayer candidat suivant
                        bool found = false;
                        for (size_t ci = 1; ci < filtered.size(); ci++) {
                            const FoodData* fd2 = catalog_.get(filtered[ci]);
                            if (!fd2) continue;
                            float g2 = g_for(*fd2, filtered[ci], rem_prot, 1);
                            if (g2 >= 0) { food = filtered[ci]; fd = fd2; g = g2; found = true; break; }
                        }
                        if (!found) { ok = false; break; }
                    }
                } else if (ti.mode == "prot_rest") {
                    g = g_for(*fd, food, rem_prot, 1);
                    auto mn_it = FOOD_MIN_PORTION.find(food);
                    float mn = (mn_it != FOOD_MIN_PORTION.end()) ? mn_it->second : 10;
                    if (g < 0 || g < mn) continue; // skip silently
                } else if (ti.mode == "gluc") {
                    g = g_for(*fd, food, rem_gluc, 2);
                    if (g < 0) {
                        bool found = false;
                        for (size_t ci = 1; ci < filtered.size(); ci++) {
                            const FoodData* fd2 = catalog_.get(filtered[ci]);
                            if (!fd2) continue;
                            float g2 = g_for(*fd2, filtered[ci], rem_gluc, 2);
                            if (g2 >= 0) { food = filtered[ci]; fd = fd2; g = g2; found = true; break; }
                        }
                        if (!found) { ok = false; break; }
                    }
                } else { continue; }

                // Cap aux portions max
                auto mx_it = FOOD_MAX_PORTION.find(food);
                float cap = (mx_it != FOOD_MAX_PORTION.end()) ? mx_it->second : FOOD_MAX_DEFAULT;
                g = std::min(cap, g);

                float k, p, gc, l;
                calc_macros(*fd, g, k, p, gc, l);
                items.push_back({food, g, k, p, gc, l});
                pending.insert(food);
                auto fam_it = FOOD_SAME_FAMILY.find(food);
                if (fam_it != FOOD_SAME_FAMILY.end())
                    for (auto& f : fam_it->second) pending.insert(f);
                rem_prot -= p;
                rem_gluc -= gc;
            } // fin boucle template items

            if (ok && !items.empty()) {
                used_today.insert(pending.begin(), pending.end());
                best_items = items;
                break;
            }
        } // fin boucle templates

        // Fallback ultime
        if (best_items.empty()) {
            for (auto& f : available) {
                const FoodData* fd = catalog_.get(f);
                if (!fd || used_today.count(f)) continue;
                float g = std::max(50.0f, g_for(*fd, f, prot_total * slot.ratio, 1));
                if (g < 0) g = 50;
                float k, p, gc, l;
                calc_macros(*fd, g, k, p, gc, l);
                best_items = {{f, g, k, p, gc, l}};
                used_today.insert(f);
                break;
            }
        }
        meals.push_back({slot, slot.type, best_items});
    } // fin boucle slots — PASSE 1 terminée

    // ── PASSE 1.5 : Boost calorique ─────────────────────────────────────────
    float cur_gluc = 0, cur_lip = 0;
    for (auto& m : meals) for (auto& i : m.items) { cur_gluc += i.gluc; cur_lip += i.lip; }

    for (auto& m : meals) {
        float t_cal_m = cal_total * m.slot.ratio;
        float got_cal_m = 0;
        for (auto& i : m.items) got_cal_m += i.kcal;
        float deficit_c = t_cal_m - got_cal_m;
        if (deficit_c <= t_cal_m * 0.25f || m.type == "coucher") continue;

        float gluc_pct = (gluc_total > 0) ? cur_gluc / gluc_total * 100 : 100;
        float lip_pct  = (lip_total > 0) ? cur_lip / lip_total * 100 : 100;

        // Choisir le type de booster
        std::vector<std::string> boosters;
        // Glucides boosters par slot
        std::map<std::string, std::vector<std::string>> gb = {
            {"matin",{"Flocons d'avoine","Pain complet","Pain blanc","Galettes de riz nature","Miel","Confiture (moyenne)"}},
            {"midi",{"Riz cuit","Riz brun (cuit)","Pâtes cuites","Pâtes complètes (cuites)","Patate douce (cuite)","Quinoa (cuit)","Semoule (cuite)"}},
            {"soir",{"Riz cuit","Riz brun (cuit)","Patate douce (cuite)","Quinoa (cuit)","Pâtes complètes (cuites)"}},
            {"collation",{"Flocons d'avoine","Galettes de riz nature","Banane"}},
        };
        std::map<std::string, std::vector<std::string>> lb = {
            {"matin",{"Beurre de cacahuète","Beurre d'amande","Beurre doux"}},
            {"midi",{"Huile d'olive","Avocat","Amandes","Noix","Beurre de cacahuète","Emmental","Comté"}},
            {"soir",{"Huile d'olive","Avocat","Amandes","Noix"}},
            {"collation",{"Amandes","Noix","Noix de cajou","Beurre de cacahuète","Beurre d'amande","Chocolat noir 70%"}},
        };

        if (gluc_pct < 85 && gb.count(m.type)) boosters = gb[m.type];
        else if (lip_pct > 105) boosters = gb.count(m.type) ? gb[m.type] : std::vector<std::string>{};
        else boosters = lb.count(m.type) ? lb[m.type] : std::vector<std::string>{};
        std::shuffle(boosters.begin(), boosters.end(), rng_);

        // Try augmenting existing starch first
        GenItem* existing_starch = nullptr;
        for (auto& it : m.items) {
            for (auto& gc : {"glucide_midi","glucide_soir","glucide_matin","glucide_collation","pain_seulement"}) {
                auto fc = FOOD_CATS.find(gc);
                if (fc != FOOD_CATS.end()) {
                    for (auto& fn : fc->second) if (it.food == fn) { existing_starch = &it; break; }
                }
                if (existing_starch) break;
            }
            if (existing_starch) break;
        }
        if (existing_starch) {
            const FoodData* efd = catalog_.get(existing_starch->food);
            auto mx = FOOD_MAX_PORTION.find(existing_starch->food);
            float ecap = mx != FOOD_MAX_PORTION.end() ? mx->second : FOOD_MAX_DEFAULT;
            if (efd && existing_starch->g < ecap && efd->kcal_100g > 0) {
                float add_g = std::min(ecap - existing_starch->g,
                    std::max(20.0f, std::round(deficit_c / (efd->kcal_100g / 100.0f))));
                if (add_g >= 15) {
                    float ng = existing_starch->g + add_g;
                    float k,p,gc2,l;
                    calc_macros(*efd, ng, k, p, gc2, l);
                    cur_gluc += (gc2 - existing_starch->gluc);
                    *existing_starch = {existing_starch->food, ng, k, p, gc2, l};
                    continue;
                }
            }
        }

        // Add new booster item
        std::set<std::string> already_foods;
        for (auto& it : m.items) already_foods.insert(it.food);
        for (auto& bst : boosters) {
            if (!sel.count(bst) || !catalog_.exists(bst)) continue;
            if (already_foods.count(bst)) continue;
            std::vector<std::string> af_vec(already_foods.begin(), already_foods.end());
            if (!filter_compatible(bst, af_vec)) continue;
            const FoodData* bfd = catalog_.get(bst);
            if (!bfd || bfd->kcal_100g <= 0) continue;
            float g_raw = std::max(10.0f, std::round(deficit_c / (bfd->kcal_100g / 100.0f)));
            auto mn_it = FOOD_MIN_PORTION.find(bst);
            auto mx_it = FOOD_MAX_PORTION.find(bst);
            float mn = (mn_it != FOOD_MIN_PORTION.end()) ? mn_it->second : 10;
            float mx = (mx_it != FOOD_MAX_PORTION.end()) ? mx_it->second : FOOD_MAX_DEFAULT;
            float g_bst = std::max(mn, std::min(mx, g_raw));
            if (mn > 0 && g_bst * (bfd->kcal_100g / 100.0f) > deficit_c * 2.5f) continue;
            float k,p,gc2,l;
            calc_macros(*bfd, g_bst, k, p, gc2, l);
            m.items.push_back({bst, g_bst, k, p, gc2, l});
            used_today.insert(bst);
            cur_gluc += gc2; cur_lip += l;
            break;
        }
    } // fin passe 1.5

    // ── PASSE 2 : Correction protéines ±5% ──────────────────────────────────
    float got_prot = 0;
    for (auto& m : meals) for (auto& i : m.items) got_prot += i.prot;
    if (prot_total > 0 && std::abs(got_prot - prot_total) / prot_total * 100 > 5) {
        float delta = prot_total - got_prot;
        // Collect protein items sorted by protein content desc
        std::vector<GenItem*> pitems;
        for (auto& m : meals) for (auto& i : m.items) {
            const FoodData* fd = catalog_.get(i.food);
            if (fd && fd->prot_100g > 5) pitems.push_back(&i);
        }
        std::sort(pitems.begin(), pitems.end(), [](auto* a, auto* b){ return a->prot > b->prot; });

        for (auto* pi : pitems) {
            if (std::abs(delta) < 2) break;
            const FoodData* fd = catalog_.get(pi->food);
            if (!fd || fd->prot_100g <= 0) continue;
            float raw_g = pi->g + std::round(delta / (fd->prot_100g / 100.0f));
            auto mn_it = FOOD_MIN_PORTION.find(pi->food);
            auto mx_it = FOOD_MAX_PORTION.find(pi->food);
            float mn = (mn_it != FOOD_MIN_PORTION.end()) ? mn_it->second : 20;
            float mx = (mx_it != FOOD_MAX_PORTION.end()) ? mx_it->second : FOOD_MAX_DEFAULT;
            float new_g = std::max(mn, std::min(mx, raw_g));
            if (new_g == pi->g) continue;
            float old_p = pi->prot;
            calc_macros(*fd, new_g, pi->kcal, pi->prot, pi->gluc, pi->lip);
            pi->g = new_g;
            delta -= (pi->prot - old_p);
        }
    }

    // ── PASSE 3 : Équilibrage glucides ±3% ──────────────────────────────────
    auto collect_gluc_items = [&]() {
        std::vector<GenItem*> gi;
        for (auto& m : meals) {
            if (m.type == "coucher") continue;
            for (auto& i : m.items) {
                for (auto& gc : {"glucide_midi","glucide_soir","glucide_matin","glucide_collation","pain_seulement"}) {
                    auto fc = FOOD_CATS.find(gc);
                    if (fc != FOOD_CATS.end())
                        for (auto& fn : fc->second) if (i.food == fn) { gi.push_back(&i); goto next_gi; }
                }
                next_gi:;
            }
        }
        std::sort(gi.begin(), gi.end(), [](auto* a, auto* b){ return a->gluc > b->gluc; });
        return gi;
    };

    // 3a. Trim if excess > 3%
    float got_gluc = 0;
    for (auto& m : meals) for (auto& i : m.items) got_gluc += i.gluc;
    if (gluc_total > 0 && (got_gluc - gluc_total) / gluc_total * 100 > 3) {
        float excess = got_gluc - gluc_total;
        auto gi = collect_gluc_items();
        for (auto* item : gi) {
            if (excess < 2) break;
            const FoodData* fd = catalog_.get(item->food);
            if (!fd || fd->gluc_100g <= 0) continue;
            auto mn_it = FOOD_MIN_PORTION.find(item->food);
            float mn = (mn_it != FOOD_MIN_PORTION.end()) ? mn_it->second : 30;
            float reduce = std::min(item->g - mn, std::round(excess / (fd->gluc_100g / 100.0f)));
            if (reduce <= 0) continue;
            float new_g = std::max(mn, item->g - reduce);
            float old_gc = item->gluc;
            calc_macros(*fd, new_g, item->kcal, item->prot, item->gluc, item->lip);
            item->g = new_g;
            excess -= (old_gc - item->gluc);
        }
    }
    // 3b. Fill if deficit > 3%
    got_gluc = 0;
    for (auto& m : meals) for (auto& i : m.items) got_gluc += i.gluc;
    if (gluc_total > 0 && (gluc_total - got_gluc) / gluc_total * 100 > 3) {
        float deficit = gluc_total - got_gluc;
        auto gi = collect_gluc_items();
        for (auto* item : gi) {
            if (deficit < 2) break;
            const FoodData* fd = catalog_.get(item->food);
            if (!fd || fd->gluc_100g <= 0) continue;
            auto mx_it = FOOD_MAX_PORTION.find(item->food);
            float mx = (mx_it != FOOD_MAX_PORTION.end()) ? mx_it->second : FOOD_MAX_DEFAULT;
            float add = std::min(mx - item->g, std::round(deficit / (fd->gluc_100g / 100.0f)));
            if (add <= 0) continue;
            float new_g = std::min(mx, item->g + add);
            float old_gc = item->gluc;
            calc_macros(*fd, new_g, item->kcal, item->prot, item->gluc, item->lip);
            item->g = new_g;
            deficit -= (item->gluc - old_gc);
        }
    }

    // ── PASSE 4 : Équilibrage lipides ±3% ────────────────────────────────────
    // 4a. Trim lipides excédentaires
    float got_lip = 0;
    for (auto& m : meals) for (auto& i : m.items) got_lip += i.lip;
    if (lip_total > 0 && (got_lip - lip_total) / lip_total * 100 > 3) {
        float excess = got_lip - lip_total;
        std::vector<std::string> lip_cats = {"huile_cuisson","beurre_pain","lipide_sain",
            "lipide_matin","lipide_collation","lipide_coucher"};
        for (auto& lcat : lip_cats) {
            if (excess <= 1) break;
            for (auto& m : meals) {
                if (m.type == "coucher") continue;
                for (auto& it : m.items) {
                    auto fc = FOOD_CATS.find(lcat);
                    if (fc == FOOD_CATS.end()) continue;
                    bool in_cat = false;
                    for (auto& fn : fc->second) if (it.food == fn) { in_cat = true; break; }
                    if (!in_cat) continue;
                    const FoodData* fd = catalog_.get(it.food);
                    if (!fd || fd->lip_100g <= 0) continue;
                    auto mn_it = FOOD_MIN_PORTION.find(it.food);
                    float mn = (mn_it != FOOD_MIN_PORTION.end()) ? mn_it->second : 5;
                    float can_trim = it.g - mn;
                    if (can_trim <= 1) continue;
                    float needed = std::round(excess / (fd->lip_100g / 100.0f));
                    float trim = std::min(can_trim, needed);
                    float old_l = it.lip;
                    float new_g = std::max(mn, it.g - trim);
                    calc_macros(*fd, new_g, it.kcal, it.prot, it.gluc, it.lip);
                    it.g = new_g;
                    excess -= (old_l - it.lip);
                    if (excess <= 2) break;
                }
                if (excess <= 2) break;
            }
        }
    }

    // 4b. Fill lipid deficit > 3% — add olive oil on midi/soir
    got_lip = 0;
    for (auto& m : meals) for (auto& i : m.items) got_lip += i.lip;
    float deficit_lip = lip_total - got_lip;
    if (deficit_lip > lip_total * 0.03f) {
        std::vector<MealGen*> tslots;
        for (auto& m : meals) if (m.type == "midi" || m.type == "soir") tslots.push_back(&m);
        if (tslots.empty()) for (auto& m : meals) if (m.type != "coucher") tslots.push_back(&m);
        std::string lip_food;
        auto lip_avail = avail("lipide_sain", {});
        for (auto& lf : lip_avail) {
            for (auto* ts : tslots) {
                std::vector<std::string> existing;
                for (auto& it : ts->items) existing.push_back(it.food);
                if (filter_compatible(lf, existing)) { lip_food = lf; break; }
            }
            if (!lip_food.empty()) break;
        }
        if (lip_food.empty() && !lip_avail.empty()) lip_food = lip_avail[0];
        if (!lip_food.empty()) {
            const FoodData* lfd = catalog_.get(lip_food);
            if (lfd && lfd->lip_100g > 0) {
                auto mn_it = FOOD_MIN_PORTION.find(lip_food);
                float mn = (mn_it != FOOD_MIN_PORTION.end()) ? mn_it->second : 8;
                float g_total = std::max(mn, std::round(deficit_lip / (lfd->lip_100g / 100.0f)));
                float g_per = g_total / std::max((int)tslots.size(), 1);
                for (auto* ts : tslots) {
                    if (g_per < 3) continue;
                    float k,p,gc,l;
                    calc_macros(*lfd, g_per, k, p, gc, l);
                    ts->items.push_back({lip_food, g_per, k, p, gc, l});
                }
            }
        }
    }

    // ── PASSE 5 : Précision protéines ±1% ────────────────────────────────────
    got_prot = 0;
    for (auto& m : meals) for (auto& i : m.items) got_prot += i.prot;
    float prot_err = (prot_total > 0) ? (got_prot - prot_total) / prot_total * 100 : 0;
    if (std::abs(prot_err) > 1.0f) {
        float delta = prot_total - got_prot;
        std::vector<GenItem*> pitems;
        for (auto& m : meals) if (m.type != "coucher")
            for (auto& i : m.items) {
                const FoodData* fd = catalog_.get(i.food);
                if (fd && fd->prot_100g > 5) pitems.push_back(&i);
            }
        std::sort(pitems.begin(), pitems.end(), [](auto* a, auto* b){ return a->prot > b->prot; });
        for (auto* pi : pitems) {
            if (std::abs(delta) < 1) break;
            const FoodData* fd = catalog_.get(pi->food);
            if (!fd || fd->prot_100g <= 0) continue;
            float add_g = std::round(delta / (fd->prot_100g / 100.0f));
            auto mn_it = FOOD_MIN_PORTION.find(pi->food);
            auto mx_it = FOOD_MAX_PORTION.find(pi->food);
            float mn = (mn_it != FOOD_MIN_PORTION.end()) ? mn_it->second : 20;
            float mx = (mx_it != FOOD_MAX_PORTION.end()) ? mx_it->second : FOOD_MAX_DEFAULT;
            float new_g = std::max(mn, std::min(mx, pi->g + add_g));
            if (new_g == pi->g) continue;
            float old_p = pi->prot;
            calc_macros(*fd, new_g, pi->kcal, pi->prot, pi->gluc, pi->lip);
            pi->g = new_g;
            delta -= (pi->prot - old_p);
        }
    }

    // ── PASSE 5b : Injection protéique d'urgence (>8% déficit) ───────────────
    got_prot = 0;
    for (auto& m : meals) for (auto& i : m.items) got_prot += i.prot;
    float deficit_p = prot_total - got_prot;
    if (deficit_p > prot_total * 0.08f) {
        MealGen* target = nullptr;
        for (auto& m : meals) {
            if (m.type == "coucher") continue;
            float mc = 0; for (auto& i : m.items) mc += i.kcal;
            float tc = cal_total * m.slot.ratio;
            if (mc < tc * 1.15f && (!target || mc < [&]{ float s=0; for(auto& i:target->items) s+=i.kcal; return s; }()))
                target = &m;
        }
        if (target) {
            std::vector<std::string> emerg = {"EvoWhey HSN","Whey protéine","Oeuf entier","Blanc d'oeuf",
                "Blanc de poulet (cuit)","Thon (en boîte, eau)"};
            std::set<std::string> efood;
            for (auto& i : target->items) efood.insert(i.food);
            for (auto& c : emerg) {
                if (!sel.count(c) || !catalog_.exists(c)) continue;
                const FoodData* fd = catalog_.get(c);
                if (!fd || fd->prot_100g <= 0) continue;
                std::vector<std::string> ev(efood.begin(), efood.end());
                if (!efood.count(c) && !filter_compatible(c, ev)) continue;
                auto mn_it = FOOD_MIN_PORTION.find(c);
                auto mx_it = FOOD_MAX_PORTION.find(c);
                float mn = (mn_it != FOOD_MIN_PORTION.end()) ? mn_it->second : 20;
                float mx = (mx_it != FOOD_MAX_PORTION.end()) ? mx_it->second : FOOD_MAX_DEFAULT;
                float g_need = std::max(mn, std::min(mx, std::round(deficit_p / (fd->prot_100g / 100.0f))));
                float k,p,gc2,l;
                calc_macros(*fd, g_need, k, p, gc2, l);
                target->items.push_back({c, g_need, k, p, gc2, l});
                break;
            }
        }
    }

    // ── PASSE 6 : Rééquilibrage croisé gluc/lip + calibrage calorique ±1% ───
    for (int rebal = 0; rebal < 6; rebal++) {
        float cg = 0, cl = 0;
        for (auto& m : meals) for (auto& i : m.items) { cg += i.gluc; cl += i.lip; }
        float g_err = (gluc_total > 0) ? (cg - gluc_total) / gluc_total * 100 : 0;
        float l_err = (lip_total > 0) ? (cl - lip_total) / lip_total * 100 : 0;
        if (std::abs(g_err) <= 5 && std::abs(l_err) <= 5) break;

        // Phase A: trim excess lipids from pure lipid categories
        if (l_err > 5) {
            float excess_l = cl - lip_total;
            std::vector<std::string> lp_cats = {"huile_cuisson","beurre_pain","lipide_sain",
                "lipide_matin","lipide_collation","lipide_coucher","fromage_dur"};
            for (auto& lcat : lp_cats) {
                if (excess_l <= 1) break;
                for (auto& m : meals) {
                    if (m.type == "coucher") continue;
                    for (auto& it : m.items) {
                        auto fc = FOOD_CATS.find(lcat);
                        if (fc == FOOD_CATS.end()) continue;
                        bool in_cat = false;
                        for (auto& fn : fc->second) if (it.food == fn) { in_cat = true; break; }
                        if (!in_cat) continue;
                        const FoodData* fd = catalog_.get(it.food);
                        if (!fd || fd->lip_100g <= 0) continue;
                        auto mn_it = FOOD_MIN_PORTION.find(it.food);
                        float mn = (mn_it != FOOD_MIN_PORTION.end()) ? mn_it->second : 5;
                        float trim = std::min(it.g - mn, std::round(excess_l / (fd->lip_100g / 100.0f)));
                        if (trim <= 0) continue;
                        float new_g = std::max(mn, it.g - trim);
                        float old_l = it.lip;
                        calc_macros(*fd, new_g, it.kcal, it.prot, it.gluc, it.lip);
                        it.g = new_g;
                        excess_l -= (old_l - it.lip);
                    }
                }
            }
        }

        // Phase B: reinject freed calories as glucides
        float cg2 = 0;
        for (auto& m : meals) for (auto& i : m.items) cg2 += i.gluc;
        float g_deficit = gluc_total - cg2;
        if (g_deficit > 2) {
            auto gi = collect_gluc_items();
            if (!gi.empty()) {
                float share = g_deficit / gi.size();
                for (auto* item : gi) {
                    if (share < 1) break;
                    const FoodData* fd = catalog_.get(item->food);
                    if (!fd || fd->gluc_100g <= 0) continue;
                    auto mx_it = FOOD_MAX_PORTION.find(item->food);
                    float mx = (mx_it != FOOD_MAX_PORTION.end()) ? mx_it->second : FOOD_MAX_DEFAULT;
                    float add = std::min(mx - item->g, std::round(share / (fd->gluc_100g / 100.0f)));
                    if (add <= 0) continue;
                    float new_g = std::min(mx, item->g + add);
                    calc_macros(*fd, new_g, item->kcal, item->prot, item->gluc, item->lip);
                    item->g = new_g;
                }
            }
        }
    } // fin boucle rebal

    // ── PASSE 6b : Calibrage calorique final ±1% ────────────────────────────
    for (int iter = 0; iter < 8; iter++) {
        float got_cal = 0;
        for (auto& m : meals) for (auto& i : m.items) got_cal += i.kcal;
        float delta_kcal = cal_total - got_cal;
        if (std::abs(delta_kcal / cal_total * 100) <= 1.0f) break;

        auto gi = collect_gluc_items();
        for (auto* item : gi) {
            if (std::abs(delta_kcal) < cal_total * 0.01f) break;
            const FoodData* fd = catalog_.get(item->food);
            if (!fd || fd->kcal_100g <= 0) continue;
            auto mn_it = FOOD_MIN_PORTION.find(item->food);
            auto mx_it = FOOD_MAX_PORTION.find(item->food);
            float mn = (mn_it != FOOD_MIN_PORTION.end()) ? mn_it->second : 30;
            float mx = (mx_it != FOOD_MAX_PORTION.end()) ? mx_it->second : FOOD_MAX_DEFAULT;
            float adj_g = std::round(delta_kcal / (fd->kcal_100g / 100.0f));
            float new_g = std::max(mn, std::min(mx, item->g + adj_g));
            if (new_g == item->g) continue;
            float old_kcal = item->kcal;
            calc_macros(*fd, new_g, item->kcal, item->prot, item->gluc, item->lip);
            item->g = new_g;
            delta_kcal -= (item->kcal - old_kcal);
        }
    }

    // ── Conversion MealGen → PlanJournalier ──────────────────────────────────
    for (auto& m : meals) {
        Repas r;
        r.nom = m.slot.name;
        r.type = m.type;
        for (auto& gi : m.items) {
            FoodItem fi;
            fi.nom = gi.food;
            fi.grammes = gi.g;
            const FoodData* fd = catalog_.get(gi.food);
            if (fd) fi.macros_100g = Macros(fd->kcal_100g, fd->prot_100g, fd->gluc_100g, fd->lip_100g, fd->fibres_100g);
            fi.macros_portion = Macros(gi.kcal, gi.prot, gi.gluc, gi.lip);
            fi.categorie = fd ? fd->categorie : "";
            r.items.push_back(fi);
        }
        r.calculer_totaux();
        plan.repas.push_back(r);
    }
    plan.calculer_totaux();
    return plan;
}

// ═════════════════════════════════════════════════════════════════════════════
//  API PUBLIQUE
// ═════════════════════════════════════════════════════════════════════════════
ResultatGeneration MealGenerator::generate_plan(const ConfigGeneration& config,
                                                DatabaseConnection* db) {
    ResultatGeneration result;
    try {
        if (config.mode == "jour") {
            result.plan_jour = generate_day(config.n_repas, config.aliments,
                                            config.objectifs, 0);
            result.succes = true;
        } else {
            int n_days = (config.mode == "semaine") ? 7 : 30;
            result.plan_multi = generate_multiday(n_days, config.n_repas,
                                                  config.aliments, config.objectifs,
                                                  config.date_debut);
            result.succes = true;
        }
    } catch (const std::exception& e) {
        result.succes = false;
        result.erreur = e.what();
    }
    return result;
}

PlanMultiJours MealGenerator::generate_multiday(int n_days, int n_repas,
                                                const std::vector<std::string>& available,
                                                const Macros& targets,
                                                const std::string& start_date) {
    PlanMultiJours plan;
    plan.mode = (n_days == 7) ? "semaine" : "mois";
    plan.n_repas = n_repas;
    for (int i = 0; i < n_days; i++) {
        PlanJournalier jour = generate_day(n_repas, available, targets, i);
        jour.date = date_add_days(start_date, i);
        plan.jours.push_back(jour);
    }
    plan.calculer_moyennes();
    return plan;
}

float MealGenerator::compute_diversity_score(const PlanMultiJours& plan) {
    std::set<std::string> all_foods;
    for (auto& jour : plan.jours)
        for (auto& repas : jour.repas)
            for (auto& item : repas.items)
                all_foods.insert(item.nom);
    float max_possible = std::min((float)catalog_.size(), (float)(plan.jours.size() * 15));
    return (max_possible > 0) ? (all_foods.size() / max_possible * 100.0f) : 0;
}

} // namespace threshold
