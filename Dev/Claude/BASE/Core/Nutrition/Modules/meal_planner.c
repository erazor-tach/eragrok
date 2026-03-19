#include "meal_planner.h"
#include <stdio.h>
#include <string.h>
#include <math.h>

void initBaseAliments(AlimentBase base[], int *nbAliments) {
    *nbAliments = 0;

    // Protéines
    strcpy(base[*nbAliments].nom, "Blanc de poulet");
    base[*nbAliments].calories = 165;
    base[*nbAliments].proteines = 31;
    base[*nbAliments].glucides = 0;
    base[*nbAliments].lipides = 3.6;
    (*nbAliments)++;

    strcpy(base[*nbAliments].nom, "Œuf entier");
    base[*nbAliments].calories = 155; // pour 100g (environ 2 œufs)
    base[*nbAliments].proteines = 13;
    base[*nbAliments].glucides = 1.1;
    base[*nbAliments].lipides = 11;
    (*nbAliments)++;

    strcpy(base[*nbAliments].nom, "Saumon");
    base[*nbAliments].calories = 208;
    base[*nbAliments].proteines = 20;
    base[*nbAliments].glucides = 0;
    base[*nbAliments].lipides = 13;
    (*nbAliments)++;

    strcpy(base[*nbAliments].nom, "Whey");
    base[*nbAliments].calories = 400; // pour 100g
    base[*nbAliments].proteines = 80;
    base[*nbAliments].glucides = 6;
    base[*nbAliments].lipides = 5;
    (*nbAliments)++;

    // Glucides
    strcpy(base[*nbAliments].nom, "Riz blanc");
    base[*nbAliments].calories = 130;
    base[*nbAliments].proteines = 2.4;
    base[*nbAliments].glucides = 28;
    base[*nbAliments].lipides = 0.3;
    (*nbAliments)++;

    strcpy(base[*nbAliments].nom, "Flocons d'avoine");
    base[*nbAliments].calories = 389;
    base[*nbAliments].proteines = 17;
    base[*nbAliments].glucides = 66;
    base[*nbAliments].lipides = 7;
    (*nbAliments)++;

    strcpy(base[*nbAliments].nom, "Patate douce");
    base[*nbAliments].calories = 86;
    base[*nbAliments].proteines = 1.6;
    base[*nbAliments].glucides = 20;
    base[*nbAliments].lipides = 0.1;
    (*nbAliments)++;

    // Lipides
    strcpy(base[*nbAliments].nom, "Huile d'olive");
    base[*nbAliments].calories = 884;
    base[*nbAliments].proteines = 0;
    base[*nbAliments].glucides = 0;
    base[*nbAliments].lipides = 100;
    (*nbAliments)++;

    strcpy(base[*nbAliments].nom, "Beurre de cacahuète");
    base[*nbAliments].calories = 588;
    base[*nbAliments].proteines = 25;
    base[*nbAliments].glucides = 20;
    base[*nbAliments].lipides = 50;
    (*nbAliments)++;

    // Légumes
    strcpy(base[*nbAliments].nom, "Brocoli");
    base[*nbAliments].calories = 34;
    base[*nbAliments].proteines = 2.8;
    base[*nbAliments].glucides = 6;
    base[*nbAliments].lipides = 0.4;
    (*nbAliments)++;
}

float calculerBMR(float poids, float taille, int age, int sexe) {
    // Mifflin-St Jeor
    if (sexe == 1) // homme
        return (10 * poids) + (6.25 * taille) - (5 * age) + 5;
    else // femme
        return (10 * poids) + (6.25 * taille) - (5 * age) - 161;
}

ObjectifsNutrition calculerObjectifs(float poids, float taille, int age, int sexe, const char *objectif) {
    float bmr = calculerBMR(poids, taille, age, sexe);
    float tdee = bmr * 1.55; // facteur d'activité modéré (à ajuster)

    ObjectifsNutrition obj;
    if (strcmp(objectif, "masse") == 0) {
        obj.caloriesCible = tdee + 300; // surplus
        obj.proteinesCible = 2.2 * poids; // 2.2g/kg
        obj.glucidesCible = 4 * poids;
        obj.lipidesCible = 1 * poids;
    } else if (strcmp(objectif, "seche") == 0) {
        obj.caloriesCible = tdee - 400; // déficit
        obj.proteinesCible = 2.5 * poids;
        obj.glucidesCible = 3 * poids;
        obj.lipidesCible = 0.8 * poids;
    } else { // maintien
        obj.caloriesCible = tdee;
        obj.proteinesCible = 1.8 * poids;
        obj.glucidesCible = 3.5 * poids;
        obj.lipidesCible = 0.9 * poids;
    }
    return obj;
}

// Fonction utilitaire pour ajouter un aliment à un repas
static void ajouterAuRepas(RepasPlan *repas, const AlimentBase *aliment, float quantite) {
    if (repas->nbAliments >= 10) return;
    repas->aliments[repas->nbAliments] = *aliment;
    repas->quantites[repas->nbAliments] = quantite;
    repas->totalCalories += (aliment->calories * quantite / 100.0);
    repas->totalProteines += (aliment->proteines * quantite / 100.0);
    repas->totalGlucides += (aliment->glucides * quantite / 100.0);
    repas->totalLipides += (aliment->lipides * quantite / 100.0);
    repas->nbAliments++;
}

void genererPlanJour(PlanJour *plan, const ObjectifsNutrition *obj, const AlimentBase base[], int nbAliments) {
    // Réinitialiser le plan
    plan->nbRepas = 0;
    plan->totalCalories = 0;
    plan->totalProteines = 0;
    plan->totalGlucides = 0;
    plan->totalLipides = 0;

    // Exemple de génération simple (5 repas) avec des quantités fixes
    // Petit-déjeuner
    strcpy(plan->repas[0].nom, "Petit-déjeuner");
    plan->repas[0].nbAliments = 0;
    plan->repas[0].totalCalories = 0;
    // Chercher les aliments dans la base (simplifié)
    for (int i = 0; i < nbAliments; i++) {
        if (strcmp(base[i].nom, "Flocons d'avoine") == 0) {
            ajouterAuRepas(&plan->repas[0], &base[i], 80);
        }
        if (strcmp(base[i].nom, "Œuf entier") == 0) {
            ajouterAuRepas(&plan->repas[0], &base[i], 100); // 2 œufs environ
        }
        if (strcmp(base[i].nom, "Beurre de cacahuète") == 0) {
            ajouterAuRepas(&plan->repas[0], &base[i], 20);
        }
    }
    plan->nbRepas++;

    // Déjeuner
    strcpy(plan->repas[1].nom, "Déjeuner");
    plan->repas[1].nbAliments = 0;
    plan->repas[1].totalCalories = 0;
    for (int i = 0; i < nbAliments; i++) {
        if (strcmp(base[i].nom, "Blanc de poulet") == 0) {
            ajouterAuRepas(&plan->repas[1], &base[i], 150);
        }
        if (strcmp(base[i].nom, "Riz blanc") == 0) {
            ajouterAuRepas(&plan->repas[1], &base[i], 200);
        }
        if (strcmp(base[i].nom, "Brocoli") == 0) {
            ajouterAuRepas(&plan->repas[1], &base[i], 100);
        }
        if (strcmp(base[i].nom, "Huile d'olive") == 0) {
            ajouterAuRepas(&plan->repas[1], &base[i], 10);
        }
    }
    plan->nbRepas++;

    // Collation
    strcpy(plan->repas[2].nom, "Collation");
    plan->repas[2].nbAliments = 0;
    plan->repas[2].totalCalories = 0;
    for (int i = 0; i < nbAliments; i++) {
        if (strcmp(base[i].nom, "Whey") == 0) {
            ajouterAuRepas(&plan->repas[2], &base[i], 30);
        }
    }
    plan->nbRepas++;

    // Dîner
    strcpy(plan->repas[3].nom, "Dîner");
    plan->repas[3].nbAliments = 0;
    plan->repas[3].totalCalories = 0;
    for (int i = 0; i < nbAliments; i++) {
        if (strcmp(base[i].nom, "Saumon") == 0) {
            ajouterAuRepas(&plan->repas[3], &base[i], 150);
        }
        if (strcmp(base[i].nom, "Patate douce") == 0) {
            ajouterAuRepas(&plan->repas[3], &base[i], 200);
        }
        if (strcmp(base[i].nom, "Brocoli") == 0) {
            ajouterAuRepas(&plan->repas[3], &base[i], 100);
        }
    }
    plan->nbRepas++;

    // Calculer les totaux du plan
    for (int i = 0; i < plan->nbRepas; i++) {
        plan->totalCalories += plan->repas[i].totalCalories;
        plan->totalProteines += plan->repas[i].totalProteines;
        plan->totalGlucides += plan->repas[i].totalGlucides;
        plan->totalLipides += plan->repas[i].totalLipides;
    }
}

void afficherPlanJour(const PlanJour *plan) {
    printf("\n=== PLAN JOURNALIER ===\n");
    printf("Objectifs : %.0f kcal, P:%.1f g, G:%.1f g, L:%.1f g\n",
           plan->totalCalories, plan->totalProteines, plan->totalGlucides, plan->totalLipides);
    for (int i = 0; i < plan->nbRepas; i++) {
        RepasPlan r = plan->repas[i];
        printf("\n%s :\n", r.nom);
        for (int j = 0; j < r.nbAliments; j++) {
            printf("  - %s (%.0fg) : %.0f kcal\n", r.aliments[j].nom, r.quantites[j],
                   r.aliments[j].calories * r.quantites[j] / 100.0);
        }
        printf("  Total repas : %.0f kcal (P:%.1f, G:%.1f, L:%.1f)\n",
               r.totalCalories, r.totalProteines, r.totalGlucides, r.totalLipides);
    }
}

void afficherPlanSemaine(const PlanSemaine *semaine) {
    printf("\n=== PLAN HEBDOMADAIRE ===\n");
    for (int i = 0; i < semaine->nbJours; i++) {
        printf("Jour %d : %.0f kcal, P:%.1f g, G:%.1f g, L:%.1f g\n", i+1,
               semaine->jours[i].totalCalories,
               semaine->jours[i].totalProteines,
               semaine->jours[i].totalGlucides,
               semaine->jours[i].totalLipides);
    }
}