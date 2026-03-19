#ifndef TODAY_WORKOUT_H
#define TODAY_WORKOUT_H

// Structure représentant un exercice
typedef struct {
    char nom[50];
    int series;          // nombre de séries prévues
    int repetitions;      // répétitions par série
    float charge;         // charge en kg
    int seriesEffectuees; // nombre de séries déjà effectuées (pour le suivi)
} Exercice;

// Structure représentant la séance du jour
typedef struct {
    char nomSeance[50];
    Exercice exercices[10]; // max 10 exercices
    int nbExercices;
    int dureeEstimee;       // en minutes
} SeanceJour;

// Initialise une séance exemple (pour les tests)
void initSeanceExemple(SeanceJour *seance);

// Affiche le détail de la séance
void afficherSeance(const SeanceJour *seance);

// Met à jour le nombre de séries effectuées pour un exercice
void validerSerie(SeanceJour *seance, int indexExercice);

// Retourne la progression globale de la séance (en pourcentage)
float calculerProgression(const SeanceJour *seance);

#endif