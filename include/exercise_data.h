// exercise_data.h — Catalogue exercices et techniques THRESHOLD
// Porté depuis Python exercices_catalogue.py + training_techniques.py
#ifndef THRESHOLD_EXERCISE_DATA_H
#define THRESHOLD_EXERCISE_DATA_H

#include <string>
#include <vector>
#include <map>

namespace threshold {

struct Exercise {
    std::string id;
    std::string nom;
    std::string cat;        // PECS, DOS, EPAULES, BICEPS, TRICEPS, ABDOS, QUADRICEPS, FESSIERS, ISCHIO, MOLLETS, FULL_BODY
    std::string faisceau;
    std::string equipement;
    int difficulte;         // 1-5
    std::string reps;
    std::string muscles_secondaires;
    std::string notes;
};

struct Technique {
    std::string id;
    std::string nom;
    std::string categorie;  // SARCOPLASMIQUE, MIXTE, MYOFIBRILLAIRE
    std::string reps;
    std::string charge;
    std::string repos;
    std::string objectif;
    int difficulte;
    int difficulty_level;
    std::string programme_recommande;
    std::string notes;
};

// Catégories et labels
extern const std::map<std::string, std::string> CAT_LABELS;
extern const std::map<std::string, std::string> CAT_ICONS;
extern const std::map<std::string, int> DIFF_LABELS; // 1-5

// Données
extern const std::vector<Exercise> EXERCICES;
extern const std::vector<Technique> TECHNIQUES;

// Helpers
std::vector<const Exercise*> get_exercises_by_cat(const std::string& cat);
std::vector<const Exercise*> get_exercises_by_equipement(const std::string& equip);
const Exercise* get_exercise_by_id(const std::string& id);
std::vector<const Technique*> get_techniques_by_categorie(const std::string& cat);

} // namespace threshold
#endif
