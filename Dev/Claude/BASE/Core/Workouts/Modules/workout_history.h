#ifndef WORKOUT_HISTORY_H
#define WORKOUT_HISTORY_H

#include <time.h>

// Structure pour un exercice effectué dans une séance
typedef struct {
    char nom[50];
    int seriesEffectuees;
    int repetitionsEffectuees;
    float chargeUtilisee;    // kg
    float volumeExercice;    // calculé : series * reps * charge
} HistoryExercise;

// Structure pour une entrée d'historique (une séance)
typedef struct {
    time_t date;                     // timestamp de la séance
    char nomSeance[50];
    HistoryExercise exercices[10];
    int nbExercices;
    float volumeTotal;               // somme des volumes des exercices
    int duree;                       // en minutes (optionnel)
    int note;                        // note de la séance (0-10) optionnelle
    char commentaire[200];            // commentaire libre
} HistoryEntry;

// Structure pour l'ensemble de l'historique
typedef struct {
    HistoryEntry entries[100];        // max 100 séances (ajustable)
    int nbEntries;
} WorkoutHistory;

// Initialise un historique vide
void initHistory(WorkoutHistory *hist);

// Ajoute une séance à l'historique (copie les données)
void ajouterSeanceHistorique(WorkoutHistory *hist,
                             const char *nomSeance,
                             const HistoryExercise exercices[],
                             int nbExercices,
                             int duree,
                             int note,
                             const char *commentaire);

// Affiche la liste des séances (date et nom)
void afficherListeHistorique(const WorkoutHistory *hist);

// Affiche le détail d'une séance (par index)
void afficherDetailSeance(const WorkoutHistory *hist, int index);

// Calcule le nombre total de séances
int totalSeances(const WorkoutHistory *hist);

// Calcule le volume total de toutes les séances
float volumeTotalHistorique(const WorkoutHistory *hist);

// Affiche quelques statistiques globales
void afficherStatistiques(const WorkoutHistory *hist);

#endif