#ifndef MEAL_HISTORY_H
#define MEAL_HISTORY_H

#include <time.h>

// Structure pour un aliment consommé (avec quantité)
typedef struct {
    char nom[50];
    float quantite;       // en grammes
    float calories;       // calculé
    float proteines;
    float glucides;
    float lipides;
} AlimentConsomme;

// Structure pour un repas consommé
typedef struct {
    time_t date;                  // timestamp du repas
    char type[30];                // "Petit-déjeuner", "Déjeuner", etc.
    AlimentConsomme aliments[20]; // max 20 aliments par repas
    int nbAliments;
    float totalCalories;
    float totalProteines;
    float totalGlucides;
    float totalLipides;
} RepasHistorique;

// Structure pour une journée d'historique
typedef struct {
    time_t date;                  // date du jour (minuit)
    RepasHistorique repas[10];    // max 10 repas dans la journée
    int nbRepas;
    float totalCaloriesJour;
    float totalProteinesJour;
    float totalGlucidesJour;
    float totalLipidesJour;
} JourHistorique;

// Structure pour l'ensemble de l'historique
typedef struct {
    JourHistorique jours[100];    // max 100 jours
    int nbJours;
} MealHistory;

// Initialise un historique vide
void initMealHistory(MealHistory *hist);

// Ajoute un repas à l'historique (à la date courante ou spécifiée)
void ajouterRepasHistorique(MealHistory *hist,
                            const char *type,
                            const AlimentConsomme aliments[],
                            int nbAliments,
                            time_t date); // si 0, date courante

// Affiche l'historique d'une journée (par index)
void afficherJourHistorique(const MealHistory *hist, int indexJour);

// Affiche l'historique complet (liste des jours)
void afficherHistoriqueComplet(const MealHistory *hist);

// Calcule les moyennes sur une période (ex: 7 derniers jours)
void afficherMoyennesRecentes(const MealHistory *hist, int nbJours);

#endif