#ifndef WORKOUT_PREFERENCES_H
#define WORKOUT_PREFERENCES_H

// Structure des préférences d'entraînement
typedef struct {
    int defaultRestTime;          // temps de repos par défaut (secondes)
    int autoStartNextExercise;    // démarrer automatiquement l'exercice suivant (0/1)
    int defaultWorkoutDuration;   // durée moyenne d'une séance (minutes)
    char defaultProgram[50];      // programme par défaut (ex: "Split 4 jours")
    int defaultRounds;            // nombre de tours par défaut (pour circuits)
    int defaultExercisesPerWorkout; // nombre d'exercices par défaut
    int remindersEnabled;         // activer les rappels d'entraînement (0/1)
    int reminderHour;             // heure du rappel (0-23)
    int reminderMinute;           // minute du rappel
} WorkoutPreferences;

// Initialise les préférences avec des valeurs par défaut
void initWorkoutPreferences(WorkoutPreferences *prefs);

// Setters
void setDefaultRestTime(WorkoutPreferences *prefs, int seconds);
void setAutoStartNextExercise(WorkoutPreferences *prefs, int enabled);
void setDefaultWorkoutDuration(WorkoutPreferences *prefs, int minutes);
void setDefaultProgram(WorkoutPreferences *prefs, const char *program);
void setDefaultRounds(WorkoutPreferences *prefs, int rounds);
void setDefaultExercisesPerWorkout(WorkoutPreferences *prefs, int nb);
void setRemindersEnabled(WorkoutPreferences *prefs, int enabled);
void setReminderTime(WorkoutPreferences *prefs, int hour, int minute);

// Getters
int getDefaultRestTime(const WorkoutPreferences *prefs);
int getAutoStartNextExercise(const WorkoutPreferences *prefs);
int getDefaultWorkoutDuration(const WorkoutPreferences *prefs);
const char* getDefaultProgram(const WorkoutPreferences *prefs);
int getDefaultRounds(const WorkoutPreferences *prefs);
int getDefaultExercisesPerWorkout(const WorkoutPreferences *prefs);
int getRemindersEnabled(const WorkoutPreferences *prefs);
int getReminderHour(const WorkoutPreferences *prefs);
int getReminderMinute(const WorkoutPreferences *prefs);

// Affichage
void displayWorkoutPreferences(const WorkoutPreferences *prefs);

#endif