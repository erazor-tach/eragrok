#ifndef RECENT_ACTIVITY_H
#define RECENT_ACTIVITY_H

#include <time.h>

// Types d'activité possibles
typedef enum {
    ACTIVITY_WORKOUT,
    ACTIVITY_NUTRITION,
    ACTIVITY_CYCLE,
    ACTIVITY_PROGRESS
} ActivityType;

// Structure pour une activité
typedef struct {
    time_t timestamp;           // date et heure
    ActivityType type;          // type d'activité
    char description[100];      // description courte
    float valeur;               // valeur associée (ex: volume, kcal, etc.)
    char unite[10];             // unité de la valeur
} Activity;

// Ajoute une activité à l'historique (stocké en mémoire statique)
void ajouterActivite(ActivityType type, const char *desc, float valeur, const char *unite);

// Retourne le nombre d'activités enregistrées
int getNbActivites(void);

// Récupère une activité par son index (0 = plus récente ?)
const Activity* getActivite(int index);

// Affiche les n dernières activités
void afficherActivitesRecentes(int n);

#endif