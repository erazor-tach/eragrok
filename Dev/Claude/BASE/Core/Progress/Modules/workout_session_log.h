#ifndef WORKOUT_SESSION_LOG_H
#define WORKOUT_SESSION_LOG_H

#include <time.h>

// Structure pour un exercice effectué
typedef struct {
    char nom[50];
    int seriesEffectuees;
    int repetitionsEffectuees;
    float charge;               // kg
    float volumeExercice;       // calculé : series * reps * charge
} LogExercise;

// Structure pour une séance enregistrée
typedef struct {
    time_t date;
    char nomSeance[50];
    LogExercise exercices[20];
    int nbExercices;
    float volumeTotal;          // somme des volumes
    int duree;                  // en minutes
    int note;                   // 0-10
    char commentaire[200];
} SessionEntry;

// Structure pour l'ensemble des logs
typedef struct {
    SessionEntry entries[100];
    int nbEntries;
} WorkoutSessionLog;

// Initialise le log
void initSessionLog(WorkoutSessionLog *log);

// Ajoute une séance au log
void addSessionEntry(WorkoutSessionLog *log,
                     const char *nomSeance,
                     const LogExercise exercices[],
                     int nbExercices,
                     int duree,
                     int note,
                     const char *commentaire);

// Supprime une séance (par index)
void removeSessionEntry(WorkoutSessionLog *log, int index);

// Affiche la liste des séances (dates et noms)
void displaySessionList(const WorkoutSessionLog *log);

// Affiche le détail d'une séance (par index)
void displaySessionDetail(const WorkoutSessionLog *log, int index);

// Calcule le volume total sur toutes les séances
float totalVolumeAll(const WorkoutSessionLog *log);

// Calcule la note moyenne
float averageNote(const WorkoutSessionLog *log);

// Retourne le nombre de séances
int totalSessions(const WorkoutSessionLog *log);

#endif