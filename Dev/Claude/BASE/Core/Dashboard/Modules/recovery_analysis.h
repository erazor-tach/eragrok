#ifndef RECOVERY_ANALYSIS_H
#define RECOVERY_ANALYSIS_H

// Structure représentant les données de récupération sur une journée
typedef struct {
    int jour;                // timestamp ou numéro du jour
    float hrv;               // variabilité cardiaque (ms)
    float sommeilHeures;     // heures de sommeil
    float sommeilQualite;    // qualité perçue (0-10)
    float frequenceCardiaqueRepos; // bpm
    float courbatures;       // indice de courbatures (0-10)
    float energie;           // niveau d'énergie subjectif (0-10)
} RecuperationJour;

// Structure pour le résumé de la semaine
typedef struct {
    RecuperationJour jours[7];
    float moyenneHRV;
    float moyenneSommeil;
    float moyenneEnergie;
} ResumeSemaine;

// Initialise des données d'exemple
void initRecuperationExemple(RecuperationJour *semaine);

// Calcule un score de récupération global (0-100) à partir d'une journée
float calculerScoreRecuperation(const RecuperationJour *jour);

// Affiche un rapport de récupération pour une journée
void afficherRapportJour(const RecuperationJour *jour);

// Affiche un résumé de la semaine
void afficherResumeSemaine(const ResumeSemaine *resume);

#endif