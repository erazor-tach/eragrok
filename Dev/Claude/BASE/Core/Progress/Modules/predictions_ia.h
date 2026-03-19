#ifndef PREDICTIONS_IA_H
#define PREDICTIONS_IA_H

#include <time.h>

// Structure pour une prédiction
typedef struct {
    char exercice[50];          // exercice concerné (ou "poids" pour le poids de forme)
    float valeurPredite;         // valeur prédite
    float confiance;             // indice de confiance (0-100)
    time_t datePrediction;       // date de la prédiction
    char unite[10];              // "kg", "L", etc.
} Prediction;

// Structure pour les données d'entrée (une série temporelle)
typedef struct {
    time_t date;
    float valeur;
} DataPoint;

// Calcule une régression linéaire simple sur un tableau de points
// Retourne la pente et l'intercept, ainsi que le coefficient R²
void linearRegression(const DataPoint points[], int nbPoints, float *pente, float *intercept, float *r2);

// Prédit la valeur à une date future donnée (timestamp) à partir d'une régression
float predireValeur(const DataPoint points[], int nbPoints, time_t dateFuture, float *confiance);

// Prédit le prochain 1RM pour un exercice à partir de l'historique des 1RM
Prediction predireProchainRM(const char *exercice, const DataPoint historiqueRM[], int nbPoints);

// Prédit le poids dans un certain nombre de jours
Prediction predirePoids(const DataPoint historiquePoids[], int nbPoints, int joursFutur);

// Affiche une prédiction
void afficherPrediction(const Prediction *p);

#endif