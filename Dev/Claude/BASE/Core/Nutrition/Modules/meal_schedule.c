#include "meal_schedule.h"
#include <stdio.h>
#include <string.h>

void initSemaineSchedule(SemaineSchedule *semaine) {
    semaine->nbJours = 0;
    // Optionnel : initialiser les 7 jours avec des noms
    const char *jours[] = {"Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"};
    for (int i = 0; i < 7; i++) {
        strcpy(semaine->jours[i].jour, jours[i]);
        semaine->jours[i].nbRepas = 0;
    }
    semaine->nbJours = 7;
}

void ajouterRepasSchedule(SemaineSchedule *semaine, const char *jour,
                          const char *type, int heure, int minute) {
    // Trouver l'index du jour
    int idxJour = -1;
    for (int i = 0; i < semaine->nbJours; i++) {
        if (strcmp(semaine->jours[i].jour, jour) == 0) {
            idxJour = i;
            break;
        }
    }
    if (idxJour == -1) return; // jour non trouvé

    JourSchedule *jr = &semaine->jours[idxJour];
    if (jr->nbRepas >= 6) return;

    RepasSchedule *repas = &jr->repas[jr->nbRepas];
    strcpy(repas->type, type);
    repas->heure = heure;
    repas->minute = minute;
    repas->nbAliments = 0;
    repas->totalCalories = 0;
    repas->totalProteines = 0;
    repas->totalGlucides = 0;
    repas->totalLipides = 0;

    jr->nbRepas++;
}

void ajouterAlimentRepas(SemaineSchedule *semaine, const char *jour, const char *type,
                         const char *nomAliment, float quantite) {
    int idxJour = -1;
    for (int i = 0; i < semaine->nbJours; i++) {
        if (strcmp(semaine->jours[i].jour, jour) == 0) {
            idxJour = i;
            break;
        }
    }
    if (idxJour == -1) return;

    JourSchedule *jr = &semaine->jours[idxJour];
    // Chercher le repas correspondant au type
    for (int i = 0; i < jr->nbRepas; i++) {
        if (strcmp(jr->repas[i].type, type) == 0) {
            RepasSchedule *repas = &jr->repas[i];
            if (repas->nbAliments >= 10) return;
            AlimentQuantite *aq = &repas->aliments[repas->nbAliments];
            strcpy(aq->nom, nomAliment);
            aq->quantite = quantite;
            repas->nbAliments++;
            // Les totaux ne sont pas recalculés ici (nécessite base)
            return;
        }
    }
}

void calculerTotauxRepas(RepasSchedule *repas) {
    // Cette fonction nécessite une base de données d'aliments (externe)
    // Pour l'instant, on laisse vide ou on fait une version simplifiée
    // On pourrait passer un tableau d'aliments avec valeurs nutritionnelles
    // Pour le squelette, on ne fait rien.
}

void afficherJourSchedule(const JourSchedule *jour) {
    printf("\n--- %s ---\n", jour->jour);
    for (int i = 0; i < jour->nbRepas; i++) {
        RepasSchedule r = jour->repas[i];
        printf("%s à %02d:%02d\n", r.type, r.heure, r.minute);
        for (int j = 0; j < r.nbAliments; j++) {
            printf("  - %s : %.0fg\n", r.aliments[j].nom, r.aliments[j].quantite);
        }
        printf("  Totaux (est.) : %.0f kcal, P:%.1f, G:%.1f, L:%.1f\n",
               r.totalCalories, r.totalProteines, r.totalGlucides, r.totalLipides);
    }
}

void afficherSemaineSchedule(const SemaineSchedule *semaine) {
    printf("\n=== PLANNING HEBDOMADAIRE ===\n");
    for (int i = 0; i < semaine->nbJours; i++) {
        afficherJourSchedule(&semaine->jours[i]);
    }
}