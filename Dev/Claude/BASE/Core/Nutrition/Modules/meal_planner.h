#ifndef MEAL_PLANNER_H
#define MEAL_PLANNER_H

// Structure pour un aliment de base
typedef struct {
    char nom[50];
    float calories;      // pour 100g
    float proteines;
    float glucides;
    float lipides;
} AlimentBase;

// Structure pour un repas (composé d'aliments avec quantités)
typedef struct {
    char nom[30];                 // ex: "Petit-déjeuner"
    AlimentBase aliments[10];
    float quantites[10];          // en grammes pour chaque aliment
    int nbAliments;
    float totalCalories;
    float totalProteines;
    float totalGlucides;
    float totalLipides;
} RepasPlan;

// Structure pour un plan journalier
typedef struct {
    RepasPlan repas[6];           // max 6 repas par jour
    int nbRepas;
    float totalCalories;
    float totalProteines;
    float totalGlucides;
    float totalLipides;
} PlanJour;

// Structure pour un plan hebdomadaire
typedef struct {
    PlanJour jours[7];
    int nbJours;
} PlanSemaine;

// Objectifs nutritionnels
typedef struct {
    float caloriesCible;
    float proteinesCible; // en grammes
    float glucidesCible;
    float lipidesCible;
} ObjectifsNutrition;

// Initialise la base d'aliments (liste prédéfinie)
void initBaseAliments(AlimentBase base[], int *nbAliments);

// Calcule les besoins caloriques de base (formule de Mifflin-St Jeor)
float calculerBMR(float poids, float taille, int age, int sexe); // sexe: 0 = femme, 1 = homme

// Calcule les objectifs en fonction du poids, taille, âge, sexe et objectif
ObjectifsNutrition calculerObjectifs(float poids, float taille, int age, int sexe, const char *objectif);

// Génère un plan journalier à partir des objectifs
void genererPlanJour(PlanJour *plan, const ObjectifsNutrition *obj, const AlimentBase base[], int nbAliments);

// Affiche un plan journalier
void afficherPlanJour(const PlanJour *plan);

// Affiche un plan hebdomadaire (simplement les totaux par jour)
void afficherPlanSemaine(const PlanSemaine *semaine);

#endif