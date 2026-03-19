#include "preferences.h"
#include <stdio.h>

void initPreferences(Preferences *prefs) {
    prefs->weightUnit = UNIT_KG;
    prefs->heightUnit = UNIT_CM;
    prefs->theme = THEME_DARK;
    prefs->language = LANG_FRENCH;
    prefs->autoSync = 1;
    prefs->restTimerDefault = 90;
    prefs->notifications = 1;
}

WeightUnit getWeightUnit(const Preferences *prefs) {
    return prefs->weightUnit;
}

HeightUnit getHeightUnit(const Preferences *prefs) {
    return prefs->heightUnit;
}

AppTheme getTheme(const Preferences *prefs) {
    return prefs->theme;
}

Language getLanguage(const Preferences *prefs) {
    return prefs->language;
}

int getAutoSync(const Preferences *prefs) {
    return prefs->autoSync;
}

int getRestTimerDefault(const Preferences *prefs) {
    return prefs->restTimerDefault;
}

int getNotifications(const Preferences *prefs) {
    return prefs->notifications;
}

void setWeightUnit(Preferences *prefs, WeightUnit unit) {
    prefs->weightUnit = unit;
}

void setHeightUnit(Preferences *prefs, HeightUnit unit) {
    prefs->heightUnit = unit;
}

void setTheme(Preferences *prefs, AppTheme theme) {
    prefs->theme = theme;
}

void setLanguage(Preferences *prefs, Language lang) {
    prefs->language = lang;
}

void setAutoSync(Preferences *prefs, int sync) {
    prefs->autoSync = sync;
}

void setRestTimerDefault(Preferences *prefs, int seconds) {
    if (seconds > 0) prefs->restTimerDefault = seconds;
}

void setNotifications(Preferences *prefs, int notif) {
    prefs->notifications = notif;
}

const char* weightUnitToString(WeightUnit unit) {
    switch (unit) {
        case UNIT_KG: return "kg";
        case UNIT_LBS: return "lbs";
        default: return "kg";
    }
}

const char* heightUnitToString(HeightUnit unit) {
    switch (unit) {
        case UNIT_CM: return "cm";
        case UNIT_INCHES: return "inches";
        default: return "cm";
    }
}

const char* themeToString(AppTheme theme) {
    switch (theme) {
        case THEME_DARK: return "Sombre";
        case THEME_LIGHT: return "Clair";
        case THEME_SYSTEM: return "Système";
        default: return "Sombre";
    }
}

const char* languageToString(Language lang) {
    switch (lang) {
        case LANG_FRENCH: return "Français";
        case LANG_ENGLISH: return "English";
        case LANG_SPANISH: return "Español";
        default: return "Français";
    }
}

void displayPreferences(const Preferences *prefs) {
    printf("\n=== PRÉFÉRENCES ===\n");
    printf("Unité de poids : %s\n", weightUnitToString(prefs->weightUnit));
    printf("Unité de taille : %s\n", heightUnitToString(prefs->heightUnit));
    printf("Thème : %s\n", themeToString(prefs->theme));
    printf("Langue : %s\n", languageToString(prefs->language));
    printf("Synchronisation auto : %s\n", prefs->autoSync ? "Oui" : "Non");
    printf("Timer de repos par défaut : %d s\n", prefs->restTimerDefault);
    printf("Notifications : %s\n", prefs->notifications ? "Activées" : "Désactivées");
}