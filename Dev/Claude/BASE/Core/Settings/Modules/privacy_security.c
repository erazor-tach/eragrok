#include "privacy_security.h"
#include <stdio.h>
#include <string.h>

void initPrivacySecurity(PrivacySecurityConfig *config) {
    // Confidentialité
    config->privacy.sharingLevel = SHARE_ANONYMOUS;
    config->privacy.allowAnalytics = 1;
    config->privacy.allowMarketing = 0;
    config->privacy.allowLocation = 0;

    // Sécurité
    config->security.authMethod = AUTH_NONE;
    config->security.pinCode[0] = '\0';
    config->security.autoLockTimeout = 300; // 5 min
    config->security.twoFactorEnabled = 0;
}

void setSharingLevel(PrivacySecurityConfig *config, DataSharingLevel level) {
    config->privacy.sharingLevel = level;
}

void setAllowAnalytics(PrivacySecurityConfig *config, int allow) {
    config->privacy.allowAnalytics = allow;
}

void setAllowMarketing(PrivacySecurityConfig *config, int allow) {
    config->privacy.allowMarketing = allow;
}

void setAllowLocation(PrivacySecurityConfig *config, int allow) {
    config->privacy.allowLocation = allow;
}

void setAuthMethod(PrivacySecurityConfig *config, AuthMethod method, const char *pin) {
    config->security.authMethod = method;
    if (method == AUTH_PIN && pin != NULL) {
        strncpy(config->security.pinCode, pin, 9);
        config->security.pinCode[9] = '\0';
    } else {
        config->security.pinCode[0] = '\0';
    }
}

void setAutoLockTimeout(PrivacySecurityConfig *config, int seconds) {
    config->security.autoLockTimeout = seconds;
}

void setTwoFactorEnabled(PrivacySecurityConfig *config, int enabled) {
    config->security.twoFactorEnabled = enabled;
}

int checkPin(const PrivacySecurityConfig *config, const char *pin) {
    if (config->security.authMethod != AUTH_PIN) return 0;
    return (strcmp(config->security.pinCode, pin) == 0);
}

const char* sharingLevelToString(DataSharingLevel level) {
    switch (level) {
        case SHARE_NONE: return "Aucun partage";
        case SHARE_ANONYMOUS: return "Anonymisé";
        case SHARE_FRIENDS: return "Amis uniquement";
        case SHARE_PUBLIC: return "Public";
        default: return "Inconnu";
    }
}

const char* authMethodToString(AuthMethod method) {
    switch (method) {
        case AUTH_NONE: return "Aucune";
        case AUTH_PIN: return "Code PIN";
        case AUTH_PASSWORD: return "Mot de passe";
        case AUTH_BIOMETRIC: return "Biométrique";
        default: return "Inconnu";
    }
}

void displayPrivacySecurity(const PrivacySecurityConfig *config) {
    printf("\n=== CONFIDENTIALITÉ ET SÉCURITÉ ===\n");
    printf("--- Confidentialité ---\n");
    printf("Partage des données : %s\n", sharingLevelToString(config->privacy.sharingLevel));
    printf("Analytics : %s\n", config->privacy.allowAnalytics ? "Autorisé" : "Refusé");
    printf("Marketing : %s\n", config->privacy.allowMarketing ? "Autorisé" : "Refusé");
    printf("Localisation : %s\n", config->privacy.allowLocation ? "Autorisée" : "Refusée");

    printf("--- Sécurité ---\n");
    printf("Authentification : %s\n", authMethodToString(config->security.authMethod));
    if (config->security.authMethod == AUTH_PIN) {
        printf("PIN : %s\n", config->security.pinCode);
    }
    printf("Verrouillage auto : %d secondes\n", config->security.autoLockTimeout);
    printf("Double authentification : %s\n", config->security.twoFactorEnabled ? "Activée" : "Désactivée");
}