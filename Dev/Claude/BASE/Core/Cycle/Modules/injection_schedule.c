#include "injection_schedule.h"
#include <stdio.h>
#include <string.h>
#include <time.h>

void initInjectionSchedule(InjectionSchedule *sched) {
    sched->nbEvenements = 0;
}

void ajouterInjection(InjectionSchedule *sched, time_t dateHeure, const char *nomProduit,
                      float dosage, const char *unite, float quantite) {
    if (sched->nbEvenements >= 100) return;
    InjectionEvent *ev = &sched->evenements[sched->nbEvenements];
    ev->id = sched->nbEvenements + 1; // simple, peut être amélioré
    ev->dateHeure = dateHeure;
    strcpy(ev->produit.nom, nomProduit);
    ev->produit.dosage = dosage;
    strcpy(ev->produit.unite, unite);
    ev->quantite = quantite;
    ev->effectue = 0;
    ev->notes[0] = '\0';
    sched->nbEvenements++;
}

void supprimerInjection(InjectionSchedule *sched, int id) {
    for (int i = 0; i < sched->nbEvenements; i++) {
        if (sched->evenements[i].id == id) {
            for (int j = i; j < sched->nbEvenements - 1; j++) {
                sched->evenements[j] = sched->evenements[j+1];
            }
            sched->nbEvenements--;
            return;
        }
    }
}

void modifierInjection(InjectionSchedule *sched, int id, time_t nouvelleDateHeure,
                       float nouvelleQuantite) {
    for (int i = 0; i < sched->nbEvenements; i++) {
        if (sched->evenements[i].id == id) {
            sched->evenements[i].dateHeure = nouvelleDateHeure;
            sched->evenements[i].quantite = nouvelleQuantite;
            return;
        }
    }
}

void marquerEffectue(InjectionSchedule *sched, int id, int effectue) {
    for (int i = 0; i < sched->nbEvenements; i++) {
        if (sched->evenements[i].id == id) {
            sched->evenements[i].effectue = effectue;
            return;
        }
    }
}

// Fonction de comparaison pour trier par date
static int comparerDates(const void *a, const void *b) {
    InjectionEvent *ea = (InjectionEvent*)a;
    InjectionEvent *eb = (InjectionEvent*)b;
    if (ea->dateHeure < eb->dateHeure) return -1;
    if (ea->dateHeure > eb->dateHeure) return 1;
    return 0;
}

void afficherInjectionsAVenir(const InjectionSchedule *sched) {
    time_t now = time(NULL);
    printf("\n=== INJECTIONS À VENIR ===\n");
    int trouve = 0;
    for (int i = 0; i < sched->nbEvenements; i++) {
        if (!sched->evenements[i].effectue && sched->evenements[i].dateHeure >= now) {
            InjectionEvent ev = sched->evenements[i];
            char dateStr[30];
            strftime(dateStr, sizeof(dateStr), "%d/%m/%Y %H:%M", localtime(&ev.dateHeure));
            printf("ID %d : %s - %s %.1f %s (dose %.1f %s)\n",
                   ev.id, dateStr, ev.produit.nom, ev.quantite, ev.produit.unite,
                   ev.produit.dosage, ev.produit.unite);
            trouve = 1;
        }
    }
    if (!trouve) printf("Aucune injection prévue.\n");
}

void afficherHistoriqueInjections(const InjectionSchedule *sched) {
    printf("\n=== HISTORIQUE DES INJECTIONS ===\n");
    int trouve = 0;
    for (int i = 0; i < sched->nbEvenements; i++) {
        if (sched->evenements[i].effectue) {
            InjectionEvent ev = sched->evenements[i];
            char dateStr[30];
            strftime(dateStr, sizeof(dateStr), "%d/%m/%Y %H:%M", localtime(&ev.dateHeure));
            printf("ID %d : %s - %s %.1f %s (fait)\n",
                   ev.id, dateStr, ev.produit.nom, ev.quantite, ev.produit.unite);
            if (ev.notes[0] != '\0') printf("    Notes: %s\n", ev.notes);
            trouve = 1;
        }
    }
    if (!trouve) printf("Aucune injection effectuée.\n");
}

void afficherPlanningComplet(const InjectionSchedule *sched) {
    // On pourrait trier par date, mais on va simplement tout afficher dans l'ordre d'ajout
    printf("\n=== PLANNING COMPLET DES INJECTIONS ===\n");
    for (int i = 0; i < sched->nbEvenements; i++) {
        InjectionEvent ev = sched->evenements[i];
        char dateStr[30];
        strftime(dateStr, sizeof(dateStr), "%d/%m/%Y %H:%M", localtime(&ev.dateHeure));
        printf("ID %d : %s - %s %.1f %s [%s]\n",
               ev.id, dateStr, ev.produit.nom, ev.quantite, ev.produit.unite,
               ev.effectue ? "FAIT" : "À FAIRE");
    }
}