#include "exercise_progress.h"
#include <stdio.h>
#include <string.h>
#include <time.h>

void initExerciseProgress(ExerciseProgress *prog, const char *nomExercice) {
    strcpy(prog->exerciceNom, nomExercice);
    prog->nbEntries = 0;
}

void ajouterProgression(ExerciseProgress *prog, float rm, float volume, int repsMax, float charge) {
    if (prog->nbEntries >= 50) return;
    ProgressEntry *e = &prog->entries[prog->nbEntries];
    e->date = time(NULL);
    e->rm = rm;
    e->volume = volume;
    e->repetitionsMax = repsMax;
    e->chargeUtilisee = charge;
    prog->nbEntries++;
}

float progressionGlobale(const ExerciseProgress *prog) {
    if (prog->nbEntries < 2) return 0.0;
    return prog->entries[prog->nbEntries - 1].rm - prog->entries[0].rm;
}

void afficherHistorique(const ExerciseProgress *prog) {
    printf("\n=== HISTORIQUE %s ===\n", prog->exerciceNom);
    printf(" # | Date       | 1RM (kg) | Volume (kg) | Reps max | Charge\n");
    printf("--------------------------------------------------------\n");
    for (int i = 0; i < prog->nbEntries; i++) {
        ProgressEntry e = prog->entries[i];
        char dateStr[20];
        strftime(dateStr, sizeof(dateStr), "%d/%m/%Y", localtime(&e.date));
        printf("%2d | %s | %8.1f | %11.1f | %8d | %.1f\n",
               i+1, dateStr, e.rm, e.volume, e.repetitionsMax, e.chargeUtilisee);
    }
}

float meilleurRM(const ExerciseProgress *prog) {
    float max = 0.0;
    for (int i = 0; i < prog->nbEntries; i++) {
        if (prog->entries[i].rm > max) max = prog->entries[i].rm;
    }
    return max;
}

void afficherGraphiqueRM(const ExerciseProgress *prog) {
    if (prog->nbEntries == 0) return;
    printf("\nÉvolution du 1RM - %s\n", prog->exerciceNom);
    // Trouver le max pour l'échelle
    float maxRM = meilleurRM(prog);
    if (maxRM == 0) return;
    for (int i = 0; i < prog->nbEntries; i++) {
        float val = prog->entries[i].rm;
        int barLength = (int)((val / maxRM) * 30); // barre de 30 caractères max
        printf("%2d | ", i+1);
        for (int j = 0; j < barLength; j++) printf("#");
        printf(" %.1f kg\n", val);
    }
}