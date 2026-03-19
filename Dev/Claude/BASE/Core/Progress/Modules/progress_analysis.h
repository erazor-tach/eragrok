#ifndef PROGRESS_ANALYSIS_H
#define PROGRESS_ANALYSIS_H

#include "personal_records.h"
#include "workout_session_log.h"
#include "recovery_analysis.h"

// Structure pour un élément d'analyse (point fort/faible)
typedef struct {
    char titre[50];
    char description[200];
    int estForce;               // 1 = force, 0 = faiblesse
} AnalysisItem;

// Structure pour une suggestion d'amélioration
typedef struct {
    char conseil[300];
} Suggestion;

// Structure contenant l'analyse complète
typedef struct {
    AnalysisItem forces[10];
    int nbForces;
    AnalysisItem faiblesses[10];
    int nbFaiblesses;
    Suggestion suggestions[10];
    int nbSuggestions;
} ProgressAnalysis;

// Génère une analyse à partir des données utilisateur
void genererAnalyse(const PersonalRecords *pr,
                    const WorkoutSessionLog *log,
                    const RecuperationJour *recup,
                    ProgressAnalysis *analyse);

// Affiche l'analyse
void afficherAnalyse(const ProgressAnalysis *analyse);

#endif