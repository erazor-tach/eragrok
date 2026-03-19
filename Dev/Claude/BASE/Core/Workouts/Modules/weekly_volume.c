#include "weekly_volume.h"
#include <stdio.h>
#include <string.h>

void initVolumeWeek(VolumeWeek *week, int semaine) {
    week->numeroSemaine = semaine;
    week->nbJours = 0;
    week->volumeTotalSemaine = 0.0;
    for (int i = 0; i < 7; i++) {
        week->jours[i].jour[0] = '\0';
        week->jours[i].nbExercices = 0;
        week->jours[i].volumeTotalJour = 0.0;
    }
}

void ajouterExerciceVolume(VolumeWeek *week, const char *jour, const char *exercice,
                           int series, int reps, float charge) {
    // Chercher si le jour existe déjà
    int jourIndex = -1;
    for (int i = 0; i < week->nbJours; i++) {
        if (strcmp(week->jours[i].jour, jour) == 0) {
            jourIndex = i;
            break;
        }
    }
    // Si le jour n'existe pas, créer une nouvelle entrée
    if (jourIndex == -1) {
        jourIndex = week->nbJours;
        strcpy(week->jours[jourIndex].jour, jour);
        week->jours[jourIndex].nbExercices = 0;
        week->jours[jourIndex].volumeTotalJour = 0.0;
        week->nbJours++;
    }

    VolumeDay *day = &week->jours[jourIndex];
    if (day->nbExercices >= 10) return; // limite atteinte

    VolumeEntry *entry = &day->exercices[day->nbExercices];
    strcpy(entry->exercice, exercice);
    entry->series = series;
    entry->repetitions = reps;
    entry->charge = charge;
    entry->volume = series * reps * charge; // volume en kg
    day->volumeTotalJour += entry->volume;
    day->nbExercices++;

    // On ne recalcule pas le total semaine ici, appel séparé
}

void calculerVolumeTotal(VolumeWeek *week) {
    week->volumeTotalSemaine = 0.0;
    for (int i = 0; i < week->nbJours; i++) {
        week->volumeTotalSemaine += week->jours[i].volumeTotalJour;
    }
}

void afficherVolumeWeek(const VolumeWeek *week) {
    printf("\n=== VOLUME SEMAINE %d ===\n", week->numeroSemaine);
    printf("Volume total : %.2f tonnes\n", week->volumeTotalSemaine / 1000.0);
    for (int i = 0; i < week->nbJours; i++) {
        VolumeDay day = week->jours[i];
        printf("\n%s :\n", day.jour);
        for (int j = 0; j < day.nbExercices; j++) {
            VolumeEntry e = day.exercices[j];
            printf("  - %s : %dx%d @ %.1f kg = %.1f kg\n",
                   e.exercice, e.series, e.repetitions, e.charge, e.volume);
        }
        printf("  Total jour : %.1f kg\n", day.volumeTotalJour);
    }
}

void afficherTendance(const VolumeWeek *semaine1, const VolumeWeek *semaine2) {
    float diff = semaine2->volumeTotalSemaine - semaine1->volumeTotalSemaine;
    float pourcent = (semaine1->volumeTotalSemaine > 0) ?
                     (diff / semaine1->volumeTotalSemaine) * 100 : 0.0;

    printf("\n=== TENDANCE ===\n");
    printf("Semaine %d : %.2f t\n", semaine1->numeroSemaine, semaine1->volumeTotalSemaine / 1000.0);
    printf("Semaine %d : %.2f t\n", semaine2->numeroSemaine, semaine2->volumeTotalSemaine / 1000.0);
    if (diff > 0) {
        printf("⬆️ Augmentation de %.2f t (%.1f%%)\n", diff / 1000.0, pourcent);
    } else if (diff < 0) {
        printf("⬇️ Diminution de %.2f t (%.1f%%)\n", -diff / 1000.0, -pourcent);
    } else {
        printf("➡️ Stable\n");
    }
}