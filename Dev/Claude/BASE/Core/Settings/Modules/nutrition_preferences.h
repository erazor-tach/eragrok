#ifndef NUTRITION_PREFERENCES_H
#define NUTRITION_PREFERENCES_H

// Allergies / intolérances (flags binaires)
typedef enum {
    ALLERGY_NONE = 0,
    ALLERGY_GLUTEN = 1 << 0,
    ALLERGY_LACTOSE = 1 << 1,
    ALLERGY_NUTS = 1 << 2,
    ALLERGY_EGGS = 1 << 3,
    ALLERGY_SOY = 1 << 4,
    ALLERGY_FISH = 1 << 5
} AllergyFlags;

// Régime par défaut
typedef enum {
    DIET_STANDARD,
    DIET_VEGETARIAN,
    DIET_VEGAN,
    DIET_KETO,
    DIET_PALEO
} DefaultDiet;

// Objectifs nutritionnels par défaut
typedef struct {
    float calories;      // kcal
    float proteines;     // g
    float glucides;      // g
    float lipides;       // g
    float eau;           // L
} DefaultTargets;

// Structure des préférences nutrition
typedef struct {
    DefaultTargets targets;          // objectifs par défaut
    DefaultDiet diet;                // régime préféré
    int allergies;                   // combinaison de AllergyFlags
    int nbRepasParJour;               // 3-6
    int remindersEnabled;             // 0/1
    int autoGenerateShoppingList;      // 0/1
    char preferredUnits[10];           // "g" ou "oz" etc.
} NutritionPreferences;

// Initialise avec des valeurs par défaut
void initNutritionPreferences(NutritionPreferences *prefs);

// Setters
void setDefaultCalories(NutritionPreferences *prefs, float cal);
void setDefaultProteines(NutritionPreferences *prefs, float prot);
void setDefaultGlucides(NutritionPreferences *prefs, float gluc);
void setDefaultLipides(NutritionPreferences *prefs, float lip);
void setDefaultEau(NutritionPreferences *prefs, float eau);
void setDiet(NutritionPreferences *prefs, DefaultDiet diet);
void addAllergy(NutritionPreferences *prefs, AllergyFlags allergy);
void removeAllergy(NutritionPreferences *prefs, AllergyFlags allergy);
void setNbRepas(NutritionPreferences *prefs, int nb);
void setRemindersEnabled(NutritionPreferences *prefs, int enabled);
void setAutoGenerateShoppingList(NutritionPreferences *prefs, int enabled);
void setPreferredUnits(NutritionPreferences *prefs, const char *units);

// Getters
DefaultTargets getDefaultTargets(const NutritionPreferences *prefs);
DefaultDiet getDiet(const NutritionPreferences *prefs);
int getAllergies(const NutritionPreferences *prefs);
int getNbRepas(const NutritionPreferences *prefs);
int getRemindersEnabled(const NutritionPreferences *prefs);
int getAutoGenerateShoppingList(const NutritionPreferences *prefs);
const char* getPreferredUnits(const NutritionPreferences *prefs);

// Affichage
void displayNutritionPreferences(const NutritionPreferences *prefs);
const char* dietToString(DefaultDiet diet);

#endif