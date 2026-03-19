#include "cycle_effects.h"
#include <stdio.h>
#include <string.h>
#include <time.h>

void initEffectLog(EffectLog *log) {
    log->nbEntries = 0;
}

void ajouterEffet(EffectLog *log, const char *nom, int intensite, const char *notes) {
    if (log->nbEntries >= 200) return;
    EffectEntry *e = &log->entries[log->nbEntries];
    e->id = log->nbEntries + 1;
    e->date = time(NULL);
    strcpy(e->nom, nom);
    e->intensite = intensite;
    strcpy(e->notes, notes);
    log->nbEntries++;
}

void supprimerEffet(EffectLog *log, int id) {
    for (int i = 0; i < log->nbEntries; i++) {
        if (log->entries[i].id == id) {
            for (int j = i; j < log->nbEntries - 1; j++) {
                log->entries[j] = log->entries[j+1];
            }
            log->nbEntries--;
            return;
        }
    }
}

void afficherTousEffets(const EffectLog *log) {
    printf("\n=== EFFETS RESSENTIS ===\n");
    if (log->nbEntries == 0) {
        printf("Aucun effet enregistré.\n");
        return;
    }
    for (int i = 0; i < log->nbEntries; i++) {
        EffectEntry e = log->entries[i];
        char dateStr[30];
        strftime(dateStr, sizeof(dateStr), "%d/%m/%Y %H:%M", localtime(&e.date));
        printf("ID %d [%s] : %s - intensité %d/10\n", e.id, dateStr, e.nom, e.intensite);
        if (e.notes[0] != '\0') printf("    Notes: %s\n", e.notes);
    }
}

void afficherEffetsRecents(const EffectLog *log, int limite) {
    printf("\n=== EFFETS RÉCENTS ===\n");
    int debut = (log->nbEntries > limite) ? log->nbEntries - limite : 0;
    for (int i = debut; i < log->nbEntries; i++) {
        EffectEntry e = log->entries[i];
        char dateStr[30];
        strftime(dateStr, sizeof(dateStr), "%d/%m/%Y %H:%M", localtime(&e.date));
        printf("%s : %s (%d/10)\n", dateStr, e.nom, e.intensite);
    }
}

float intensiteMoyenne(const EffectLog *log, const char *nom) {
    int total = 0;
    int count = 0;
    for (int i = 0; i < log->nbEntries; i++) {
        if (strcasecmp(log->entries[i].nom, nom) == 0) {
            total += log->entries[i].intensite;
            count++;
        }
    }
    return (count == 0) ? 0 : (float)total / count;
}

void afficherResumeEffets(const EffectLog *log) {
    // Comptage des occurrences par nom
    char noms[50][30];
    int counts[50] = {0};
    int nbTypes = 0;

    for (int i = 0; i < log->nbEntries; i++) {
        const char *nom = log->entries[i].nom;
        int trouve = 0;
        for (int j = 0; j < nbTypes; j++) {
            if (strcmp(noms[j], nom) == 0) {
                counts[j]++;
                trouve = 1;
                break;
            }
        }
        if (!trouve && nbTypes < 50) {
            strcpy(noms[nbTypes], nom);
            counts[nbTypes] = 1;
            nbTypes++;
        }
    }

    printf("\n=== RÉSUMÉ DES EFFETS ===\n");
    if (nbTypes == 0) {
        printf("Aucun effet enregistré.\n");
        return;
    }
    for (int j = 0; j < nbTypes; j++) {
        float moy = intensiteMoyenne(log, noms[j]);
        printf("%s : %d occurrence(s), intensité moyenne %.1f/10\n", noms[j], counts[j], moy);
    }
}