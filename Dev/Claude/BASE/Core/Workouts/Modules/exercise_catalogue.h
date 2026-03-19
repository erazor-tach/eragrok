#ifndef EXERCISE_CATALOGUE_H
#define EXERCISE_CATALOGUE_H

// Groupes musculaires principaux
typedef enum {
    PECTORAUX,
    DOS,
    JAMBES,
    EPAULES,
    BRAS,
    ABDOS,
    CARDIO,
    AUTRE
} GroupeMuscle;

// Structure pour un exercice du catalogue
typedef struct {
    int id;                         // identifiant unique
    char nom[50];
    GroupeMuscle groupe;
    char description[300];          // description / conseils
    char materiel[100];             // ex: "Barre, haltères, poulie"
    char videoUrl[100];             // lien vers vidéo (simulé)
    int niveau;                     // 1 = débutant, 2 = intermédiaire, 3 = avancé
} ExerciceCatalogue;

// Structure pour la collection d'exercices
typedef struct {
    ExerciceCatalogue exercices[100]; // taille max arbitraire
    int nbExercices;
} Catalogue;

// Initialise le catalogue avec des exercices prédéfinis
void initCatalogue(Catalogue *cat);

// Ajoute un exercice au catalogue (pour extension)
void ajouterExerciceCatalogue(Catalogue *cat, const char *nom, GroupeMuscle groupe,
                              const char *desc, const char *materiel, int niveau);

// Recherche un exercice par son nom (première occurrence)
int rechercherExercice(const Catalogue *cat, const char *nom);

// Affiche tous les exercices d'un groupe musculaire
void afficherParGroupe(const Catalogue *cat, GroupeMuscle groupe);

// Affiche les détails d'un exercice (par index)
void afficherExerciceDetail(const Catalogue *cat, int index);

// Affiche tout le catalogue
void afficherCatalogue(const Catalogue *cat);

// Retourne le nom du groupe musculaire sous forme de chaîne
const char* nomGroupe(GroupeMuscle groupe);

#endif