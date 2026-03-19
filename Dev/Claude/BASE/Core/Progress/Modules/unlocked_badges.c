#include "unlocked_badges.h"
#include <stdio.h>
#include <string.h>
#include <time.h>

void initUnlockedCollection(UnlockedCollection *uc) {
    uc->nbBadges = 0;
}

void addUnlockedBadge(UnlockedCollection *uc, int id, const char *nom, const char *desc, const char *icone) {
    // Vérifier si déjà présent
    for (int i = 0; i < uc->nbBadges; i++) {
        if (uc->badges[i].id == id) return;
    }
    if (uc->nbBadges >= 100) return;
    UnlockedBadge *b = &uc->badges[uc->nbBadges];
    b->id = id;
    strcpy(b->nom, nom);
    strcpy(b->description, desc);
    strcpy(b->icone, icone);
    b->dateDeblocage = time(NULL);
    uc->nbBadges++;
}

void removeUnlockedBadge(UnlockedCollection *uc, int id) {
    for (int i = 0; i < uc->nbBadges; i++) {
        if (uc->badges[i].id == id) {
            for (int j = i; j < uc->nbBadges - 1; j++) {
                uc->badges[j] = uc->badges[j+1];
            }
            uc->nbBadges--;
            return;
        }
    }
}

void displayAllUnlocked(const UnlockedCollection *uc) {
    printf("\n=== SUCCÈS DÉBLOQUÉS ===\n");
    if (uc->nbBadges == 0) {
        printf("Aucun succès débloqué pour le moment.\n");
        return;
    }
    for (int i = 0; i < uc->nbBadges; i++) {
        UnlockedBadge b = uc->badges[i];
        char dateStr[30];
        strftime(dateStr, sizeof(dateStr), "%d/%m/%Y", localtime(&b.dateDeblocage));
        printf("%s %s : %s (débloqué le %s)\n", b.icone, b.nom, b.description, dateStr);
    }
}

void displayRecentUnlocked(const UnlockedCollection *uc, int limit) {
    printf("\n=== SUCCÈS RÉCENTS ===\n");
    int start = (uc->nbBadges > limit) ? uc->nbBadges - limit : 0;
    for (int i = start; i < uc->nbBadges; i++) {
        UnlockedBadge b = uc->badges[i];
        char dateStr[30];
        strftime(dateStr, sizeof(dateStr), "%d/%m/%Y", localtime(&b.dateDeblocage));
        printf("%s %s - %s\n", b.icone, b.nom, dateStr);
    }
}