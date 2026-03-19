#ifndef UNLOCKED_BADGES_H
#define UNLOCKED_BADGES_H

#include <time.h>

// Structure pour un badge débloqué
typedef struct {
    int id;
    char nom[50];
    char description[200];
    char icone[20];          // emoji ou code
    time_t dateDeblocage;
} UnlockedBadge;

// Structure pour la collection de badges débloqués
typedef struct {
    UnlockedBadge badges[100];
    int nbBadges;
} UnlockedCollection;

// Initialise la collection (vide)
void initUnlockedCollection(UnlockedCollection *uc);

// Ajoute un badge débloqué (vérifie s'il n'est pas déjà présent)
void addUnlockedBadge(UnlockedCollection *uc, int id, const char *nom, const char *desc, const char *icone);

// Supprime un badge (si nécessaire)
void removeUnlockedBadge(UnlockedCollection *uc, int id);

// Affiche tous les badges débloqués
void displayAllUnlocked(const UnlockedCollection *uc);

// Affiche les badges débloqués récents (par date)
void displayRecentUnlocked(const UnlockedCollection *uc, int limit);

#endif