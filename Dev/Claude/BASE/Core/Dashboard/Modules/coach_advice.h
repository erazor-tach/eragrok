#ifndef COACH_ADVICE_H
#define COACH_ADVICE_H

// Structure pour un conseil unique
typedef struct {
    char titre[50];
    char description[200];
    int priorite;          // 1 = haute, 2 = moyenne, 3 = faible
} Conseil;

// Structure pour les données utilisateur (simplifiée)
typedef struct {
    float dernierDC;       // dernier 1RM développé couché (kg)
    float dernierSquat;    // dernier 1RM squat (kg)
    float dernierSDT;      // dernier 1RM soulevé de terre (kg)
    float volumeHebdo;     // volume total de la semaine (tonnes)
    float sommeilMoyen;    // heures de sommeil moyennes
    float energieMoyenne;  // énergie moyenne (0-10)
} DonneesUtilisateur;

// Génère une liste de conseils basés sur les données utilisateur
// Retourne le nombre de conseils générés (max 10)
int genererConseils(const DonneesUtilisateur *donnees, Conseil conseils[], int maxConseils);

// Affiche une liste de conseils
void afficherConseils(const Conseil conseils[], int nbConseils);

#endif