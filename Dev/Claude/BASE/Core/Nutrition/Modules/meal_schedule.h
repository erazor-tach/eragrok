#ifndef MEAL_SCHEDULE_H
#define MEAL_SCHEDULE_H

// Structure pour un aliment avec sa quantité dans un repas
typedef struct {
    char nom[50];
    float quantite;       // en grammes
} AlimentQuantite;

// Structure pour un repas planifié
typedef struct {
    char type[30];        // ex: "Petit-déjeuner", "Déjeuner", "Dîner", "Collation"
    int heure;            // heure prévue (0-23)
    int minute;           // minute
    AlimentQuantite aliments[10];
    int nbAliments;
    float totalCalories;  // calculé à partir des aliments (nécessite une base)
    float totalProteines;
    float totalGlucides;
    float totalLipides;
} RepasSchedule;

// Structure pour une journée de repas
typedef struct {
    char jour[15];        // "Lundi", "Mardi", etc.
    RepasSchedule repas[6]; // max 6 repas par jour
    int nbRepas;
} JourSchedule;

// Structure pour la semaine
typedef struct {
    JourSchedule jours[7];
    int nbJours;
} SemaineSchedule;

// Initialise une semaine vide
void initSemaineSchedule(SemaineSchedule *semaine);

// Ajoute un repas à un jour donné
void ajouterRepasSchedule(SemaineSchedule *semaine, const char *jour,
                          const char *type, int heure, int minute);

// Ajoute un aliment à un repas (doit être appelé après ajouterRepasSchedule)
void ajouterAlimentRepas(SemaineSchedule *semaine, const char *jour, const char *type,
                         const char *nomAliment, float quantite);

// Calcule les totaux nutritionnels d'un repas (si on a une base d'aliments)
void calculerTotauxRepas(RepasSchedule *repas); // à compléter avec base externe

// Affiche le planning d'une journée
void afficherJourSchedule(const JourSchedule *jour);

// Affiche le planning complet de la semaine
void afficherSemaineSchedule(const SemaineSchedule *semaine);

#endif