#include "progress_comparison.h"
#include <stdio.h>
#include <string.h>
#include <math.h>

ComparisonResult comparerPeriodes(const PeriodeStats *p1, const PeriodeStats *p2) {
    ComparisonResult res;
    res.poidsDiff = p2->poidsMoyen - p1->poidsMoyen;
    res.forceDiff = p2->forceMoyenne - p1->forceMoyenne;
    res.volumeDiff = p2->volumeTotal - p1->volumeTotal;
    res.seancesDiff = p2->nbSeances - p1->nbSeances;
    res.sommeilDiff = p2->sommeilMoyen - p1->sommeilMoyen;
    res.energieDiff = p2->energieMoyenne - p1->energieMoyenne;

    // Pourcentages (éviter division par zéro)
    res.poidsPct = (p1->poidsMoyen != 0) ? (res.poidsDiff / p1->poidsMoyen) * 100 : 0;
    res.forcePct = (p1->forceMoyenne != 0) ? (res.forceDiff / p1->forceMoyenne) * 100 : 0;
    res.volumePct = (p1->volumeTotal != 0) ? (res.volumeDiff / p1->volumeTotal) * 100 : 0;
    res.sommeilPct = (p1->sommeilMoyen != 0) ? (res.sommeilDiff / p1->sommeilMoyen) * 100 : 0;
    res.energiePct = (p1->energieMoyenne != 0) ? (res.energieDiff / p1->energieMoyenne) * 100 : 0;

    return res;
}

void afficherComparaison(const PeriodeStats *p1, const PeriodeStats *p2, const ComparisonResult *res) {
    printf("\n=== COMPARAISON : %s vs %s ===\n", p1->nom, p2->nom);
    printf("Indicateur        %10s  %10s  %10s  %10s\n", p1->nom, p2->nom, "Différence", "Évolution");
    printf("------------------------------------------------------------\n");

    // Poids
    printf("Poids moyen (kg)  %10.1f  %10.1f  %+10.1f  %+9.1f%%\n",
           p1->poidsMoyen, p2->poidsMoyen, res->poidsDiff, res->poidsPct);

    // Force
    printf("Force 1RM (kg)    %10.1f  %10.1f  %+10.1f  %+9.1f%%\n",
           p1->forceMoyenne, p2->forceMoyenne, res->forceDiff, res->forcePct);

    // Volume
    printf("Volume (t)        %10.2f  %10.2f  %+10.2f  %+9.1f%%\n",
           p1->volumeTotal/1000.0, p2->volumeTotal/1000.0, res->volumeDiff/1000.0, res->volumePct);

    // Nombre de séances
    printf("Séances           %10d  %10d  %+10d  %9s\n",
           p1->nbSeances, p2->nbSeances, res->seancesDiff, "-");

    // Sommeil
    printf("Sommeil (h)       %10.1f  %10.1f  %+10.1f  %+9.1f%%\n",
           p1->sommeilMoyen, p2->sommeilMoyen, res->sommeilDiff, res->sommeilPct);

    // Énergie
    printf("Énergie (/10)     %10.1f  %10.1f  %+10.1f  %+9.1f%%\n",
           p1->energieMoyenne, p2->energieMoyenne, res->energieDiff, res->energiePct);

    printf("\nTendance :\n");
    if (res->poidsDiff > 0) printf("  Poids ⬆️\n");
    else if (res->poidsDiff < 0) printf("  Poids ⬇️\n");
    else printf("  Poids ➡️\n");

    if (res->forceDiff > 0) printf("  Force ⬆️\n");
    else if (res->forceDiff < 0) printf("  Force ⬇️\n");
    else printf("  Force ➡️\n");

    if (res->volumeDiff > 0) printf("  Volume ⬆️\n");
    else if (res->volumeDiff < 0) printf("  Volume ⬇️\n");
    else printf("  Volume ➡️\n");
}

void initPeriodeExemple(PeriodeStats *periode, const char *nom, float poids, float force, float volume, int seances, float sommeil, float energie) {
    strcpy(periode->nom, nom);
    periode->poidsMoyen = poids;
    periode->forceMoyenne = force;
    periode->volumeTotal = volume;
    periode->nbSeances = seances;
    periode->sommeilMoyen = sommeil;
    periode->energieMoyenne = energie;
}