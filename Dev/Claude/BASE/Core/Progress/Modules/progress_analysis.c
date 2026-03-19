#include "progress_analysis.h"
#include <stdio.h>
#include <string.h>
#include <math.h>

// Fonction interne pour ajouter une force
static void ajouterForce(ProgressAnalysis *a, const char *titre, const char *desc) {
    if (a->nbForces >= 10) return;
    AnalysisItem *item = &a->forces[a->nbForces];
    strcpy(item->titre, titre);
    strcpy(item->description, desc);
    item->estForce = 1;
    a->nbForces++;
}

static void ajouterFaiblesse(ProgressAnalysis *a, const char *titre, const char *desc) {
    if (a->nbFaiblesses >= 10) return;
    AnalysisItem *item = &a->faiblesses[a->nbFaiblesses];
    strcpy(item->titre, titre);
    strcpy(item->description, desc);
    item->estForce = 0;
    a->nbFaiblesses++;
}

static void ajouterSuggestion(ProgressAnalysis *a, const char *conseil) {
    if (a->nbSuggestions >= 10) return;
    strcpy(a->suggestions[a->nbSuggestions].conseil, conseil);
    a->nbSuggestions++;
}

void genererAnalyse(const PersonalRecords *pr,
                    const WorkoutSessionLog *log,
                    const RecuperationJour *recup,
                    ProgressAnalysis *analyse) {
    // Initialiser
    analyse->nbForces = 0;
    analyse->nbFaiblesses = 0;
    analyse->nbSuggestions = 0;

    // Analyser les records
    if (pr->nbRecords > 0) {
        // Exemple : trouver l'exercice avec le meilleur 1RM relatif (par rapport à une référence)
        // Ici on simplifie en prenant le record absolu
        float maxRM = 0;
        char meilleurExo[50] = "";
        for (int i = 0; i < pr->nbRecords; i++) {
            if (pr->records[i].estimated1RM > maxRM) {
                maxRM = pr->records[i].estimated1RM;
                strcpy(meilleurExo, pr->records[i].exercice);
            }
        }
        if (maxRM > 0) {
            char desc[200];
            sprintf(desc, "Ton meilleur 1RM est au %s avec %.1f kg.", meilleurExo, maxRM);
            ajouterForce(analyse, "Record absolu", desc);
        }
    }

    // Analyser le volume hebdomadaire (à partir du log)
    if (log->nbEntries > 0) {
        // Calculer le volume total des 7 derniers jours
        time_t now = time(NULL);
        time_t weekAgo = now - 7 * 24 * 3600;
        float volumeSemaine = 0;
        int seancesSemaine = 0;
        for (int i = 0; i < log->nbEntries; i++) {
            if (log->entries[i].date >= weekAgo) {
                volumeSemaine += log->entries[i].volumeTotal;
                seancesSemaine++;
            }
        }
        if (seancesSemaine >= 3) {
            char desc[200];
            sprintf(desc, "Volume hebdomadaire de %.0f kg sur %d séances.", volumeSemaine, seancesSemaine);
            ajouterForce(analyse, "Volume récent", desc);
        } else {
            ajouterFaiblesse(analyse, "Fréquence d'entraînement",
                             "Moins de 3 séances cette semaine. Vise au moins 3-4 séances pour progresser.");
        }
    } else {
        ajouterFaiblesse(analyse, "Aucune donnée", "Commence à enregistrer tes séances pour obtenir une analyse.");
    }

    // Analyser la récupération
    if (recup != NULL) {
        if (recup->energie < 5.0) {
            ajouterFaiblesse(analyse, "Énergie basse",
                             "Ton niveau d'énergie est faible. Pense à la récupération et à la nutrition.");
        } else if (recup->energie > 8.0) {
            ajouterForce(analyse, "Bonne énergie", "Tu te sens en forme, profites-en pour battre des records !");
        }
        if (recup->sommeilHeures < 6.5) {
            ajouterFaiblesse(analyse, "Manque de sommeil",
                             "Tu dors moins de 6h30 en moyenne. Vise 7-8h pour une meilleure récupération.");
        }
    }

    // Suggestions basées sur les faiblesses
    if (analyse->nbFaiblesses > 0) {
        for (int i = 0; i < analyse->nbFaiblesses; i++) {
            AnalysisItem f = analyse->faiblesses[i];
            if (strstr(f.titre, "Fréquence") != NULL) {
                ajouterSuggestion(analyse, "Ajoute une séance légère ou du cardio pour augmenter ta fréquence.");
            } else if (strstr(f.titre, "sommeil") != NULL) {
                ajouterSuggestion(analyse, "Essaie d'aller te coucher 30 min plus tôt et limite les écrans avant de dormir.");
            } else if (strstr(f.titre, "énergie") != NULL) {
                ajouterSuggestion(analyse, "Vérifie ton alimentation et ton hydratation. Une semaine de deload peut aider.");
            }
        }
    } else {
        ajouterSuggestion(analyse, "Continue sur ta lancée, tout va bien !");
    }

    // Si pas assez de données
    if (pr->nbRecords == 0 && log->nbEntries == 0) {
        ajouterSuggestion(analyse, "Ajoute des records et des séances pour débloquer une analyse détaillée.");
    }
}

void afficherAnalyse(const ProgressAnalysis *analyse) {
    printf("\n=== ANALYSE DE PROGRESSION ===\n");

    printf("\nPoints forts :\n");
    if (analyse->nbForces == 0) {
        printf("  Aucun point fort identifié pour le moment.\n");
    } else {
        for (int i = 0; i < analyse->nbForces; i++) {
            printf("  ✅ %s : %s\n", analyse->forces[i].titre, analyse->forces[i].description);
        }
    }

    printf("\nPoints faibles :\n");
    if (analyse->nbFaiblesses == 0) {
        printf("  Aucun point faible détecté, bravo !\n");
    } else {
        for (int i = 0; i < analyse->nbFaiblesses; i++) {
            printf("  ⚠️ %s : %s\n", analyse->faiblesses[i].titre, analyse->faiblesses[i].description);
        }
    }

    printf("\nSuggestions :\n");
    for (int i = 0; i < analyse->nbSuggestions; i++) {
        printf("  💡 %s\n", analyse->suggestions[i].conseil);
    }
}