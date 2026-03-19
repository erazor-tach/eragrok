#ifndef CYCLE_TIMELINE_H
#define CYCLE_TIMELINE_H

#include <time.h>

// Types d'événements possibles
typedef enum {
    EVENT_CYCLE_START,
    EVENT_INJECTION,
    EVENT_SIDE_EFFECT,
    EVENT_BLOOD_TEST,
    EVENT_CYCLE_END,
    EVENT_PCT_START,
    EVENT_NOTE,
    EVENT_CUSTOM
} EventType;

// Structure pour un événement
typedef struct {
    int id;
    time_t date;
    EventType type;
    char description[100];
    char details[200];      // informations supplémentaires
} TimelineEvent;

// Structure pour la timeline
typedef struct {
    TimelineEvent evenements[100];
    int nbEvenements;
} CycleTimeline;

// Initialise la timeline
void initCycleTimeline(CycleTimeline *tl);

// Ajoute un événement
void ajouterEvenement(CycleTimeline *tl, time_t date, EventType type, const char *desc, const char *details);

// Supprime un événement
void supprimerEvenement(CycleTimeline *tl, int id);

// Affiche la timeline complète (triée par date)
void afficherTimeline(const CycleTimeline *tl);

// Affiche les événements à venir
void afficherEvenementsAVenir(const CycleTimeline *tl);

// Retourne le nom d'un type d'événement
const char* eventTypeToString(EventType type);

#endif