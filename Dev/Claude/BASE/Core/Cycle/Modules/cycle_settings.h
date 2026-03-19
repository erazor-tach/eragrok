#ifndef CYCLE_SETTINGS_H
#define CYCLE_SETTINGS_H

#include <time.h>

// Structure pour un produit dans le cycle
typedef struct {
    char nom[50];
    float dosage;           // mg par semaine ou par injection
    char unite[10];         // "mg/sem", "mg/jour", etc.
    float quantiteTotale;   // quantité totale pour le cycle (optionnel)
} CycleProduct;

// Structure pour les paramètres d'un cycle
typedef struct {
    char nomCycle[50];
    time_t dateDebut;
    int dureeSemaines;      // durée en semaines
    CycleProduct produits[10];
    int nbProduits;
    float eauQuotidienne;    // recommandation L/jour
    char notes[200];
    // Paramètres PCT
    int pctActif;            // 0/1
    char pctProtocole[100];  // description du PCT
    time_t dateDebutPCT;     // calculée automatiquement ou manuelle
} CycleSettings;

// Structure pour l'ensemble des cycles (historique des paramètres)
typedef struct {
    CycleSettings cycles[20];
    int nbCycles;
} CycleHistory;

// Initialise un cycle avec des valeurs par défaut
void initCycleSettings(CycleSettings *cycle, const char *nom, time_t debut, int duree);

// Ajoute un produit au cycle
void ajouterProduitCycle(CycleSettings *cycle, const char *nom, float dosage, const char *unite, float quantiteTotale);

// Calcule la date de début du PCT (fin cycle + délai)
time_t calculerDatePCT(const CycleSettings *cycle, int delaiJours);

// Affiche les paramètres d'un cycle
void afficherCycleSettings(const CycleSettings *cycle);

// Sauvegarde un cycle dans l'historique
void sauvegarderCycle(CycleHistory *hist, const CycleSettings *cycle);

// Affiche l'historique des cycles
void afficherCycleHistory(const CycleHistory *hist);

#endif