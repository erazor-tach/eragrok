#include "weight_history.h"
#include <stdio.h>
#include <string.h>
#include <time.h>

void initWeightHistory(WeightHistory *hist) {
    hist->nbEntries = 0;
}

void addWeight(WeightHistory *hist, float poids, time_t date) {
    if (hist->nbEntries >= 365) return;
    if (date == 0) date = time(NULL);
    WeightEntry *e = &hist->entries[hist->nbEntries];
    e->date = date;
    e->poids = poids;
    // e->imc pourrait être calculé si on a la taille
    hist->nbEntries++;
}

float getLastWeight(const WeightHistory *hist) {
    if (hist->nbEntries == 0) return 0;
    return hist->entries[hist->nbEntries - 1].poids;
}

void getStats(const WeightHistory *hist, float *min, float *max, float *avg) {
    if (hist->nbEntries == 0) {
        *min = *max = *avg = 0;
        return;
    }
    *min = hist->entries[0].poids;
    *max = hist->entries[0].poids;
    float sum = 0;
    for (int i = 0; i < hist->nbEntries; i++) {
        float p = hist->entries[i].poids;
        if (p < *min) *min = p;
        if (p > *max) *max = p;
        sum += p;
    }
    *avg = sum / hist->nbEntries;
}

float getTotalChange(const WeightHistory *hist) {
    if (hist->nbEntries < 2) return 0;
    return hist->entries[hist->nbEntries - 1].poids - hist->entries[0].poids;
}

void displayWeightHistory(const WeightHistory *hist) {
    printf("\n=== HISTORIQUE DU POIDS ===\n");
    printf(" # | Date       | Poids (kg) | Variation\n");
    printf("----------------------------------------\n");
    float prev = 0;
    for (int i = 0; i < hist->nbEntries; i++) {
        WeightEntry e = hist->entries[i];
        char dateStr[20];
        strftime(dateStr, sizeof(dateStr), "%d/%m/%Y", localtime(&e.date));
        float var = (i > 0) ? e.poids - prev : 0;
        printf("%2d | %s | %8.1f | %+6.1f\n", i+1, dateStr, e.poids, var);
        prev = e.poids;
    }
}

void displayWeightChart(const WeightHistory *hist) {
    if (hist->nbEntries == 0) return;
    float min, max, avg;
    getStats(hist, &min, &max, &avg);
    float range = max - min;
    if (range < 0.1) range = 0.1;
    printf("\nÉvolution du poids (chaque # ≈ 1 kg):\n");
    for (int i = 0; i < hist->nbEntries; i++) {
        WeightEntry e = hist->entries[i];
        char dateStr[20];
        strftime(dateStr, sizeof(dateStr), "%d/%m", localtime(&e.date));
        int barLength = (int)((e.poids - min) / range * 20);
        if (barLength < 0) barLength = 0;
        printf("%s | ", dateStr);
        for (int j = 0; j < barLength; j++) printf("#");
        printf(" %.1f kg\n", e.poids);
    }
}