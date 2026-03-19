#include "nutrition_preferences.h"
#include <stdio.h>
#include <string.h>

void initNutritionPreferences(NutritionPreferences *prefs) {
    prefs->targets.calories = 2500;
    prefs->targets.proteines = 180;
    prefs->targets.glucides = 300;
    prefs->targets.lipides = 70;
    prefs->targets.eau = 3.0;
    prefs->diet = DIET_STANDARD;
    prefs->allergies = ALLERGY_NONE;
    prefs->nbRepasParJour = 4;
    prefs->remindersEnabled = 1;
    prefs->autoGenerateShoppingList = 1;
    strcpy(prefs->preferredUnits, "g");
}

void setDefaultCalories(NutritionPreferences *prefs, float cal) {
    if (cal > 0) prefs->targets.calories = cal;
}

void setDefaultProteines(NutritionPreferences *prefs, float prot) {
    if (prot > 0) prefs->targets.proteines = prot;
}

void setDefaultGlucides(NutritionPreferences *prefs, float gluc) {
    if (gluc > 0) prefs->targets.glucides = gluc;
}

void setDefaultLipides(NutritionPreferences *prefs, float lip) {
    if (lip > 0) prefs->targets.lipides = lip;
}

void setDefaultEau(NutritionPreferences *prefs, float eau) {
    if (eau > 0) prefs->targets.eau = eau;
}

void setDiet(NutritionPreferences *prefs, DefaultDiet diet) {
    prefs->diet = diet;
}

void addAllergy(NutritionPreferences *prefs, AllergyFlags allergy) {
    prefs->allergies |= allergy;
}

void removeAllergy(NutritionPreferences *prefs, AllergyFlags allergy) {
    prefs->allergies &= ~allergy;
}

void setNbRepas(NutritionPreferences *prefs, int nb) {
    if (nb >= 2 && nb <= 8) prefs->nbRepasParJour = nb;
}

void setRemindersEnabled(NutritionPreferences *prefs, int enabled) {
    prefs->remindersEnabled = enabled;
}

void setAutoGenerateShoppingList(NutritionPreferences *prefs, int enabled) {
    prefs->autoGenerateShoppingList = enabled;
}

void setPreferredUnits(NutritionPreferences *prefs, const char *units) {
    strncpy(prefs->preferredUnits, units, sizeof(prefs->preferredUnits)-1);
    prefs->preferredUnits[sizeof(prefs->preferredUnits)-1] = '\0';
}

DefaultTargets getDefaultTargets(const NutritionPreferences *prefs) {
    return prefs->targets;
}

DefaultDiet getDiet(const NutritionPreferences *prefs) {
    return prefs->diet;
}

int getAllergies(const NutritionPreferences *prefs) {
    return prefs->allergies;
}

int getNbRepas(const NutritionPreferences *prefs) {
    return prefs->nbRepasParJour;
}

int getRemindersEnabled(const NutritionPreferences *prefs) {
    return prefs->remindersEnabled;
}

int getAutoGenerateShoppingList(const NutritionPreferences *prefs) {
    return prefs->autoGenerateShoppingList;
}

const char* getPreferredUnits(const NutritionPreferences *prefs) {
    return prefs->preferredUnits;
}

const char* dietToString(DefaultDiet diet) {
    switch (diet) {
        case DIET_STANDARD: return "Standard";
        case DIET_VEGETARIAN: return "Végétarien";
        case DIET_VEGAN: return "Végan";
        case DIET_KETO: return "Kéto";
        case DIET_PALEO: return "Paléo";
        default: return "Inconnu";
    }
}

void displayNutritionPreferences(const NutritionPreferences *prefs) {
    printf("\n=== PARAMÈTRES NUTRITION ===\n");
    printf("Objectifs par défaut :\n");
    printf("  Calories : %.0f kcal\n", prefs->targets.calories);
    printf("  Protéines : %.1f g\n", prefs->targets.proteines);
    printf("  Glucides : %.1f g\n", prefs->targets.glucides);
    printf("  Lipides : %.1f g\n", prefs->targets.lipides);
    printf("  Eau : %.1f L\n", prefs->targets.eau);
    printf("Régime : %s\n", dietToString(prefs->diet));
    printf("Allergies : ");
    if (prefs->allergies == ALLERGY_NONE) printf("Aucune");
    else {
        if (prefs->allergies & ALLERGY_GLUTEN) printf("Gluten ");
        if (prefs->allergies & ALLERGY_LACTOSE) printf("Lactose ");
        if (prefs->allergies & ALLERGY_NUTS) printf("Fruits à coque ");
        if (prefs->allergies & ALLERGY_EGGS) printf("Œufs ");
        if (prefs->allergies & ALLERGY_SOY) printf("Soja ");
        if (prefs->allergies & ALLERGY_FISH) printf("Poisson ");
    }
    printf("\nNombre de repas par jour : %d\n", prefs->nbRepasParJour);
    printf("Rappels : %s\n", prefs->remindersEnabled ? "Activés" : "Désactivés");
    printf("Génération auto liste de courses : %s\n", prefs->autoGenerateShoppingList ? "Oui" : "Non");
    printf("Unités préférées : %s\n", prefs->preferredUnits);
}