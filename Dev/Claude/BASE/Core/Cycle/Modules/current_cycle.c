#include "current_cycle.h"
#include <stdio.h>
#include <string.h>
#include <time.h>

void initCurrentCycle(CurrentCycle *cycle) {
    cycle->actif = 0;
    cycle->nbProduits = 0;
}

void startCycle(CurrentCycle *cycle, const char *nom, time_t dateDebut, time_t dateFin) {
    strcpy(cycle->nom, nom);
    cycle->dateDebut = dateDebut;
    cycle->dateFin = dateFin;
    cycle->nbProduits = 0;
    cycle->actif = 1;
    cycle->progression = calculateCycleProgress(cycle);
}

void addProductToCycle(CurrentCycle *cycle, const char *nom, float dosage, const char *frequence, const char *voie) {
    if (cycle->nbProduits >= 5) return;
    CycleProduct *p = &cycle->produits[cycle->nbProduits];
    strcpy(p->nom, nom);
    p->dosage = dosage;
    strcpy(p->frequence, frequence);
    strcpy(p->voie, voie);
    cycle->nbProduits++;
}

float calculateCycleProgress(const CurrentCycle *cycle) {
    if (!cycle->actif) return 0;
    time_t now = time(NULL);
    if (now <= cycle->dateDebut) return 0;
    if (now >= cycle->dateFin) return 100;
    float total = (float)(cycle->dateFin - cycle->dateDebut);
    float ecoule = (float)(now - cycle->dateDebut);
    return (ecoule / total) * 100;
}

void displayCurrentCycle(const CurrentCycle *cycle) {
    printf("\n=== CYCLE EN COURS ===\n");
    if (!cycle->actif) {
        printf("Aucun cycle actif.\n");
        return;
    }
    printf("Nom : %s\n", cycle->nom);
    char debut[30], fin[30];
    strftime(debut, sizeof(debut), "%d/%m/%Y", localtime(&cycle->dateDebut));
    strftime(fin, sizeof(fin), "%d/%m/%Y", localtime(&cycle->dateFin));
    printf("Dates : du %s au %s\n", debut, fin);
    printf("Progression : %.1f%%\n", cycle->progression);
    printf("Produits :\n");
    for (int i = 0; i < cycle->nbProduits; i++) {
        CycleProduct p = cycle->produits[i];
        printf("  - %s : %.0f mg/sem (%s) - %s\n", p.nom, p.dosage, p.frequence, p.voie);
    }
}

void endCycle(CurrentCycle *cycle) {
    cycle->actif = 0;
}