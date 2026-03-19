#ifndef USER_PROFILE_H
#define USER_PROFILE_H

// Objectif principal
typedef enum {
    OBJECTIF_PRISE_MASSE,
    OBJECTIF_SECHE,
    OBJECTIF_MAINTIEN,
    OBJECTIF_FORCE,
    OBJECTIF_ENDURANCE
} ObjectifPrincipal;

// Structure du profil utilisateur
typedef struct {
    char nom[50];
    int age;
    float taille;        // en cm
    float poids;         // en kg
    ObjectifPrincipal objectif;
    char email[100];
    char telephone[20];
    // Options supplémentaires
    int notifications;   // 0/1
    int partageDonnees;  // 0/1
} UserProfile;

// Initialise le profil avec des valeurs par défaut ou vides
void initProfile(UserProfile *profile);

// Affiche les informations du profil
void afficherProfile(const UserProfile *profile);

// Modifie le nom
void setNom(UserProfile *profile, const char *nom);

// Modifie l'âge
void setAge(UserProfile *profile, int age);

// Modifie la taille
void setTaille(UserProfile *profile, float taille);

// Modifie le poids
void setPoids(UserProfile *profile, float poids);

// Modifie l'objectif
void setObjectif(UserProfile *profile, ObjectifPrincipal obj);

// Retourne une chaîne pour l'objectif
const char* objectifToString(ObjectifPrincipal obj);

#endif