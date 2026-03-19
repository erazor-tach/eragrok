#include "cycle_history.h"
#include <stdio.h>
#include <string.h>
#include <time.h>

void initCycleHistory(CycleHistoryArchive *arch) {
    arch->nbCycles = 0;
}

void ajouterCycleHistorique(CycleHistoryArchive *arch,
                            const char *nom,
                            time_t debut,
                            time_t fin,
                            const HistoricCycleProduct produits[],
                            int nbProduits,
                            int pct,
                            const char *notes,
                            float priseMasse,
                            float progressionForce) {
    if (arch->nbCycles >= 20) return;
    HistoricCycleEntry *c = &arch->cycles[arch->nbCycles];
    c->id = arch->nbCycles + 1;
    strcpy(c->nom, nom);
    c->dateDebut = debut;
    c->dateFin = fin;
    c->nbProduits = nbProduits;
    for (int i = 0; i < nbProduits; i++) {
        c->produits[i] = produits[i];
    }
    c->pctInclus = pct;
    strcpy(c->notes, notes);
    c->priseMasse = priseMasse;
    c->progressionForce = progressionForce;
    arch->nbCycles++;
}

void supprimerCycleHistorique(CycleHistoryArchive *arch, int id) {
    for (int i = 0; i < arch->nbCycles; i++) {
        if (arch->cycles[i].id == id) {
            for (int j = i; j < arch->nbCycles - 1; j++) {
                arch->cycles[j] = arch->cycles[j+1];
            }
            arch->nbCycles--;
            return;
        }
    }
}

int dureeCycleJours(const HistoricCycleEntry *cycle) {
    return (int)((cycle->dateFin - cycle->dateDebut) / (24 * 3600));
}

void afficherListeCycles(const CycleHistoryArchive *arch) {
    printf("\n=== HISTORIQUE DES CYCLES ===\n");
    if (arch->nbCycles == 0) {
        printf("Aucun cycle enregistré.\n");
        return;
    }
    for (int i = 0; i < arch->nbCycles; i++) {
        HistoricCycleEntry c = arch->cycles[i];
        char debutStr[20], finStr[20];
        strftime(debutStr, sizeof(debutStr), "%d/%m/%Y", localtime(&c.dateDebut));
        strftime(finStr, sizeof(finStr), "%d/%m/%Y", localtime(&c.dateFin));
        printf("ID %d : %s (%s - %s, %d jours)\n",
               c.id, c.nom, debutStr, finStr, dureeCycleJours(&c));
    }
}

void afficherCycleDetail(const CycleHistoryArchive *arch, int index) {
    if (index < 0 || index >= arch->nbCycles) return;
    HistoricCycleEntry c = arch->cycles[index];
    char debutStr[30], finStr[30];
    strftime(debutStr, sizeof(debutStr), "%d/%m/%Y", localtime(&c.dateDebut));
    strftime(finStr, sizeof(finStr), "%d/%m/%Y", localtime(&c.dateFin));

    printf("\n=== CYCLE : %s ===\n", c.nom);
    printf("Début : %s\n", debutStr);
    printf("Fin : %s\n", finStr);
    printf("Durée : %d jours\n", dureeCycleJours(&c));
    printf("Produits :\n");
    for (int i = 0; i < c.nbProduits; i++) {
        printf("  - %s : %.0f %s\n", c.produits[i].nom, c.produits[i].dosage, c.produits[i].unite);
    }
    printf("PCT inclus : %s\n", c.pctInclus ? "Oui" : "Non");
    printf("Prise de masse : %.1f kg\n", c.priseMasse);
    printf("Progression force : %.1f kg\n", c.progressionForce);
    printf("Notes : %s\n", c.notes);
}