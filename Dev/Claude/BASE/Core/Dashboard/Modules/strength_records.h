#ifndef STRENGTH_RECORDS_H
#define STRENGTH_RECORDS_H

// Structure pour un record (1RM) sur un exercice
typedef struct {
    char exercice[50];
    float poids;          // 1RM en kg
    char date[11];        // format JJ/MM/AAAA
    float progression;    // évolution depuis le dernier record (en kg ou %)
} Record;

// Structure pour gérer une collection de records
typedef struct {
    Record records[20];   // max 20 exercices suivis
    int nbRecords;
} CollectionRecords;

// Ajoute ou met à jour un record pour un exercice
// Retourne 1 si nouveau record, 0 sinon
int ajouterRecord(CollectionRecords *collection, const char *exercice, float poids, const char *date);

// Supprime un record (par index)
void supprimerRecord(CollectionRecords *collection, int index);

// Affiche tous les records
void afficherRecords(const CollectionRecords *collection);

// Calcule la progression en pourcentage entre deux valeurs
float calculerProgression(float ancien, float nouveau);

// Retourne un record spécifique par nom d'exercice (ou NULL si non trouvé)
Record* rechercherRecord(CollectionRecords *collection, const char *exercice);

#endif