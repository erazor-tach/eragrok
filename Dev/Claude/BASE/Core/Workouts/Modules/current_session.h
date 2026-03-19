#ifndef CURRENT_SESSION_H
#define CURRENT_SESSION_H

#include "today_workout.h"  // pour réutiliser la structure Exercice si besoin

// Structure pour un exercice en cours (avec suivi)
typedef struct {
    char nom[50];
    int seriesPrevues;
    int repetitionsPrevues;
    float chargePrevue;
    int seriesEffectuees;
    int repetitionsEffectuees; // optionnel
} ExerciceEnCours;

// Structure pour la séance en cours
typedef struct {
    char nomSeance[50];
    ExerciceEnCours exercices[10];
    int nbExercices;
    int exerciceEnCoursIndex;   // index de l'exercice actuellement réalisé
    time_t debutSeance;          // timestamp de début
    int dureeEcoulee;            // en secondes, mise à jour périodiquement
    int terminee;                // 1 si séance terminée
} SessionEnCours;

// Initialise une nouvelle session à partir d'une séance planifiée (par exemple depuis today_workout)
void demarrerSession(SessionEnCours *session, const SeanceJour *plan);

// Valide une série pour l'exercice en cours (incrémente seriesEffectuees)
void validerSerieEnCours(SessionEnCours *session);

// Passe à l'exercice suivant (si l'exercice actuel est terminé)
void passerExerciceSuivant(SessionEnCours *session);

// Met à jour le chronomètre (à appeler régulièrement)
void mettreAJourChrono(SessionEnCours *session);

// Affiche l'état actuel de la session (console)
void afficherSession(const SessionEnCours *session);

// Termine la session et retourne un résumé (peut être sauvegardé)
void terminerSession(SessionEnCours *session);

#endif