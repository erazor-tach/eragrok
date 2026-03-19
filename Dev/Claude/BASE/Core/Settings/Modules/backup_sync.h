#ifndef BACKUP_SYNC_H
#define BACKUP_SYNC_H

#include <time.h>

// Fréquence de sauvegarde automatique
typedef enum {
    BACKUP_NEVER,
    BACKUP_DAILY,
    BACKUP_WEEKLY,
    BACKUP_MONTHLY
} BackupFrequency;

// Type de synchronisation cloud
typedef enum {
    SYNC_NONE,
    SYNC_CLOUD,
    SYNC_LOCAL
} SyncType;

// Structure pour les paramètres de sauvegarde
typedef struct {
    BackupFrequency frequency;
    time_t lastBackup;          // timestamp de la dernière sauvegarde
    int autoBackup;             // 0/1 (si activé indépendamment de la fréquence)
    char backupPath[200];       // chemin local (si SYNC_LOCAL)
} BackupSettings;

// Structure pour les paramètres de synchronisation
typedef struct {
    SyncType syncType;
    int autoSync;               // 0/1
    time_t lastSync;            // dernière synchronisation
    char cloudService[50];      // "Google Drive", "Dropbox", etc.
} SyncSettings;

// Structure globale
typedef struct {
    BackupSettings backup;
    SyncSettings sync;
} BackupSyncConfig;

// Initialise avec des valeurs par défaut
void initBackupSync(BackupSyncConfig *config);

// Définit la fréquence de sauvegarde
void setBackupFrequency(BackupSyncConfig *config, BackupFrequency freq);

// Active/désactive la sauvegarde automatique
void setAutoBackup(BackupSyncConfig *config, int enabled);

// Met à jour la date de dernière sauvegarde à maintenant
void updateLastBackup(BackupSyncConfig *config);

// Définit le chemin de sauvegarde local
void setBackupPath(BackupSyncConfig *config, const char *path);

// Définit le type de synchronisation
void setSyncType(BackupSyncConfig *config, SyncType type);

// Active/désactive la synchronisation automatique
void setAutoSync(BackupSyncConfig *config, int enabled);

// Met à jour la date de dernière synchronisation
void updateLastSync(BackupSyncConfig *config);

// Définit le service cloud
void setCloudService(BackupSyncConfig *config, const char *service);

// Affiche les paramètres
void displayBackupSync(const BackupSyncConfig *config);

// Conversions en chaînes pour affichage
const char* backupFrequencyToString(BackupFrequency freq);
const char* syncTypeToString(SyncType type);

#endif