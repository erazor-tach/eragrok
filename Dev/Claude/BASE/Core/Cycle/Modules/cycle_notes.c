#include "cycle_notes.h"
#include <stdio.h>
#include <string.h>
#include <time.h>

void initCycleNotes(CycleNoteCollection *col) {
    col->nbNotes = 0;
}

void ajouterNote(CycleNoteCollection *col, const char *titre, const char *contenu) {
    if (col->nbNotes >= 50) return;
    CycleNote *n = &col->notes[col->nbNotes];
    n->id = col->nbNotes + 1; // simple, pourrait être géré autrement
    n->date = time(NULL);
    strcpy(n->titre, titre);
    strcpy(n->contenu, contenu);
    col->nbNotes++;
}

void modifierNote(CycleNoteCollection *col, int id, const char *titre, const char *contenu) {
    for (int i = 0; i < col->nbNotes; i++) {
        if (col->notes[i].id == id) {
            strcpy(col->notes[i].titre, titre);
            strcpy(col->notes[i].contenu, contenu);
            col->notes[i].date = time(NULL); // on met à jour la date
            return;
        }
    }
}

void supprimerNote(CycleNoteCollection *col, int id) {
    for (int i = 0; i < col->nbNotes; i++) {
        if (col->notes[i].id == id) {
            for (int j = i; j < col->nbNotes - 1; j++) {
                col->notes[j] = col->notes[j+1];
            }
            col->nbNotes--;
            return;
        }
    }
}

void afficherToutesNotes(const CycleNoteCollection *col) {
    printf("\n=== NOTES DU CYCLE ===\n");
    if (col->nbNotes == 0) {
        printf("Aucune note.\n");
        return;
    }
    for (int i = 0; i < col->nbNotes; i++) {
        CycleNote n = col->notes[i];
        char dateStr[30];
        strftime(dateStr, sizeof(dateStr), "%d/%m/%Y %H:%M", localtime(&n.date));
        printf("ID %d [%s] : %s\n", n.id, dateStr, n.titre);
    }
}

void afficherNote(const CycleNote *note) {
    char dateStr[30];
    strftime(dateStr, sizeof(dateStr), "%d/%m/%Y %H:%M", localtime(&note->date));
    printf("\n--- %s (%s) ---\n", note->titre, dateStr);
    printf("%s\n", note->contenu);
}