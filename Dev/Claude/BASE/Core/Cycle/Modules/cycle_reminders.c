#include "cycle_reminders.h"
#include <stdio.h>
#include <string.h>
#include <time.h>

void initReminderList(ReminderList *list) {
    list->nbReminders = 0;
}

void ajouterRappel(ReminderList *list,
                   ReminderType type,
                   const char *titre,
                   const char *desc,
                   time_t dateHeure,
                   Recurrence recurrence,
                   int intervalle) {
    if (list->nbReminders >= 50) return;
    CycleReminder *r = &list->reminders[list->nbReminders];
    r->id = list->nbReminders + 1;
    r->type = type;
    strcpy(r->titre, titre);
    strcpy(r->description, desc);
    r->dateHeure = dateHeure;
    r->recurrence = recurrence;
    r->intervalle = intervalle;
    r->actif = 1;
    list->nbReminders++;
}

void supprimerRappel(ReminderList *list, int id) {
    for (int i = 0; i < list->nbReminders; i++) {
        if (list->reminders[i].id == id) {
            for (int j = i; j < list->nbReminders - 1; j++) {
                list->reminders[j] = list->reminders[j+1];
            }
            list->nbReminders--;
            return;
        }
    }
}

void setRappelActif(ReminderList *list, int id, int actif) {
    for (int i = 0; i < list->nbReminders; i++) {
        if (list->reminders[i].id == id) {
            list->reminders[i].actif = actif;
            return;
        }
    }
}

void marquerEffectue(ReminderList *list, int id) {
    time_t now = time(NULL);
    for (int i = 0; i < list->nbReminders; i++) {
        if (list->reminders[i].id == id) {
            CycleReminder *r = &list->reminders[i];
            if (!r->actif) return;
            switch (r->recurrence) {
                case RECUR_NONE:
                    // Désactiver après exécution
                    r->actif = 0;
                    break;
                case RECUR_DAILY:
                    r->dateHeure += 24 * 3600;
                    break;
                case RECUR_WEEKLY:
                    r->dateHeure += 7 * 24 * 3600;
                    break;
                case RECUR_BIWEEKLY:
                    r->dateHeure += 3 * 24 * 3600; // approximatif, à améliorer
                    break;
                case RECUR_CUSTOM:
                    r->dateHeure += r->intervalle * 24 * 3600;
                    break;
            }
            return;
        }
    }
}

void afficherRappelsActifs(const ReminderList *list) {
    time_t now = time(NULL);
    printf("\n=== RAPPELS ACTIFS ===\n");
    int trouve = 0;
    for (int i = 0; i < list->nbReminders; i++) {
        CycleReminder r = list->reminders[i];
        if (r.actif && r.dateHeure >= now) {
            char dateStr[30];
            strftime(dateStr, sizeof(dateStr), "%d/%m/%Y %H:%M", localtime(&r.dateHeure));
            printf("ID %d [%s] : %s\n", r.id, dateStr, r.titre);
            printf("  %s\n", r.description);
            trouve = 1;
        }
    }
    if (!trouve) printf("Aucun rappel actif.\n");
}

void afficherTousRappels(const ReminderList *list) {
    printf("\n=== TOUS LES RAPPELS ===\n");
    for (int i = 0; i < list->nbReminders; i++) {
        CycleReminder r = list->reminders[i];
        char dateStr[30];
        strftime(dateStr, sizeof(dateStr), "%d/%m/%Y %H:%M", localtime(&r.dateHeure));
        printf("ID %d : %s - %s [%s]\n", r.id, dateStr, r.titre, r.actif ? "ACTIF" : "INACTIF");
    }
}

void mettreAJourRappels(ReminderList *list) {
    // Pourrait gérer les rappels manqués, mais simple ici
    // On pourrait recalculer les dates si on a sauté un rappel
    time_t now = time(NULL);
    for (int i = 0; i < list->nbReminders; i++) {
        CycleReminder *r = &list->reminders[i];
        if (r->actif && r->dateHeure < now) {
            // Rappel en retard : on avance jusqu'à la prochaine occurrence future
            if (r->recurrence != RECUR_NONE) {
                while (r->dateHeure < now) {
                    switch (r->recurrence) {
                        case RECUR_DAILY: r->dateHeure += 24 * 3600; break;
                        case RECUR_WEEKLY: r->dateHeure += 7 * 24 * 3600; break;
                        case RECUR_BIWEEKLY: r->dateHeure += 3 * 24 * 3600; break;
                        case RECUR_CUSTOM: r->dateHeure += r->intervalle * 24 * 3600; break;
                        default: break;
                    }
                }
            } else {
                // Non récurrent : on désactive
                r->actif = 0;
            }
        }
    }
}