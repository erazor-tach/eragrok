#ifndef PRODUCT_CATALOGUE_H
#define PRODUCT_CATALOGUE_H

// Types d'administration
typedef enum {
    ADMIN_INJECTABLE,
    ADMIN_ORAL,
    ADMIN_AUTRE
} AdminType;

// Catégories de produits
typedef enum {
    CAT_TESTOSTERONE,
    CAT_TRENBOLONE,
    CAT_NANDROLONE,
    CAT_MASTERON,
    CAT_ANAVAR,
    CAT_WINSTROL,
    CAT_CLENBUTEROL,
    CAT_HGH,
    CAT_INSULINE,
    CAT_AUTRE
} ProductCategory;

// Structure pour un produit
typedef struct {
    int id;
    char nom[50];
    ProductCategory categorie;
    AdminType administration;
    float demiVie;              // en heures (0 si inconnu)
    float dosageStandard;       // mg/sem ou mg/jour
    char unite[10];             // "mg", "g", "UI", etc.
    char description[300];
    char effetsSecondaires[300];
} Product;

// Structure pour le catalogue
typedef struct {
    Product produits[100];
    int nbProduits;
} ProductCatalogue;

// Initialise le catalogue avec quelques produits prédéfinis
void initProductCatalogue(ProductCatalogue *cat);

// Ajoute un produit au catalogue
void ajouterProduit(ProductCatalogue *cat,
                    const char *nom,
                    ProductCategory categorie,
                    AdminType admin,
                    float demiVie,
                    float dosageStandard,
                    const char *unite,
                    const char *description,
                    const char *effets);

// Recherche un produit par son nom (retourne l'index)
int rechercherProduit(const ProductCatalogue *cat, const char *nom);

// Affiche tous les produits du catalogue
void afficherCatalogue(const ProductCatalogue *cat);

// Affiche les produits d'une catégorie donnée
void afficherParCategorie(const ProductCatalogue *cat, ProductCategory catg);

// Retourne le nom d'une catégorie
const char* categorieProduitToString(ProductCategory cat);

// Retourne le nom d'un type d'administration
const char* adminToString(AdminType admin);

#endif