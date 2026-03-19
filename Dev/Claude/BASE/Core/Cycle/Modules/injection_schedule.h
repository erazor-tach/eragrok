#ifndef INJECTION_SCHEDULE_H
#define INJECTION_SCHEDULE_H

#include <time.h>

// Structure pour un produit injectable
typedef struct {
    char nom[50];
    float dosage;           // en mg/ml ou autre unité
    char unite[10];         // "mg", "ml", etc.
} ProduitInject;

// Structure pour un événement d'injection
typedef struct {
    int id;
    time_t dateHeure;       // date et heure prévues
    ProduitInject produit;
    float quantite;         // quantité injectée (en ml ou mg)
    int effectue;           // 0 = à faire, 1 = fait
    char notes[100];        // notes éventuelles (réaction, etc.)
} InjectionEvent;

// Structure pour le planning d'injections
typedef struct {
    InjectionEvent evenements[100];
    int nbEvenements;
} InjectionSchedule;

// Initialise un planning vide
void initInjectionSchedule(InjectionSchedule *sched);

// Ajoute un événement d'injection
void ajouterInjection(InjectionSchedule *sched, time_t dateHeure, const char *nomProduit,
                      float dosage, const char *unite, float quantite);

// Supprime un événement (par id)
void supprimerInjection(InjectionSchedule *sched, int id);

// Modifie un événement
void modifierInjection(InjectionSchedule *sched, int id, time_t nouvelleDateHeure,
                       float nouvelleQuantite);

// Marque une injection comme effectuée (ou non)
void marquerEffectue(InjectionSchedule *sched, int id, int effectue);

// Affiche toutes les injections à venir (futures)
void afficherInjectionsAVenir(const InjectionSchedule *sched);

// Affiche l'historique des injections passées
void afficherHistoriqueInjections(const InjectionSchedule *sched);

// Affiche le planning complet (trié par date)
void afficherPlanningComplet(const InjectionSchedule *sched);

#endif