#ifndef ADVANCED_NUTRITION_H
#define ADVANCED_NUTRITION_H

// Structure pour un aliment
typedef struct {
    char nom[50];
    float calories;      // pour 100g ou par portion
    float proteines;     // en g
    float glucides;      // en g
    float lipides;       // en g
    int quantite;        // en grammes (par défaut)
} Aliment;

// Structure pour un repas
typedef struct {
    char nom[30];        // ex: "Petit-déjeuner"
    Aliment aliments[10];
    int nbAliments;
} Repas;

// Structure pour un plan alimentaire journalier
typedef struct {
    Repas repas[5];      // max 5 repas par jour
    int nbRepas;
    float totalCalories;
    float totalProteines;
    float totalGlucides;
    float totalLipides;
} PlanJour;

// Structure pour un article de course
typedef struct {
    char nom[50];
    float quantite;      // en grammes ou unités
    int achete;          // 0 ou 1
} ArticleCourse;

// Calcule l'IMC à partir du poids (kg) et de la taille (cm)
float calculerIMC(float poids, float taille);

// Initialise un plan journalier exemple (régime prise de masse)
void initPlanMasse(PlanJour *plan);

// Affiche le plan journalier
void afficherPlan(const PlanJour *plan);

// Ajoute un article à la liste de courses
void ajouterArticle(ArticleCourse *liste, int *nbArticles, const char *nom, float quantite);

// Affiche la liste de courses
void afficherListeCourses(const ArticleCourse *liste, int nbArticles);

#endif