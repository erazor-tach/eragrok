#include "workout_history.h"
#include <stdio.h>
#include <string.h>
#include <time.h>

void initHistory(WorkoutHistory *hist) {
    hist->nbEntries = 0;
}

void ajouterSeanceHistorique(WorkoutHistory *hist,
                             const char *nomSeance,
                             const HistoryExercise exercices[],
                             int nbExercices,
                             int duree,
                             int note,
                             const char *commentaire) {
    if (hist->nbEntries >= 100) return;

    HistoryEntry *entry = &hist->entries[hist->nbEntries];
    entry->date = time(NULL); // on utilise l'heure actuelle (ou on pourrait passer une date)
    strcpy(entry->nomSeance, nomSeance);
    entry->nbExercices = nbExercices;
    entry->duree = duree;
    entry->note = note;
    strcpy(entry->commentaire, commentaire);
    entry->volumeTotal = 0.0;

    for (int i = 0; i < nbExercices; i++) {
        entry->exercices[i] = exercices[i];
        entry->volumeTotal += exercices[i].volumeExercice;
    }

    hist->nbEntries++;
}

void afficherListeHistorique(const WorkoutHistory *hist) {
    printf("\n=== HISTORIQUE DES SÉANCES (%d) ===\n", hist->nbEntries);
    for (int i = 0; i < hist->nbEntries; i++) {
        HistoryEntry e = hist->entries[i];
        char dateStr[30];
        strftime(dateStr, sizeof(dateStr), "%d/%m/%Y %H:%M", localtime(&e.date));
        printf("%2d. [%s] %s - volume: %.1f kg - note: %d/10\n",
               i+1, dateStr, e.nomSeance, e.volumeTotal, e.note);
    }
}

void afficherDetailSeance(const WorkoutHistory *hist, int index) {
    if (index < 0 || index >= hist->nbEntries) return;

    HistoryEntry e = hist->entries[index];
    char dateStr[30];
    strftime(dateStr, sizeof(dateStr), "%d/%m/%Y %H:%M", localtime(&e.date));

    printf("\n=== SÉANCE DU %s ===\n", dateStr);
    printf("Nom : %s\n", e.nomSeance);
    printf("Durée : %d min\n", e.duree);
    printf("Note : %d/10\n", e.note);
    printf("Commentaire : %s\n", e.commentaire);
    printf("Exercices :\n");
    for (int i = 0; i < e.nbExercices; i++) {
        HistoryExercise ex = e.exercices[i];
        printf("  - %s : %dx%d @ %.1f kg (volume: %.1f kg)\n",
               ex.nom, ex.seriesEffectuees, ex.repetitionsEffectuees,
               ex.chargeUtilisee, ex.volumeExercice);
    }
    printf("Volume total : %.1f kg\n", e.volumeTotal);
}

int totalSeances(const WorkoutHistory *hist) {
    return hist->nbEntries;
}

float volumeTotalHistorique(const WorkoutHistory *hist) {
    float total = 0.0;
    for (int i = 0; i < hist->nbEntries; i++) {
        total += hist->entries[i].volumeTotal;
    }
    return total;
}

void afficherStatistiques(const WorkoutHistory *hist) {
    printf("\n=== STATISTIQUES GLOBALES ===\n");
    printf("Nombre total de séances : %d\n", hist->nbEntries);
    printf("Volume total soulevé : %.2f tonnes\n", volumeTotalHistorique(hist) / 1000.0);
    if (hist->nbEntries > 0) {
        float volumeMoyen = volumeTotalHistorique(hist) / hist->nbEntries;
        printf("Volume moyen par séance : %.1f kg\n", volumeMoyen);
        // note moyenne
        int sommeNotes = 0;
        for (int i = 0; i < hist->nbEntries; i++) {
            sommeNotes += hist->entries[i].note;
        }
        float noteMoyenne = (float)sommeNotes / hist->nbEntries;
        printf("Note moyenne : %.1f/10\n", noteMoyenne);
    }
}