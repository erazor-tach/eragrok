#include "bmi_calculator.h"
#include <stdio.h>
#include <string.h>
#include <math.h>

float calculerIMC(float poids, float taille) {
    // taille en cm, on convertit en mètres
    float tailleM = taille / 100.0;
    return poids / (tailleM * tailleM);
}

IMCCategory interpreterIMC(float imc) {
    if (imc < 18.5) return INSUFFISANCE_PONDERALE;
    if (imc < 25.0) return CORPULENCE_NORMALE;
    if (imc < 30.0) return SURPOIDS;
    if (imc < 35.0) return OBESITE_MODEREE;
    if (imc < 40.0) return OBESITE_SEVERE;
    return OBESITE_MORBIDE;
}

const char* categorieToString(IMCCategory cat) {
    switch (cat) {
        case INSUFFISANCE_PONDERALE: return "Insuffisance pondérale";
        case CORPULENCE_NORMALE:     return "Corpulence normale";
        case SURPOIDS:               return "Surpoids";
        case OBESITE_MODEREE:        return "Obésité modérée";
        case OBESITE_SEVERE:         return "Obésité sévère";
        case OBESITE_MORBIDE:        return "Obésité morbide";
        default: return "Inconnu";
    }
}

void ajouterMesure(IMCHistory *hist, float poids, float taille) {
    if (hist->nbMesures >= 50) return;
    IMCMesure *m = &hist->mesures[hist->nbMesures];
    m->date = time(NULL);
    m->poids = poids;
    m->taille = taille;
    m->imc = calculerIMC(poids, taille);
    m->categorie = interpreterIMC(m->imc);
    hist->nbMesures++;
}

void afficherHistoriqueIMC(const IMCHistory *hist) {
    printf("\n=== HISTORIQUE IMC ===\n");
    for (int i = 0; i < hist->nbMesures; i++) {
        IMCMesure m = hist->mesures[i];
        char dateStr[30];
        strftime(dateStr, sizeof(dateStr), "%d/%m/%Y", localtime(&m.date));
        printf("%2d. %s : poids %.1f kg, taille %.1f cm, IMC = %.1f (%s)\n",
               i+1, dateStr, m.poids, m.taille, m.imc, categorieToString(m.categorie));
    }
}

void afficherDerniereMesure(const IMCHistory *hist) {
    if (hist->nbMesures == 0) {
        printf("Aucune mesure enregistrée.\n");
        return;
    }
    IMCMesure m = hist->mesures[hist->nbMesures-1];
    char dateStr[30];
    strftime(dateStr, sizeof(dateStr), "%d/%m/%Y", localtime(&m.date));
    printf("\n=== DERNIÈRE MESURE ===\n");
    printf("Date : %s\n", dateStr);
    printf("Poids : %.1f kg\n", m.poids);
    printf("Taille : %.1f cm\n", m.taille);
    printf("IMC : %.1f (%s)\n", m.imc, categorieToString(m.categorie));
}