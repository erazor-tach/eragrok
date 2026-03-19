#include "hydration_tracker.h"
#include <stdio.h>
#include <string.h>
#include <time.h>

void initHydrationHistory(HydrationHistory *hist) {
    hist->nbJours = 0;
}

// Fonction utilitaire pour trouver ou créer l'entrée du jour
static HydrationDay* getOrCreateDay(HydrationHistory *hist, time_t date) {
    // Normaliser à minuit
    struct tm *tm = localtime(&date);
    tm->tm_hour = 0;
    tm->tm_min = 0;
    tm->tm_sec = 0;
    time_t jour = mktime(tm);

    // Chercher si le jour existe
    for (int i = 0; i < hist->nbJours; i++) {
        if (hist->jours[i].date == jour) {
            return &hist->jours[i];
        }
    }
    // Créer un nouveau jour
    if (hist->nbJours >= 365) return NULL;
    HydrationDay *day = &hist->jours[hist->nbJours];
    day->date = jour;
    day->objectif = 2.5; // objectif par défaut
    day->consomme = 0;
    hist->nbJours++;
    return day;
}

void setDailyGoal(HydrationHistory *hist, float litres, time_t date) {
    if (date == 0) date = time(NULL);
    HydrationDay *day = getOrCreateDay(hist, date);
    if (day) {
        day->objectif = litres;
    }
}

void addWater(HydrationHistory *hist, float litres) {
    time_t now = time(NULL);
    HydrationDay *day = getOrCreateDay(hist, now);
    if (day) {
        day->consomme += litres;
    }
}

float getTodayProgress(const HydrationHistory *hist) {
    time_t now = time(NULL);
    struct tm *tm = localtime(&now);
    tm->tm_hour = 0; tm->tm_min = 0; tm->tm_sec = 0;
    time_t aujourdhui = mktime(tm);
    for (int i = 0; i < hist->nbJours; i++) {
        if (hist->jours[i].date == aujourdhui) {
            if (hist->jours[i].objectif > 0)
                return (hist->jours[i].consomme / hist->jours[i].objectif) * 100;
            else
                return 0;
        }
    }
    return 0; // aucun jour trouvé
}

void displayToday(const HydrationHistory *hist) {
    time_t now = time(NULL);
    struct tm *tm = localtime(&now);
    tm->tm_hour = 0; tm->tm_min = 0; tm->tm_sec = 0;
    time_t aujourdhui = mktime(tm);
    for (int i = 0; i < hist->nbJours; i++) {
        if (hist->jours[i].date == aujourdhui) {
            HydrationDay d = hist->jours[i];
            float progress = (d.objectif > 0) ? (d.consomme / d.objectif) * 100 : 0;
            printf("\n=== HYDRATATION AUJOURD'HUI ===\n");
            printf("Objectif : %.1f L\n", d.objectif);
            printf("Bu : %.1f L (%.1f%%)\n", d.consomme, progress);
            // Barre de progression
            int barLength = 20;
            int pos = (int)(progress / 100 * barLength);
            printf("[");
            for (int j = 0; j < barLength; j++) {
                if (j < pos) printf("#");
                else printf("-");
            }
            printf("]\n");
            return;
        }
    }
    // Pas d'entrée pour aujourd'hui
    printf("\nAucune donnée pour aujourd'hui. Objectif par défaut : 2.5 L\n");
}

void displayHistory(const HydrationHistory *hist, int nbJours) {
    printf("\n=== HISTORIQUE HYDRATATION ===\n");
    int debut = hist->nbJours - nbJours;
    if (debut < 0) debut = 0;
    for (int i = debut; i < hist->nbJours; i++) {
        HydrationDay d = hist->jours[i];
        char dateStr[30];
        strftime(dateStr, sizeof(dateStr), "%d/%m/%Y", localtime(&d.date));
        printf("%s : %.1f / %.1f L (%.0f%%)\n", dateStr, d.consomme, d.objectif,
               (d.objectif > 0) ? (d.consomme / d.objectif) * 100 : 0);
    }
}