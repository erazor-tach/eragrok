#ifndef ACHIEVEMENTS_H
#define ACHIEVEMENTS_H

#include <time.h>

// Structure représentant un succès (badge)
typedef struct {
    int id;
    char nom[50];
    char description[200];
    char icone[20];          // nom d'icône (ex: "🏆", "💪")
    int debloque;            // 0 ou 1
    time_t dateDeblocage;    // timestamp quand débloqué
} Achievement;

// Collection des succès de l'utilisateur
typedef struct {
    Achievement liste[50];   // max 50 succès
    int nbTotal;             // nombre total de succès possibles
    int nbDebloques;         // nombre de succès débloqués
} Achievements;

// Initialise la liste des succès possibles (prédéfinis)
void initAchievements(Achievements *ach);

// Met à jour les succès en fonction des données utilisateur (appelée régulièrement)
// Retourne le nombre de nouveaux succès débloqués
int verifierAchievements(Achievements *ach,
                         int totalSeances,
                         float meilleurDC,
                         float meilleurSquat,
                         float volumeTotal,
                         int joursConsecutifs,
                         /* autres paramètres selon besoins */);

// Affiche tous les succès (débloqués et non débloqués)
void afficherAchievements(const Achievements *ach);

// Affiche uniquement les succès débloqués
void afficherDebloques(const Achievements *ach);

// Retourne le nombre de succès débloqués
int totalDebloques(const Achievements *ach);

#endif