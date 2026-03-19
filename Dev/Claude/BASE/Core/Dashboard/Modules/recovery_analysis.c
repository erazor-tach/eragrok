#include "recovery_analysis.h"
#include <stdio.h>

void initRecuperationExemple(RecuperationJour *semaine) {
    // Données fictives pour une semaine
    float hrvs[7] = {65, 62, 58, 63, 68, 70, 72};
    float sommeils[7] = {7.5, 7.0, 6.8, 7.2, 8.0, 8.5, 8.2};
    float energies[7] = {8, 7, 6, 7, 8, 9, 9};
    for (int i = 0; i < 7; i++) {
        semaine[i].jour = i+1;
        semaine[i].hrv = hrvs[i];
        semaine[i].sommeilHeures = sommeils[i];
        semaine[i].sommeilQualite = 7.0; // valeur fixe pour l'exemple
        semaine[i].frequenceCardiaqueRepos = 58.0;
        semaine[i].courbatures = 3.0;
        semaine[i].energie = energies[i];
    }
}

float calculerScoreRecuperation(const RecuperationJour *jour) {
    // Pondérations simples pour l'exemple
    float score = 0;
    score += (jour->hrv / 100) * 30;        // max 30 points si HRV = 100
    score += (jour->sommeilHeures / 9) * 30; // max 30 points si 9h
    score += (jour->energie / 10) * 20;      // max 20 points
    score += (10 - jour->courbatures) * 2;   // max 20 points (si courbatures = 0)
    if (score > 100) score = 100;
    return score;
}

void afficherRapportJour(const RecuperationJour *jour) {
    printf("\n--- Récupération Jour %d ---\n", jour->jour);
    printf("HRV : %.1f ms\n", jour->hrv);
    printf("Sommeil : %.1f h (qualité %.1f/10)\n", jour->sommeilHeures, jour->sommeilQualite);
    printf("FC repos : %.0f bpm\n", jour->frequenceCardiaqueRepos);
    printf("Courbatures : %.1f/10\n", jour->courbatures);
    printf("Énergie : %.1f/10\n", jour->energie);
    printf("Score récupération : %.1f/100\n", calculerScoreRecuperation(jour));
}

void afficherResumeSemaine(const ResumeSemaine *resume) {
    printf("\n=== RÉSUMÉ SEMAINE ===\n");
    printf("HRV moyenne : %.1f ms\n", resume->moyenneHRV);
    printf("Sommeil moyen : %.1f h\n", resume->moyenneSommeil);
    printf("Énergie moyenne : %.1f/10\n", resume->moyenneEnergie);
    // On pourrait aussi afficher les tendances
}