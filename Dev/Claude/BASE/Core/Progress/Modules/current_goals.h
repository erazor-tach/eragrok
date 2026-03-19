#ifndef CURRENT_GOALS_H
#define CURRENT_GOALS_H

#include <time.h>

// Types d'objectifs possibles
typedef enum {
    GOAL_WEIGHT,        // poids de corps
    GOAL_STRENGTH,      // force sur un exercice (1RM)
    GOAL_VOLUME,        // volume hebdomadaire
    GOAL_CALORIES,      // calories journalières
    GOAL_WATER,         // hydratation
    GOAL_CUSTOM         // personnalisé
} GoalType;

// Structure pour un objectif
typedef struct {
    int id;
    char nom[100];               // description
    GoalType type;
    char exercice[50];           // pour GOAL_STRENGTH, nom de l'exercice
    float valeurCible;
    float valeurActuelle;
    time_t dateDebut;
    time_t dateFin;              // 0 si pas de date limite
    int atteint;                  // 0 non, 1 oui
} Goal;

// Structure pour la liste des objectifs
typedef struct {
    Goal goals[50];
    int nbGoals;
} CurrentGoals;

// Initialise la liste
void initCurrentGoals(CurrentGoals *cg);

// Ajoute un nouvel objectif
void addGoal(CurrentGoals *cg, const char *nom, GoalType type, const char *exercice,
             float cible, time_t dateFin);

// Met à jour la valeur actuelle d'un objectif (par id)
void updateGoalProgress(CurrentGoals *cg, int id, float nouvelleValeur);

// Supprime un objectif
void removeGoal(CurrentGoals *cg, int id);

// Affiche tous les objectifs
void displayAllGoals(const CurrentGoals *cg);

// Affiche les objectifs en cours (non atteints)
void displayActiveGoals(const CurrentGoals *cg);

// Calcule le pourcentage de progression d'un objectif
float getGoalProgress(const Goal *g);

#endif