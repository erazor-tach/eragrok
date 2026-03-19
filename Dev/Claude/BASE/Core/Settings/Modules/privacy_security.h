#ifndef PRIVACY_SECURITY_H
#define PRIVACY_SECURITY_H

// Niveau de partage des données
typedef enum {
    SHARE_NONE,         // Aucun partage
    SHARE_ANONYMOUS,    // Données anonymisées
    SHARE_FRIENDS,      // Amis uniquement
    SHARE_PUBLIC        // Public
} DataSharingLevel;

// Authentification
typedef enum {
    AUTH_NONE,
    AUTH_PIN,
    AUTH_PASSWORD,
    AUTH_BIOMETRIC
} AuthMethod;

// Structure pour les paramètres de confidentialité
typedef struct {
    DataSharingLevel sharingLevel;
    int allowAnalytics;          // 0/1
    int allowMarketing;          // 0/1
    int allowLocation;           // 0/1
} PrivacySettings;

// Structure pour les paramètres de sécurité
typedef struct {
    AuthMethod authMethod;
    char pinCode[10];            // code PIN (si utilisé)
    int autoLockTimeout;         // secondes (0 = jamais)
    int twoFactorEnabled;        // 0/1
} SecuritySettings;

// Structure globale
typedef struct {
    PrivacySettings privacy;
    SecuritySettings security;
} PrivacySecurityConfig;

// Initialise avec des valeurs par défaut
void initPrivacySecurity(PrivacySecurityConfig *config);

// Met à jour le niveau de partage
void setSharingLevel(PrivacySecurityConfig *config, DataSharingLevel level);

// Active/désactive les analytics
void setAllowAnalytics(PrivacySecurityConfig *config, int allow);

// Active/désactive le marketing
void setAllowMarketing(PrivacySecurityConfig *config, int allow);

// Active/désactive la localisation
void setAllowLocation(PrivacySecurityConfig *config, int allow);

// Définit la méthode d'authentification
void setAuthMethod(PrivacySecurityConfig *config, AuthMethod method, const char *pin);

// Définit le délai de verrouillage automatique
void setAutoLockTimeout(PrivacySecurityConfig *config, int seconds);

// Active/désactive la double authentification
void setTwoFactorEnabled(PrivacySecurityConfig *config, int enabled);

// Vérifie le PIN (retourne 1 si correct)
int checkPin(const PrivacySecurityConfig *config, const char *pin);

// Affiche les paramètres
void displayPrivacySecurity(const PrivacySecurityConfig *config);

// Conversions en chaînes pour affichage
const char* sharingLevelToString(DataSharingLevel level);
const char* authMethodToString(AuthMethod method);

#endif