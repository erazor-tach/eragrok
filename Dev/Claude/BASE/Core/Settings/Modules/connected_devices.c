#include "connected_devices.h"
#include <stdio.h>
#include <string.h>
#include <time.h>

const char* deviceTypeToString(DeviceType type) {
    switch (type) {
        case DEVICE_WATCH: return "Montre connectée";
        case DEVICE_SCALE: return "Balance";
        case DEVICE_HEART_RATE: return "Cardiofréquencemètre";
        case DEVICE_SMART_PHONE: return "Application smartphone";
        default: return "Autre";
    }
}

void initDeviceList(DeviceList *list) {
    list->nbDevices = 0;
}

void ajouterAppareil(DeviceList *list,
                     const char *nom,
                     DeviceType type,
                     const char *modele,
                     const char *adresse) {
    if (list->nbDevices >= 20) return;
    ConnectedDevice *d = &list->devices[list->nbDevices];
    d->id = list->nbDevices + 1;
    strcpy(d->nom, nom);
    d->type = type;
    strcpy(d->modele, modele);
    strcpy(d->adresseMAC, adresse);
    d->connecte = 0; // déconnecté par défaut
    d->derniereSync = 0; // jamais synchronisé
    d->actif = 1;
    list->nbDevices++;
}

void supprimerAppareil(DeviceList *list, int id) {
    for (int i = 0; i < list->nbDevices; i++) {
        if (list->devices[i].id == id) {
            for (int j = i; j < list->nbDevices - 1; j++) {
                list->devices[j] = list->devices[j+1];
            }
            list->nbDevices--;
            return;
        }
    }
}

void setAppareilConnecte(DeviceList *list, int id, int connecte) {
    for (int i = 0; i < list->nbDevices; i++) {
        if (list->devices[i].id == id) {
            list->devices[i].connecte = connecte;
            return;
        }
    }
}

void updateDerniereSync(DeviceList *list, int id) {
    for (int i = 0; i < list->nbDevices; i++) {
        if (list->devices[i].id == id) {
            list->devices[i].derniereSync = time(NULL);
            return;
        }
    }
}

void afficherAppareils(const DeviceList *list) {
    printf("\n=== APPAREILS CONNECTÉS ===\n");
    if (list->nbDevices == 0) {
        printf("Aucun appareil enregistré.\n");
        return;
    }
    for (int i = 0; i < list->nbDevices; i++) {
        ConnectedDevice d = list->devices[i];
        printf("ID %d : %s [%s]\n", d.id, d.nom, deviceTypeToString(d.type));
        printf("  Modèle : %s\n", d.modele);
        printf("  Adresse : %s\n", d.adresseMAC);
        printf("  État : %s\n", d.connecte ? "Connecté" : "Déconnecté");
        if (d.derniereSync != 0) {
            char dateStr[30];
            strftime(dateStr, sizeof(dateStr), "%d/%m/%Y %H:%M", localtime(&d.derniereSync));
            printf("  Dernière synchro : %s\n", dateStr);
        } else {
            printf("  Jamais synchronisé\n");
        }
        printf("  Actif : %s\n\n", d.actif ? "Oui" : "Non");
    }
}

void afficherAppareilsActifs(const DeviceList *list) {
    printf("\n=== APPAREILS ACTIFS ===\n");
    int trouve = 0;
    for (int i = 0; i < list->nbDevices; i++) {
        if (list->devices[i].actif) {
            ConnectedDevice d = list->devices[i];
            printf("ID %d : %s (%s) - %s\n", d.id, d.nom, deviceTypeToString(d.type),
                   d.connecte ? "Connecté" : "Déconnecté");
            trouve = 1;
        }
    }
    if (!trouve) printf("Aucun appareil actif.\n");
}