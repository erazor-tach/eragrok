#include "daily_targets.h"
#include <stdio.h>

void initDefaultTargets(DailyTargets *targets, float poids) {
    // Exemple de calcul pour un homme modérément actif
    targets->caloriesCible = 33 * poids;       // ~2800 pour 85kg
    targets->proteinesCible = 2.2 * poids;     // ~187g
    targets->glucidesCible = 4 * poids;        // ~340g
    targets->lipidesCible = 1 * poids;         // ~85g
    targets->eauCible = 3.0;                   // 3 litres
}

void initDailyProgress(DailyProgress *progress) {
    progress->consomme.calories = 0;
    progress->consomme.proteines = 0;
    progress->consomme.glucides = 0;
    progress->consomme.lipides = 0;
    progress->consomme.eau = 0;
    // On laisse les objectifs inchangés (à définir séparément)
}

void setDailyTargets(DailyProgress *progress, float calories, float proteines, float glucides, float lipides, float eau) {
    progress->objectifs.caloriesCible = calories;
    progress->objectifs.proteinesCible = proteines;
    progress->objectifs.glucidesCible = glucides;
    progress->objectifs.lipidesCible = lipides;
    progress->objectifs.eauCible = eau;
}

void addFood(DailyProgress *progress, float calories, float proteines, float glucides, float lipides) {
    progress->consomme.calories += calories;
    progress->consomme.proteines += proteines;
    progress->consomme.glucides += glucides;
    progress->consomme.lipides += lipides;
}

void addWater(DailyProgress *progress, float litres) {
    progress->consomme.eau += litres;
}

void addMeal(DailyProgress *progress, const float *calories, const float *proteines,
             const float *glucides, const float *lipides, int nbAliments) {
    for (int i = 0; i < nbAliments; i++) {
        progress->consomme.calories += calories[i];
        progress->consomme.proteines += proteines[i];
        progress->consomme.glucides += glucides[i];
        progress->consomme.lipides += lipides[i];
    }
}

void getProgressPercent(const DailyProgress *progress, float *pCal, float *pProt, float *pGluc, float *pLip, float *pEau) {
    if (progress->objectifs.caloriesCible > 0)
        *pCal = (progress->consomme.calories / progress->objectifs.caloriesCible) * 100;
    else
        *pCal = 0;
    if (progress->objectifs.proteinesCible > 0)
        *pProt = (progress->consomme.proteines / progress->objectifs.proteinesCible) * 100;
    else
        *pProt = 0;
    if (progress->objectifs.glucidesCible > 0)
        *pGluc = (progress->consomme.glucides / progress->objectifs.glucidesCible) * 100;
    else
        *pGluc = 0;
    if (progress->objectifs.lipidesCible > 0)
        *pLip = (progress->consomme.lipides / progress->objectifs.lipidesCible) * 100;
    else
        *pLip = 0;
    if (progress->objectifs.eauCible > 0)
        *pEau = (progress->consomme.eau / progress->objectifs.eauCible) * 100;
    else
        *pEau = 0;
}

void displayProgress(const DailyProgress *progress) {
    float pCal, pProt, pGluc, pLip, pEau;
    getProgressPercent(progress, &pCal, &pProt, &pGluc, &pLip, &pEau);

    printf("\n=== OBJECTIFS DU JOUR ===\n");
    printf("Calories : %.0f / %.0f kcal (%.1f%%)\n", progress->consomme.calories, progress->objectifs.caloriesCible, pCal);
    printf("Protéines : %.1f / %.1f g (%.1f%%)\n", progress->consomme.proteines, progress->objectifs.proteinesCible, pProt);
    printf("Glucides : %.1f / %.1f g (%.1f%%)\n", progress->consomme.glucides, progress->objectifs.glucidesCible, pGluc);
    printf("Lipides : %.1f / %.1f g (%.1f%%)\n", progress->consomme.lipides, progress->objectifs.lipidesCible, pLip);
    printf("Eau : %.1f / %.1f L (%.1f%%)\n", progress->consomme.eau, progress->objectifs.eauCible, pEau);

    // Barres de progression simples
    printf("\n[");
    int barLength = 20;
    int pos = (int)(pCal / 100 * barLength);
    for (int i = 0; i < barLength; i++) {
        if (i < pos) printf("#");
        else printf("-");
    }
    printf("] Calories\n");

    pos = (int)(pProt / 100 * barLength);
    printf("[");
    for (int i = 0; i < barLength; i++) {
        if (i < pos) printf("#");
        else printf("-");
    }
    printf("] Protéines\n");

    pos = (int)(pGluc / 100 * barLength);
    printf("[");
    for (int i = 0; i < barLength; i++) {
        if (i < pos) printf("#");
        else printf("-");
    }
    printf("] Glucides\n");

    pos = (int)(pLip / 100 * barLength);
    printf("[");
    for (int i = 0; i < barLength; i++) {
        if (i < pos) printf("#");
        else printf("-");
    }
    printf("] Lipides\n");

    pos = (int)(pEau / 100 * barLength);
    printf("[");
    for (int i = 0; i < barLength; i++) {
        if (i < pos) printf("#");
        else printf("-");
    }
    printf("] Eau\n");
}