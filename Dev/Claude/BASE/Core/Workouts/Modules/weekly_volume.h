#ifndef WEEKLY_VOLUME_H
#define WEEKLY_VOLUME_H

// Structure pour une entrée de volume (par exercice)
typedef struct {
    char exercice[50];
    int series;
    int repetitions;
    float charge;      // kg
    float volume;      // calculé : series * repetitions * charge
} VolumeEntry;

// Structure pour une journée d'entraînement
typedef struct {
    char jour[15];                 // "Lundi", "Mardi", ...
    VolumeEntry exercices[10];
    int nbExercices;
    float volumeTotalJour;         // somme des volumes des exercices
} VolumeDay;

// Structure pour la semaine
typedef struct {
    int numeroSemaine;             // numéro de semaine dans l'année
    VolumeDay jours[7];            // une entrée par jour (même si vide)
    int nbJours;
    float volumeTotalSemaine;      // somme des volumes de tous les jours
} VolumeWeek;

// Initialise une structure VolumeWeek vide
void initVolumeWeek(VolumeWeek *week, int semaine);

// Ajoute un exercice à un jour donné
void ajouterExerciceVolume(VolumeWeek *week, const char *jour, const char *exercice,
                           int series, int reps, float charge);

// Calcule le volume total de la semaine (et met à jour les champs)
void calculerVolumeTotal(VolumeWeek *week);

// Affiche le résumé de la semaine
void afficherVolumeWeek(const VolumeWeek *week);

// Compare deux semaines et affiche la tendance (évolution)
void afficherTendance(const VolumeWeek *semaine1, const VolumeWeek *semaine2);

#endif