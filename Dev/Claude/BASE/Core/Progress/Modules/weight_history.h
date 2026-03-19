#ifndef WEIGHT_HISTORY_H
#define WEIGHT_HISTORY_H

#include <time.h>

// Structure pour une mesure de poids
typedef struct {
    time_t date;
    float poids;          // en kg
    float imc;            // optionnel, calculé si taille connue
} WeightEntry;

// Structure pour l'historique
typedef struct {
    WeightEntry entries[365]; // max un an
    int nbEntries;
} WeightHistory;

// Initialise l'historique vide
void initWeightHistory(WeightHistory *hist);

// Ajoute une mesure de poids (avec date automatique ou spécifiée)
void addWeight(WeightHistory *hist, float poids, time_t date);

// Retourne le dernier poids enregistré
float getLastWeight(const WeightHistory *hist);

// Retourne le poids minimum, maximum et moyen
void getStats(const WeightHistory *hist, float *min, float *max, float *avg);

// Affiche l'historique sous forme de tableau
void displayWeightHistory(const WeightHistory *hist);

// Affiche un graphique simplifié de l'évolution
void displayWeightChart(const WeightHistory *hist);

// Calcule la variation entre la première et la dernière mesure
float getTotalChange(const WeightHistory *hist);

#endif