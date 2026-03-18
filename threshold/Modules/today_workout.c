#include "today_workout.h"
#include <stdio.h>
#include <string.h>

void initSeanceExemple(SeanceJour *seance) {
    strcpy(seance->nomSeance, "Pectoraux / Triceps");
    seance->nbExercices = 4;
    seance->dureeEstimee = 55;

    // Développé couché
    strcpy(seance->exercices[0].nom, "Développé couché");
    seance->exercices[0].series = 5;
    seance->exercices[0].repetitions = 5;
    seance->exercices[0].charge = 85.0;
    seance->exercices[0].seriesEffectuees = 0;

    // Dips lestés
    strcpy(seance->exercices[1].nom, "Dips lestés");
    seance->exercices[1].series = 4;
    seance->exercices[1].repetitions = 8;
    seance->exercices[1].charge = 30.0;
    seance->exercices[1].seriesEffectuees = 0;

    // Tirage poulie
    strcpy(seance->exercices[2].nom, "Tirage poulie");
    seance->exercices[2].series = 4;
    seance->exercices[2].repetitions = 10;
    seance->exercices[2].charge = 70.0;
    seance->exercices[2].seriesEffectuees = 0;

    // Élévations latérales
    strcpy(seance->exercices[3].nom, "Élévations latérales");
    seance->exercices[3].series = 3;
    seance->exercices[3].repetitions = 12;
    seance->exercices[3].charge = 14.0;
    seance->exercices[3].seriesEffectuees = 0;
}

void afficherSeance(const SeanceJour *seance) {
    printf("\n=== SÉANCE DU JOUR : %s ===\n", seance->nomSeance);
    printf("Durée estimée : %d minutes\n", seance->dureeEstimee);
    printf("Exercices :\n");
    for (int i = 0; i < seance->nbExercices; i++) {
        Exercice ex = seance->exercices[i];
        printf("  %d. %s : %d x %d kg (effectué : %d/%d)\n",
               i+1, ex.nom, ex.series, (int)ex.charge, ex.seriesEffectuees, ex.series);
    }
    printf("Progression : %.1f%%\n", calculerProgression(seance));
}

void validerSerie(SeanceJour *seance, int indexExercice) {
    if (indexExercice < 0 || indexExercice >= seance->nbExercices) return;
    Exercice *ex = &seance->exercices[indexExercice];
    if (ex->seriesEffectuees < ex->series) {
        ex->seriesEffectuees++;
        printf("Série validée pour %s (%d/%d)\n", ex->nom, ex->seriesEffectuees, ex->series);
    } else {
        printf("Toutes les séries de %s sont déjà effectuées.\n", ex->nom);
    }
}

float calculerProgression(const SeanceJour *seance) {
    int totalSeries = 0;
    int totalEffectuees = 0;
    for (int i = 0; i < seance->nbExercices; i++) {
        totalSeries += seance->exercices[i].series;
        totalEffectuees += seance->exercices[i].seriesEffectuees;
    }
    if (totalSeries == 0) return 0.0;
    return (totalEffectuees * 100.0) / totalSeries;
}