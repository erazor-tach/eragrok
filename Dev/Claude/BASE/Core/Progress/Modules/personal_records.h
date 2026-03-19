#ifndef PERSONAL_RECORDS_H
#define PERSONAL_RECORDS_H

#include <time.h>

// Structure pour un record sur un exercice
typedef struct {
    char exercice[50];      // nom de l'exercice
    float charge;           // charge en kg
    int repetitions;        // nombre de répétitions
    time_t date;            // date du record
    float estimated1RM;     // 1RM estimé (calculé automatiquement)
} RecordEntry;

// Structure pour l'ensemble des records
typedef struct {
    RecordEntry records[50]; // capacité max
    int nbRecords;
} PersonalRecords;

// Initialise la liste des records
void initPersonalRecords(PersonalRecords *pr);

// Ajoute ou met à jour un record pour un exercice
// Retourne 1 si nouveau record, 0 sinon
int updateRecord(PersonalRecords *pr, const char *exercice, float charge, int reps);

// Supprime le record d'un exercice
void deleteRecord(PersonalRecords *pr, const char *exercice);

// Récupère le record d'un exercice (retourne NULL si non trouvé)
RecordEntry* getRecord(PersonalRecords *pr, const char *exercice);

// Affiche tous les records
void displayAllRecords(const PersonalRecords *pr);

// Affiche les records les plus récents (par date)
void displayRecentRecords(const PersonalRecords *pr, int limit);

// Calcule le 1RM estimé selon la formule d'Epley : charge * (1 + reps/30)
float estimate1RM(float charge, int reps);

#endif