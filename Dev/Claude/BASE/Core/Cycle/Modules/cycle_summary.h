#ifndef CYCLE_SUMMARY_H
#define CYCLE_SUMMARY_H

#include <time.h>
#include "cycle_settings.h"
#include "injection_schedule.h"

// Structure pour un effet secondaire noté
typedef struct {
    char nom[30];
    int intensite;      // 1-10
    char commentaire[100];
} SideEffect;

// Structure pour le résumé du cycle
typedef struct {
    char nomCycle[50];
    int joursEcoules;
    int joursRestants;
    float progression;   // pourcentage
    int injectionsPrevues;
    int injectionsEffectuees;
    CycleProduct produits[10];
    int nbProduits;
    SideEffect effets[10];
    int nbEffets;
    char recommandations[5][200];  // max 5 recommandations
    int nbRecommandations;
} CycleSummary;

// Génère un résumé à partir des paramètres du cycle et du planning d'injections
void genererCycleSummary(const CycleSettings *settings, const InjectionSchedule *sched, CycleSummary *summary);

// Ajoute un effet secondaire observé
void ajouterEffet(CycleSummary *summary, const char *nom, int intensite, const char *commentaire);

// Affiche le résumé complet
void afficherCycleSummary(const CycleSummary *summary);

#endif