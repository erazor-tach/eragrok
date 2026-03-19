#ifndef CYCLE_REMINDERS_H
#define CYCLE_REMINDERS_H

#include <time.h>

// Types de rappels
typedef enum {
    REMINDER_INJECTION,
    REMINDER_ORAL,
    REMINDER_PRISE_SANG,
    REMINDER_AUTRE
} ReminderType;

// Récurrence
typedef enum {
    RECUR_NONE,        // une fois
    RECUR_DAILY,
    RECUR_WEEKLY,
    RECUR_BIWEEKLY,    // deux fois par semaine
    RECUR_CUSTOM
} Recurrence;

// Structure pour un rappel
typedef struct {
    int id;
    ReminderType type;
    char titre[100];
    char description[200];
    time_t dateHeure;           // prochaine occurrence
    Recurrence recurrence;
    int intervalle;             // pour récurrence personnalisée (en jours)
    int actif;                   // 0 = désactivé, 1 = actif
} CycleReminder;

// Collection de rappels
typedef struct {
    CycleReminder reminders[50];
    int nbReminders;
} ReminderList;

// Initialise la liste
void initReminderList(ReminderList *list);

// Ajoute un rappel
void ajouterRappel(ReminderList *list,
                   ReminderType type,
                   const char *titre,
                   const char *desc,
                   time_t dateHeure,
                   Recurrence recurrence,
                   int intervalle);

// Supprime un rappel (par id)
void supprimerRappel(ReminderList *list, int id);

// Active/désactive un rappel
void setRappelActif(ReminderList *list, int id, int actif);

// Marque un rappel comme effectué (pour les non récurrents) ou recalcule la prochaine date
void marquerEffectue(ReminderList *list, int id);

// Affiche tous les rappels actifs à venir
void afficherRappelsActifs(const ReminderList *list);

// Affiche tous les rappels (pour gestion)
void afficherTousRappels(const ReminderList *list);

// Met à jour les rappels (à appeler périodiquement) pour recalculer les occurrences dépassées
void mettreAJourRappels(ReminderList *list);

#endif