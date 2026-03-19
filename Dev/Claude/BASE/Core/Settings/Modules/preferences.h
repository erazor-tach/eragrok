#ifndef PREFERENCES_H
#define PREFERENCES_H

// Unités de poids
typedef enum {
    UNIT_KG,
    UNIT_LBS
} WeightUnit;

// Unités de taille
typedef enum {
    UNIT_CM,
    UNIT_INCHES
} HeightUnit;

// Thème de l'application
typedef enum {
    THEME_DARK,
    THEME_LIGHT,
    THEME_SYSTEM
} AppTheme;

// Langue (simplifié)
typedef enum {
    LANG_FRENCH,
    LANG_ENGLISH,
    LANG_SPANISH
} Language;

// Structure des préférences
typedef struct {
    WeightUnit weightUnit;
    HeightUnit heightUnit;
    AppTheme theme;
    Language language;
    int autoSync;           // 0/1
    int restTimerDefault;    // secondes
    int notifications;       // 0/1
} Preferences;

// Initialise les préférences avec des valeurs par défaut
void initPreferences(Preferences *prefs);

// Getters
WeightUnit getWeightUnit(const Preferences *prefs);
HeightUnit getHeightUnit(const Preferences *prefs);
AppTheme getTheme(const Preferences *prefs);
Language getLanguage(const Preferences *prefs);
int getAutoSync(const Preferences *prefs);
int getRestTimerDefault(const Preferences *prefs);
int getNotifications(const Preferences *prefs);

// Setters
void setWeightUnit(Preferences *prefs, WeightUnit unit);
void setHeightUnit(Preferences *prefs, HeightUnit unit);
void setTheme(Preferences *prefs, AppTheme theme);
void setLanguage(Preferences *prefs, Language lang);
void setAutoSync(Preferences *prefs, int sync);
void setRestTimerDefault(Preferences *prefs, int seconds);
void setNotifications(Preferences *prefs, int notif);

// Affiche toutes les préférences (pour debug/affichage)
void displayPreferences(const Preferences *prefs);

// Convertit les énumérations en chaînes pour l'affichage
const char* weightUnitToString(WeightUnit unit);
const char* heightUnitToString(HeightUnit unit);
const char* themeToString(AppTheme theme);
const char* languageToString(Language lang);

#endif