#include "coach_advice.h"
#include <stdio.h>
#include <string.h>

int genererConseils(const DonneesUtilisateur *donnees, Conseil conseils[], int maxConseils) {
    int nb = 0;

    // Exemple de règle : si le DC est faible par rapport au poids de corps (on suppose poids 85kg)
    if (donnees->dernierDC < 100) {
        strcpy(conseils[nb].titre, "Progresser au développé couché");
        strcpy(conseils[nb].description, "Incorpore des séries de 5 répétitions lourdes et du travail accessoire (dips, épaules).");
        conseils[nb].priorite = 1;
        nb++;
    }

    // Règle : si le squat est faible
    if (donnees->dernierSquat < 140) {
        strcpy(conseils[nb].titre, "Renforcer les jambes");
        strcpy(conseils[nb].description, "Ajoute des squats avant et du travail de mobilité pour augmenter la profondeur.");
        conseils[nb].priorite = 2;
        nb++;
    }

    // Règle : volume hebdomadaire bas
    if (donnees->volumeHebdo < 10.0) {
        strcpy(conseils[nb].titre, "Augmenter le volume");
        strcpy(conseils[nb].description, "Tu es en dessous de 10 tonnes/semaine. Ajoute une série supplémentaire sur tes exercices principaux.");
        conseils[nb].priorite = 2;
        nb++;
    }

    // Règle : sommeil insuffisant
    if (donnees->sommeilMoyen < 7.0) {
        strcpy(conseils[nb].titre, "Améliorer la récupération");
        strcpy(conseils[nb].description, "Vise 7-8h de sommeil. Évite les écrans avant de dormir et prends de la mélatonine si besoin.");
        conseils[nb].priorite = 1;
        nb++;
    }

    // Règle : énergie basse
    if (donnees->energieMoyenne < 6.0) {
        strcpy(conseils[nb].titre, "Gérer la fatigue");
        strcpy(conseils[nb].description, "Envisage une semaine de deload ou augmente tes apports caloriques.");
        conseils[nb].priorite = 1;
        nb++;
    }

    // Conseil par défaut si aucun déclenché (optionnel)
    if (nb == 0) {
        strcpy(conseils[nb].titre, "Bon travail !");
        strcpy(conseils[nb].description, "Continue comme ça, tu progresses bien. Pense à varier tes exercices.");
        conseils[nb].priorite = 3;
        nb++;
    }

    return nb;
}

void afficherConseils(const Conseil conseils[], int nbConseils) {
    printf("\n=== CONSEILS DU COACH ===\n");
    for (int i = 0; i < nbConseils; i++) {
        printf("[Priorité %d] %s :\n", conseils[i].priorite, conseils[i].titre);
        printf("  %s\n\n", conseils[i].description);
    }
}