#include "achievements.h"
#include <stdio.h>
#include <string.h>
#include <time.h>

void initAchievements(Achievements *ach) {
    ach->nbTotal = 0;
    ach->nbDebloques = 0;

    // Succès liés au nombre de séances
    int i = ach->nbTotal;
    ach->liste[i].id = i+1;
    strcpy(ach->liste[i].nom, "Premier pas");
    strcpy(ach->liste[i].description, "Effectuer sa première séance.");
    strcpy(ach->liste[i].icone, "👟");
    ach->liste[i].debloque = 0;
    ach->nbTotal++;

    i = ach->nbTotal;
    ach->liste[i].id = i+1;
    strcpy(ach->liste[i].nom, "Régulier");
    strcpy(ach->liste[i].description, "Effectuer 10 séances.");
    strcpy(ach->liste[i].icone, "📅");
    ach->liste[i].debloque = 0;
    ach->nbTotal++;

    i = ach->nbTotal;
    strcpy(ach->liste[i].nom, "Habitué");
    strcpy(ach->liste[i].description, "Effectuer 50 séances.");
    strcpy(ach->liste[i].icone, "🔥");
    ach->liste[i].debloque = 0;
    ach->nbTotal++;

    i = ach->nbTotal;
    strcpy(ach->liste[i].nom, "Guerrier");
    strcpy(ach->liste[i].description, "Effectuer 100 séances.");
    strcpy(ach->liste[i].icone, "⚔️");
    ach->liste[i].debloque = 0;
    ach->nbTotal++;

    // Succès liés aux records
    i = ach->nbTotal;
    strcpy(ach->liste[i].nom, "Débutant en force");
    strcpy(ach->liste[i].description, "Atteindre 100 kg au développé couché.");
    strcpy(ach->liste[i].icone, "🏋️");
    ach->liste[i].debloque = 0;
    ach->nbTotal++;

    i = ach->nbTotal;
    strcpy(ach->liste[i].nom, "Intermédiaire");
    strcpy(ach->liste[i].description, "Atteindre 120 kg au développé couché.");
    strcpy(ach->liste[i].icone, "💪");
    ach->liste[i].debloque = 0;
    ach->nbTotal++;

    i = ach->nbTotal;
    strcpy(ach->liste[i].nom, "Avancé");
    strcpy(ach->liste[i].description, "Atteindre 140 kg au développé couché.");
    strcpy(ach->liste[i].icone, "🦍");
    ach->liste[i].debloque = 0;
    ach->nbTotal++;

    i = ach->nbTotal;
    strcpy(ach->liste[i].nom, "Roi du squat");
    strcpy(ach->liste[i].description, "Atteindre 150 kg au squat.");
    strcpy(ach->liste[i].icone, "👑");
    ach->liste[i].debloque = 0;
    ach->nbTotal++;

    // Succès de volume
    i = ach->nbTotal;
    strcpy(ach->liste[i].nom, "Charge lourde");
    strcpy(ach->liste[i].description, "Soulever 10 tonnes au total.");
    strcpy(ach->liste[i].icone, "⛰️");
    ach->liste[i].debloque = 0;
    ach->nbTotal++;

    i = ach->nbTotal;
    strcpy(ach->liste[i].nom, "Déménageur");
    strcpy(ach->liste[i].description, "Soulever 50 tonnes au total.");
    strcpy(ach->liste[i].icone, "🚛");
    ach->liste[i].debloque = 0;
    ach->nbTotal++;

    // Succès de régularité
    i = ach->nbTotal;
    strcpy(ach->liste[i].nom, "7 jours de suite");
    strcpy(ach->liste[i].description, "S'entraîner 7 jours consécutifs.");
    strcpy(ach->liste[i].icone, "📆");
    ach->liste[i].debloque = 0;
    ach->nbTotal++;

    i = ach->nbTotal;
    strcpy(ach->liste[i].nom, "2 semaines intenses");
    strcpy(ach->liste[i].description, "S'entraîner 14 jours consécutifs.");
    strcpy(ach->liste[i].icone, "⚡");
    ach->liste[i].debloque = 0;
    ach->nbTotal++;
}

int verifierAchievements(Achievements *ach,
                         int totalSeances,
                         float meilleurDC,
                         float meilleurSquat,
                         float volumeTotal,
                         int joursConsecutifs) {
    int nouveaux = 0;

    for (int i = 0; i < ach->nbTotal; i++) {
        if (ach->liste[i].debloque) continue;

        int debloque = 0;

        // Séances
        if (strcmp(ach->liste[i].nom, "Premier pas") == 0 && totalSeances >= 1) debloque = 1;
        else if (strcmp(ach->liste[i].nom, "Régulier") == 0 && totalSeances >= 10) debloque = 1;
        else if (strcmp(ach->liste[i].nom, "Habitué") == 0 && totalSeances >= 50) debloque = 1;
        else if (strcmp(ach->liste[i].nom, "Guerrier") == 0 && totalSeances >= 100) debloque = 1;
        // Records DC
        else if (strcmp(ach->liste[i].nom, "Débutant en force") == 0 && meilleurDC >= 100) debloque = 1;
        else if (strcmp(ach->liste[i].nom, "Intermédiaire") == 0 && meilleurDC >= 120) debloque = 1;
        else if (strcmp(ach->liste[i].nom, "Avancé") == 0 && meilleurDC >= 140) debloque = 1;
        // Squat
        else if (strcmp(ach->liste[i].nom, "Roi du squat") == 0 && meilleurSquat >= 150) debloque = 1;
        // Volume
        else if (strcmp(ach->liste[i].nom, "Charge lourde") == 0 && volumeTotal >= 10000) debloque = 1;
        else if (strcmp(ach->liste[i].nom, "Déménageur") == 0 && volumeTotal >= 50000) debloque = 1;
        // Jours consécutifs
        else if (strcmp(ach->liste[i].nom, "7 jours de suite") == 0 && joursConsecutifs >= 7) debloque = 1;
        else if (strcmp(ach->liste[i].nom, "2 semaines intenses") == 0 && joursConsecutifs >= 14) debloque = 1;

        if (debloque) {
            ach->liste[i].debloque = 1;
            ach->liste[i].dateDeblocage = time(NULL);
            nouveaux++;
        }
    }

    // Recompter le nombre débloqués
    int count = 0;
    for (int i = 0; i < ach->nbTotal; i++) {
        if (ach->liste[i].debloque) count++;
    }
    ach->nbDebloques = count;

    return nouveaux;
}

void afficherAchievements(const Achievements *ach) {
    printf("\n=== SUCCÈS (%d/%d) ===\n", ach->nbDebloques, ach->nbTotal);
    for (int i = 0; i < ach->nbTotal; i++) {
        Achievement a = ach->liste[i];
        printf("%s %s : %s ", a.icone, a.nom, a.description);
        if (a.debloque) {
            char buf[20];
            strftime(buf, sizeof(buf), "%d/%m/%Y", localtime(&a.dateDeblocage));
            printf("[DÉBLOQUÉ le %s]\n", buf);
        } else {
            printf("[🔒]\n");
        }
    }
}

void afficherDebloques(const Achievements *ach) {
    printf("\n=== SUCCÈS DÉBLOQUÉS ===\n");
    for (int i = 0; i < ach->nbTotal; i++) {
        if (ach->liste[i].debloque) {
            Achievement a = ach->liste[i];
            char buf[20];
            strftime(buf, sizeof(buf), "%d/%m/%Y", localtime(&a.dateDeblocage));
            printf("%s %s - %s (le %s)\n", a.icone, a.nom, a.description, buf);
        }
    }
}

int totalDebloques(const Achievements *ach) {
    return ach->nbDebloques;
}