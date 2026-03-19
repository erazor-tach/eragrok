#ifndef PRO_TECHNIQUES_H
#define PRO_TECHNIQUES_H

#include "exercise_catalogue.h" // pour réutiliser GroupeMuscle si besoin

// Structure pour une technique avancée
typedef struct {
    int id;
    char titre[100];
    char description[500];
    GroupeMuscle groupe;         // groupe musculaire concerné (ou -1 pour général)
    char exerciceConcerne[50];   // nom de l'exercice spécifique (optionnel)
    int niveau;                  // 1 = débutant, 2 = intermédiaire, 3 = avancé
    char videoUrl[150];          // lien vers une démonstration
} TechniquePro;

// Collection de techniques
typedef struct {
    TechniquePro techniques[50];
    int nbTechniques;
} Bibliotech;

// Initialise la bibliothèque avec quelques techniques pré-définies
void initBibliotech(Bibliotech *bib);

// Ajoute une technique à la bibliothèque
void ajouterTechnique(Bibliotech *bib, const char *titre, const char *desc,
                      GroupeMuscle groupe, const char *exercice, int niveau);

// Affiche toutes les techniques (liste simple)
void afficherToutesTechniques(const Bibliotech *bib);

// Affiche les techniques pour un groupe musculaire donné
void afficherTechniquesParGroupe(const Bibliotech *bib, GroupeMuscle groupe);

// Affiche les techniques pour un exercice spécifique
void afficherTechniquesParExercice(const Bibliotech *bib, const char *exercice);

// Affiche le détail d'une technique (par index)
void afficherTechniqueDetail(const Bibliotech *bib, int index);

#endif