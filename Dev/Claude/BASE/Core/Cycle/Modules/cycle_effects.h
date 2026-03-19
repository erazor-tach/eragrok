#ifndef CYCLE_EFFECTS_H
#define CYCLE_EFFECTS_H

#include <time.h>

// Structure pour un effet enregistré
typedef struct {
    int id;
    time_t date;                // date de l'observation
    char nom[30];                // ex: "Acné", "Agressivité"
    int intensite;               // 1-10
    char notes[100];             // commentaire libre
} EffectEntry;

// Collection d'effets
typedef struct {
    EffectEntry entries[200];
    int nbEntries;
} EffectLog;

// Initialise le journal
void initEffectLog(EffectLog *log);

// Ajoute un effet
void ajouterEffet(EffectLog *log, const char *nom, int intensite, const char *notes);

// Supprime un effet (par id)
void supprimerEffet(EffectLog *log, int id);

// Affiche tous les effets enregistrés
void afficherTousEffets(const EffectLog *log);

// Affiche les effets récents (par exemple les 10 derniers)
void afficherEffetsRecents(const EffectLog *log, int limite);

// Affiche un résumé : fréquence des effets, intensité moyenne
void afficherResumeEffets(const EffectLog *log);

// Calcule l'intensité moyenne pour un effet donné
float intensiteMoyenne(const EffectLog *log, const char *nom);

#endif