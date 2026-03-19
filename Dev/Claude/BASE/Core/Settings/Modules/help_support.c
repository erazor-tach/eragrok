#include "help_support.h"
#include <stdio.h>
#include <string.h>

void initHelpSupport(HelpSupport *help) {
    // FAQ
    help->nbFAQ = 0;

    strcpy(help->faq[help->nbFAQ].question, "Comment démarrer un cycle ?");
    strcpy(help->faq[help->nbFAQ].reponse, "Rendez-vous dans l'onglet Cycle, puis 'Nouveau cycle' et suivez les étapes. Vous pourrez y définir les produits, dosages et dates.");
    help->nbFAQ++;

    strcpy(help->faq[help->nbFAQ].question, "Comment ajouter une séance d'entraînement ?");
    strcpy(help->faq[help->nbFAQ].reponse, "Dans l'onglet Workouts, cliquez sur le bouton '+' en bas à droite pour créer une nouvelle séance. Vous pouvez aussi utiliser un modèle.");
    help->nbFAQ++;

    strcpy(help->faq[help->nbFAQ].question, "Mes données sont-elles sauvegardées ?");
    strcpy(help->faq[help->nbFAQ].reponse, "Oui, vous pouvez activer la sauvegarde automatique dans Paramètres > Sauvegarde & synchronisation. Vous pouvez aussi exporter manuellement.");
    help->nbFAQ++;

    strcpy(help->faq[help->nbFAQ].question, "Comment calculer mon 1RM ?");
    strcpy(help->faq[help->nbFAQ].reponse, "Lorsque vous enregistrez une performance, l'application calcule automatiquement votre 1RM estimé via la formule d'Epley. Vous pouvez le voir dans Progrès > Records.");
    help->nbFAQ++;

    strcpy(help->faq[help->nbFAQ].question, "Que faire si je rencontre un bug ?");
    strcpy(help->faq[help->nbFAQ].reponse, "Contactez notre support à l'adresse support@threshold.app en décrivant le problème et en joignant si possible une capture d'écran.");
    help->nbFAQ++;

    // Contacts
    strcpy(help->contacts.email, "support@threshold.app");
    strcpy(help->contacts.telephone, "+33 1 23 45 67 89");
    strcpy(help->contacts.siteWeb, "https://www.threshold.app");
    strcpy(help->contacts.facebook, "https://facebook.com/threshold.app");
    strcpy(help->contacts.instagram, "https://instagram.com/threshold.app");
    strcpy(help->contacts.twitter, "https://twitter.com/threshold_app");

    // Informations légales
    strcpy(help->legal.version, "3.2.1");
    strcpy(help->legal.buildDate, "18/03/2026");
    strcpy(help->legal.termsUrl, "https://www.threshold.app/terms");
    strcpy(help->legal.privacyUrl, "https://www.threshold.app/privacy");
    strcpy(help->legal.licenses, "Licences open source : SQLite, cJSON, etc.");
}

void displayFAQ(const HelpSupport *help) {
    printf("\n=== FOIRE AUX QUESTIONS ===\n");
    for (int i = 0; i < help->nbFAQ; i++) {
        printf("\nQ%d : %s\n", i+1, help->faq[i].question);
        printf("R : %s\n", help->faq[i].reponse);
    }
}

void displayContacts(const HelpSupport *help) {
    printf("\n=== CONTACT & SUPPORT ===\n");
    printf("Email : %s\n", help->contacts.email);
    printf("Téléphone : %s\n", help->contacts.telephone);
    printf("Site web : %s\n", help->contacts.siteWeb);
    printf("Facebook : %s\n", help->contacts.facebook);
    printf("Instagram : %s\n", help->contacts.instagram);
    printf("Twitter : %s\n", help->contacts.twitter);
}

void displayLegalInfo(const HelpSupport *help) {
    printf("\n=== INFORMATIONS LÉGALES ===\n");
    printf("Version : %s\n", help->legal.version);
    printf("Date de build : %s\n", help->legal.buildDate);
    printf("Conditions d'utilisation : %s\n", help->legal.termsUrl);
    printf("Politique de confidentialité : %s\n", help->legal.privacyUrl);
    printf("Licences : %s\n", help->legal.licenses);
}

void displayHelpMenu(const HelpSupport *help) {
    printf("\n=== AIDE & SUPPORT ===\n");
    printf("1. FAQ\n");
    printf("2. Nous contacter\n");
    printf("3. Informations légales\n");
    printf("4. Retour\n");
}