#include "user_profile.h"
#include <stdio.h>
#include <string.h>

void initProfile(UserProfile *profile) {
    strcpy(profile->nom, "Utilisateur");
    profile->age = 30;
    profile->taille = 175.0;
    profile->poids = 75.0;
    profile->objectif = OBJECTIF_MAINTIEN;
    strcpy(profile->email, "email@exemple.com");
    strcpy(profile->telephone, "");
    profile->notifications = 1;
    profile->partageDonnees = 0;
}

const char* objectifToString(ObjectifPrincipal obj) {
    switch (obj) {
        case OBJECTIF_PRISE_MASSE: return "Prise de masse";
        case OBJECTIF_SECHE: return "Sèche";
        case OBJECTIF_MAINTIEN: return "Maintien";
        case OBJECTIF_FORCE: return "Force";
        case OBJECTIF_ENDURANCE: return "Endurance";
        default: return "Inconnu";
    }
}

void afficherProfile(const UserProfile *profile) {
    printf("\n=== PROFIL UTILISATEUR ===\n");
    printf("Nom : %s\n", profile->nom);
    printf("Âge : %d ans\n", profile->age);
    printf("Taille : %.1f cm\n", profile->taille);
    printf("Poids : %.1f kg\n", profile->poids);
    printf("Objectif : %s\n", objectifToString(profile->objectif));
    printf("Email : %s\n", profile->email);
    printf("Téléphone : %s\n", profile->telephone);
    printf("Notifications : %s\n", profile->notifications ? "Oui" : "Non");
    printf("Partage des données : %s\n", profile->partageDonnees ? "Oui" : "Non");
}

void setNom(UserProfile *profile, const char *nom) {
    strcpy(profile->nom, nom);
}

void setAge(UserProfile *profile, int age) {
    if (age >= 0 && age <= 120) profile->age = age;
}

void setTaille(UserProfile *profile, float taille) {
    if (taille > 0) profile->taille = taille;
}

void setPoids(UserProfile *profile, float poids) {
    if (poids > 0) profile->poids = poids;
}

void setObjectif(UserProfile *profile, ObjectifPrincipal obj) {
    profile->objectif = obj;
}