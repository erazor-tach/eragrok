// food_data.h — Données statiques du moteur nutritionnel THRESHOLD
// ─────────────────────────────────────────────────────────────────────────────
// Porté depuis Python meal_engine.py : FOOD_CATS, SLOT_TEMPLATES, MEAL_SLOTS,
// FOOD_INCOMPATIBLE, FOOD_SAME_FAMILY, FOOD_MIN_PORTION, FOOD_MAX_PORTION
// ─────────────────────────────────────────────────────────────────────────────
#ifndef THRESHOLD_FOOD_DATA_H
#define THRESHOLD_FOOD_DATA_H

#include <string>
#include <vector>
#include <map>
#include <set>
#include <unordered_map>
#include <unordered_set>

namespace threshold {

// Portion par défaut pour aliments non listés dans FOOD_MAX_PORTION
constexpr float FOOD_MAX_DEFAULT = 300.0f;
// Ratio skip anti-gaspillage : si besoin < 60% du minimum → skip
constexpr float FOOD_MIN_SKIP_RATIO = 0.60f;

// Catégories fonctionnelles (clé → liste de noms d'aliments)
extern const std::map<std::string, std::vector<std::string>> FOOD_CATS;

// Portions min/max par aliment
extern const std::unordered_map<std::string, float> FOOD_MIN_PORTION;
extern const std::unordered_map<std::string, float> FOOD_MAX_PORTION;

// Template d'un repas : (catégorie, mode)
// mode: "prot" = calcul grammes pour protéines cibles
//       "gluc" = calcul grammes pour glucides cibles
//       "prot_rest" = protéines restantes (optionnel, skip si trop bas)
//       entier positif = portion fixe en grammes
struct TemplateItem {
    std::string cat;
    std::string mode;  // "prot", "gluc", "prot_rest", ou ""
    int fixed_g;       // portion fixe si mode == "", sinon 0
    TemplateItem(const std::string& c, const std::string& m)
        : cat(c), mode(m), fixed_g(0) {}
    TemplateItem(const std::string& c, int g)
        : cat(c), mode(""), fixed_g(g) {}
};

using MealTemplate = std::vector<TemplateItem>;

// Templates par type de slot
extern const std::map<std::string, std::vector<MealTemplate>> SLOT_TEMPLATES;

// Description des slots
extern const std::map<std::string, std::string> SLOT_DESC;

// Structure d'un slot dans un plan repas
struct SlotDef {
    std::string name;
    std::string type;
    float ratio;
};

// Répartition des repas selon le nombre de repas/jour
extern const std::map<int, std::vector<SlotDef>> MEAL_SLOTS;

// Incompatibilités alimentaires (set symétrique pour lookup O(1))
extern const std::set<std::pair<std::string, std::string>> INCOMPAT_SET;

// Familles d'aliments (anti-répétition journalière)
extern const std::unordered_map<std::string, std::unordered_set<std::string>> FOOD_SAME_FAMILY;

// Helpers
bool is_compatible(const std::string& a, const std::string& b);
bool filter_compatible(const std::string& candidate, const std::vector<std::string>& already);

} // namespace threshold
#endif // THRESHOLD_FOOD_DATA_H
