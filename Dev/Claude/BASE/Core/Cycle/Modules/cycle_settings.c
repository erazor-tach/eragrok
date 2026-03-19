#include "cycle_settings.h"
#include <stdio.h>
#include <string.h>
#include <time.h>

void initCycleSettings(CycleSettings *cycle, const char *nom, time_t debut, int duree) {
    strcpy(cycle->nomCycle, nom);
    cycle->dateDebut = debut;
    cycle->dureeSemaines = duree;
    cycle->nbProduits = 0;
    cycle->eauQuotidienne = 3.0; // défaut
    cycle->notes[0] = '\0';
    cycle->pctActif = 0;
    strcpy(cycle->pctProtocole, "");
    cycle->dateDebutPCT = 0;
}

void ajouterProduitCycle(CycleSettings *cycle, const char *nom, float dosage, const char *unite, float quantiteTotale) {
    if (cycle->nbProduits >= 10) return;
    CycleProduct *p = &cycle->produits[cycle->nbProduits];
    strcpy(p->nom, nom);
    p->dosage = dosage;
    strcpy(p->unite, unite);
    p->quantiteTotale = quantiteTotale;
    cycle->nbProduits++;
}

time_t calculerDatePCT(const CycleSettings *cycle, int delaiJours) {
    // La PCT commence après la fin du cycle + delai
    time_t finCycle = cycle->dateDebut + cycle->dureeSemaines * 7 * 24 * 3600;
    return finCycle + delaiJours * 24 * 3600;
}

void afficherCycleSettings(const CycleSettings *cycle) {
    char debutStr[30], finStr[30], pctStr[30];
    time_t finCycle = cycle->dateDebut + cycle->dureeSemaines * 7 * 24 * 3600;
    strftime(debutStr, sizeof(debutStr), "%d/%m/%Y", localtime(&cycle->dateDebut));
    strftime(finStr, sizeof(finStr), "%d/%m/%Y", localtime(&finCycle));

    printf("\n=== PARAMÈTRES DU CYCLE : %s ===\n", cycle->nomCycle);
    printf("Début : %s\n", debutStr);
    printf("Durée : %d semaines (fin prévue le %s)\n", cycle->dureeSemaines, finStr);
    printf("Produits :\n");
    for (int i = 0; i < cycle->nbProduits; i++) {
        CycleProduct p = cycle->produits[i];
        printf("  - %s : %.0f %s", p.nom, p.dosage, p.unite);
        if (p.quantiteTotale > 0) printf(" (total cycle: %.0f)", p.quantiteTotale);
        printf("\n");
    }
    printf("Eau recommandée : %.1f L/jour\n", cycle->eauQuotidienne);
    if (cycle->pctActif) {
        if (cycle->dateDebutPCT != 0) {
            strftime(pctStr, sizeof(pctStr), "%d/%m/%Y", localtime(&cycle->dateDebutPCT));
            printf("PCT : %s (début le %s)\n", cycle->pctProtocole, pctStr);
        } else {
            printf("PCT : %s (date à définir)\n", cycle->pctProtocole);
        }
    }
    if (cycle->notes[0] != '\0') {
        printf("Notes : %s\n", cycle->notes);
    }
}

void sauvegarderCycle(CycleHistory *hist, const CycleSettings *cycle) {
    if (hist->nbCycles >= 20) return;
    hist->cycles[hist->nbCycles] = *cycle;
    hist->nbCycles++;
}

void afficherCycleHistory(const CycleHistory *hist) {
    printf("\n=== HISTORIQUE DES CYCLES ===\n");
    for (int i = 0; i < hist->nbCycles; i++) {
        CycleSettings c = hist->cycles[i];
        char debutStr[30];
        strftime(debutStr, sizeof(debutStr), "%d/%m/%Y", localtime(&c.dateDebut));
        printf("%d. %s (début %s, %d semaines, %d produits)\n",
               i+1, c.nomCycle, debutStr, c.dureeSemaines, c.nbProduits);
    }
}