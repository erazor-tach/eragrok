/* 
 * THRESHOLD - API CGI
 * Expose le backend C++ via Apache CGI
 */

#include <iostream>
#include <string>
#include <cstdlib>
#include "../include/utils.h"
#include "../include/db_wrapper.h"
#include "../include/meal_engine.h"
#include "../include/exercise_data.h"

using namespace threshold;

// URL decode
std::string urlDecode(const std::string& s) {
    std::string result;
    result.reserve(s.size());
    for (size_t i = 0; i < s.size(); i++) {
        if (s[i] == '%' && i + 2 < s.size()) {
            int val = 0;
            if (sscanf(s.c_str() + i + 1, "%2x", &val) == 1) {
                result += (char)val;
                i += 2;
            } else { result += s[i]; }
        } else if (s[i] == '+') { result += ' '; }
        else { result += s[i]; }
    }
    return result;
}

// Helper pour lire query string (corrigé : match exact du nom de paramètre)
std::string getQueryParam(const std::string& name) {
    const char* query = std::getenv("QUERY_STRING");
    if (!query) return "";
    
    std::string qstr(query);
    std::string needle = name + "=";
    size_t pos = 0;
    while (true) {
        pos = qstr.find(needle, pos);
        if (pos == std::string::npos) return "";
        // Vérifier que c'est le début ou après un &
        if (pos == 0 || qstr[pos - 1] == '&') {
            pos += needle.length();
            size_t end = qstr.find('&', pos);
            if (end == std::string::npos) end = qstr.length();
            return urlDecode(qstr.substr(pos, end - pos));
        }
        pos += needle.length(); // avancer pour éviter boucle infinie
    }
}

// Convertir string en float
float toFloat(const std::string& s) {
    return s.empty() ? 0.0f : std::stof(s);
}

// Convertir string en int
int toInt(const std::string& s) {
    return s.empty() ? 0 : std::stoi(s);
}

int main() {
    // Header HTTP
    std::cout << "Content-Type: application/json\r\n";
    std::cout << "Access-Control-Allow-Origin: *\r\n";
    std::cout << "\r\n";
    
    // DB paths
    std::string global_db = "/mnt/e/Projet/GIT/C/users/threshold.db";
    std::string users_dir = "/mnt/e/Projet/GIT/C/users/";
    
    // Helper: get user DB path from profile name
    auto getUserDB = [&](const std::string& name) -> std::string {
        auto gdb = DatabasePool::get(global_db);
        DatabaseMigrator::apply_migrations(*gdb, "global");
        UserProfile p = gdb->get_user(name);
        if (p.folder.empty()) p.folder = to_folder_name(name);
        std::string dir = users_dir + p.folder;
        // Create dir if needed (simple mkdir)
        system(("mkdir -p " + dir).c_str());
        std::string path = dir + "/" + p.folder + ".db";
        auto udb = DatabasePool::get(path);
        DatabaseMigrator::apply_migrations(*udb, "user");
        return path;
    };
    
    // Lire l'action demandée
    std::string action = getQueryParam("action");
    
    try {
        if (action == "tdee") {
            // Construire le profil selon la vraie structure
            UserProfile profile;
            profile.poids = toFloat(getQueryParam("poids"));
            profile.age = toInt(getQueryParam("age"));
            profile.sexe = getQueryParam("sexe");
            profile.objectif = "Maintien";  // Par défaut
            profile.taille = toFloat(getQueryParam("taille"));
            profile.ajustement = "Maintien (0%)";  // Par défaut
            
            // Calculer
            NutritionTargets targets = calcul_nutrition(profile);
            
            // Retourner JSON
            std::cout << "{\n";
            std::cout << "  \"tdee\": " << targets.tdee << ",\n";
            std::cout << "  \"calories\": " << targets.calories << ",\n";
            std::cout << "  \"proteines\": " << targets.proteines << ",\n";
            std::cout << "  \"glucides\": " << targets.glucides << ",\n";
            std::cout << "  \"lipides\": " << targets.lipides << "\n";
            std::cout << "}\n";
            
        } else if (action == "meal") {
            // Générer un plan repas depuis le profil en base
            std::string db_path = "/mnt/e/Projet/GIT/C/users/threshold.db";
            auto db = DatabasePool::get(db_path);
            DatabaseMigrator::apply_migrations(*db, "global");
            std::string name = getQueryParam("name");
            int n_repas = toInt(getQueryParam("n_repas"));
            if (n_repas < 3 || n_repas > 6) n_repas = 4;

            UserProfile p = db->get_user(name);
            if (p.nom.empty()) {
                std::cout << "{ \"error\": \"Profile not found\" }\n";
            } else {
                NutritionTargets t = calcul_nutrition(p);
                FoodCatalog catalog;
                catalog.load_default_catalog();
                MealGenerator gen(catalog);
                // Use all available foods
                auto all_foods = catalog.get_all_names();
                ConfigGeneration cfg;
                cfg.n_repas = n_repas;
                cfg.mode = "jour";
                cfg.aliments = all_foods;
                cfg.objectifs = Macros(t.calories, t.proteines, t.glucides, t.lipides);
                auto result = gen.generate_plan(cfg);

                std::cout << "{\n";
                std::cout << "  \"success\": " << (result.succes ? "true" : "false") << ",\n";
                if (result.succes) {
                    auto& pj = result.plan_jour;
                    std::cout << "  \"totaux\": {\"kcal\":" << pj.totaux_jour.kcal
                              << ",\"prot\":" << pj.totaux_jour.proteines
                              << ",\"gluc\":" << pj.totaux_jour.glucides
                              << ",\"lip\":" << pj.totaux_jour.lipides << "},\n";
                    std::cout << "  \"cibles\": {\"kcal\":" << t.calories
                              << ",\"prot\":" << t.proteines
                              << ",\"gluc\":" << t.glucides
                              << ",\"lip\":" << t.lipides << "},\n";
                    std::cout << "  \"repas\": [\n";
                    for (size_t r = 0; r < pj.repas.size(); r++) {
                        auto& rep = pj.repas[r];
                        std::cout << "    {\"nom\":\"" << json_escape(rep.nom)
                                  << "\",\"type\":\"" << json_escape(rep.type)
                                  << "\",\"items\":[\n";
                        for (size_t j = 0; j < rep.items.size(); j++) {
                            auto& it = rep.items[j];
                            std::cout << "      {\"food\":\"" << json_escape(it.nom)
                                      << "\",\"g\":" << it.grammes
                                      << ",\"kcal\":" << it.macros_portion.kcal
                                      << ",\"prot\":" << it.macros_portion.proteines
                                      << ",\"gluc\":" << it.macros_portion.glucides
                                      << ",\"lip\":" << it.macros_portion.lipides << "}";
                            if (j + 1 < rep.items.size()) std::cout << ",";
                            std::cout << "\n";
                        }
                        std::cout << "    ]}";
                        if (r + 1 < pj.repas.size()) std::cout << ",";
                        std::cout << "\n";
                    }
                    std::cout << "  ]\n";
                } else {
                    std::cout << "  \"error\": \"" << json_escape(result.erreur) << "\"\n";
                }
                std::cout << "}\n";
            }

            
        } else if (action == "profile_get") {
            std::string db_path = "/mnt/e/Projet/GIT/C/users/threshold.db";
            auto db = DatabasePool::get(db_path);
            DatabaseMigrator::apply_migrations(*db, "global");
            std::string name = getQueryParam("name");
            UserProfile p = db->get_user(name);
            
            std::cout << "{\n";
            std::cout << "  \"nom\": \"" << json_escape(p.nom) << "\",\n";
            std::cout << "  \"age\": " << p.age << ",\n";
            std::cout << "  \"sexe\": \"" << json_escape(p.sexe) << "\",\n";
            std::cout << "  \"taille\": " << p.taille << ",\n";
            std::cout << "  \"poids\": " << p.poids << ",\n";
            std::cout << "  \"objectif\": \"" << json_escape(p.objectif) << "\",\n";
            std::cout << "  \"ajustement\": \"" << json_escape(p.ajustement) << "\",\n";
            std::cout << "  \"date_naissance\": \"" << json_escape(p.date_naissance) << "\",\n";
            std::cout << "  \"folder\": \"" << json_escape(p.folder) << "\"\n";
            std::cout << "}\n";

        } else if (action == "profile_list") {
            std::string db_path = "/mnt/e/Projet/GIT/C/users/threshold.db";
            auto db = DatabasePool::get(db_path);
            DatabaseMigrator::apply_migrations(*db, "global");
            auto users = db->list_users();
            
            std::cout << "{ \"users\": [";
            for (size_t i = 0; i < users.size(); i++) {
                if (i > 0) std::cout << ",";
                std::cout << "\"" << json_escape(users[i]) << "\"";
            }
            std::cout << "] }\n";

        } else if (action == "profile_add") {
            std::string db_path = "/mnt/e/Projet/GIT/C/users/threshold.db";
            auto db = DatabasePool::get(db_path);
            DatabaseMigrator::apply_migrations(*db, "global");
            
            UserProfile p;
            p.nom             = getQueryParam("nom");
            p.date_naissance  = getQueryParam("date_naissance");
            p.sexe            = getQueryParam("sexe");
            p.taille          = toFloat(getQueryParam("taille"));
            p.poids           = toFloat(getQueryParam("poids"));
            p.ajustement      = getQueryParam("ajustement");
            if (p.ajustement.empty()) p.ajustement = "Maintien (0%)";
            p.objectif        = ajustement_to_objectif(p.ajustement);
            p.age             = age_depuis_naissance(p.date_naissance);
            
            bool ok = db->add_user(p);
            std::cout << "{ \"success\": " << (ok ? "true" : "false") << " }\n";

        } else if (action == "profile_update") {
            std::string db_path = "/mnt/e/Projet/GIT/C/users/threshold.db";
            auto db = DatabasePool::get(db_path);
            DatabaseMigrator::apply_migrations(*db, "global");
            
            std::string old_name = getQueryParam("old_name");
            UserProfile p;
            p.nom             = getQueryParam("nom");
            p.date_naissance  = getQueryParam("date_naissance");
            p.sexe            = getQueryParam("sexe");
            p.taille          = toFloat(getQueryParam("taille"));
            p.poids           = toFloat(getQueryParam("poids"));
            p.ajustement      = getQueryParam("ajustement");
            if (p.ajustement.empty()) p.ajustement = "Maintien (0%)";
            p.objectif        = ajustement_to_objectif(p.ajustement);
            p.age             = age_depuis_naissance(p.date_naissance);
            if (old_name.empty()) old_name = p.nom;
            
            bool ok = db->update_user(old_name, p);
            if (ok) {
                UserProfile updated = db->get_user(p.nom);
                std::cout << "{\n  \"success\": true,\n";
                std::cout << "  \"nom\": \"" << json_escape(updated.nom) << "\",\n";
                std::cout << "  \"age\": " << updated.age << ",\n";
                std::cout << "  \"taille\": " << updated.taille << ",\n";
                std::cout << "  \"poids\": " << updated.poids << ",\n";
                std::cout << "  \"objectif\": \"" << json_escape(updated.objectif) << "\",\n";
                std::cout << "  \"ajustement\": \"" << json_escape(updated.ajustement) << "\"\n}\n";
            } else {
                std::cout << "{ \"success\": false, \"error\": \"Update failed\" }\n";
            }


        } else if (action == "food_list") {
            FoodCatalog catalog;
            catalog.load_default_catalog();
            auto categories = catalog.get_category_names();
            
            std::cout << "{ \"total\": " << catalog.size() << ", \"categories\": {\n";
            for (size_t c = 0; c < categories.size(); c++) {
                auto foods = catalog.get_category(categories[c]);
                std::cout << "  \"" << json_escape(categories[c]) << "\": [\n";
                for (size_t i = 0; i < foods.size(); i++) {
                    const FoodData* f = catalog.get(foods[i]);
                    if (!f) continue;
                    std::cout << "    {\"nom\":\"" << json_escape(foods[i])
                              << "\",\"kcal\":" << f->kcal_100g
                              << ",\"prot\":" << f->prot_100g
                              << ",\"gluc\":" << f->gluc_100g
                              << ",\"lip\":" << f->lip_100g
                              << ",\"fibres\":" << f->fibres_100g << "}";
                    if (i + 1 < foods.size()) std::cout << ",";
                    std::cout << "\n";
                }
                std::cout << "  ]";
                if (c + 1 < categories.size()) std::cout << ",";
                std::cout << "\n";
            }
            std::cout << "} }\n";

        } else if (action == "tdee_from_profile") {
            std::string db_path = "/mnt/e/Projet/GIT/C/users/threshold.db";
            auto db = DatabasePool::get(db_path);
            DatabaseMigrator::apply_migrations(*db, "global");
            std::string name = getQueryParam("name");
            UserProfile p = db->get_user(name);
            
            if (p.nom.empty()) {
                std::cout << "{ \"error\": \"Profile not found\" }\n";
            } else {
                NutritionTargets t = calcul_nutrition(p);
                std::cout << "{\n";
                std::cout << "  \"nom\": \"" << json_escape(p.nom) << "\",\n";
                std::cout << "  \"tdee\": " << t.tdee << ",\n";
                std::cout << "  \"calories\": " << t.calories << ",\n";
                std::cout << "  \"proteines\": " << t.proteines << ",\n";
                std::cout << "  \"glucides\": " << t.glucides << ",\n";
                std::cout << "  \"lipides\": " << t.lipides << "\n";
                std::cout << "}\n";
            }

        } else if (action == "exercise_list") {
            std::cout << "{ \"total\": " << EXERCICES.size() << ", \"categories\": {\n";
            bool first_cat = true;
            for (auto& [cat, label] : CAT_LABELS) {
                auto exos = get_exercises_by_cat(cat);
                if (exos.empty()) continue;
                if (!first_cat) std::cout << ",\n";
                first_cat = false;
                std::cout << "  \"" << json_escape(cat) << "\": {\"label\":\"" << json_escape(label) << "\",\"exercices\":[\n";
                for (size_t i = 0; i < exos.size(); i++) {
                    auto* e = exos[i];
                    std::cout << "    {\"id\":\"" << json_escape(e->id)
                              << "\",\"nom\":\"" << json_escape(e->nom)
                              << "\",\"faisceau\":\"" << json_escape(e->faisceau)
                              << "\",\"equipement\":\"" << json_escape(e->equipement)
                              << "\",\"difficulte\":" << e->difficulte
                              << ",\"reps\":\"" << json_escape(e->reps)
                              << "\",\"muscles_secondaires\":\"" << json_escape(e->muscles_secondaires)
                              << "\",\"notes\":\"" << json_escape(e->notes) << "\"}";
                    if (i + 1 < exos.size()) std::cout << ",";
                    std::cout << "\n";
                }
                std::cout << "  ]}";
            }
            std::cout << "\n} }\n";

        } else if (action == "technique_list") {
            std::cout << "{ \"total\": " << TECHNIQUES.size() << ", \"techniques\": [\n";
            for (size_t i = 0; i < TECHNIQUES.size(); i++) {
                auto& t = TECHNIQUES[i];
                std::cout << "  {\"id\":\"" << json_escape(t.id)
                          << "\",\"nom\":\"" << json_escape(t.nom)
                          << "\",\"categorie\":\"" << json_escape(t.categorie)
                          << "\",\"reps\":\"" << json_escape(t.reps)
                          << "\",\"charge\":\"" << json_escape(t.charge)
                          << "\",\"repos\":\"" << json_escape(t.repos)
                          << "\",\"objectif\":\"" << json_escape(t.objectif)
                          << "\",\"difficulte\":" << t.difficulte
                          << ",\"programme\":\"" << json_escape(t.programme_recommande)
                          << "\",\"notes\":\"" << json_escape(t.notes) << "\"}";
                if (i + 1 < TECHNIQUES.size()) std::cout << ",";
                std::cout << "\n";
            }
            std::cout << "] }\n";

        } else if (action == "planning_add") {
            std::string name = getQueryParam("name");
            std::string udb_path = getUserDB(name);
            auto udb = DatabasePool::get(udb_path);
            
            std::string date = getQueryParam("date");
            std::string groupes = getQueryParam("groupes");
            std::string programme = getQueryParam("programme");
            std::string types = getQueryParam("types");
            std::string note = getQueryParam("note");
            std::string line = getQueryParam("line");
            std::string exercises = getQueryParam("exercises");
            if (exercises.empty()) exercises = "[]";
            
            bool ok = udb->add_planning(date, groupes, programme, types, note, line, exercises);
            std::cout << "{ \"success\": " << (ok ? "true" : "false") << " }\n";

        } else if (action == "planning_today") {
            std::string name = getQueryParam("name");
            std::string udb_path = getUserDB(name);
            auto udb = DatabasePool::get(udb_path);
            
            std::string today = date_iso_today();
            // Planning uses DD/MM/YYYY format (like Python)
            std::string today_fr = today.substr(8,2) + "/" + today.substr(5,2) + "/" + today.substr(0,4);
            auto entries = udb->get_planning_by_date(today_fr);
            
            std::cout << "{ \"date\": \"" << json_escape(today_fr) << "\", \"entries\": [\n";
            for (size_t i = 0; i < entries.size(); i++) {
                auto& e = entries[i];
                std::cout << "  {\"id\":" << e.id
                          << ",\"date\":\"" << json_escape(e.date)
                          << "\",\"groupes\":\"" << json_escape(e.groupes)
                          << "\",\"programme\":\"" << json_escape(e.programme)
                          << "\",\"types\":\"" << json_escape(e.types)
                          << "\",\"note\":\"" << json_escape(e.note)
                          << "\",\"line\":\"" << json_escape(e.line)
                          << "\",\"exercises\":" << (e.exercises.empty() ? "[]" : e.exercises)
                          << "}";
                if (i + 1 < entries.size()) std::cout << ",";
                std::cout << "\n";
            }
            std::cout << "] }\n";

        } else if (action == "planning_range") {
            std::string name = getQueryParam("name");
            std::string udb_path = getUserDB(name);
            auto udb = DatabasePool::get(udb_path);
            
            std::string start = getQueryParam("start");
            std::string end = getQueryParam("end");
            auto entries = udb->get_planning_range(start, end);
            
            std::cout << "{ \"start\": \"" << json_escape(start) << "\", \"end\": \"" << json_escape(end) << "\", \"entries\": [\n";
            for (size_t i = 0; i < entries.size(); i++) {
                auto& e = entries[i];
                std::cout << "  {\"id\":" << e.id
                          << ",\"date\":\"" << json_escape(e.date)
                          << "\",\"groupes\":\"" << json_escape(e.groupes)
                          << "\",\"programme\":\"" << json_escape(e.programme)
                          << "\",\"exercises\":" << (e.exercises.empty() ? "[]" : e.exercises)
                          << "}";
                if (i + 1 < entries.size()) std::cout << ",";
                std::cout << "\n";
            }
            std::cout << "] }\n";

        } else {
            // Action inconnue
            std::cout << "{\n";
            std::cout << "  \"error\": \"Unknown action: " << action << "\"\n";
            std::cout << "}\n";
        }
        
    } catch (const std::exception& e) {
        std::cout << "{\n";
        std::cout << "  \"error\": \"" << e.what() << "\"\n";
        std::cout << "}\n";
    }
    
    return 0;
}
