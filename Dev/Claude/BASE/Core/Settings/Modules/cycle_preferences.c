#include "cycle_preferences.h"
#include <stdio.h>
#include <string.h>

void initCyclePreferences(CyclePreferences *prefs) {
    prefs->defaultDurationWeeks = 12;
    prefs->pctDelayDays = 14;
    strcpy(prefs->defaultPCTProtocol, "Nolvadex 40/40/20/20");
    prefs->defaultWaterTarget = 3.0;

    prefs->alerts.acneThreshold = 5.0;
    prefs->alerts.aggressionThreshold = 6.0;
    prefs->alerts.insomniaThreshold = 5.0;
    prefs->alerts.enableAlerts = 1;

    prefs->autoReminders = 1;
}

void setDefaultCycleDuration(CyclePreferences *prefs, int weeks) {
    if (weeks >= 4 && weeks <= 52) prefs->defaultDurationWeeks = weeks;
}

void setPCTDelay(CyclePreferences *prefs, int days) {
    if (days >= 0 && days <= 30) prefs->pctDelayDays = days;
}

void setDefaultPCTProtocol(CyclePreferences *prefs, const char *protocol) {
    strncpy(prefs->defaultPCTProtocol, protocol, sizeof(prefs->defaultPCTProtocol) - 1);
    prefs->defaultPCTProtocol[sizeof(prefs->defaultPCTProtocol) - 1] = '\0';
}

void setDefaultWaterTarget(CyclePreferences *prefs, float liters) {
    if (liters > 0) prefs->defaultWaterTarget = liters;
}

void setAlertThresholds(CyclePreferences *prefs, float acne, float aggression, float insomnia, int enable) {
    prefs->alerts.acneThreshold = acne;
    prefs->alerts.aggressionThreshold = aggression;
    prefs->alerts.insomniaThreshold = insomnia;
    prefs->alerts.enableAlerts = enable;
}

void setAutoReminders(CyclePreferences *prefs, int enable) {
    prefs->autoReminders = enable;
}

int getDefaultCycleDuration(const CyclePreferences *prefs) {
    return prefs->defaultDurationWeeks;
}

int getPCTDelay(const CyclePreferences *prefs) {
    return prefs->pctDelayDays;
}

const char* getDefaultPCTProtocol(const CyclePreferences *prefs) {
    return prefs->defaultPCTProtocol;
}

float getDefaultWaterTarget(const CyclePreferences *prefs) {
    return prefs->defaultWaterTarget;
}

CycleAlertThresholds getAlertThresholds(const CyclePreferences *prefs) {
    return prefs->alerts;
}

int getAutoReminders(const CyclePreferences *prefs) {
    return prefs->autoReminders;
}

void displayCyclePreferences(const CyclePreferences *prefs) {
    printf("\n=== PARAMÈTRES CYCLE (par défaut) ===\n");
    printf("Durée cycle par défaut : %d semaines\n", prefs->defaultDurationWeeks);
    printf("Délai PCT : %d jours après fin cycle\n", prefs->pctDelayDays);
    printf("Protocole PCT par défaut : %s\n", prefs->defaultPCTProtocol);
    printf("Objectif eau : %.1f L/jour\n", prefs->defaultWaterTarget);

    printf("Alertes effets secondaires : %s\n", prefs->alerts.enableAlerts ? "Activées" : "Désactivées");
    if (prefs->alerts.enableAlerts) {
        printf("  Seuil acné : %.1f/10\n", prefs->alerts.acneThreshold);
        printf("  Seuil agressivité : %.1f/10\n", prefs->alerts.aggressionThreshold);
        printf("  Seuil insomnie : %.1f/10\n", prefs->alerts.insomniaThreshold);
    }

    printf("Création automatique des rappels d'injection : %s\n", prefs->autoReminders ? "Oui" : "Non");
}