#ifndef SHOPPING_LIST_H
#define SHOPPING_LIST_H

// Structure pour un article de course
typedef struct {
    char nom[50];
    float quantite;       // en grammes ou unités
    char unite[10];       // "g", "kg", "unité", "L", etc.
    int achete;           // 0 = non acheté, 1 = acheté
    char categorie[30];   // "Protéines", "Légumes", etc. (optionnel)
} ArticleCourse;

// Structure pour la liste de courses
typedef struct {
    ArticleCourse articles[100];
    int nbArticles;
} ShoppingList;

// Initialise une liste vide
void initShoppingList(ShoppingList *liste);

// Ajoute un article à la liste (si déjà présent, cumule les quantités)
void ajouterArticle(ShoppingList *liste, const char *nom, float quantite, const char *unite, const char *categorie);

// Supprime un article de la liste (par nom)
void supprimerArticle(ShoppingList *liste, const char *nom);

// Marque un article comme acheté (ou non)
void marquerAchete(ShoppingList *liste, const char *nom, int achete);

// Affiche toute la liste de courses
void afficherListe(const ShoppingList *liste);

// Affiche uniquement les articles non achetés
void afficherRestant(const ShoppingList *liste);

// Vide la liste (supprime tous les articles)
void viderListe(ShoppingList *liste);

// Génère une liste de courses à partir d'un plan de repas (optionnel, nécessite un autre module)
// void genererDepuisPlan(ShoppingList *liste, const PlanSemaine *plan);

#endif