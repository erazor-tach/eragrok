#include "current_session.h"
#include <stdio.h>
#include <time.h>
#include <string.h>

void demarrerSession(SessionEnCours *session, const SeanceJour *plan) {
    strcpy(session->nomSeance, plan->nomSeance);
    session->nbExercices = plan->nbExercices;
    session->exerciceEnCoursIndex = 0;
    session->debutSeance = time(NULL);
    session->dureeEcoulee = 0;
    session->terminee = 0;

    for (int i = 0; i < plan->nbExercices; i++) {
        strcpy(session->exercices[i].nom, plan->exercices[i].nom);
        session->exercices[i].seriesPrevues = plan->exercices[i].series;
        session->exercices[i].repetitionsPrevues = plan->exercices[i].repetitions;
        session->exercices[i].chargePrevue = plan->exercices[i].charge;
        session->exercices[i].seriesEffectuees = 0;
        session->exercices[i].repetitionsEffectuees = 0;
    }

    printf("Séance \"%s\" démarrée à %s", session->nomSeance, ctime(&session->debutSeance));
}

void validerSerieEnCours(SessionEnCours *session) {
    if (session->terminee) return;
    ExerciceEnCours *ex = &session->exercices[session->exerciceEnCoursIndex];
    if (ex->seriesEffectuees < ex->seriesPrevues) {
        ex->seriesEffectuees++;
        printf("Série %d/%d validée pour %s\n", ex->seriesEffectuees, ex->seriesPrevues, ex->nom);
    } else {
        printf("Toutes les séries de %s sont déjà effectuées. Passe à l'exercice suivant.\n", ex->nom);
        passerExerciceSuivant(session);
    }
}

void passerExerciceSuivant(SessionEnCours *session) {
    if (session->terminee) return;
    if (session->exerciceEnCoursIndex < session->nbExercices - 1) {
        session->exerciceEnCoursIndex++;
        printf("Passage à l'exercice : %s\n", session->exercices[session->exerciceEnCoursIndex].nom);
    } else {
        printf("Tous les exercices sont terminés !\n");
        terminerSession(session);
    }
}

void mettreAJourChrono(SessionEnCours *session) {
    if (session->terminee) return;
    time_t maintenant = time(NULL);
    session->dureeEcoulee = (int)difftime(maintenant, session->debutSeance);
}

void afficherSession(const SessionEnCours *session) {
    if (session->terminee) {
        printf("Séance terminée.\n");
        return;
    }
    printf("\n=== SESSION EN COURS : %s ===\n", session->nomSeance);
    printf("Temps écoulé : %02d:%02d\n", session->dureeEcoulee / 60, session->dureeEcoulee % 60);
    printf("Exercice en cours (%d/%d) : %s\n", session->exerciceEnCoursIndex+1, session->nbExercices,
           session->exercices[session->exerciceEnCoursIndex].nom);
    ExerciceEnCours ex = session->exercices[session->exerciceEnCoursIndex];
    printf("  Séries : %d/%d - Reps : %d - Charge : %.1f kg\n",
           ex.seriesEffectuees, ex.seriesPrevues, ex.repetitionsPrevues, ex.chargePrevue);
    // Option : afficher les exercices suivants
}

void terminerSession(SessionEnCours *session) {
    session->terminee = 1;
    time_t fin = time(NULL);
    int dureeTotale = (int)difftime(fin, session->debutSeance);
    printf("\n=== SÉANCE TERMINÉE ===\n");
    printf("Durée totale : %02d:%02d\n", dureeTotale / 60, dureeTotale % 60);
    printf("Résumé :\n");
    for (int i = 0; i < session->nbExercices; i++) {
        ExerciceEnCours ex = session->exercices[i];
        printf("  %s : %d/%d séries\n", ex.nom, ex.seriesEffectuees, ex.seriesPrevues);
    }
}