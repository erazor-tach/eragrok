#include "notification_settings.h"
#include <stdio.h>

void initNotificationSettings(NotificationSettings *settings) {
    // Workout
    settings->workout.actif = 1;
    settings->workout.heure = 18;
    settings->workout.minute = 0;
    settings->workout.recurrence = 1; // quotidien

    // Meal
    settings->meal.actif = 1;
    settings->meal.heure = 12;
    settings->meal.minute = 0;
    settings->meal.recurrence = 1;

    // Injection
    settings->injection.actif = 1;
    settings->injection.heure = 8;
    settings->injection.minute = 0;
    settings->injection.recurrence = 0; // à définir par le planning

    // Water
    settings->water.actif = 1;
    settings->water.heure = 10;
    settings->water.minute = 0;
    settings->water.recurrence = 1;

    // Progress
    settings->progress.actif = 0;
    settings->progress.heure = 20;
    settings->progress.minute = 0;
    settings->progress.recurrence = 7; // hebdomadaire

    // Cycle
    settings->cycle.actif = 1;
    settings->cycle.heure = 9;
    settings->cycle.minute = 0;
    settings->cycle.recurrence = 0;

    // General
    settings->general.actif = 1;
    settings->general.heure = 9;
    settings->general.minute = 0;
    settings->general.recurrence = 1;
}

const char* notificationTypeToString(NotificationType type) {
    switch (type) {
        case NOTIF_WORKOUT_REMINDER: return "Rappels d'entraînement";
        case NOTIF_MEAL_REMINDER: return "Rappels de repas";
        case NOTIF_INJECTION_REMINDER: return "Rappels d'injection";
        case NOTIF_WATER_REMINDER: return "Rappels d'hydratation";
        case NOTIF_PROGRESS_UPDATE: return "Mises à jour de progression";
        case NOTIF_CYCLE_ALERT: return "Alertes cycle";
        case NOTIF_GENERAL: return "Général";
        default: return "Inconnu";
    }
}

NotificationSetting* getSettingPtr(NotificationSettings *settings, NotificationType type) {
    switch (type) {
        case NOTIF_WORKOUT_REMINDER: return &settings->workout;
        case NOTIF_MEAL_REMINDER: return &settings->meal;
        case NOTIF_INJECTION_REMINDER: return &settings->injection;
        case NOTIF_WATER_REMINDER: return &settings->water;
        case NOTIF_PROGRESS_UPDATE: return &settings->progress;
        case NOTIF_CYCLE_ALERT: return &settings->cycle;
        case NOTIF_GENERAL: return &settings->general;
        default: return NULL;
    }
}

void setNotificationActive(NotificationSettings *settings, NotificationType type, int actif) {
    NotificationSetting *s = getSettingPtr(settings, type);
    if (s) s->actif = actif;
}

void setNotificationTime(NotificationSettings *settings, NotificationType type, int heure, int minute) {
    NotificationSetting *s = getSettingPtr(settings, type);
    if (s) {
        s->heure = heure;
        s->minute = minute;
    }
}

NotificationSetting getNotificationSetting(const NotificationSettings *settings, NotificationType type) {
    // Version const, on ne modifie pas
    switch (type) {
        case NOTIF_WORKOUT_REMINDER: return settings->workout;
        case NOTIF_MEAL_REMINDER: return settings->meal;
        case NOTIF_INJECTION_REMINDER: return settings->injection;
        case NOTIF_WATER_REMINDER: return settings->water;
        case NOTIF_PROGRESS_UPDATE: return settings->progress;
        case NOTIF_CYCLE_ALERT: return settings->cycle;
        case NOTIF_GENERAL: return settings->general;
        default: { NotificationSetting empty = {0,0,0,0}; return empty; }
    }
}

void displayNotificationSettings(const NotificationSettings *settings) {
    printf("\n=== PARAMÈTRES DE NOTIFICATION ===\n");
    NotificationType types[] = {
        NOTIF_WORKOUT_REMINDER,
        NOTIF_MEAL_REMINDER,
        NOTIF_INJECTION_REMINDER,
        NOTIF_WATER_REMINDER,
        NOTIF_PROGRESS_UPDATE,
        NOTIF_CYCLE_ALERT,
        NOTIF_GENERAL
    };
    int nbTypes = sizeof(types) / sizeof(NotificationType);

    for (int i = 0; i < nbTypes; i++) {
        NotificationSetting s = getNotificationSetting(settings, types[i]);
        printf("%s : %s", notificationTypeToString(types[i]), s.actif ? "Actif" : "Inactif");
        if (s.actif) {
            printf(" à %02d:%02d", s.heure, s.minute);
        }
        printf("\n");
    }
}