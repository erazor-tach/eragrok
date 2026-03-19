#include "about.h"
#include <stdio.h>
#include <string.h>

void initAbout(AboutInfo *about) {
    strcpy(about->appName, "Threshold");
    strcpy(about->version, "3.2.1");
    strcpy(about->buildDate, "18/03/2026");
    strcpy(about->author, "Équipe Threshold");
    strcpy(about->website, "https://www.threshold.app");
    strcpy(about->license, "Logiciel propriétaire - Tous droits réservés");
    strcpy(about->description, "Application de suivi bodybuilding, nutrition et cycles. Développée avec passion.");
}

void setAppName(AboutInfo *about, const char *name) {
    strncpy(about->appName, name, sizeof(about->appName)-1);
    about->appName[sizeof(about->appName)-1] = '\0';
}

void setVersion(AboutInfo *about, const char *version) {
    strncpy(about->version, version, sizeof(about->version)-1);
    about->version[sizeof(about->version)-1] = '\0';
}

void setBuildDate(AboutInfo *about, const char *date) {
    strncpy(about->buildDate, date, sizeof(about->buildDate)-1);
    about->buildDate[sizeof(about->buildDate)-1] = '\0';
}

void setAuthor(AboutInfo *about, const char *author) {
    strncpy(about->author, author, sizeof(about->author)-1);
    about->author[sizeof(about->author)-1] = '\0';
}

void setWebsite(AboutInfo *about, const char *url) {
    strncpy(about->website, url, sizeof(about->website)-1);
    about->website[sizeof(about->website)-1] = '\0';
}

void setLicense(AboutInfo *about, const char *license) {
    strncpy(about->license, license, sizeof(about->license)-1);
    about->license[sizeof(about->license)-1] = '\0';
}

void setDescription(AboutInfo *about, const char *desc) {
    strncpy(about->description, desc, sizeof(about->description)-1);
    about->description[sizeof(about->description)-1] = '\0';
}

void displayAbout(const AboutInfo *about) {
    printf("\n=== À PROPOS ===\n");
    printf("Application : %s\n", about->appName);
    printf("Version : %s\n", about->version);
    printf("Date de build : %s\n", about->buildDate);
    printf("Auteur : %s\n", about->author);
    printf("Site web : %s\n", about->website);
    printf("Licence : %s\n", about->license);
    printf("Description : %s\n", about->description);
}