#ifndef CYCLE_HISTORY_H
#define CYCLE_HISTORY_H

#include <time.h>

// Structure pour un produit utilisé dans un cycle passé
typedef struct {
    char nom[50];
    float dosage;           // dosage moyen (mg/sem, etc.)
    char unite[10];
} HistoricCycleProduct;

// Structure pour une entrée d'historique de cycle
typedef struct {
    int id;
    char nom[50];
    time_t dateDebut;
    time_t dateFin;
    HistoricCycleProduct produits[10];
    int nbProduits;
    int pctInclus;           // 0/1
    char notes[300];         // notes personnelles sur le cycle
    float priseMasse;        // kg gagnés/perdus (optionnel)
    float progressionForce;   // évolution sur un exo de référence
} HistoricCycleEntry;

// Structure pour l'historique complet
typedef struct {
    HistoricCycleEntry cycles[20];
    int nbCycles;
} CycleHistoryArchive;

// Initialise l'archive
void initCycleHistory(CycleHistoryArchive *arch);

// Ajoute un cycle terminé à l'archive
void ajouterCycleHistorique(CycleHistoryArchive *arch,
                            const char *nom,
                            time_t debut,
                            time_t fin,
                            const HistoricCycleProduct produits[],
                            int nbProduits,
                            int pct,
                            const char *notes,
                            float priseMasse,
                            float progressionForce);

// Supprime un cycle de l'archive (par id)
void supprimerCycleHistorique(CycleHistoryArchive *arch, int id);

// Affiche la liste des cycles (résumé)
void afficherListeCycles(const CycleHistoryArchive *arch);

// Affiche le détail d'un cycle (par index)
void afficherCycleDetail(const CycleHistoryArchive *arch, int index);

// Calcule la durée d'un cycle en jours
int dureeCycleJours(const HistoricCycleEntry *cycle);

#endif