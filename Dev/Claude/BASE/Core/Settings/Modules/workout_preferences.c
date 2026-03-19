#include "workout_preferences.h"
#include <stdio.h>
#include <string.h>

void initWorkoutPreferences(WorkoutPreferences *prefs) {
    prefs->defaultRestTime = 90;
    prefs->autoStartNextExercise = 1;
    prefs->defaultWorkoutDuration = 60;
    strcpy(prefs->defaultProgram, "Split 4 jours");
    prefs->defaultRounds = 3;
    prefs->defaultExercisesPerWorkout = 6;
    prefs->remindersEnabled = 1;
    prefs->reminderHour = 18;
    prefs->reminderMinute = 0;
}

void setDefaultRestTime(WorkoutPreferences *prefs, int seconds) {
    if (seconds >= 15 && seconds <= 300) prefs->defaultRestTime = seconds;
}

void setAutoStartNextExercise(WorkoutPreferences *prefs, int enabled) {
    prefs->autoStartNextExercise = enabled;
}

void setDefaultWorkoutDuration(WorkoutPreferences *prefs, int minutes) {
    if (minutes >= 15 && minutes <= 180) prefs->defaultWorkoutDuration = minutes;
}

void setDefaultProgram(WorkoutPreferences *prefs, const char *program) {
    strncpy(prefs->defaultProgram, program, sizeof(prefs->defaultProgram)-1);
    prefs->defaultProgram[sizeof(prefs->defaultProgram)-1] = '\0';
}

void setDefaultRounds(WorkoutPreferences *prefs, int rounds) {
    if (rounds >= 1 && rounds <= 10) prefs->defaultRounds = rounds;
}

void setDefaultExercisesPerWorkout(WorkoutPreferences *prefs, int nb) {
    if (nb >= 1 && nb <= 20) prefs->defaultExercisesPerWorkout = nb;
}

void setRemindersEnabled(WorkoutPreferences *prefs, int enabled) {
    prefs->remindersEnabled = enabled;
}

void setReminderTime(WorkoutPreferences *prefs, int hour, int minute) {
    if (hour >= 0 && hour <= 23) prefs->reminderHour = hour;
    if (minute >= 0 && minute <= 59) prefs->reminderMinute = minute;
}

int getDefaultRestTime(const WorkoutPreferences *prefs) {
    return prefs->defaultRestTime;
}

int getAutoStartNextExercise(const WorkoutPreferences *prefs) {
    return prefs->autoStartNextExercise;
}

int getDefaultWorkoutDuration(const WorkoutPreferences *prefs) {
    return prefs->defaultWorkoutDuration;
}

const char* getDefaultProgram(const WorkoutPreferences *prefs) {
    return prefs->defaultProgram;
}

int getDefaultRounds(const WorkoutPreferences *prefs) {
    return prefs->defaultRounds;
}

int getDefaultExercisesPerWorkout(const WorkoutPreferences *prefs) {
    return prefs->defaultExercisesPerWorkout;
}

int getRemindersEnabled(const WorkoutPreferences *prefs) {
    return prefs->remindersEnabled;
}

int getReminderHour(const WorkoutPreferences *prefs) {
    return prefs->reminderHour;
}

int getReminderMinute(const WorkoutPreferences *prefs) {
    return prefs->reminderMinute;
}

void displayWorkoutPreferences(const WorkoutPreferences *prefs) {
    printf("\n=== PARAMÈTRES ENTRAÎNEMENT ===\n");
    printf("Temps de repos par défaut : %d s\n", prefs->defaultRestTime);
    printf("Passage auto à l'exercice suivant : %s\n", prefs->autoStartNextExercise ? "Oui" : "Non");
    printf("Durée moyenne d'une séance : %d min\n", prefs->defaultWorkoutDuration);
    printf("Programme par défaut : %s\n", prefs->defaultProgram);
    printf("Nombre de tours par défaut : %d\n", prefs->defaultRounds);
    printf("Exercices par séance : %d\n", prefs->defaultExercisesPerWorkout);
    printf("Rappels d'entraînement : %s\n", prefs->remindersEnabled ? "Activés" : "Désactivés");
    if (prefs->remindersEnabled) {
        printf("Heure du rappel : %02d:%02d\n", prefs->reminderHour, prefs->reminderMinute);
    }
}