#ifndef DAILY_TARGETS_H
#define DAILY_TARGETS_H

// Structure pour les objectifs quotidiens
typedef struct {
    float caloriesCible;
    float proteinesCible;  // grammes
    float glucidesCible;
    float lipidesCible;
    float eauCible;        // litres
} DailyTargets;

// Structure pour les consommations en cours
typedef struct {
    float calories;
    float proteines;
    float glucides;
    float lipides;
    float eau;             // litres
} DailyIntake;

// Structure pour l'état du jour
typedef struct {
    DailyTargets objectifs;
    DailyIntake consomme;
    // Optionnel : on pourrait stocker les repas de la journée
} DailyProgress;

// Initialise les objectifs avec des valeurs par défaut (ex: pour un homme de 85kg)
void initDefaultTargets(DailyTargets *targets, float poids);

// Initialise le suivi journalier (remet à zéro les consommations)
void initDailyProgress(DailyProgress *progress);

// Définit les objectifs personnalisés
void setDailyTargets(DailyProgress *progress, float calories, float proteines, float glucides, float lipides, float eau);

// Ajoute un aliment (avec ses valeurs nutritionnelles pour la quantité consommée)
void addFood(DailyProgress *progress, float calories, float proteines, float glucides, float lipides);

// Ajoute de l'eau (en litres)
void addWater(DailyProgress *progress, float litres);

// Ajoute un repas complet à partir d'un tableau d'aliments (simplifié)
void addMeal(DailyProgress *progress, const float *calories, const float *proteines,
             const float *glucides, const float *lipides, int nbAliments);

// Calcule les pourcentages d'atteinte des objectifs
void getProgressPercent(const DailyProgress *progress, float *pCal, float *pProt, float *pGluc, float *pLip, float *pEau);

// Affiche un résumé textuel avec barres de progression
void displayProgress(const DailyProgress *progress);

#endif