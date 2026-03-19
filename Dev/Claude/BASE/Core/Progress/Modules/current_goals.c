#include "current_goals.h"
#include <stdio.h>
#include <string.h>
#include <time.h>

void initCurrentGoals(CurrentGoals *cg) {
    cg->nbGoals = 0;
}

void addGoal(CurrentGoals *cg, const char *nom, GoalType type, const char *exercice,
             float cible, time_t dateFin) {
    if (cg->nbGoals >= 50) return;
    Goal *g = &cg->goals[cg->nbGoals];
    g->id = cg->nbGoals + 1;
    strcpy(g->nom, nom);
    g->type = type;
    if (exercice) strcpy(g->exercice, exercice);
    else g->exercice[0] = '\0';
    g->valeurCible = cible;
    g->valeurActuelle = 0;
    g->dateDebut = time(NULL);
    g->dateFin = dateFin;
    g->atteint = 0;
    cg->nbGoals++;
}

void updateGoalProgress(CurrentGoals *cg, int id, float nouvelleValeur) {
    for (int i = 0; i < cg->nbGoals; i++) {
        if (cg->goals[i].id == id) {
            cg->goals[i].valeurActuelle = nouvelleValeur;
            if (nouvelleValeur >= cg->goals[i].valeurCible) {
                cg->goals[i].atteint = 1;
            }
            return;
        }
    }
}

void removeGoal(CurrentGoals *cg, int id) {
    for (int i = 0; i < cg->nbGoals; i++) {
        if (cg->goals[i].id == id) {
            for (int j = i; j < cg->nbGoals - 1; j++) {
                cg->goals[j] = cg->goals[j+1];
            }
            cg->nbGoals--;
            return;
        }
    }
}

float getGoalProgress(const Goal *g) {
    if (g->valeurCible == 0) return 0;
    float prog = (g->valeurActuelle / g->valeurCible) * 100;
    if (prog > 100) prog = 100;
    return prog;
}

void displayAllGoals(const CurrentGoals *cg) {
    printf("\n=== OBJECTIFS EN COURS ===\n");
    for (int i = 0; i < cg->nbGoals; i++) {
        Goal g = cg->goals[i];
        printf("%d. %s", g.id, g.nom);
        if (g.type == GOAL_STRENGTH) printf(" [%s]", g.exercice);
        printf(" : %.1f / %.1f", g.valeurActuelle, g.valeurCible);
        if (g.atteint) printf(" (ATTEINT)");
        else {
            float prog = getGoalProgress(&g);
            printf(" (%.0f%%)", prog);
        }
        if (g.dateFin != 0) {
            char buf[20];
            strftime(buf, sizeof(buf), "%d/%m/%Y", localtime(&g.dateFin));
            printf(" - échéance %s", buf);
        }
        printf("\n");
    }
}

void displayActiveGoals(const CurrentGoals *cg) {
    printf("\n=== OBJECTIFS ACTIFS ===\n");
    for (int i = 0; i < cg->nbGoals; i++) {
        if (!cg->goals[i].atteint) {
            Goal g = cg->goals[i];
            printf("%d. %s", g.id, g.nom);
            if (g.type == GOAL_STRENGTH) printf(" [%s]", g.exercice);
            printf(" : %.1f / %.1f (%.0f%%)", g.valeurActuelle, g.valeurCible, getGoalProgress(&g));
            printf("\n");
        }
    }
}