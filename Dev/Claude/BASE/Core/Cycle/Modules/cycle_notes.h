#ifndef CYCLE_NOTES_H
#define CYCLE_NOTES_H

#include <time.h>

// Structure pour une note de cycle
typedef struct {
    int id;
    time_t date;            // date de la note
    char titre[100];
    char contenu[500];
} CycleNote;

// Structure pour la collection de notes
typedef struct {
    CycleNote notes[50];
    int nbNotes;
} CycleNoteCollection;

// Initialise la collection
void initCycleNotes(CycleNoteCollection *col);

// Ajoute une note
void ajouterNote(CycleNoteCollection *col, const char *titre, const char *contenu);

// Modifie une note existante
void modifierNote(CycleNoteCollection *col, int id, const char *titre, const char *contenu);

// Supprime une note
void supprimerNote(CycleNoteCollection *col, int id);

// Affiche toutes les notes (triées par date)
void afficherToutesNotes(const CycleNoteCollection *col);

// Affiche une note spécifique
void afficherNote(const CycleNote *note);

#endif