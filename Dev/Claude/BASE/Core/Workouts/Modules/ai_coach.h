#ifndef AI_COACH_H
#define AI_COACH_H

#include "workout_history.h"   // pour récupérer l'historique
#include "recovery_analysis.h" // pour les données de récupération
#include "strength_records.h"  // pour les records

// Structure pour un conseil généré par l'IA
typedef struct {
    char titre[100];
    char description[300];
    int priorite;           // 1 = haute, 2 = moyenne, 3 = faible
    char categorie[30];     // ex: "force", "volume", "récupération", "technique"
} AIContext;

// Génère une liste de conseils en fonction du contexte utilisateur
// Retourne le nombre de conseils générés
int genererConseilsIA( const WorkoutHistory *hist,
                       const RecuperationJour *recupRecente,
                       const StrengthRecords *records,
                       AIContext conseils[],
                       int maxConseils );

// Affiche les conseils dans la console
void afficherConseilsIA(const AIContext conseils[], int nbConseils);

#endif