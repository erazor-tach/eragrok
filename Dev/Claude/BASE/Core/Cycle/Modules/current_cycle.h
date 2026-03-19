#ifndef CURRENT_CYCLE_H
#define CURRENT_CYCLE_H

#include <time.h>

// Structure pour un produit dans le cycle
typedef struct {
    char nom[50];
    float dosage;           // mg par semaine (ou par injection)
    char frequence[30];     // "2x/semaine", "quotidien", etc.
    char voie[20];          // "IM", "oral", etc.
} CycleProduct;

// Structure pour le cycle en cours
typedef struct {
    char nom[50];           // ex: "Prise de masse #4"
    time_t dateDebut;
    time_t dateFin;         // date estimée de fin
    CycleProduct produits[5];
    int nbProduits;
    float progression;      // pourcentage calculé automatiquement
    int actif;              // 1 si cycle en cours, 0 sinon
} CurrentCycle;

// Initialise le cycle (vide)
void initCurrentCycle(CurrentCycle *cycle);

// Démarre un nouveau cycle
void startCycle(CurrentCycle *cycle, const char *nom, time_t dateDebut, time_t dateFin);

// Ajoute un produit au cycle
void addProductToCycle(CurrentCycle *cycle, const char *nom, float dosage, const char *frequence, const char *voie);

// Calcule la progression du cycle (basé sur dates)
float calculateCycleProgress(const CurrentCycle *cycle);

// Affiche les détails du cycle en cours
void displayCurrentCycle(const CurrentCycle *cycle);

// Termine le cycle (passe actif à 0)
void endCycle(CurrentCycle *cycle);

#endif