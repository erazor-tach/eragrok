#include "shopping_list.h"
#include <stdio.h>
#include <string.h>

void initShoppingList(ShoppingList *liste) {
    liste->nbArticles = 0;
}

void ajouterArticle(ShoppingList *liste, const char *nom, float quantite, const char *unite, const char *categorie) {
    // Chercher si l'article existe déjà
    for (int i = 0; i < liste->nbArticles; i++) {
        if (strcasecmp(liste->articles[i].nom, nom) == 0) {
            // Ajouter la quantité (en supposant la même unité)
            liste->articles[i].quantite += quantite;
            return;
        }
    }
    // Nouvel article
    if (liste->nbArticles >= 100) return;
    ArticleCourse *a = &liste->articles[liste->nbArticles];
    strcpy(a->nom, nom);
    a->quantite = quantite;
    strcpy(a->unite, unite);
    a->achete = 0;
    strcpy(a->categorie, categorie);
    liste->nbArticles++;
}

void supprimerArticle(ShoppingList *liste, const char *nom) {
    for (int i = 0; i < liste->nbArticles; i++) {
        if (strcasecmp(liste->articles[i].nom, nom) == 0) {
            // Décaler les suivants
            for (int j = i; j < liste->nbArticles - 1; j++) {
                liste->articles[j] = liste->articles[j+1];
            }
            liste->nbArticles--;
            return;
        }
    }
}

void marquerAchete(ShoppingList *liste, const char *nom, int achete) {
    for (int i = 0; i < liste->nbArticles; i++) {
        if (strcasecmp(liste->articles[i].nom, nom) == 0) {
            liste->articles[i].achete = achete;
            return;
        }
    }
}

void afficherListe(const ShoppingList *liste) {
    printf("\n=== LISTE DE COURSES (%d articles) ===\n", liste->nbArticles);
    for (int i = 0; i < liste->nbArticles; i++) {
        ArticleCourse a = liste->articles[i];
        printf("%s [%s] : %.1f %s %s\n",
               a.nom,
               a.categorie,
               a.quantite,
               a.unite,
               a.achete ? "[ACHETÉ]" : "");
    }
}

void afficherRestant(const ShoppingList *liste) {
    printf("\n=== ARTICLES RESTANTS ===\n");
    int restant = 0;
    for (int i = 0; i < liste->nbArticles; i++) {
        if (!liste->articles[i].achete) {
            ArticleCourse a = liste->articles[i];
            printf("%s : %.1f %s\n", a.nom, a.quantite, a.unite);
            restant++;
        }
    }
    if (restant == 0) printf("Tout est acheté !\n");
}

void viderListe(ShoppingList *liste) {
    liste->nbArticles = 0;
}