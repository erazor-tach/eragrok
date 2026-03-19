#ifndef PROGRESS_COMPARISON_H
#define PROGRESS_COMPARISON_H

// Structure représentant une période (ex: semaine)
typedef struct {
    char nom[30];               // ex: "Semaine 12", "Mars 2026"
    float poidsMoyen;            // poids de corps moyen (kg)
    float forceMoyenne;          // 1RM moyen (pour un exercice représentatif)
    float volumeTotal;           // volume total soulevé (kg)
    int nbSeances;               // nombre de séances
    float sommeilMoyen;          // heures de sommeil moyennes
    float energieMoyenne;        // énergie moyenne (0-10)
} PeriodeStats;

// Calcule la différence absolue entre deux périodes
typedef struct {
    float poidsDiff;             // différence absolue
    float forceDiff;
    float volumeDiff;
    int seancesDiff;
    float sommeilDiff;
    float energieDiff;
    float poidsPct;               // différence en pourcentage
    float forcePct;
    float volumePct;
    float sommeilPct;
    float energiePct;
} ComparisonResult;

// Compare deux périodes et retourne les différences
ComparisonResult comparerPeriodes(const PeriodeStats *periode1, const PeriodeStats *periode2);

// Affiche un rapport de comparaison
void afficherComparaison(const PeriodeStats *periode1, const PeriodeStats *periode2, const ComparisonResult *res);

// Initialise une période avec des données d'exemple
void initPeriodeExemple(PeriodeStats *periode, const char *nom, float poids, float force, float volume, int seances, float sommeil, float energie);

#endif