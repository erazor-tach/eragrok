#ifndef WORKOUT_PLANNING_H
#define WORKOUT_PLANNING_H

// Structure pour un exercice planifié
typedef struct {
    char nom[50];
    int seriesPrevues;
    int repetitionsPrevues;
    float chargePrevues;      // en kg
    int ordre;                // position dans la séance
} ExercicePlanifie;

// Structure pour une séance d'entraînement planifiée
typedef struct {
    char nomSeance[50];
    char jour[15];             // ex: "Lundi", "Mercredi", ...
    ExercicePlanifie exercices[10];
    int nbExercices;
    int dureeEstimee;          // en minutes
} SeancePlanifiee;

// Structure pour le planning hebdomadaire
typedef struct {
    SeancePlanifiee seances[7]; // une par jour maximum
    int nbSeances;
    char semaine[20];           // ex: "Semaine 12"
} PlanningHebdo;

// Initialise un planning exemple (split 4 jours)
void initPlanningExemple(PlanningHebdo *planning);

// Ajoute un exercice à une séance
void ajouterExercice(SeancePlanifiee *seance, const char *nom, int series, int reps, float charge);

// Affiche le détail d'une séance planifiée
void afficherSeancePlanifiee(const SeancePlanifiee *seance);

// Affiche le planning complet
void afficherPlanning(const PlanningHebdo *planning);

// Retourne le nombre total d'exercices dans le planning
int totalExercices(const PlanningHebdo *planning);

#endif