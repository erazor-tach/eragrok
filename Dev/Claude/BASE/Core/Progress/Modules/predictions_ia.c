#include "predictions_ia.h"
#include <stdio.h>
#include <string.h>
#include <math.h>

void linearRegression(const DataPoint points[], int nbPoints, float *pente, float *intercept, float *r2) {
    if (nbPoints < 2) {
        *pente = 0;
        *intercept = 0;
        *r2 = 0;
        return;
    }

    float sumX = 0, sumY = 0, sumXY = 0, sumX2 = 0, sumY2 = 0;
    for (int i = 0; i < nbPoints; i++) {
        float x = (float)points[i].date;  // attention: très grand nombre, mais on peut normaliser
        float y = points[i].valeur;
        sumX += x;
        sumY += y;
        sumXY += x * y;
        sumX2 += x * x;
        sumY2 += y * y;
    }

    float n = (float)nbPoints;
    float denom = n * sumX2 - sumX * sumX;
    if (denom == 0) {
        *pente = 0;
        *intercept = sumY / n;
        *r2 = 0;
        return;
    }

    *pente = (n * sumXY - sumX * sumY) / denom;
    *intercept = (sumY - *pente * sumX) / n;

    // Coefficient de détermination R²
    float moyenneY = sumY / n;
    float ssTot = 0, ssRes = 0;
    for (int i = 0; i < nbPoints; i++) {
        float x = (float)points[i].date;
        float y = points[i].valeur;
        float yPred = *pente * x + *intercept;
        ssTot += (y - moyenneY) * (y - moyenneY);
        ssRes += (y - yPred) * (y - yPred);
    }
    if (ssTot == 0) *r2 = 1;
    else *r2 = 1 - (ssRes / ssTot);
}

float predireValeur(const DataPoint points[], int nbPoints, time_t dateFuture, float *confiance) {
    if (nbPoints < 2) {
        *confiance = 0;
        return 0;
    }

    float pente, intercept, r2;
    linearRegression(points, nbPoints, &pente, &intercept, &r2);

    *confiance = r2 * 100; // confiance basée sur R²
    return pente * (float)dateFuture + intercept;
}

Prediction predireProchainRM(const char *exercice, const DataPoint historiqueRM[], int nbPoints) {
    Prediction pred;
    strcpy(pred.exercice, exercice);
    strcpy(pred.unite, "kg");

    if (nbPoints < 2) {
        pred.valeurPredite = 0;
        pred.confiance = 0;
        pred.datePrediction = time(NULL) + 7 * 24 * 3600; // +7 jours
        return pred;
    }

    // Prendre la date du dernier point + 7 jours pour la prédiction
    time_t derniereDate = historiqueRM[nbPoints-1].date;
    time_t dateFuture = derniereDate + 7 * 24 * 3600; // +7 jours

    float confiance;
    pred.valeurPredite = predireValeur(historiqueRM, nbPoints, dateFuture, &confiance);
    pred.confiance = confiance;
    pred.datePrediction = dateFuture;

    return pred;
}

Prediction predirePoids(const DataPoint historiquePoids[], int nbPoints, int joursFutur) {
    Prediction pred;
    strcpy(pred.exercice, "Poids de forme");
    strcpy(pred.unite, "kg");

    if (nbPoints < 2) {
        pred.valeurPredite = 0;
        pred.confiance = 0;
        pred.datePrediction = time(NULL) + joursFutur * 24 * 3600;
        return pred;
    }

    time_t derniereDate = historiquePoids[nbPoints-1].date;
    time_t dateFuture = derniereDate + joursFutur * 24 * 3600;

    float confiance;
    pred.valeurPredite = predireValeur(historiquePoids, nbPoints, dateFuture, &confiance);
    pred.confiance = confiance;
    pred.datePrediction = dateFuture;

    return pred;
}

void afficherPrediction(const Prediction *p) {
    char dateStr[30];
    strftime(dateStr, sizeof(dateStr), "%d/%m/%Y", localtime(&p->datePrediction));

    printf("\n=== PRÉDICTION ===\n");
    printf("%s : %.1f %s (estimé au %s)\n", p->exercice, p->valeurPredite, p->unite, dateStr);
    printf("Indice de confiance : %.1f%%\n", p->confiance);
    if (p->confiance < 30) printf("(Données insuffisantes pour une prédiction fiable)\n");
    else if (p->confiance < 60) printf("(Confiance moyenne)\n");
    else printf("(Bonne confiance)\n");
}