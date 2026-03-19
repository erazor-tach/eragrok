#include "advanced_nutrition.h"
#include <stdio.h>
#include <string.h>

float calculerIMC(float poids, float taille) {
    // taille en cm, on convertit en m
    float tailleM = taille / 100.0;
    return poids / (tailleM * tailleM);
}

void initPlanMasse(PlanJour *plan) {
    plan->nbRepas = 4;
    plan->totalCalories = 0;
    plan->totalProteines = 0;
    plan->totalGlucides = 0;
    plan->totalLipides = 0;

    // Petit-déjeuner
    strcpy(plan->repas[0].nom, "Petit-déjeuner");
    plan->repas[0].nbAliments = 3;
    strcpy(plan->repas[0].aliments[0].nom, "Flocons avoine");
    plan->repas[0].aliments[0].calories = 150;
    plan->repas[0].aliments[0].proteines = 5;
    plan->repas[0].aliments[0].glucides = 27;
    plan->repas[0].aliments[0].lipides = 3;
    plan->repas[0].aliments[0].quantite = 100;

    strcpy(plan->repas[0].aliments[1].nom, "Lait");
    plan->repas[0].aliments[1].calories = 50;
    plan->repas[0].aliments[1].proteines = 3.5;
    plan->repas[0].aliments[1].glucides = 5;
    plan->repas[0].aliments[1].lipides = 1.5;
    plan->repas[0].aliments[1].quantite = 200;

    strcpy(plan->repas[0].aliments[2].nom, "Whey");
    plan->repas[0].aliments[2].calories = 120;
    plan->repas[0].aliments[2].proteines = 24;
    plan->repas[0].aliments[2].glucides = 2;
    plan->repas[0].aliments[2].lipides = 1;
    plan->repas[0].aliments[2].quantite = 30;

    // Déjeuner (similaire, on simplifie)
    strcpy(plan->repas[1].nom, "Déjeuner");
    plan->repas[1].nbAliments = 2;
    strcpy(plan->repas[1].aliments[0].nom, "Poulet");
    plan->repas[1].aliments[0].calories = 165;
    plan->repas[1].aliments[0].proteines = 31;
    plan->repas[1].aliments[0].glucides = 0;
    plan->repas[1].aliments[0].lipides = 3.6;
    plan->repas[1].aliments[0].quantite = 150;

    strcpy(plan->repas[1].aliments[1].nom, "Riz");
    plan->repas[1].aliments[1].calories = 130;
    plan->repas[1].aliments[1].proteines = 2.4;
    plan->repas[1].aliments[1].glucides = 28;
    plan->repas[1].aliments[1].lipides = 0.3;
    plan->repas[1].aliments[1].quantite = 200;

    // Ajouter dîner, collation...

    // Calcul des totaux (simplifié)
    for (int i = 0; i < plan->nbRepas; i++) {
        for (int j = 0; j < plan->repas[i].nbAliments; j++) {
            Aliment *a = &plan->repas[i].aliments[j];
            // On suppose que les valeurs sont pour la quantité donnée (pas pour 100g)
            plan->totalCalories += a->calories;
            plan->totalProteines += a->proteines;
            plan->totalGlucides += a->glucides;
            plan->totalLipides += a->lipides;
        }
    }
}

void afficherPlan(const PlanJour *plan) {
    printf("\n=== PLAN ALIMENTAIRE ===\n");
    for (int i = 0; i < plan->nbRepas; i++) {
        printf("\n%s :\n", plan->repas[i].nom);
        for (int j = 0; j < plan->repas[i].nbAliments; j++) {
            Aliment a = plan->repas[i].aliments[j];
            printf("  - %s (%dg) : %.0f kcal, P:%.1f G:%.1f L:%.1f\n",
                   a.nom, a.quantite, a.calories, a.proteines, a.glucides, a.lipides);
        }
    }
    printf("\nTOTAUX : %.0f kcal, Protéines: %.1f g, Glucides: %.1f g, Lipides: %.1f g\n",
           plan->totalCalories, plan->totalProteines, plan->totalGlucides, plan->totalLipides);
}

void ajouterArticle(ArticleCourse *liste, int *nbArticles, const char *nom, float quantite) {
    strcpy(liste[*nbArticles].nom, nom);
    liste[*nbArticles].quantite = quantite;
    liste[*nbArticles].achete = 0;
    (*nbArticles)++;
}

void afficherListeCourses(const ArticleCourse *liste, int nbArticles) {
    printf("\n=== LISTE DE COURSES ===\n");
    for (int i = 0; i < nbArticles; i++) {
        printf("%s - %.1f g %s\n", liste[i].nom, liste[i].quantite, liste[i].achete ? "[Acheté]" : "");
    }
}