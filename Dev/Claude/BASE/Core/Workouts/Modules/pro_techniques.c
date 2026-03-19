#include "pro_techniques.h"
#include <stdio.h>
#include <string.h>

void initBibliotech(Bibliotech *bib) {
    bib->nbTechniques = 0;

    ajouterTechnique(bib,
        "Grip au développé couché",
        "Maintiens la barre avec une prise large, les coudes à 45° du corps pour protéger les épaules. Ne laisse pas les poignets se plier.",
        PECTORAUX, "Développé couché", 2);

    ajouterTechnique(bib,
        "Profondeur au squat",
        "Descends jusqu'à ce que le pli de la hanche soit sous le genou. Utilise une boîte ou un banc pour vérifier la profondeur si nécessaire.",
        JAMBES, "Squat", 2);

    ajouterTechnique(bib,
        "Tractions strictes",
        "Évite le balancement. Garde les épaules basses et tirées en arrière. Monte jusqu'à ce que le menton dépasse la barre.",
        DOS, "Tractions", 2);

    ajouterTechnique(bib,
        "Respiration au soulevé de terre",
        "Prends une grande inspiration avant chaque répétition, bloque le dos et pousse à travers les talons.",
        DOS, "Soulevé de terre", 3);

    ajouterTechnique(bib,
        "Fixation des omoplates au rowing",
        "Tire d'abord les omoplates en arrière avant de plier les bras. Cela engage mieux les dorsaux.",
        DOS, "Rowing barre", 2);

    ajouterTechnique(bib,
        "Descente contrôlée aux dips",
        "Ne te laisse pas tomber. Descends lentement (2-3 secondes) pour augmenter la tension musculaire.",
        PECTORAUX, "Dips", 2);
}

void ajouterTechnique(Bibliotech *bib, const char *titre, const char *desc,
                      GroupeMuscle groupe, const char *exercice, int niveau) {
    if (bib->nbTechniques >= 50) return;
    TechniquePro *t = &bib->techniques[bib->nbTechniques];
    t->id = bib->nbTechniques + 1;
    strcpy(t->titre, titre);
    strcpy(t->description, desc);
    t->groupe = groupe;
    strcpy(t->exerciceConcerne, exercice);
    t->niveau = niveau;
    snprintf(t->videoUrl, sizeof(t->videoUrl), "https://threshold.app/tech/%d", t->id);
    bib->nbTechniques++;
}

void afficherToutesTechniques(const Bibliotech *bib) {
    printf("\n=== BIBLIOTHÈQUE DE TECHNIQUES AVANCÉES (%d) ===\n", bib->nbTechniques);
    for (int i = 0; i < bib->nbTechniques; i++) {
        TechniquePro t = bib->techniques[i];
        printf("%3d. [%s] %s (exercice: %s, niveau %d)\n",
               t.id, nomGroupe(t.groupe), t.titre, t.exerciceConcerne, t.niveau);
    }
}

void afficherTechniquesParGroupe(const Bibliotech *bib, GroupeMuscle groupe) {
    printf("\n=== TECHNIQUES POUR %s ===\n", nomGroupe(groupe));
    for (int i = 0; i < bib->nbTechniques; i++) {
        TechniquePro t = bib->techniques[i];
        if (t.groupe == groupe) {
            printf("  - %s (exercice: %s, niveau %d)\n", t.titre, t.exerciceConcerne, t.niveau);
        }
    }
}

void afficherTechniquesParExercice(const Bibliotech *bib, const char *exercice) {
    printf("\n=== TECHNIQUES POUR L'EXERCICE \"%s\" ===\n", exercice);
    for (int i = 0; i < bib->nbTechniques; i++) {
        TechniquePro t = bib->techniques[i];
        if (strcasecmp(t.exerciceConcerne, exercice) == 0) {
            printf("  - %s (niveau %d)\n", t.titre, t.niveau);
        }
    }
}

void afficherTechniqueDetail(const Bibliotech *bib, int index) {
    if (index < 0 || index >= bib->nbTechniques) return;
    TechniquePro t = bib->techniques[index];
    printf("\n=== TECHNIQUE #%d : %s ===\n", t.id, t.titre);
    printf("Groupe : %s\n", nomGroupe(t.groupe));
    printf("Exercice concerné : %s\n", t.exerciceConcerne);
    printf("Niveau : %d\n", t.niveau);
    printf("Description : %s\n", t.description);
    printf("Vidéo : %s\n", t.videoUrl);
}