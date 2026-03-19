#ifndef CONNECTED_DEVICES_H
#define CONNECTED_DEVICES_H

#include <time.h>

// Types d'appareils supportés
typedef enum {
    DEVICE_WATCH,           // montre connectée
    DEVICE_SCALE,           // balance
    DEVICE_HEART_RATE,      // cardiofréquencemètre
    DEVICE_SMART_PHONE,     // application smartphone
    DEVICE_OTHER
} DeviceType;

// Structure pour un appareil
typedef struct {
    int id;
    char nom[50];
    DeviceType type;
    char modele[50];
    char adresseMAC[20];     // ou identifiant unique
    int connecte;            // 0 = déconnecté, 1 = connecté
    time_t derniereSync;     // timestamp de la dernière synchro
    int actif;               // 0 = désactivé, 1 = actif
} ConnectedDevice;

// Collection d'appareils
typedef struct {
    ConnectedDevice devices[20];
    int nbDevices;
} DeviceList;

// Initialise la liste (vide)
void initDeviceList(DeviceList *list);

// Ajoute un appareil
void ajouterAppareil(DeviceList *list,
                     const char *nom,
                     DeviceType type,
                     const char *modele,
                     const char *adresse);

// Supprime un appareil (par id)
void supprimerAppareil(DeviceList *list, int id);

// Marque un appareil comme connecté/déconnecté
void setAppareilConnecte(DeviceList *list, int id, int connecte);

// Met à jour la date de dernière synchronisation
void updateDerniereSync(DeviceList *list, int id);

// Affiche la liste des appareils
void afficherAppareils(const DeviceList *list);

// Affiche les appareils actifs uniquement
void afficherAppareilsActifs(const DeviceList *list);

// Retourne le nom du type d'appareil
const char* deviceTypeToString(DeviceType type);

#endif