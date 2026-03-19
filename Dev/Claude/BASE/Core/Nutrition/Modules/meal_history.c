#include "meal_history.h"
#include <stdio.h>
#include <string.h>
#include <time.h>

void initMealHistory(MealHistory *hist) {
    hist->nbJours = 0;
}

// Fonction utilitaire pour trouver ou créer une journée dans l'historique
static JourHistorique* trouverOuCreerJour(MealHistory *hist, time_t date) {
    // Normaliser la date à minuit
    struct tm *tm = localtime(&date);
    tm->tm_hour = 0;
    tm->tm_min = 0;
    tm->tm_sec = 0;
    time_t jour = mktime(tm);

    // Chercher si le jour existe déjà
    for (int i = 0; i < hist->nbJours; i++) {
        if (hist->jours[i].date == jour) {
            return &hist->jours[i];
        }
    }
    // Sinon, créer un nouveau jour
    if (hist->nbJours >= 100) return NULL;
    JourHistorique *j = &hist->jours[hist->nbJours];
    j->date = jour;
    j->nbRepas = 0;
    j->totalCaloriesJour = 0;
    j->totalProteinesJour = 0;
    j->totalGlucidesJour = 0;
    j->totalLipidesJour = 0;
    hist->nbJours++;
    return j;
}

void ajouterRepasHistorique(MealHistory *hist,
                            const char *type,
                            const AlimentConsomme aliments[],
                            int nbAliments,
                            time_t date) {
    if (date == 0) date = time(NULL);
    JourHistorique *jour = trouverOuCreerJour(hist, date);
    if (!jour || jour->nbRepas >= 10) return;

    RepasHistorique *repas = &jour->repas[jour->nbRepas];
    repas->date = date;
    strcpy(repas->type, type);
    repas->nbAliments = nbAliments;
    repas->totalCalories = 0;
    repas->totalProteines = 0;
    repas->totalGlucides = 0;
    repas->totalLipides = 0;

    for (int i = 0; i < nbAliments; i++) {
        repas->aliments[i] = aliments[i];
        repas->totalCalories += aliments[i].calories;
        repas->totalProteines += aliments[i].proteines;
        repas->totalGlucides += aliments[i].glucides;
        repas->totalLipides += aliments[i].lipides;
    }

    jour->totalCaloriesJour += repas->totalCalories;
    jour->totalProteinesJour += repas->totalProteines;
    jour->totalGlucidesJour += repas->totalGlucides;
    jour->totalLipidesJour += repas->totalLipides;

    jour->nbRepas++;
}

void afficherJourHistorique(const MealHistory *hist, int indexJour) {
    if (indexJour < 0 || indexJour >= hist->nbJours) return;
    JourHistorique j = hist->jours[indexJour];
    char dateStr[30];
    strftime(dateStr, sizeof(dateStr), "%d/%m/%Y", localtime(&j.date));
    printf("\n=== %s ===\n", dateStr);
    printf("Total jour : %.0f kcal, P:%.1f g, G:%.1f g, L:%.1f g\n",
           j.totalCaloriesJour, j.totalProteinesJour, j.totalGlucidesJour, j.totalLipidesJour);
    for (int r = 0; r < j.nbRepas; r++) {
        RepasHistorique rep = j.repas[r];
        char heureStr[20];
        strftime(heureStr, sizeof(heureStr), "%H:%M", localtime(&rep.date));
        printf("\n  %s (%s) :\n", rep.type, heureStr);
        for (int a = 0; a < rep.nbAliments; a++) {
            AlimentConsomme al = rep.aliments[a];
            printf("    - %s : %.0fg (%.0f kcal, P:%.1f, G:%.1f, L:%.1f)\n",
                   al.nom, al.quantite, al.calories, al.proteines, al.glucides, al.lipides);
        }
        printf("    Total repas : %.0f kcal\n", rep.totalCalories);
    }
}

void afficherHistoriqueComplet(const MealHistory *hist) {
    printf("\n=== HISTORIQUE DES REPAS ===\n");
    for (int i = 0; i < hist->nbJours; i++) {
        JourHistorique j = hist->jours[i];
        char dateStr[30];
        strftime(dateStr, sizeof(dateStr), "%d/%m/%Y", localtime(&j.date));
        printf("%s : %d repas, %.0f kcal\n", dateStr, j.nbRepas, j.totalCaloriesJour);
    }
}

void afficherMoyennesRecentes(const MealHistory *hist, int nbJours) {
    if (hist->nbJours == 0) return;
    int debut = hist->nbJours - nbJours;
    if (debut < 0) debut = 0;
    int joursComptes = hist->nbJours - debut;
    float sumCal = 0, sumP = 0, sumG = 0, sumL = 0;
    for (int i = debut; i < hist->nbJours; i++) {
        JourHistorique j = hist->jours[i];
        sumCal += j.totalCaloriesJour;
        sumP += j.totalProteinesJour;
        sumG += j.totalGlucidesJour;
        sumL += j.totalLipidesJour;
    }
    printf("\n=== MOYENNES SUR %d JOURS ===\n", joursComptes);
    printf("Calories : %.0f kcal/jour\n", sumCal / joursComptes);
    printf("Protéines : %.1f g/jour\n", sumP / joursComptes);
    printf("Glucides : %.1f g/jour\n", sumG / joursComptes);
    printf("Lipides : %.1f g/jour\n", sumL / joursComptes);
}