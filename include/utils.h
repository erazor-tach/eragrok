// utils.h — Fonctions utilitaires THRESHOLD
// ─────────────────────────────────────────────────────────────────────────────
// Calculs macros, dates, conversions
// ─────────────────────────────────────────────────────────────────────────────
#ifndef THRESHOLD_UTILS_H
#define THRESHOLD_UTILS_H

#include "threshold_types.h"
#include <chrono>
#include <ctime>

namespace threshold {

// ═════════════════════════════════════════════════════════════════════════════
//  CALCULS NUTRITION
// ═════════════════════════════════════════════════════════════════════════════

struct UserProfile {
    std::string nom;            // Nom complet (ex: "Erazor")
    float poids;                // kg
    int age;                    // années (calculé depuis date_naissance)
    std::string sexe;           // "Homme" ou "Femme"
    std::string objectif;       // "Gain de masse", "Perte de poids", "Maintien"
    float taille;               // cm
    std::string ajustement;     // Clé ADJUSTMENTS (ex: "Maintien (0%)")
    std::string date_naissance; // "JJ/MM/AAAA"
    std::string folder;         // nom en minuscule, espaces → underscores

    UserProfile() : poids(0), age(0), taille(0) {}
};

// Table des ajustements caloriques (portée depuis Python utils.ADJUSTMENTS)
extern const std::map<std::string, float> ADJUSTMENTS;

struct NutritionTargets {
    float tdee;       // Dépense énergétique totale
    float calories;   // Calories ajustées
    float proteines;  // g
    float glucides;   // g
    float lipides;    // g
};

NutritionTargets calcul_nutrition(const UserProfile& profil);

// Helpers profil
std::string to_folder_name(const std::string& display_name);
int age_depuis_naissance(const std::string& date_naissance); // "JJ/MM/AAAA" → âge
std::string ajustement_to_objectif(const std::string& ajustement);

// ═════════════════════════════════════════════════════════════════════════════
//  DATES
// ═════════════════════════════════════════════════════════════════════════════

std::string date_iso_today();                          // "2026-03-16"
std::string date_format_fr(const std::string& iso);    // "16/03/2026"
std::string date_add_days(const std::string& iso, int days);
int date_weekday(const std::string& iso);              // 0=lundi, 6=dimanche

// ═════════════════════════════════════════════════════════════════════════════
//  CONVERSIONS
// ═════════════════════════════════════════════════════════════════════════════

float parse_float(const std::string& s, float default_val = 0.0f);
int parse_int(const std::string& s, int default_val = 0);

// ═════════════════════════════════════════════════════════════════════════════
//  JSON HELPERS (simple — pas de lib externe pour le squelette)
// ═════════════════════════════════════════════════════════════════════════════

std::string json_escape(const std::string& s);
std::string macros_to_json(const Macros& m);
std::string plan_to_json(const PlanJournalier& plan);
std::string multiday_to_json(const PlanMultiJours& plan);

} // namespace threshold

#endif // THRESHOLD_UTILS_H
