#ifndef EXERCISE_PROGRESS_H
#define EXERCISE_PROGRESS_H

#include <time.h>

// Structure pour une entrée de progression (une séance)
typedef struct {
    time_t date;            // timestamp de la séance
    float rm;               // 1RM estimé (kg)
    float volume;           // volume total pour cet exercice (kg)
    int repetitionsMax;     // répétitions max à une charge donnée (optionnel)
    float chargeUtilisee;   // charge utilisée ce jour-là (pour info)
} ProgressEntry;

// Structure pour l'historique d'un exercice
typedef struct {
    char exerciceNom[50];
    ProgressEntry entries[50]; // max 50 entrées
    int nbEntries;
} ExerciseProgress;

// Initialise le suivi pour un exercice
void initExerciseProgress(ExerciseProgress *prog, const char *nomExercice);

// Ajoute une entrée de progression (avec date automatique)
void ajouterProgression(ExerciseProgress *prog, float rm, float volume, int repsMax, float charge);

// Calcule la progression entre la première et la dernière entrée
float progressionGlobale(const ExerciseProgress *prog);

// Affiche l'historique sous forme de tableau
void afficherHistorique(const ExerciseProgress *prog);

// Affiche un graphique en barres simplifié de l'évolution du 1RM
void afficherGraphiqueRM(const ExerciseProgress *prog);

// Retourne le meilleur 1RM
float meilleurRM(const ExerciseProgress *prog);

#endif