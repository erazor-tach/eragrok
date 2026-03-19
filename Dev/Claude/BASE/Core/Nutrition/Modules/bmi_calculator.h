#ifndef BMI_CALCULATOR_H
#define BMI_CALCULATOR_H

#include <time.h>

// Catégories d'IMC
typedef enum {
    INSUFFISANCE_PONDERALE,
    CORPULENCE_NORMALE,
    SURPOIDS,
    OBESITE_MODEREE,
    OBESITE_SEVERE,
    OBESITE_MORBIDE
} IMCCategory;

// Structure pour une mesure d'IMC
typedef struct {
    time_t date;
    float poids;        // en kg
    float taille;       // en cm
    float imc;          // calculé
    IMCCategory categorie;
} IMCMesure;

// Structure pour l'historique des mesures
typedef struct {
    IMCMesure mesures[50];
    int nbMesures;
} IMCHistory;

// Calcule l'IMC à partir du poids (kg) et de la taille (cm)
float calculerIMC(float poids, float taille);

// Retourne la catégorie correspondant à un IMC
IMCCategory interpreterIMC(float imc);

// Retourne une chaîne descriptive pour une catégorie
const char* categorieToString(IMCCategory cat);

// Ajoute une mesure à l'historique
void ajouterMesure(IMCHistory *hist, float poids, float taille);

// Affiche l'historique des mesures
void afficherHistoriqueIMC(const IMCHistory *hist);

// Affiche un résumé de la dernière mesure
void afficherDerniereMesure(const IMCHistory *hist);

#endif