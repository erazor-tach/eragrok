#include "food_catalogue.h"
#include <stdio.h>
#include <string.h>

const char* categorieToString(CategorieAliment cat) {
    switch (cat) {
        case CAT_PROTEINES: return "Protéines";
        case CAT_GLUCIDES:  return "Glucides";
        case CAT_LIPIDES:   return "Lipides";
        case CAT_LEGUMES:   return "Légumes";
        case CAT_FRUITS:    return "Fruits";
        default:            return "Autre";
    }
}

void initCatalogue(FoodCatalogue *cat) {
    cat->nbAliments = 0;

    ajouterAliment(cat, "Blanc de poulet", CAT_PROTEINES, 165, 31, 0, 3.6, "g");
    ajouterAliment(cat, "Œuf entier", CAT_PROTEINES, 155, 13, 1.1, 11, "g");
    ajouterAliment(cat, "Saumon", CAT_PROTEINES, 208, 20, 0, 13, "g");
    ajouterAliment(cat, "Whey", CAT_PROTEINES, 400, 80, 6, 5, "g");

    ajouterAliment(cat, "Riz blanc", CAT_GLUCIDES, 130, 2.4, 28, 0.3, "g");
    ajouterAliment(cat, "Flocons d'avoine", CAT_GLUCIDES, 389, 17, 66, 7, "g");
    ajouterAliment(cat, "Patate douce", CAT_GLUCIDES, 86, 1.6, 20, 0.1, "g");

    ajouterAliment(cat, "Huile d'olive", CAT_LIPIDES, 884, 0, 0, 100, "ml");
    ajouterAliment(cat, "Beurre de cacahuète", CAT_LIPIDES, 588, 25, 20, 50, "g");

    ajouterAliment(cat, "Brocoli", CAT_LEGUMES, 34, 2.8, 6, 0.4, "g");
    ajouterAliment(cat, "Épinards", CAT_LEGUMES, 23, 2.9, 3.6, 0.4, "g");

    ajouterAliment(cat, "Pomme", CAT_FRUITS, 52, 0.3, 14, 0.2, "g");
    ajouterAliment(cat, "Banane", CAT_FRUITS, 89, 1.1, 23, 0.3, "g");
}

void ajouterAliment(FoodCatalogue *cat,
                    const char *nom,
                    CategorieAliment categorie,
                    float calories,
                    float proteines,
                    float glucides,
                    float lipides,
                    const char *unite) {
    if (cat->nbAliments >= 200) return;
    Aliment *a = &cat->aliments[cat->nbAliments];
    a->id = cat->nbAliments + 1;
    strcpy(a->nom, nom);
    a->categorie = categorie;
    a->calories = calories;
    a->proteines = proteines;
    a->glucides = glucides;
    a->lipides = lipides;
    strcpy(a->unite, unite);
    cat->nbAliments++;
}

int rechercherAliment(const FoodCatalogue *cat, const char *nom) {
    for (int i = 0; i < cat->nbAliments; i++) {
        if (strcasecmp(cat->aliments[i].nom, nom) == 0) {
            return i;
        }
    }
    return -1;
}

void afficherCatalogue(const FoodCatalogue *cat) {
    printf("\n=== CATALOGUE ALIMENTAIRE (%d aliments) ===\n", cat->nbAliments);
    for (int i = 0; i < cat->nbAliments; i++) {
        Aliment a = cat->aliments[i];
        printf("%3d. %-20s [%s] : %.0f kcal, P:%.1f, G:%.1f, L:%.1f (pour 100%s)\n",
               a.id, a.nom, categorieToString(a.categorie),
               a.calories, a.proteines, a.glucides, a.lipides, a.unite);
    }
}

void afficherParCategorie(const FoodCatalogue *cat, CategorieAliment catg) {
    printf("\n=== ALIMENTS : %s ===\n", categorieToString(catg));
    for (int i = 0; i < cat->nbAliments; i++) {
        Aliment a = cat->aliments[i];
        if (a.categorie == catg) {
            printf("  - %s : %.0f kcal, P:%.1f, G:%.1f, L:%.1f (100%s)\n",
                   a.nom, a.calories, a.proteines, a.glucides, a.lipides, a.unite);
        }
    }
}