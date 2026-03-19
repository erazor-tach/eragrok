#ifndef ABOUT_H
#define ABOUT_H

// Structure pour les informations "À propos"
typedef struct {
    char appName[50];
    char version[20];
    char buildDate[30];
    char author[100];
    char website[100];
    char license[200];
    char description[300];
} AboutInfo;

// Initialise les informations avec des valeurs par défaut
void initAbout(AboutInfo *about);

// Affiche les informations "À propos"
void displayAbout(const AboutInfo *about);

// Setters (si nécessaire)
void setAppName(AboutInfo *about, const char *name);
void setVersion(AboutInfo *about, const char *version);
void setBuildDate(AboutInfo *about, const char *date);
void setAuthor(AboutInfo *about, const char *author);
void setWebsite(AboutInfo *about, const char *url);
void setLicense(AboutInfo *about, const char *license);
void setDescription(AboutInfo *about, const char *desc);

#endif