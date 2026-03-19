// meal_engine.h — Moteur génération plans alimentaires THRESHOLD
// ─────────────────────────────────────────────────────────────────────────────
// Port C++ du générateur Python meal_engine.py + meal_generator.py
// Algorithme 7 passes + anti-gaspillage + budget
// ─────────────────────────────────────────────────────────────────────────────
#ifndef THRESHOLD_MEAL_ENGINE_H
#define THRESHOLD_MEAL_ENGINE_H

#include "threshold_types.h"
#include "db_wrapper.h"
#include "food_data.h"
#include <random>
#include <set>
#include <unordered_map>

namespace threshold {

// ═════════════════════════════════════════════════════════════════════════════
//  CATALOGUE ALIMENTS (port de FOOD_DB_EXT)
// ═════════════════════════════════════════════════════════════════════════════

struct FoodData {
    float kcal_100g;
    float prot_100g;
    float gluc_100g;
    float lip_100g;
    float fibres_100g;
    std::string categorie;      // "proteine_maigre", "glucide_matin"...
    std::vector<std::string> incompatibilites; // Aliments à séparer
    float portion_min;          // Grammes minimum (anti-gaspillage)
    float portion_max;          // Grammes maximum
    float cooked_to_raw;        // Coefficient cuisson (pâtes 2.5, etc.)
};

// Catalogue global (chargé au démarrage)
class FoodCatalog {
private:
    std::unordered_map<std::string, FoodData> catalog_;
    std::unordered_map<std::string, std::vector<std::string>> categories_;
    
    void add(const std::string& nom, const std::string& cat,
             float kcal, float prot, float gluc, float lip, float fib,
             float pmin = 50, float pmax = 300, float cook = 1.0f);
    
public:
    void load_default_catalog();  // Charge FOOD_DB_EXT
    void add_custom_food(const std::string& nom, const FoodData& data);
    
    const FoodData* get(const std::string& nom) const;
    std::vector<std::string> get_category(const std::string& cat) const;
    std::vector<std::string> get_category_names() const;
    std::vector<std::string> get_all_names() const;
    size_t size() const { return catalog_.size(); }
    bool exists(const std::string& nom) const;
};

// ═════════════════════════════════════════════════════════════════════════════
//  MOTEUR GÉNÉRATION (port de _generate_meal_plan)
// ═════════════════════════════════════════════════════════════════════════════

class MealGenerator {
private:
    const FoodCatalog& catalog_;
    std::mt19937 rng_;
    
    // Helpers internes (7 passes)
    Repas generate_repas(const std::string& type, int pass_number,
                         const std::vector<std::string>& available,
                         const Macros& targets_repas,
                         const std::set<std::string>& used_incompatibles);
    
    void apply_budget_pass(PlanJournalier& plan,
                          const std::vector<std::string>& available,
                          float budget_day,
                          DatabaseConnection& db);
    
    float compute_diversity_score(const PlanMultiJours& plan);
    
public:
    MealGenerator(const FoodCatalog& catalog);
    
    // API publique
    ResultatGeneration generate_plan(const ConfigGeneration& config,
                                     DatabaseConnection* db = nullptr);
    
    PlanJournalier generate_day(int n_repas,
                                const std::vector<std::string>& available,
                                const Macros& targets,
                                int day_offset = 0);
    
    PlanMultiJours generate_multiday(int n_days, int n_repas,
                                     const std::vector<std::string>& available,
                                     const Macros& targets,
                                     const std::string& start_date);
};

} // namespace threshold

#endif // THRESHOLD_MEAL_ENGINE_H
