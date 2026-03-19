// threshold_types.h — Types fondamentaux THRESHOLD C++/JNI
// ─────────────────────────────────────────────────────────────────────────────
// Port C++ de l'architecture Python THRESHOLD
// Compatible Android NDK r25+ / C++17
// ─────────────────────────────────────────────────────────────────────────────
#ifndef THRESHOLD_TYPES_H
#define THRESHOLD_TYPES_H

#include <string>
#include <vector>
#include <map>
#include <memory>
#include <cstdint>

namespace threshold {

// ═════════════════════════════════════════════════════════════════════════════
//  STRUCTURES DONNÉES NUTRITION
// ═════════════════════════════════════════════════════════════════════════════

struct Macros {
    float kcal;      // Calories totales
    float proteines; // Protéines (g)
    float glucides;  // Glucides (g)
    float lipides;   // Lipides (g)
    float fibres;    // Fibres (g) - optionnel
    
    Macros() : kcal(0), proteines(0), glucides(0), lipides(0), fibres(0) {}
    Macros(float k, float p, float g, float l, float f = 0)
        : kcal(k), proteines(p), glucides(g), lipides(l), fibres(f) {}
};

struct FoodItem {
    std::string nom;         // Nom de l'aliment
    float grammes;           // Quantité (g)
    Macros macros_100g;      // Macros pour 100g
    Macros macros_portion;   // Macros calculées pour la portion
    std::string categorie;   // Catégorie (glucide_matin, proteine_maigre...)
    
    FoodItem() : grammes(0) {}
};

struct Repas {
    std::string nom;              // "Petit-déjeuner", "Déjeuner"...
    std::string type;             // "matin", "midi", "collation", "soir", "coucher"
    std::vector<FoodItem> items;  // Liste d'aliments
    Macros totaux;                // Somme des macros
    
    void calculer_totaux();       // Recalcule les macros totaux
};

struct PlanJournalier {
    std::string date;             // Format ISO "YYYY-MM-DD"
    std::string label;            // "Lundi 16/03" affichage
    std::vector<Repas> repas;     // Liste des repas (3 à 6)
    Macros totaux_jour;           // Somme quotidienne
    float cout_estime;            // Coût estimé (€)
    
    void calculer_totaux();
};

struct PlanMultiJours {
    std::vector<PlanJournalier> jours;  // 7j (semaine) ou 30j (mois)
    std::string mode;                   // "semaine", "mois"
    int n_repas;                        // Nombre de repas/jour
    Macros objectifs_moyens;            // Objectifs quotidiens moyens
    float budget_semaine;               // Budget hebdomadaire (€)
    
    void calculer_moyennes();           // Recalcule moyennes sur tous les jours
};

// ═════════════════════════════════════════════════════════════════════════════
//  CONFIGURATION GÉNÉRATION
// ═════════════════════════════════════════════════════════════════════════════

struct ConfigGeneration {
    int n_repas;                        // 3 à 6 repas/jour
    std::string mode;                   // "jour", "semaine", "mois"
    std::vector<std::string> aliments;  // Liste aliments disponibles
    std::vector<std::string> blacklist; // Aliments exclus
    Macros objectifs;                   // Macros cibles
    float budget_semaine;               // Budget optionnel (0 = illimité)
    std::string date_debut;             // Date départ (ISO)
    
    ConfigGeneration() : n_repas(4), mode("jour"), budget_semaine(0) {}
};

// ═════════════════════════════════════════════════════════════════════════════
//  RÉSULTAT GÉNÉRATION
// ═════════════════════════════════════════════════════════════════════════════

struct ResultatGeneration {
    bool succes;                        // Génération réussie ?
    std::string erreur;                 // Message d'erreur si échec
    PlanJournalier plan_jour;           // Si mode = "jour"
    PlanMultiJours plan_multi;          // Si mode = "semaine" ou "mois"
    float score_diversite;              // 0-100%
    std::string rating_diversite;       // "excellent", "bon", "moyen", "faible"
    
    ResultatGeneration() : succes(false), score_diversite(0) {}
};

// ═════════════════════════════════════════════════════════════════════════════
//  DONNÉES DB
// ═════════════════════════════════════════════════════════════════════════════

struct NutritionEntry {
    int64_t id;
    std::string date;        // "DD/MM/YYYY"
    float poids;
    int age;
    Macros macros;
    std::string note;
};

struct CycleEntry {
    int64_t id;
    std::string debut;       // "DD/MM/YYYY"
    std::string fin_estimee;
    int longueur_sem;
    std::string produits_doses; // JSON
    std::string note;
    std::string end_mode;       // "PCT", "TRT", "Cruise"
    std::string days_2x_config; // JSON
};

struct PlanningEntry {
    int64_t id;
    std::string date;           // "DD/MM/YYYY"
    std::string groupes;
    std::string programme;
    std::string types;
    std::string note;
    std::string line;
    std::string exercises;      // JSON
};

} // namespace threshold

#endif // THRESHOLD_TYPES_H
