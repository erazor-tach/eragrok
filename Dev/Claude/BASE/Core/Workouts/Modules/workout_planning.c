#include "workout_planning.h"
#include <stdio.h>
#include <string.h>

void initPlanningExemple(PlanningHebdo *planning) {
    strcpy(planning->semaine, "Semaine 12");
    planning->nbSeances = 4;

    // Lundi : Pecs/Triceps
    strcpy(planning->seances[0].nomSeance, "Pectoraux / Triceps");
    strcpy(planning->seances[0].jour, "Lundi");
    planning->seances[0].nbExercices = 4;
    planning->seances[0].dureeEstimee = 55;

    ajouterExercice(&planning->seances[0], "Développé couché", 5, 5, 85.0);
    ajouterExercice(&planning->seances[0], "Dips lestés", 4, 8, 30.0);
    ajouterExercice(&planning->seances[0], "Tirage poulie", 4, 10, 70.0);
    ajouterExercice(&planning->seances[0], "Élévations latérales", 3, 12, 14.0);

    // Mercredi : Jambes
    strcpy(planning->seances[1].nomSeance, "Jambes");
    strcpy(planning->seances[1].jour, "Mercredi");
    planning->seances[1].nbExercices = 3;
    planning->seances[1].dureeEstimee = 60;

    ajouterExercice(&planning->seances[1], "Squat", 5, 5, 120.0);
    ajouterExercice(&planning->seances[1], "Presse", 4, 10, 180.0);
    ajouterExercice(&planning->seances[1], "Leg curl", 4, 12, 45.0);

    // Vendredi : Dos/Biceps
    strcpy(planning->seances[2].nomSeance, "Dos / Biceps");
    strcpy(planning->seances[2].jour, "Vendredi");
    planning->seances[2].nbExercices = 4;
    planning->seances[2].dureeEstimee = 50;

    ajouterExercice(&planning->seances[2], "Tractions", 4, 8, 0.0);
    ajouterExercice(&planning->seances[2], "Rowing barre", 4, 10, 80.0);
    ajouterExercice(&planning->seances[2], "Tirage horizontal", 3, 12, 70.0);
    ajouterExercice(&planning->seances[2], "Curl barre", 3, 10, 35.0);

    // Samedi : Épaules/Cardio
    strcpy(planning->seances[3].nomSeance, "Épaules / Cardio");
    strcpy(planning->seances[3].jour, "Samedi");
    planning->seances[3].nbExercices = 3;
    planning->seances[3].dureeEstimee = 45;

    ajouterExercice(&planning->seances[3], "Développé militaire", 4, 8, 50.0);
    ajouterExercice(&planning->seances[3], "Oiseau", 3, 12, 12.0);
    ajouterExercice(&planning->seances[3], "Cardio (HIIT)", 1, 20, 0.0);
}

void ajouterExercice(SeancePlanifiee *seance, const char *nom, int series, int reps, float charge) {
    if (seance->nbExercices >= 10) return;
    ExercicePlanifie *ex = &seance->exercices[seance->nbExercices];
    strcpy(ex->nom, nom);
    ex->seriesPrevues = series;
    ex->repetitionsPrevues = reps;
    ex->chargePrevues = charge;
    ex->ordre = seance->nbExercices + 1;
    seance->nbExercices++;
}

void afficherSeancePlanifiee(const SeancePlanifiee *seance) {
    printf("\n--- %s (%s) ---\n", seance->nomSeance, seance->jour);
    printf("Durée estimée : %d min\n", seance->dureeEstimee);
    for (int i = 0; i < seance->nbExercices; i++) {
        ExercicePlanifie ex = seance->exercices[i];
        printf("  %d. %s : %dx%d", ex.ordre, ex.nom, ex.seriesPrevues, ex.repetitionsPrevues);
        if (ex.chargePrevues > 0)
            printf(" - %.1f kg", ex.chargePrevues);
        printf("\n");
    }
}

void afficherPlanning(const PlanningHebdo *planning) {
    printf("\n=== PLANNING HEBDOMADAIRE : %s ===\n", planning->semaine);
    for (int i = 0; i < planning->nbSeances; i++) {
        afficherSeancePlanifiee(&planning->seances[i]);
    }
    printf("\nTotal séances : %d, Total exercices : %d\n", planning->nbSeances, totalExercices(planning));
}

int totalExercices(const PlanningHebdo *planning) {
    int total = 0;
    for (int i = 0; i < planning->nbSeances; i++) {
        total += planning->seances[i].nbExercices;
    }
    return total;
}