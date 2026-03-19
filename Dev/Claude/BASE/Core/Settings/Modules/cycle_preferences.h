#ifndef CYCLE_PREFERENCES_H
#define CYCLE_PREFERENCES_H

// Seuils d'alerte pour les effets secondaires
typedef struct {
    float acneThreshold;       // seuil d'intensité pour alerte acné (1-10)
    float aggressionThreshold;
    float insomniaThreshold;
    int enableAlerts;          // 0/1
} CycleAlertThresholds;

// Paramètres par défaut pour un nouveau cycle
typedef struct {
    int defaultDurationWeeks;      // durée par défaut en semaines
    int pctDelayDays;               // nombre de jours après cycle pour débuter PCT
    char defaultPCTProtocol[100];   // protocole PCT par défaut
    float defaultWaterTarget;       // objectif eau par défaut (L/jour)
    CycleAlertThresholds alerts;
    int autoReminders;               // créer automatiquement des rappels d'injection
} CyclePreferences;

// Initialise les préférences avec des valeurs par défaut
void initCyclePreferences(CyclePreferences *prefs);

// Setters
void setDefaultCycleDuration(CyclePreferences *prefs, int weeks);
void setPCTDelay(CyclePreferences *prefs, int days);
void setDefaultPCTProtocol(CyclePreferences *prefs, const char *protocol);
void setDefaultWaterTarget(CyclePreferences *prefs, float liters);
void setAlertThresholds(CyclePreferences *prefs, float acne, float aggression, float insomnia, int enable);
void setAutoReminders(CyclePreferences *prefs, int enable);

// Getters
int getDefaultCycleDuration(const CyclePreferences *prefs);
int getPCTDelay(const CyclePreferences *prefs);
const char* getDefaultPCTProtocol(const CyclePreferences *prefs);
float getDefaultWaterTarget(const CyclePreferences *prefs);
CycleAlertThresholds getAlertThresholds(const CyclePreferences *prefs);
int getAutoReminders(const CyclePreferences *prefs);

// Affiche les préférences
void displayCyclePreferences(const CyclePreferences *prefs);

#endif