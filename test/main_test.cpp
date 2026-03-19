// main_test.cpp — Programme test THRESHOLD (sans JNI)
// ─────────────────────────────────────────────────────────────────────────────
// Compilation : build.sh → threshold_test
// Exécution : build/threshold_test
// ─────────────────────────────────────────────────────────────────────────────
#include "threshold_types.h"
#include "db_wrapper.h"
#include "meal_engine.h"
#include "utils.h"

#include <iostream>
#include <iomanip>

using namespace threshold;

// ═════════════════════════════════════════════════════════════════════════════
//  AFFICHAGE RÉSULTATS
// ═════════════════════════════════════════════════════════════════════════════

void afficher_macros(const Macros& m) {
    std::cout << "  🔥 Calories : " << std::fixed << std::setprecision(0) << m.kcal << " kcal\n";
    std::cout << "  🥩 Protéines: " << m.proteines << " g\n";
    std::cout << "  🍚 Glucides : " << m.glucides << " g\n";
    std::cout << "  🥑 Lipides  : " << m.lipides << " g\n";
    if (m.fibres > 0.1f) {
        std::cout << "  🌾 Fibres   : " << m.fibres << " g\n";
    }
}

void afficher_repas(const Repas& r) {
    std::cout << "\n  📋 " << r.nom << " (" << r.type << ")\n";
    std::cout << "  ───────────────────────────────────────\n";
    
    for (const auto& item : r.items) {
        std::cout << "    • " << item.nom << " — " << item.grammes << "g\n";
        std::cout << "      → " << item.macros_portion.kcal << " kcal | "
             << item.macros_portion.proteines << "P "
             << item.macros_portion.glucides << "G "
             << item.macros_portion.lipides << "L\n";
    }
    
    std::cout << "  ───────────────────────────────────────\n";
    afficher_macros(r.totaux);
}

void afficher_plan(const PlanJournalier& plan) {
    std::cout << "\n═══════════════════════════════════════════════════════════════════\n";
    std::cout << "  📅 PLAN JOURNALIER — " << plan.label << "\n";
    std::cout << "═══════════════════════════════════════════════════════════════════\n";
    
    for (const auto& repas : plan.repas) {
        afficher_repas(repas);
    }
    
    std::cout << "\n  ╔════════════════════════════════════════════════════════════╗\n";
    std::cout << "  ║ TOTAUX JOUR                                                ║\n";
    std::cout << "  ╚════════════════════════════════════════════════════════════╝\n";
    afficher_macros(plan.totaux_jour);
    
    if (plan.cout_estime > 0.01f) {
        std::cout << "  💰 Coût estimé : " << std::setprecision(2) << plan.cout_estime << " €\n";
    }
    std::cout << "═══════════════════════════════════════════════════════════════════\n\n";
}

// ═════════════════════════════════════════════════════════════════════════════
//  TESTS MODULES
// ═════════════════════════════════════════════════════════════════════════════

void test_database() {
    std::cout << "\n🧪 TEST 1 : Base de données SQLite\n";
    std::cout << "──────────────────────────────────────────────────────────\n";
    
    try {
        auto db = DatabasePool::get("test_threshold.db");
        std::cout << "✅ Connexion DB établie\n";
        
        // Test settings
        db->set_setting("test_key", "test_value");
        std::string val = db->get_setting("test_key");
        std::cout << "✅ Settings : test_key = " << val << "\n";
        
        std::cout << "✅ Base de données fonctionnelle\n";
    } catch (const std::exception& e) {
        std::cout << "❌ ERREUR DB : " << e.what() << "\n";
    }
}

void test_calculs_nutrition() {
    std::cout << "\n🧪 TEST 2 : Calculs nutrition\n";
    std::cout << "──────────────────────────────────────────────────────────\n";
    
    UserProfile profil;
    profil.poids = 80.0f;
    profil.age = 30;
    profil.sexe = "M";
    profil.objectif = "Prise de masse";
    profil.taille = 180.0f;
    profil.ajustement = "+20%";
    
    NutritionTargets targets = calcul_nutrition(profil);
    
    std::cout << "  Profil : Homme, 80kg, 30 ans, 180cm\n";
    std::cout << "  Objectif : Prise de masse (+20%)\n\n";
    std::cout << "  Résultats :\n";
    std::cout << "    TDEE        : " << targets.tdee << " kcal\n";
    std::cout << "    Calories    : " << targets.calories << " kcal\n";
    std::cout << "    Protéines   : " << targets.proteines << " g\n";
    std::cout << "    Glucides    : " << targets.glucides << " g\n";
    std::cout << "    Lipides     : " << targets.lipides << " g\n";
    std::cout << "✅ Calculs nutrition OK\n";
}

void test_meal_generator() {
    std::cout << "\n🧪 TEST 3 : Générateur de plans\n";
    std::cout << "──────────────────────────────────────────────────────────\n";
    
    // Charger catalogue
    FoodCatalog catalog;
    catalog.load_default_catalog();
    std::cout << "✅ Catalogue aliments chargé\n";
    
    // Configurer génération
    ConfigGeneration config;
    config.n_repas = 4;
    config.mode = "jour";
    config.aliments = {"Œuf entier"}; // Test minimal
    config.objectifs = Macros(2500, 180, 280, 70);
    
    // Générer
    MealGenerator generator(catalog);
    ResultatGeneration result = generator.generate_plan(config);
    
    if (result.succes) {
        std::cout << "✅ Génération réussie\n";
        afficher_plan(result.plan_jour);
    } else {
        std::cout << "❌ Échec : " << result.erreur << "\n";
    }
}

// ═════════════════════════════════════════════════════════════════════════════
//  MAIN
// ═════════════════════════════════════════════════════════════════════════════

int main() {
    std::cout << R"(
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║   THRESHOLD C++ — Tests Module                                   ║
║   Version squelette 1.0                                          ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
)" << std::endl;

    try {
        test_database();
        test_calculs_nutrition();
        test_meal_generator();
        
        std::cout << "\n╔═══════════════════════════════════════════════════════════════════╗\n";
        std::cout << "║ ✅ TOUS LES TESTS PASSÉS                                         ║\n";
        std::cout << "╚═══════════════════════════════════════════════════════════════════╝\n";
        
    } catch (const std::exception& e) {
        std::cerr << "\n❌ ERREUR FATALE : " << e.what() << std::endl;
        return 1;
    }
    
    return 0;
}
