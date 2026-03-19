#include "cycle_summary.h"
#include <stdio.h>
#include <string.h>
#include <time.h>

void genererCycleSummary(const CycleSettings *settings, const InjectionSchedule *sched, CycleSummary *summary) {
    strcpy(summary->nomCycle, settings->nomCycle);
    time_t now = time(NULL);
    int secondesParJour = 24 * 3600;
    summary->joursEcoules = (int)((now - settings->dateDebut) / secondesParJour);
    summary->joursRestants = settings->dureeSemaines * 7 - summary->joursEcoules;
    if (summary->joursRestants < 0) summary->joursRestants = 0;
    summary->progression = (settings->dureeSemaines * 7 > 0) ?
                            (summary->joursEcoules * 100.0) / (settings->dureeSemaines * 7) : 0;
    if (summary->progression > 100) summary->progression = 100;

    // Compter les injections
    summary->injectionsPrevues = 0;
    summary->injectionsEffectuees = 0;
    for (int i = 0; i < sched->nbEvenements; i++) {
        // On ne compte que les injections du cycle en cours (par date)
        if (sched->evenements[i].dateHeure >= settings->dateDebut) {
            summary->injectionsPrevues++;
            if (sched->evenements[i].effectue) {
                summary->injectionsEffectuees++;
            }
        }
    }

    // Copier les produits
    summary->nbProduits = settings->nbProduits;
    for (int i = 0; i < settings->nbProduits; i++) {
        summary->produits[i] = settings->produits[i];
    }

    // Initialiser les effets et recommandations
    summary->nbEffets = 0;
    summary->nbRecommandations = 0;

    // Recommandations basiques
    if (summary->joursRestants < 7) {
        strcpy(summary->recommandations[summary->nbRecommandations++],
               "Cycle bientôt terminé. Prépare ton PCT.");
    }
    if (summary->injectionsEffectuees < summary->injectionsPrevues / 2) {
        strcpy(summary->recommandations[summary->nbRecommandations++],
               "Tu as pris du retard dans les injections. Rattrape ton planning.");
    }
    if (summary->joursEcoules > 14 && summary->nbEffets == 0) {
        strcpy(summary->recommandations[summary->nbRecommandations++],
               "Pense à noter les éventuels effets secondaires pour le suivi.");
    }
    // Recommandation par défaut si aucune
    if (summary->nbRecommandations == 0) {
        strcpy(summary->recommandations[summary->nbRecommandations++],
               "Continue comme ça, tout se déroule normalement.");
    }
}

void ajouterEffet(CycleSummary *summary, const char *nom, int intensite, const char *commentaire) {
    if (summary->nbEffets >= 10) return;
    SideEffect *e = &summary->effets[summary->nbEffets];
    strcpy(e->nom, nom);
    e->intensite = intensite;
    strcpy(e->commentaire, commentaire);
    summary->nbEffets++;
}

void afficherCycleSummary(const CycleSummary *summary) {
    printf("\n=== RÉSUMÉ DU CYCLE : %s ===\n", summary->nomCycle);
    printf("Progression : %d/%d jours (%.1f%%)\n", summary->joursEcoules,
           summary->joursEcoules + summary->joursRestants, summary->progression);
    printf("Temps restant : %d jours\n", summary->joursRestants);

    printf("\nProduits :\n");
    for (int i = 0; i < summary->nbProduits; i++) {
        CycleProduct p = summary->produits[i];
        printf("  - %s : %.0f %s\n", p.nom, p.dosage, p.unite);
    }

    printf("\nInjections : %d effectuées sur %d prévues\n",
           summary->injectionsEffectuees, summary->injectionsPrevues);

    if (summary->nbEffets > 0) {
        printf("\nEffets secondaires notés :\n");
        for (int i = 0; i < summary->nbEffets; i++) {
            SideEffect e = summary->effets[i];
            printf("  - %s (intensité %d/10) : %s\n", e.nom, e.intensite, e.commentaire);
        }
    } else {
        printf("\nAucun effet secondaire signalé.\n");
    }

    printf("\nRecommandations :\n");
    for (int i = 0; i < summary->nbRecommandations; i++) {
        printf("  💡 %s\n", summary->recommandations[i]);
    }
}