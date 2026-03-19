#include "ai_coach.h"
#include <stdio.h>
#include <string.h>
#include <math.h>

static void ajouterConseil(AIContext conseils[], int *nb, const char *titre,
                           const char *desc, int priorite, const char *categorie) {
    strcpy(conseils[*nb].titre, titre);
    strcpy(conseils[*nb].description, desc);
    conseils[*nb].priorite = priorite;
    strcpy(conseils[*nb].categorie, categorie);
    (*nb)++;
}

int genererConseilsIA(const WorkoutHistory *hist,
                      const RecuperationJour *recupRecente,
                      const StrengthRecords *records,
                      AIContext conseils[], int maxConseils) {
    int nb = 0;

    // 1. Analyser la fréquence des séances
    if (hist->nbEntries > 0) {
        // Calcul de la moyenne d'espacement (simplifié)
        time_t now = time(NULL);
        time_t last = hist->entries[hist->nbEntries-1].date;
        double joursDepuisDerniereSeance = difftime(now, last) / (60*60*24);
        if (joursDepuisDerniereSeance > 5) {
            ajouterConseil(conseils, &nb,
                "Reprise d'activité",
                "Cela fait plusieurs jours sans entraînement. Reprends en douceur avec une séance légère pour éviter les courbatures excessives.",
                1, "récupération");
        }
    }

    // 2. Analyser la récupération
    if (recupRecente != NULL) {
        if (recupRecente->energie < 5.0) {
            ajouterConseil(conseils, &nb,
                "Fatigue détectée",
                "Ton niveau d'énergie est bas. Envisage une semaine de deload ou augmente tes apports caloriques et le sommeil.",
                1, "récupération");
        }
        if (recupRecente->sommeilHeures < 6.5) {
            ajouterConseil(conseils, &nb,
                "Manque de sommeil",
                "Tu dors moins de 6h30 en moyenne. Le sommeil est crucial pour la récupération et la progression.",
                2, "récupération");
        }
    }

    // 3. Analyser les records (si fournis)
    if (records != NULL) {
        // Exemple : si le développé couché stagne depuis plus de 3 semaines
        // (on aurait besoin d'un historique, ici simplifié)
        // On simule une règle : si le dernier record est ancien
        // Pour l'exemple, on utilise un champ factice lastUpdate
        time_t now = time(NULL);
        if (difftime(now, records->lastUpdate) > 21 * 24 * 60 * 60) { // 21 jours
            ajouterConseil(conseils, &nb,
                "Progression stagnante",
                "Aucun nouveau record depuis 3 semaines. Change de programme ou introduis de la variation (séries lourdes, exercices complémentaires).",
                1, "force");
        }
    }

    // 4. Analyser le volume hebdomadaire (on peut le déduire de l'historique)
    // Calcul simplifié : volume total de la dernière semaine
    if (hist->nbEntries > 0) {
        float volumeSemaine = 0;
        int compteur = 0;
        time_t uneSemaine = 7 * 24 * 60 * 60;
        for (int i = hist->nbEntries - 1; i >= 0; i--) {
            if (difftime(time(NULL), hist->entries[i].date) <= uneSemaine) {
                volumeSemaine += hist->entries[i].volumeTotal;
                compteur++;
            } else break;
        }
        if (compteur > 0) {
            if (volumeSemaine < 5000) { // moins de 5 tonnes
                ajouterConseil(conseils, &nb,
                    "Volume faible",
                    "Ton volume hebdomadaire est inférieur à 5 tonnes. Augmente le nombre de séries ou la charge pour stimuler la croissance.",
                    2, "volume");
            } else if (volumeSemaine > 20000) {
                ajouterConseil(conseils, &nb,
                    "Volume élevé",
                    "Attention au surentraînement avec un volume >20t/sem. Assure-toi de bien récupérer et de manger suffisamment.",
                    2, "volume");
            }
        }
    }

    // Si aucun conseil, message par défaut
    if (nb == 0) {
        ajouterConseil(conseils, &nb,
            "Tout va bien !",
            "Continue sur ta lancée. Pense à varier les plaisirs et à écouter ton corps.",
            3, "général");
    }

    return nb;
}

void afficherConseilsIA(const AIContext conseils[], int nbConseils) {
    printf("\n=== COACH IA ===\n");
    for (int i = 0; i < nbConseils; i++) {
        const char *prioriteStr = (conseils[i].priorite == 1) ? "Haute" :
                                   (conseils[i].priorite == 2) ? "Moyenne" : "Basse";
        printf("[%s - %s] %s\n", prioriteStr, conseils[i].categorie, conseils[i].titre);
        printf("  %s\n\n", conseils[i].description);
    }
}