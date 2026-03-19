#include "personal_records.h"
#include <stdio.h>
#include <string.h>
#include <time.h>

float estimate1RM(float charge, int reps) {
    // Formule d'Epley
    return charge * (1 + reps / 30.0);
}

void initPersonalRecords(PersonalRecords *pr) {
    pr->nbRecords = 0;
}

int updateRecord(PersonalRecords *pr, const char *exercice, float charge, int reps) {
    // Chercher si l'exercice existe déjà
    for (int i = 0; i < pr->nbRecords; i++) {
        if (strcasecmp(pr->records[i].exercice, exercice) == 0) {
            float ancien1RM = pr->records[i].estimated1RM;
            float nouveau1RM = estimate1RM(charge, reps);
            if (nouveau1RM > ancien1RM) {
                // Mise à jour
                pr->records[i].charge = charge;
                pr->records[i].repetitions = reps;
                pr->records[i].date = time(NULL);
                pr->records[i].estimated1RM = nouveau1RM;
                return 1; // nouveau record
            }
            return 0; // pas de nouveau record
        }
    }
    // Nouvel exercice
    if (pr->nbRecords < 50) {
        RecordEntry *r = &pr->records[pr->nbRecords];
        strcpy(r->exercice, exercice);
        r->charge = charge;
        r->repetitions = reps;
        r->date = time(NULL);
        r->estimated1RM = estimate1RM(charge, reps);
        pr->nbRecords++;
        return 1; // nouveau record
    }
    return 0; // liste pleine
}

void deleteRecord(PersonalRecords *pr, const char *exercice) {
    for (int i = 0; i < pr->nbRecords; i++) {
        if (strcasecmp(pr->records[i].exercice, exercice) == 0) {
            // Décaler les suivants
            for (int j = i; j < pr->nbRecords - 1; j++) {
                pr->records[j] = pr->records[j+1];
            }
            pr->nbRecords--;
            return;
        }
    }
}

RecordEntry* getRecord(PersonalRecords *pr, const char *exercice) {
    for (int i = 0; i < pr->nbRecords; i++) {
        if (strcasecmp(pr->records[i].exercice, exercice) == 0) {
            return &pr->records[i];
        }
    }
    return NULL;
}

void displayAllRecords(const PersonalRecords *pr) {
    printf("\n=== RECORDS PERSONNELS ===\n");
    if (pr->nbRecords == 0) {
        printf("Aucun record enregistré.\n");
        return;
    }
    for (int i = 0; i < pr->nbRecords; i++) {
        RecordEntry r = pr->records[i];
        char dateStr[30];
        strftime(dateStr, sizeof(dateStr), "%d/%m/%Y", localtime(&r.date));
        printf("%2d. %-20s : %.1f kg x %d = 1RM estimé %.1f kg (le %s)\n",
               i+1, r.exercice, r.charge, r.repetitions, r.estimated1RM, dateStr);
    }
}

void displayRecentRecords(const PersonalRecords *pr, int limit) {
    printf("\n=== RECORDS RÉCENTS ===\n");
    if (pr->nbRecords == 0) {
        printf("Aucun record.\n");
        return;
    }
    // On suppose que les derniers ajoutés sont à la fin du tableau (ordre chronologique)
    int start = (pr->nbRecords > limit) ? pr->nbRecords - limit : 0;
    for (int i = start; i < pr->nbRecords; i++) {
        RecordEntry r = pr->records[i];
        char dateStr[30];
        strftime(dateStr, sizeof(dateStr), "%d/%m/%Y", localtime(&r.date));
        printf("%-20s : %.1f kg x %d (1RM %.1f) - %s\n",
               r.exercice, r.charge, r.repetitions, r.estimated1RM, dateStr);
    }
}