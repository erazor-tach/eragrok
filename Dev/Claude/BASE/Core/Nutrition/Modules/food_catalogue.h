#ifndef FOOD_CATALOGUE_H
#define FOOD_CATALOGUE_H

// Catégories d'aliments
typedef enum {
    CAT_PROTEINES,
    CAT_GLUCIDES,
    CAT_LIPIDES,
    CAT_LEGUMES,
    CAT_FRUITS,
    CAT_AUTRE
} CategorieAliment;

// Structure pour un aliment
typedef struct {
    int id;
    char nom[50];
    CategorieAliment categorie;
    float calories;      // pour 100g
    float proteines;
    float glucides;
    float lipides;
    char unite[10];       // "g", "ml", "unité" (par défaut "g")
} Aliment;

// Structure pour le catalogue
typedef struct {
    Aliment aliments[200];  // capacité max
    int nbAliments;
} FoodCatalogue;

// Initialise le catalogue avec quelques aliments de base
void initCatalogue(FoodCatalogue *cat);

// Ajoute un aliment au catalogue
void ajouterAliment(FoodCatalogue *cat,
                    const char *nom,
                    CategorieAliment categorie,
                    float calories,
                    float proteines,
                    float glucides,
                    float lipides,
                    const char *unite);

// Recherche un aliment par son nom (retourne l'index ou -1)
int rechercherAliment(const FoodCatalogue *cat, const char *nom);

// Affiche tous les aliments du catalogue
void afficherCatalogue(const FoodCatalogue *cat);

// Affiche les aliments d'une catégorie donnée
void afficherParCategorie(const FoodCatalogue *cat, CategorieAliment catg);

// Retourne le nom d'une catégorie sous forme de chaîne
const char* categorieToString(CategorieAliment cat);

#endif