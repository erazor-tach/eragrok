#include "cycle_timeline.h"
#include <stdio.h>
#include <string.h>
#include <time.h>

const char* eventTypeToString(EventType type) {
    switch (type) {
        case EVENT_CYCLE_START: return "Début cycle";
        case EVENT_INJECTION: return "Injection";
        case EVENT_SIDE_EFFECT: return "Effet secondaire";
        case EVENT_BLOOD_TEST: return "Prise de sang";
        case EVENT_CYCLE_END: return "Fin cycle";
        case EVENT_PCT_START: return "Début PCT";
        case EVENT_NOTE: return "Note";
        case EVENT_CUSTOM: return "Personnalisé";
        default: return "Inconnu";
    }
}

void initCycleTimeline(CycleTimeline *tl) {
    tl->nbEvenements = 0;
}

void ajouterEvenement(CycleTimeline *tl, time_t date, EventType type, const char *desc, const char *details) {
    if (tl->nbEvenements >= 100) return;
    TimelineEvent *e = &tl->evenements[tl->nbEvenements];
    e->id = tl->nbEvenements + 1;
    e->date = date;
    e->type = type;
    strcpy(e->description, desc);
    strcpy(e->details, details);
    tl->nbEvenements++;
}

void supprimerEvenement(CycleTimeline *tl, int id) {
    for (int i = 0; i < tl->nbEvenements; i++) {
        if (tl->evenements[i].id == id) {
            for (int j = i; j < tl->nbEvenements - 1; j++) {
                tl->evenements[j] = tl->evenements[j+1];
            }
            tl->nbEvenements--;
            return;
        }
    }
}

// Fonction de comparaison pour trier par date
static int comparerDates(const void *a, const void *b) {
    TimelineEvent *ea = (TimelineEvent*)a;
    TimelineEvent *eb = (TimelineEvent*)b;
    if (ea->date < eb->date) return -1;
    if (ea->date > eb->date) return 1;
    return 0;
}

void afficherTimeline(const CycleTimeline *tl) {
    // Copier les événements pour tri
    TimelineEvent temp[100];
    for (int i = 0; i < tl->nbEvenements; i++) {
        temp[i] = tl->evenements[i];
    }
    qsort(temp, tl->nbEvenements, sizeof(TimelineEvent), comparerDates);

    printf("\n=== TIMELINE DU CYCLE ===\n");
    if (tl->nbEvenements == 0) {
        printf("Aucun événement enregistré.\n");
        return;
    }
    for (int i = 0; i < tl->nbEvenements; i++) {
        TimelineEvent e = temp[i];
        char dateStr[30];
        strftime(dateStr, sizeof(dateStr), "%d/%m/%Y", localtime(&e.date));
        printf("[%s] %s : %s\n", dateStr, eventTypeToString(e.type), e.description);
        if (e.details[0] != '\0') {
            printf("      → %s\n", e.details);
        }
    }
}

void afficherEvenementsAVenir(const CycleTimeline *tl) {
    time_t now = time(NULL);
    printf("\n=== ÉVÉNEMENTS À VENIR ===\n");
    int trouve = 0;
    for (int i = 0; i < tl->nbEvenements; i++) {
        if (tl->evenements[i].date > now) {
            TimelineEvent e = tl->evenements[i];
            char dateStr[30];
            strftime(dateStr, sizeof(dateStr), "%d/%m/%Y", localtime(&e.date));
            printf("%s : %s\n", dateStr, e.description);
            trouve = 1;
        }
    }
    if (!trouve) printf("Aucun événement à venir.\n");
}