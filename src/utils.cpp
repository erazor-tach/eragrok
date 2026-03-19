// utils.cpp — Implémentation utilitaires
// ─────────────────────────────────────────────────────────────────────────────
#include "utils.h"
#include <sstream>
#include <iomanip>
#include <cmath>

namespace threshold {

// ═════════════════════════════════════════════════════════════════════════════
//  ADJUSTMENTS (porté depuis Python utils.ADJUSTMENTS)
// ═════════════════════════════════════════════════════════════════════════════

const std::map<std::string, float> ADJUSTMENTS = {
    {"Déficit léger (-10 à -15%)",       -0.125f},
    {"Déficit modéré (-15 à -25%)",      -0.20f},
    {"Maintien (0%)",                     0.0f},
    {"Surplus léger (lean) (+5 à +10%)", 0.075f},
    {"Surplus standard (+10 à +15%)",    0.125f},
    {"Surplus agressif (+15 à +20%)",    0.175f},
};

// ═════════════════════════════════════════════════════════════════════════════
//  CALCULS NUTRITION
// ═════════════════════════════════════════════════════════════════════════════

NutritionTargets calcul_nutrition(const UserProfile& profil) {
    NutritionTargets result;
    
    // MB (métabolisme de base) — Formule de Harris-Benedict
    float mb;
    if (profil.sexe == "Homme" || profil.sexe == "M") {
        mb = 88.362f + (13.397f * profil.poids) + (4.799f * profil.taille)
             - (5.677f * profil.age);
    } else {
        mb = 447.593f + (9.247f * profil.poids) + (3.098f * profil.taille)
             - (4.330f * profil.age);
    }
    
    // TDEE (activité moyenne — facteur 1.55)
    result.tdee = mb * 1.55f;
    
    // Ajustement depuis la table ADJUSTMENTS
    float adj = 0.0f;
    auto it = ADJUSTMENTS.find(profil.ajustement);
    if (it != ADJUSTMENTS.end()) {
        adj = it->second;
    }
    result.calories = result.tdee * (1.0f + adj);
    
    // Protéines : 2.3g/kg (comme Python)
    result.proteines = profil.poids * 2.3f;
    
    // Répartition glucides/lipides selon objectif
    float coef_g = 0.45f, coef_l = 0.25f;
    if (profil.objectif == "Gain de masse") {
        coef_g = 0.47f; coef_l = 0.23f;
    } else if (profil.objectif == "Perte de poids") {
        coef_g = 0.37f; coef_l = 0.23f;
    }
    
    result.glucides = (result.calories * coef_g) / 4.0f;
    result.lipides = (result.calories * coef_l) / 9.0f;
    
    return result;
}

// ═════════════════════════════════════════════════════════════════════════════
//  DATES
// ═════════════════════════════════════════════════════════════════════════════

std::string date_iso_today() {
    auto now = std::chrono::system_clock::now();
    auto time_t = std::chrono::system_clock::to_time_t(now);
    std::tm tm;
    #ifdef _WIN32
        localtime_s(&tm, &time_t);
    #else
        localtime_r(&time_t, &tm);
    #endif
    
    std::ostringstream oss;
    oss << std::put_time(&tm, "%Y-%m-%d");
    return oss.str();
}

std::string date_add_days(const std::string& iso, int days) {
    // TODO: Parsing ISO + addition jours (chrono)
    // Pour le squelette : retour simple
    return iso;
}

float parse_float(const std::string& s, float default_val) {
    try {
        return std::stof(s);
    } catch (...) {
        return default_val;
    }
}

int parse_int(const std::string& s, int default_val) {
    try {
        return std::stoi(s);
    } catch (...) {
        return default_val;
    }
}

// Méthodes des structures (inline dans types — juste pour compilation)

// ═════════════════════════════════════════════════════════════════════════════
//  HELPERS PROFIL
// ═════════════════════════════════════════════════════════════════════════════

std::string to_folder_name(const std::string& display_name) {
    std::string result;
    for (char c : display_name) {
        if (c == ' ') result += '_';
        else result += (char)std::tolower((unsigned char)c);
    }
    // trim
    while (!result.empty() && result.back() == '_') result.pop_back();
    while (!result.empty() && result.front() == '_') result.erase(result.begin());
    return result;
}

int age_depuis_naissance(const std::string& date_naissance) {
    // Format attendu : "JJ/MM/AAAA"
    if (date_naissance.size() < 10 || date_naissance[2] != '/' || date_naissance[5] != '/')
        return 0;
    int jour  = parse_int(date_naissance.substr(0, 2));
    int mois  = parse_int(date_naissance.substr(3, 2));
    int annee = parse_int(date_naissance.substr(6, 4));
    if (annee <= 0 || mois <= 0 || jour <= 0) return 0;

    auto now = std::chrono::system_clock::now();
    auto tt = std::chrono::system_clock::to_time_t(now);
    std::tm tm;
    #ifdef _WIN32
        localtime_s(&tm, &tt);
    #else
        localtime_r(&tt, &tm);
    #endif
    int y = tm.tm_year + 1900;
    int m = tm.tm_mon + 1;
    int d = tm.tm_mday;

    int age = y - annee;
    if (m < mois || (m == mois && d < jour)) age--;
    return (age >= 0) ? age : 0;
}

std::string ajustement_to_objectif(const std::string& ajustement) {
    if (ajustement.find("ficit") != std::string::npos) return "Perte de poids";
    if (ajustement.find("urplus") != std::string::npos) return "Gain de masse";
    return "Maintien";
}

// ═════════════════════════════════════════════════════════════════════════════
//  JSON HELPERS
// ═════════════════════════════════════════════════════════════════════════════

std::string json_escape(const std::string& s) {
    std::string result;
    result.reserve(s.size() + 8);
    for (char c : s) {
        switch (c) {
            case '"':  result += "\\\""; break;
            case '\\': result += "\\\\"; break;
            case '\'': result += "''";   break;  // SQL escape
            case '\n': result += "\\n";  break;
            case '\r': result += "\\r";  break;
            case '\t': result += "\\t";  break;
            default:   result += c;
        }
    }
    return result;
}
} // namespace threshold
