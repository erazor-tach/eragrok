#include "exercise_catalogue.h"
#include <stdio.h>
#include <string.h>

const char* nomGroupe(GroupeMuscle groupe) {
    switch (groupe) {
        case PECTORAUX: return "Pectoraux";
        case DOS: return "Dos";
        case JAMBES: return "Jambes";
        case EPAULES: return "Épaules";
        case BRAS: return "Bras";
        case ABDOS: return "Abdominaux";
        case CARDIO: return "Cardio";
        default: return "Autre";
    }
}

void initCatalogue(Catalogue *cat) {
    cat->nbExercices = 0;

    ajouterExerciceCatalogue(cat, "Développé couché", PECTORAUX,
        "Allongé sur un banc, descendre la barre jusqu'à la poitrine puis pousser.",
        "Barre, banc", 2);

    ajouterExerciceCatalogue(cat, "Dips", PECTORAUX,
        "Soutenir le poids sur les barres parallèles, descendre puis remonter.",
        "Barres parallèles, ceinture lestée", 2);

    ajouterExerciceCatalogue(cat, "Tractions", DOS,
        "Suspendu à une barre, tirer le menton au-dessus de la barre.",
        "Barre de traction, prise large/serrée", 2);

    ajouterExerciceCatalogue(cat, "Rowing barre", DOS,
        "Penché en avant, tirer la barre vers le bas-ventre.",
        "Barre", 2);

    ajouterExerciceCatalogue(cat, "Squat", JAMBES,
        "Barre sur les épaules, fléchir les jambes jusqu'à cuisses parallèles au sol.",
        "Barre, cage à squat", 2);

    ajouterExerciceCatalogue(cat, "Presse à cuisses", JAMBES,
        "Pousser la plateforme avec les pieds, en contrôlant la descente.",
        "Presse inclinée", 1);

    ajouterExerciceCatalogue(cat, "Développé militaire", EPAULES,
        "Assis ou debout, pousser la barre au-dessus de la tête.",
        "Barre, banc", 2);

    ajouterExerciceCatalogue(cat, "Curl barre", BRAS,
        "Debout, barre en mains, fléchir les coudes pour amener la barre aux épaules.",
        "Barre", 1);

    ajouterExerciceCatalogue(cat, "Crunch", ABDOS,
        "Allongé, relever le buste en contractant les abdominaux.",
        "Tapis", 1);

    ajouterExerciceCatalogue(cat, "Course à pied", CARDIO,
        "Courir à intensité modérée ou élevée.",
        "Tapis ou extérieur", 1);
}

void ajouterExerciceCatalogue(Catalogue *cat, const char *nom, GroupeMuscle groupe,
                              const char *desc, const char *materiel, int niveau) {
    if (cat->nbExercices >= 100) return;
    ExerciceCatalogue *ex = &cat->exercices[cat->nbExercices];
    ex->id = cat->nbExercices + 1;
    strcpy(ex->nom, nom);
    ex->groupe = groupe;
    strcpy(ex->description, desc);
    strcpy(ex->materiel, materiel);
    ex->niveau = niveau;
    snprintf(ex->videoUrl, sizeof(ex->videoUrl), "https://threshold.app/exos/%d", ex->id); // simulé
    cat->nbExercices++;
}

int rechercherExercice(const Catalogue *cat, const char *nom) {
    for (int i = 0; i < cat->nbExercices; i++) {
        if (strcasecmp(cat->exercices[i].nom, nom) == 0) {
            return i;
        }
    }
    return -1;
}

void afficherParGroupe(const Catalogue *cat, GroupeMuscle groupe) {
    printf("\n=== Exercices - %s ===\n", nomGroupe(groupe));
    for (int i = 0; i < cat->nbExercices; i++) {
        if (cat->exercices[i].groupe == groupe) {
            printf("  %d. %s (niveau %d)\n", i+1, cat->exercices[i].nom, cat->exercices[i].niveau);
        }
    }
}

void afficherExerciceDetail(const Catalogue *cat, int index) {
    if (index < 0 || index >= cat->nbExercices) return;
    ExerciceCatalogue ex = cat->exercices[index];
    printf("\n=== %s (ID %d) ===\n", ex.nom, ex.id);
    printf("Groupe : %s\n", nomGroupe(ex.groupe));
    printf("Niveau : %d\n", ex.niveau);
    printf("Matériel : %s\n", ex.materiel);
    printf("Description : %s\n", ex.description);
    printf("Vidéo : %s\n", ex.videoUrl);
}

void afficherCatalogue(const Catalogue *cat) {
    printf("\n=== CATALOGUE DES EXERCICES (%d) ===\n", cat->nbExercices);
    for (int i = 0; i < cat->nbExercices; i++) {
        ExerciceCatalogue ex = cat->exercices[i];
        printf("%3d. %-25s [%s] (niv.%d)\n", ex.id, ex.nom, nomGroupe(ex.groupe), ex.niveau);
    }
}