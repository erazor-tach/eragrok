// food_data.cpp — Données statiques moteur nutritionnel THRESHOLD
// Porté depuis Python meal_engine.py
#include "food_data.h"
#include <algorithm>

namespace threshold {

// ═════════════════════════════════════════════════════════════════════════════
//  CATÉGORIES FONCTIONNELLES
// ═════════════════════════════════════════════════════════════════════════════
const std::map<std::string, std::vector<std::string>> FOOD_CATS = {
    {"oeuf", {"Oeuf entier","Blanc d'oeuf"}},
    {"glucide_matin", {"Flocons d'avoine","Galettes de riz nature"}},
    {"glucide_collation", {"Flocons d'avoine"}},
    {"glucide_midi", {"Riz cuit","Riz brun (cuit)","Pâtes cuites",
        "Pâtes complètes (cuites)","Patate douce (cuite)",
        "Pomme de terre (cuite)","Quinoa (cuit)",
        "Lentilles (cuites)","Pois chiches (cuits)",
        "Haricots rouges (cuits)","Boulgour (cuit)",
        "Semoule (cuite)","Haricots blancs (cuits)"}},
    {"glucide_soir", {"Riz cuit","Riz brun (cuit)","Patate douce (cuite)",
        "Quinoa (cuit)","Pâtes complètes (cuites)",
        "Boulgour (cuit)","Lentilles (cuites)",
        "Haricots blancs (cuits)","Semoule (cuite)","Pâtes cuites"}},
    {"fruit", {"Banane","Pomme","Orange","Kiwi","Fraises",
        "Myrtilles","Mangue","Ananas","Pastèque"}},
    {"legume", {"Brocoli (cuit)","Épinards (crus)","Courgette (cuite)",
        "Haricots verts (cuits)","Asperges (cuites)",
        "Poivron (cru)","Tomate (crue)","Salade verte",
        "Champignons (cuits)","Chou-fleur (cuit)","Concombre (cru)"}},
    {"lipide_sain", {"Huile d'olive","Avocat","Amandes",
        "Beurre de cacahuète","Beurre d'amande","Noix",
        "Noix de cajou","Graines de chia","Graines de lin","Beurre doux"}},
    {"laitier", {"Skyr 0%","Fromage blanc 0%","Yaourt grec 0%",
        "Cottage cheese","Lait écrémé","Yaourt grec entier (5%)",
        "Lait entier"}},
    {"laitier_lent", {"Cottage cheese","Skyr 0%","Fromage blanc 0%"}},
    {"whey", {"Whey protéine","EvoWhey HSN"}},
    {"supplement_lent", {"Caséine"}},
    {"proteine_maigre", {"Blanc de poulet (cuit)","Blanc de dinde (cuit)",
        "Thon (en boîte, eau)","Cabillaud (cuit)",
        "Crevettes (cuites)","Jambon blanc (dégraissé)","Tofu ferme"}},
    {"proteine_grasse", {"Boeuf haché 5% MG","Boeuf haché 15% MG",
        "Boeuf haché 20% MG","Saumon (cuit)",
        "Oeuf entier","Steak (rumsteck, cuit)",
        "Maquereau (cuit)","Sardines (en boîte, huile)"}},
    {"proteine_midi", {"Boeuf haché 5% MG","Boeuf haché 15% MG",
        "Boeuf haché 20% MG","Saumon (cuit)","Oeuf entier",
        "Steak (rumsteck, cuit)","Maquereau (cuit)",
        "Sardines (en boîte, huile)","Blanc de poulet (cuit)",
        "Blanc de dinde (cuit)","Thon (en boîte, eau)",
        "Cabillaud (cuit)","Crevettes (cuites)",
        "Blanc d'oeuf","Jambon blanc (dégraissé)","Tofu ferme"}},
    {"fromage_dur", {"Emmental","Comté"}},
    {"sucrant_matin", {"Confiture (moyenne)","Miel","Cacao pur en poudre"}},
    {"pain_seulement", {"Pain blanc","Pain complet"}},
    {"lipide_matin", {"Beurre de cacahuète","Beurre d'amande","Amandes","Noix"}},
    {"beurre_pain", {"Beurre doux"}},
    {"lipide_collation", {"Beurre de cacahuète","Beurre d'amande",
        "Amandes","Noix","Noix de cajou","Chocolat noir 70%"}},
    {"huile_cuisson", {"Huile d'olive"}},
    {"lipide_coucher", {"Noix","Amandes","Noix de cajou",
        "Beurre de cacahuète","Beurre d'amande","Chocolat noir 70%"}},
};

// ═════════════════════════════════════════════════════════════════════════════
//  SLOT TEMPLATES
// ═════════════════════════════════════════════════════════════════════════════
const std::map<std::string, std::vector<MealTemplate>> SLOT_TEMPLATES = {
    {"matin", {
        {{"oeuf","prot"},{"glucide_matin","gluc"},{"huile_cuisson",8},{"fruit",120},{"laitier","prot_rest"}},
        {{"oeuf","prot"},{"glucide_matin","gluc"},{"huile_cuisson",8},{"fruit",120}},
        {{"laitier","prot"},{"glucide_matin","gluc"},{"lipide_matin",15},{"fruit",120}},
        {{"pain_seulement","gluc"},{"beurre_pain",10},{"oeuf","prot"},{"fromage_dur",25}},
        {{"pain_seulement","gluc"},{"beurre_pain",10},{"laitier","prot"}},
        {{"pain_seulement","gluc"},{"beurre_pain",10},{"sucrant_matin",20},{"laitier","prot"}},
        {{"pain_seulement","gluc"},{"beurre_pain",10},{"sucrant_matin",20},{"oeuf","prot"}},
        {{"oeuf","prot"},{"glucide_matin","gluc"},{"huile_cuisson",8},{"sucrant_matin",20}},
        {{"laitier","prot"},{"glucide_matin","gluc"},{"fromage_dur",25},{"fruit",100}},
        {{"oeuf","prot"},{"glucide_matin","gluc"},{"fruit",130}},
        {{"laitier","prot"},{"glucide_matin","gluc"},{"fruit",130}},
        {{"laitier","prot"},{"glucide_matin","gluc"}},
    }},
    {"midi", {
        {{"proteine_midi","prot"},{"glucide_midi","gluc"},{"legume",150},{"huile_cuisson",8}},
        {{"proteine_midi","prot"},{"glucide_midi","gluc"},{"legume",150},{"lipide_sain",10}},
        {{"proteine_midi","prot"},{"glucide_midi","gluc"},{"legume",150},{"fromage_dur",20}},
        {{"proteine_midi","prot"},{"glucide_midi","gluc"},{"legume",150}},
        {{"proteine_midi","prot"},{"glucide_midi","gluc"},{"legume",180}},
    }},
    {"collation", {
        {{"whey","prot"},{"glucide_collation","gluc"}},
        {{"laitier","prot"},{"glucide_collation","gluc"},{"lipide_collation",15}},
        {{"laitier","prot"},{"lipide_collation",20},{"fruit",130}},
        {{"laitier","prot"},{"fruit",130}},
        {{"whey","prot"}},
        {{"fromage_dur",30},{"fruit",150}},
        {{"laitier","prot"},{"lipide_collation",20}},
        {{"laitier","prot"},{"glucide_collation","gluc"}},
        {{"whey","prot"},{"fruit",130}},
    }},
    {"soir", {
        {{"proteine_maigre","prot"},{"glucide_soir","gluc"},{"legume",180},{"huile_cuisson",8}},
        {{"proteine_maigre","prot"},{"glucide_soir","gluc"},{"legume",150},{"lipide_sain",10}},
        {{"proteine_grasse","prot"},{"glucide_soir","gluc"},{"legume",180}},
        {{"proteine_grasse","prot"},{"legume",200}},
        {{"proteine_maigre","prot"},{"legume",200},{"huile_cuisson",8}},
        {{"proteine_maigre","prot"},{"glucide_soir","gluc"},{"legume",150},{"fromage_dur",20}},
        {{"proteine_maigre","prot"},{"glucide_soir","gluc"},{"legume",180}},
    }},
    {"coucher", {
        {{"supplement_lent","prot"}},
        {{"laitier_lent","prot"},{"lipide_coucher",15}},
        {{"laitier","prot"},{"lipide_coucher",15}},
        {{"supplement_lent","prot"},{"lipide_coucher",15}},
        {{"laitier_lent","prot"}},
        {{"laitier","prot"}},
        {{"whey","prot"}},
    }},
};

// ═════════════════════════════════════════════════════════════════════════════
//  SLOT DESC & MEAL_SLOTS
// ═════════════════════════════════════════════════════════════════════════════
const std::map<std::string, std::string> SLOT_DESC = {
    {"matin",     "Œufs / laitiers / pain+beurre / flocons / fruits"},
    {"midi",      "Repas principal — grasses OK — glucides complets"},
    {"collation", "Whey+crème de riz · skyr+beurre de cac · fruit"},
    {"soir",      "Protéines maigres uniquement — légumes"},
    {"coucher",   "Protéines lentes (caséine/cottage/whey) — zéro glucide"},
};

const std::map<int, std::vector<SlotDef>> MEAL_SLOTS = {
    {3, {{"Petit-déjeuner","matin",0.28f},{"Déjeuner","midi",0.44f},{"Dîner","soir",0.28f}}},
    {4, {{"Petit-déjeuner","matin",0.22f},{"Déjeuner","midi",0.35f},
         {"Collation","collation",0.18f},{"Dîner","soir",0.25f}}},
    {5, {{"Petit-déjeuner","matin",0.20f},{"Déjeuner","midi",0.30f},
         {"Collation après-midi","collation",0.15f},{"Dîner","soir",0.25f},
         {"Avant coucher","coucher",0.10f}}},
    {6, {{"Petit-déjeuner","matin",0.16f},{"Collation matin","collation",0.10f},
         {"Déjeuner","midi",0.30f},{"Collation après-midi","collation",0.14f},
         {"Dîner","soir",0.20f},{"Avant coucher","coucher",0.10f}}},
};

// ═════════════════════════════════════════════════════════════════════════════
//  PORTIONS MIN / MAX
// ═════════════════════════════════════════════════════════════════════════════
const std::unordered_map<std::string, float> FOOD_MIN_PORTION = {
    {"Banane",100},{"Pomme",100},{"Kiwi",60},{"Orange",120},{"Mangue",150},
    {"Ananas",100},{"Pastèque",150},{"Fraises",80},{"Myrtilles",60},
    {"Avocat",80},{"Poivron (cru)",80},{"Tomate (crue)",80},{"Concombre (cru)",100},
    {"Salade verte",60},
    {"Amandes",15},{"Noix",15},{"Noix de cajou",15},{"Graines de chia",10},
    {"Graines de lin",10},{"Beurre de cacahuète",15},{"Beurre d'amande",15},
    {"Beurre doux",10},{"Huile d'olive",8},
    {"Emmental",20},{"Comté",25},{"Chocolat noir 70%",15},{"Cacao pur en poudre",8},
    {"Saumon (cuit)",100},{"Maquereau (cuit)",80},{"Cabillaud (cuit)",100},
    {"Sardines (en boîte, huile)",75},
    {"Steak (rumsteck, cuit)",120},{"Crevettes (cuites)",80},
    {"Brocoli (cuit)",80},{"Courgette (cuite)",80},{"Chou-fleur (cuit)",80},
    {"Asperges (cuites)",60},{"Champignons (cuits)",60},{"Haricots verts (cuits)",70},
    {"Skyr 0%",125},{"Yaourt grec 0%",125},{"Yaourt grec entier (5%)",125},
    {"Cottage cheese",100},{"Fromage blanc 0%",100},
    {"Lait entier",100},{"Lait écrémé",100},
    {"Miel",10},{"Confiture (moyenne)",15},
    {"Jambon blanc (dégraissé)",40},
    {"Oeuf entier",55},{"Blanc d'oeuf",30},
    {"Tofu ferme",80},{"Edamame (cuit)",60},
    {"Blanc de poulet (cuit)",80},{"Blanc de dinde (cuit)",80},
    {"Thon (en boîte, eau)",60},
    {"EvoWhey HSN",25},{"Whey protéine",25},{"Caséine",25},
};

const std::unordered_map<std::string, float> FOOD_MAX_PORTION = {
    {"Oeuf entier",240},{"Blanc d'oeuf",280},
    {"Blanc de poulet (cuit)",250},{"Blanc de dinde (cuit)",250},
    {"Boeuf haché 5% MG",250},{"Boeuf haché 15% MG",220},{"Boeuf haché 20% MG",200},
    {"Saumon (cuit)",220},{"Thon (en boîte, eau)",200},
    {"Cabillaud (cuit)",250},{"Crevettes (cuites)",200},
    {"Steak (rumsteck, cuit)",250},{"Maquereau (cuit)",200},
    {"Sardines (en boîte, huile)",150},{"Jambon blanc (dégraissé)",150},
    {"Tofu ferme",250},
    {"Riz cuit",280},{"Riz brun (cuit)",280},
    {"Pâtes cuites",250},{"Pâtes complètes (cuites)",250},
    {"Patate douce (cuite)",250},{"Pomme de terre (cuite)",300},
    {"Quinoa (cuit)",250},{"Lentilles (cuites)",250},
    {"Pois chiches (cuits)",250},{"Haricots rouges (cuits)",250},
    {"Haricots blancs (cuits)",250},{"Boulgour (cuit)",250},{"Semoule (cuite)",250},
    {"Flocons d'avoine",100},{"Pain complet",100},{"Pain blanc",100},
    {"Galettes de riz nature",60},
    {"Skyr 0%",200},{"Cottage cheese",200},{"Fromage blanc 0%",200},
    {"Yaourt grec 0%",200},{"Yaourt grec entier (5%)",200},
    {"Lait écrémé",300},{"Lait entier",300},{"Ricotta",150},
    {"EvoWhey HSN",50},{"Whey protéine",50},{"Caséine",50},
    {"Emmental",50},{"Comté",50},
    {"Avocat",150},{"Amandes",40},{"Noix",40},{"Noix de cajou",40},
    {"Beurre de cacahuète",40},{"Beurre d'amande",35},
    {"Graines de chia",30},{"Graines de lin",30},
    {"Huile d'olive",25},{"Beurre doux",25},{"Chocolat noir 70%",40},
    {"Cacao pur en poudre",15},{"Confiture (moyenne)",30},{"Miel",25},
    {"Banane",200},{"Pomme",200},{"Orange",200},{"Kiwi",150},
    {"Fraises",200},{"Myrtilles",150},{"Mangue",200},{"Ananas",200},{"Pastèque",300},
    {"Brocoli (cuit)",250},{"Courgette (cuite)",250},{"Haricots verts (cuits)",250},
    {"Asperges (cuites)",200},{"Champignons (cuits)",200},{"Chou-fleur (cuit)",250},
    {"Poivron (cru)",200},{"Tomate (crue)",250},{"Salade verte",150},
    {"Concombre (cru)",250},{"Épinards (crus)",150},
};

// ═════════════════════════════════════════════════════════════════════════════
//  FAMILLES ANTI-RÉPÉTITION
// ═════════════════════════════════════════════════════════════════════════════
const std::unordered_map<std::string, std::unordered_set<std::string>> FOOD_SAME_FAMILY = {
    {"EvoWhey HSN",     {"Whey protéine","Caséine"}},
    {"Whey protéine",   {"EvoWhey HSN","Caséine"}},
    {"Caséine",         {"EvoWhey HSN","Whey protéine"}},
    {"Pâtes cuites",             {"Pâtes complètes (cuites)"}},
    {"Pâtes complètes (cuites)", {"Pâtes cuites"}},
    {"Riz cuit",        {"Riz brun (cuit)"}},
    {"Riz brun (cuit)", {"Riz cuit"}},
    {"Beurre de cacahuète", {"Beurre d'amande"}},
    {"Beurre d'amande",     {"Beurre de cacahuète"}},
    {"Blanc de poulet (cuit)", {"Blanc de dinde (cuit)"}},
    {"Blanc de dinde (cuit)",  {"Blanc de poulet (cuit)"}},
};

// ═════════════════════════════════════════════════════════════════════════════
//  INCOMPATIBILITÉS (set symétrique)
// ═════════════════════════════════════════════════════════════════════════════
static std::set<std::pair<std::string, std::string>> build_incompat() {
    std::vector<std::pair<std::string,std::string>> pairs = {
        {"Flocons d'avoine","Sardines (en boîte, huile)"},
        {"Flocons d'avoine","Maquereau (cuit)"},
        {"Flocons d'avoine","Thon (en boîte, eau)"},
        {"Flocons d'avoine","Saumon (cuit)"},
        {"Flocons d'avoine","Blanc de poulet (cuit)"},
        {"Flocons d'avoine","Blanc de dinde (cuit)"},
        {"Flocons d'avoine","Boeuf haché 5% MG"},
        {"Flocons d'avoine","Steak (rumsteck, cuit)"},
        {"Galettes de riz nature","Sardines (en boîte, huile)"},
        {"Galettes de riz nature","Maquereau (cuit)"},
        {"Pain complet","Sardines (en boîte, huile)"},
        {"Pain complet","Maquereau (cuit)"},
        {"Banane","Sardines (en boîte, huile)"},
        {"Beurre doux","Banane"},{"Beurre doux","Pomme"},{"Beurre doux","Orange"},
        {"Beurre doux","Fraises"},{"Beurre doux","Myrtilles"},{"Beurre doux","Mangue"},
        {"Beurre doux","Whey protéine"},{"Beurre doux","EvoWhey HSN"},{"Beurre doux","Caséine"},
        {"Beurre doux","Sardines (en boîte, huile)"},{"Beurre doux","Maquereau (cuit)"},
        {"Huile d'olive","Skyr 0%"},{"Huile d'olive","Yaourt grec 0%"},
        {"Huile d'olive","Fromage blanc 0%"},{"Huile d'olive","Cottage cheese"},
        {"Huile d'olive","Yaourt grec entier (5%)"},
        {"Huile d'olive","Whey protéine"},{"Huile d'olive","EvoWhey HSN"},
        {"Huile d'olive","Caséine"},
        {"Huile d'olive","Banane"},{"Huile d'olive","Pomme"},
        {"Huile d'olive","Fraises"},{"Huile d'olive","Orange"},
        {"Huile d'olive","Flocons d'avoine"},
        {"Huile d'olive","Galettes de riz nature"},
        {"Huile d'olive","Miel"},{"Huile d'olive","Confiture (moyenne)"},
        {"Huile d'olive","Chocolat noir 70%"},
    };
    std::set<std::pair<std::string,std::string>> s;
    for (auto& [a,b] : pairs) { s.insert({a,b}); s.insert({b,a}); }
    return s;
}
const std::set<std::pair<std::string,std::string>> INCOMPAT_SET = build_incompat();

// ═════════════════════════════════════════════════════════════════════════════
//  HELPERS
// ═════════════════════════════════════════════════════════════════════════════
bool is_compatible(const std::string& a, const std::string& b) {
    return INCOMPAT_SET.find({a, b}) == INCOMPAT_SET.end();
}

bool filter_compatible(const std::string& candidate, const std::vector<std::string>& already) {
    for (auto& f : already) {
        if (!is_compatible(candidate, f)) return false;
    }
    return true;
}

} // namespace threshold
