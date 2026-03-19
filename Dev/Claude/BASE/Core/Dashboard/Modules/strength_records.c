#include "strength_records.h"
#include <stdio.h>
#include <string.h>

int ajouterRecord(CollectionRecords *collection, const char *exercice, float poids, const char *date) {
    // Chercher si l'exercice existe déjà
    for (int i = 0; i < collection->nbRecords; i++) {
        if (strcmp(collection->records[i].exercice, exercice) == 0) {
            // Exercice trouvé, vérifier si c'est un nouveau record
            if (poids > collection->records[i].poids) {
                float ancien = collection->records[i].poids;
                collection->records[i].poids = poids;
                strcpy(collection->records[i].date, date);
                collection->records[i].progression = poids - ancien; // ou calculerProgression(ancien, poids)
                return 1; // nouveau record
            } else {
                return 0; // pas de record
            }
        }
    }

    // Nouvel exercice, ajouter à la fin si la place le permet
    if (collection->nbRecords < 20) {
        strcpy(collection->records[collection->nbRecords].exercice, exercice);
        collection->records[collection->nbRecords].poids = poids;
        strcpy(collection->records[collection->nbRecords].date, date);
        collection->records[collection->nbRecords].progression = 0;
        collection->nbRecords++;
        return 1; // premier record
    }
    return -1; // liste pleine
}

void supprimerRecord(CollectionRecords *collection, int index) {
    if (index < 0 || index >= collection->nbRecords) return;
    // Décaler les éléments suivants
    for (int i = index; i < collection->nbRecords - 1; i++) {
        collection->records[i] = collection->records[i + 1];
    }
    collection->nbRecords--;
}

void afficherRecords(const CollectionRecords *collection) {
    printf("\n=== RECORDS PERSONNELS (1RM) ===\n");
    if (collection->nbRecords == 0) {
        printf("Aucun record enregistré.\n");
        return;
    }
    for (int i = 0; i < collection->nbRecords; i++) {
        Record r = collection->records[i];
        printf("%d. %s : %.1f kg (le %s) ", i+1, r.exercice, r.poids, r.date);
        if (r.progression > 0) {
            printf("+%.1f kg", r.progression);
        } else if (r.progression < 0) {
            printf("%.1f kg", r.progression);
        }
        printf("\n");
    }
}

float calculerProgression(float ancien, float nouveau) {
    if (ancien == 0) return 0;
    return (nouveau - ancien) / ancien * 100.0;
}

Record* rechercherRecord(CollectionRecords *collection, const char *exercice) {
    for (int i = 0; i < collection->nbRecords; i++) {
        if (strcmp(collection->records[i].exercice, exercice) == 0) {
            return &collection->records[i];
        }
    }
    return NULL;
}