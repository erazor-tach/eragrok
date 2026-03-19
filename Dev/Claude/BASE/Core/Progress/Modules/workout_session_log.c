#include "workout_session_log.h"
#include <stdio.h>
#include <string.h>
#include <time.h>

void initSessionLog(WorkoutSessionLog *log) {
    log->nbEntries = 0;
}

void addSessionEntry(WorkoutSessionLog *log,
                     const char *nomSeance,
                     const LogExercise exercices[],
                     int nbExercices,
                     int duree,
                     int note,
                     const char *commentaire) {
    if (log->nbEntries >= 100) return;

    SessionEntry *e = &log->entries[log->nbEntries];
    e->date = time(NULL);
    strcpy(e->nomSeance, nomSeance);
    e->nbExercices = nbExercices;
    e->duree = duree;
    e->note = note;
    strcpy(e->commentaire, commentaire);
    e->volumeTotal = 0.0;

    for (int i = 0; i < nbExercices; i++) {
        e->exercices[i] = exercices[i];
        e->volumeTotal += exercices[i].volumeExercice;
    }

    log->nbEntries++;
}

void removeSessionEntry(WorkoutSessionLog *log, int index) {
    if (index < 0 || index >= log->nbEntries) return;
    for (int i = index; i < log->nbEntries - 1; i++) {
        log->entries[i] = log->entries[i+1];
    }
    log->nbEntries--;
}

void displaySessionList(const WorkoutSessionLog *log) {
    printf("\n=== HISTORIQUE DES SÉANCES ===\n");
    for (int i = 0; i < log->nbEntries; i++) {
        SessionEntry e = log->entries[i];
        char dateStr[30];
        strftime(dateStr, sizeof(dateStr), "%d/%m/%Y %H:%M", localtime(&e.date));
        printf("%2d. [%s] %s - volume: %.1f kg - note: %d/10\n",
               i+1, dateStr, e.nomSeance, e.volumeTotal, e.note);
    }
}

void displaySessionDetail(const WorkoutSessionLog *log, int index) {
    if (index < 0 || index >= log->nbEntries) return;
    SessionEntry e = log->entries[index];
    char dateStr[30];
    strftime(dateStr, sizeof(dateStr), "%d/%m/%Y %H:%M", localtime(&e.date));

    printf("\n=== SÉANCE DU %s ===\n", dateStr);
    printf("Nom : %s\n", e.nomSeance);
    printf("Durée : %d min\n", e.duree);
    printf("Note : %d/10\n", e.note);
    printf("Commentaire : %s\n", e.commentaire);
    printf("Exercices :\n");
    for (int i = 0; i < e.nbExercices; i++) {
        LogExercise ex = e.exercices[i];
        printf("  - %s : %dx%d @ %.1f kg (volume: %.1f kg)\n",
               ex.nom, ex.seriesEffectuees, ex.repetitionsEffectuees,
               ex.charge, ex.volumeExercice);
    }
    printf("Volume total : %.1f kg\n", e.volumeTotal);
}

float totalVolumeAll(const WorkoutSessionLog *log) {
    float total = 0;
    for (int i = 0; i < log->nbEntries; i++) {
        total += log->entries[i].volumeTotal;
    }
    return total;
}

float averageNote(const WorkoutSessionLog *log) {
    if (log->nbEntries == 0) return 0;
    int sum = 0;
    for (int i = 0; i < log->nbEntries; i++) {
        sum += log->entries[i].note;
    }
    return (float)sum / log->nbEntries;
}

int totalSessions(const WorkoutSessionLog *log) {
    return log->nbEntries;
}