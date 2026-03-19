#include "product_catalogue.h"
#include <stdio.h>
#include <string.h>

const char* categorieProduitToString(ProductCategory cat) {
    switch (cat) {
        case CAT_TESTOSTERONE: return "Testostérone";
        case CAT_TRENBOLONE: return "Trenbolone";
        case CAT_NANDROLONE: return "Nandrolone";
        case CAT_MASTERON: return "Masteron";
        case CAT_ANAVAR: return "Anavar";
        case CAT_WINSTROL: return "Winstrol";
        case CAT_CLENBUTEROL: return "Clenbuterol";
        case CAT_HGH: return "HGH";
        case CAT_INSULINE: return "Insuline";
        default: return "Autre";
    }
}

const char* adminToString(AdminType admin) {
    switch (admin) {
        case ADMIN_INJECTABLE: return "Injectable";
        case ADMIN_ORAL: return "Oral";
        default: return "Autre";
    }
}

void initProductCatalogue(ProductCatalogue *cat) {
    cat->nbProduits = 0;

    ajouterProduit(cat,
        "Testostérone Enanthate",
        CAT_TESTOSTERONE,
        ADMIN_INJECTABLE,
        104,                    // 4.5 jours environ
        500, "mg/sem",
        "Esther longue durée, injections 1-2 fois par semaine.",
        "Gynécomastie, rétention d'eau, acné, agressivité.");

    ajouterProduit(cat,
        "Trenbolone Acétate",
        CAT_TRENBOLONE,
        ADMIN_INJECTABLE,
        72,                     // 3 jours
        200, "mg/sem",
        "Très puissant, augmente la force et la sécheresse musculaire.",
        "Insomnie, sueurs nocturnes, agressivité, baisse de libido.");

    ajouterProduit(cat,
        "Nandrolone Decanoate (Deca)",
        CAT_NANDROLONE,
        ADMIN_INJECTABLE,
        360,                    // 15 jours
        400, "mg/sem",
        "Favorise la prise de masse et le confort articulaire.",
        "Prolactine, baisse de libido, prise de poids.");

    ajouterProduit(cat,
        "Anavar (Oxandrolone)",
        CAT_ANAVAR,
        ADMIN_ORAL,
        9,                      // 9 heures
        50, "mg/jour",
        "Oral doux, utilisé en sèche pour préserver le muscle.",
        "Hépatotoxicité modérée, baisse du HDL.");

    ajouterProduit(cat,
        "Clenbuterol",
        CAT_CLENBUTEROL,
        ADMIN_ORAL,
        34,                     // 34 heures
        120, "mcg/jour",
        "Bronchodilatateur, utilisé pour ses propriétés thermogéniques.",
        "Tremblements, insomnie, tachycardie.");
}

void ajouterProduit(ProductCatalogue *cat,
                    const char *nom,
                    ProductCategory categorie,
                    AdminType admin,
                    float demiVie,
                    float dosageStandard,
                    const char *unite,
                    const char *description,
                    const char *effets) {
    if (cat->nbProduits >= 100) return;
    Product *p = &cat->produits[cat->nbProduits];
    p->id = cat->nbProduits + 1;
    strcpy(p->nom, nom);
    p->categorie = categorie;
    p->administration = admin;
    p->demiVie = demiVie;
    p->dosageStandard = dosageStandard;
    strcpy(p->unite, unite);
    strcpy(p->description, description);
    strcpy(p->effetsSecondaires, effets);
    cat->nbProduits++;
}

int rechercherProduit(const ProductCatalogue *cat, const char *nom) {
    for (int i = 0; i < cat->nbProduits; i++) {
        if (strcasecmp(cat->produits[i].nom, nom) == 0) {
            return i;
        }
    }
    return -1;
}

void afficherCatalogue(const ProductCatalogue *cat) {
    printf("\n=== CATALOGUE PRODUITS ===\n");
    for (int i = 0; i < cat->nbProduits; i++) {
        Product p = cat->produits[i];
        printf("ID %d : %s\n", p.id, p.nom);
        printf("  Catégorie : %s\n", categorieProduitToString(p.categorie));
        printf("  Administration : %s\n", adminToString(p.administration));
        printf("  Demi-vie : %.1f h\n", p.demiVie);
        printf("  Dosage standard : %.0f %s\n", p.dosageStandard, p.unite);
        printf("  Description : %s\n", p.description);
        printf("  Effets secondaires : %s\n", p.effetsSecondaires);
        printf("\n");
    }
}

void afficherParCategorie(const ProductCatalogue *cat, ProductCategory catg) {
    printf("\n=== PRODUITS - %s ===\n", categorieProduitToString(catg));
    for (int i = 0; i < cat->nbProduits; i++) {
        if (cat->produits[i].categorie == catg) {
            Product p = cat->produits[i];
            printf("  %s : %.0f %s\n", p.nom, p.dosageStandard, p.unite);
        }
    }
}