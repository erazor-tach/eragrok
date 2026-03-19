#include "recent_activity.h"
#include <stdio.h>
#include <string.h>
#include <time.h>

#define MAX_ACTIVITIES 100

static Activity historique[MAX_ACTIVITIES];
static int nbActivites = 0;

void ajouterActivite(ActivityType type, const char *desc, float valeur, const char *unite) {
    if (nbActivites >= MAX_ACTIVITIES) {
        // Décaler ou ignorer ? Pour simplifier, on ignore
        return;
    }
    time(&historique[nbActivites].timestamp);
    historique[nbActivites].type = type;
    strncpy(historique[nbActivites].description, desc, sizeof(historique[nbActivites].description) - 1);
    historique[nbActivites].description[sizeof(historique[nbActivites].description)-1] = '\0';
    historique[nbActivites].valeur = valeur;
    strncpy(historique[nbActivites].unite, unite, sizeof(historique[nbActivites].unite)-1);
    historique[nbActivites].unite[sizeof(historique[nbActivites].unite)-1] = '\0';
    nbActivites++;
}

int getNbActivites(void) {
    return nbActivites;
}

const Activity* getActivite(int index) {
    if (index < 0 || index >= nbActivites) return NULL;
    return &historique[index];
}

// Fonction utilitaire pour formater une date
static void formatDate(time_t t, char *buf, size_t len) {
    struct tm *tm_info = localtime(&t);
    strftime(buf, len, "%d/%m %H:%M", tm_info);
}

void afficherActivitesRecentes(int n) {
    if (n > nbActivites) n = nbActivites;
    printf("\n=== ACTIVITÉS RÉCENTES ===\n");
    for (int i = nbActivites - 1; i >= nbActivites - n; i--) {
        const Activity *a = &historique[i];
        char date[20];
        formatDate(a->timestamp, date, sizeof(date));
        const char *typeStr = "";
        switch (a->type) {
            case ACTIVITY_WORKOUT: typeStr = "🏋️"; break;
            case ACTIVITY_NUTRITION: typeStr = "🥗"; break;
            case ACTIVITY_CYCLE: typeStr = "💉"; break;
            case ACTIVITY_PROGRESS: typeStr = "📈"; break;
        }
        printf("%s [%s] %s - %s : %.1f %s\n", typeStr, date, a->description, typeStr, a->valeur, a->unite);
    }
}