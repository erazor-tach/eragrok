#ifndef HYDRATION_TRACKER_H
#define HYDRATION_TRACKER_H

#include <time.h>

// Structure pour une entrée de consommation (par jour)
typedef struct {
    time_t date;                // timestamp du jour (minuit)
    float objectif;             // objectif en litres
    float consomme;              // litres bus
} HydrationDay;

// Structure pour l'historique
typedef struct {
    HydrationDay jours[365];    // max un an
    int nbJours;
} HydrationHistory;

// Initialise le tracker (historique vide)
void initHydrationHistory(HydrationHistory *hist);

// Définit l'objectif quotidien (pour aujourd'hui ou un jour donné)
void setDailyGoal(HydrationHistory *hist, float litres, time_t date);

// Ajoute de l'eau bue (pour aujourd'hui)
void addWater(HydrationHistory *hist, float litres);

// Retourne la progression du jour courant (pourcentage)
float getTodayProgress(const HydrationHistory *hist);

// Affiche le résumé du jour courant
void displayToday(const HydrationHistory *hist);

// Affiche l'historique des derniers jours
void displayHistory(const HydrationHistory *hist, int nbJours);

#endif