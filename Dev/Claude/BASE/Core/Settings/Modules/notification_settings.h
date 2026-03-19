#ifndef NOTIFICATION_SETTINGS_H
#define NOTIFICATION_SETTINGS_H

// Types de notifications
typedef enum {
    NOTIF_WORKOUT_REMINDER,
    NOTIF_MEAL_REMINDER,
    NOTIF_INJECTION_REMINDER,
    NOTIF_WATER_REMINDER,
    NOTIF_PROGRESS_UPDATE,
    NOTIF_CYCLE_ALERT,
    NOTIF_GENERAL
} NotificationType;

// Structure pour les paramètres d'un type de notification
typedef struct {
    int actif;              // 0/1
    int heure;              // heure par défaut (0-23)
    int minute;             // minute
    int recurrence;         // 0: une fois, 1: quotidien, etc. (simplifié)
} NotificationSetting;

// Structure globale des paramètres de notification
typedef struct {
    NotificationSetting workout;
    NotificationSetting meal;
    NotificationSetting injection;
    NotificationSetting water;
    NotificationSetting progress;
    NotificationSetting cycle;
    NotificationSetting general;
} NotificationSettings;

// Initialise les paramètres avec des valeurs par défaut
void initNotificationSettings(NotificationSettings *settings);

// Active/désactive un type de notification
void setNotificationActive(NotificationSettings *settings, NotificationType type, int actif);

// Définit l'heure pour un type de notification
void setNotificationTime(NotificationSettings *settings, NotificationType type, int heure, int minute);

// Affiche tous les paramètres de notification
void displayNotificationSettings(const NotificationSettings *settings);

// Retourne le nom d'un type de notification (pour affichage)
const char* notificationTypeToString(NotificationType type);

// Récupère les paramètres pour un type donné
NotificationSetting getNotificationSetting(const NotificationSettings *settings, NotificationType type);

#endif