#ifndef HELP_SUPPORT_H
#define HELP_SUPPORT_H

// Structure pour une entrée de FAQ
typedef struct {
    int id;
    char question[200];
    char reponse[500];
} FAQEntry;

// Structure pour les coordonnées de support
typedef struct {
    char email[100];
    char telephone[20];
    char siteWeb[100];
    char facebook[100];
    char instagram[100];
    char twitter[100];
} SupportContacts;

// Structure pour les informations légales
typedef struct {
    char version[20];
    char buildDate[30];
    char termsUrl[100];
    char privacyUrl[100];
    char licenses[300];
} LegalInfo;

// Structure globale de l'aide
typedef struct {
    FAQEntry faq[20];
    int nbFAQ;
    SupportContacts contacts;
    LegalInfo legal;
} HelpSupport;

// Initialise les données d'aide (FAQs, contacts, etc.)
void initHelpSupport(HelpSupport *help);

// Affiche la FAQ
void displayFAQ(const HelpSupport *help);

// Affiche les coordonnées de contact
void displayContacts(const HelpSupport *help);

// Affiche les informations légales
void displayLegalInfo(const HelpSupport *help);

// Affiche le menu d'aide complet
void displayHelpMenu(const HelpSupport *help);

#endif