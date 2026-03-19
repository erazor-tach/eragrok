#include "backup_sync.h"
#include <stdio.h>
#include <string.h>
#include <time.h>

void initBackupSync(BackupSyncConfig *config) {
    // Sauvegarde
    config->backup.frequency = BACKUP_WEEKLY;
    config->backup.lastBackup = 0; // jamais
    config->backup.autoBackup = 1;
    strcpy(config->backup.backupPath, "/sdcard/Threshold/backups/");

    // Synchronisation
    config->sync.syncType = SYNC_NONE;
    config->sync.autoSync = 0;
    config->sync.lastSync = 0;
    strcpy(config->sync.cloudService, "Aucun");
}

const char* backupFrequencyToString(BackupFrequency freq) {
    switch (freq) {
        case BACKUP_NEVER: return "Jamais";
        case BACKUP_DAILY: return "Quotidienne";
        case BACKUP_WEEKLY: return "Hebdomadaire";
        case BACKUP_MONTHLY: return "Mensuelle";
        default: return "Inconnu";
    }
}

const char* syncTypeToString(SyncType type) {
    switch (type) {
        case SYNC_NONE: return "Aucune";
        case SYNC_CLOUD: return "Cloud";
        case SYNC_LOCAL: return "Locale";
        default: return "Inconnu";
    }
}

void setBackupFrequency(BackupSyncConfig *config, BackupFrequency freq) {
    config->backup.frequency = freq;
}

void setAutoBackup(BackupSyncConfig *config, int enabled) {
    config->backup.autoBackup = enabled;
}

void updateLastBackup(BackupSyncConfig *config) {
    config->backup.lastBackup = time(NULL);
}

void setBackupPath(BackupSyncConfig *config, const char *path) {
    strncpy(config->backup.backupPath, path, sizeof(config->backup.backupPath) - 1);
    config->backup.backupPath[sizeof(config->backup.backupPath) - 1] = '\0';
}

void setSyncType(BackupSyncConfig *config, SyncType type) {
    config->sync.syncType = type;
}

void setAutoSync(BackupSyncConfig *config, int enabled) {
    config->sync.autoSync = enabled;
}

void updateLastSync(BackupSyncConfig *config) {
    config->sync.lastSync = time(NULL);
}

void setCloudService(BackupSyncConfig *config, const char *service) {
    strncpy(config->sync.cloudService, service, sizeof(config->sync.cloudService) - 1);
    config->sync.cloudService[sizeof(config->sync.cloudService) - 1] = '\0';
}

void displayBackupSync(const BackupSyncConfig *config) {
    printf("\n=== SAUVEGARDE & SYNCHRONISATION ===\n");
    printf("--- Sauvegarde ---\n");
    printf("Fréquence : %s\n", backupFrequencyToString(config->backup.frequency));
    printf("Auto backup : %s\n", config->backup.autoBackup ? "Activé" : "Désactivé");
    if (config->backup.lastBackup != 0) {
        char dateStr[30];
        strftime(dateStr, sizeof(dateStr), "%d/%m/%Y %H:%M", localtime(&config->backup.lastBackup));
        printf("Dernière sauvegarde : %s\n", dateStr);
    } else {
        printf("Dernière sauvegarde : jamais\n");
    }
    printf("Chemin : %s\n", config->backup.backupPath);

    printf("--- Synchronisation ---\n");
    printf("Type : %s\n", syncTypeToString(config->sync.syncType));
    printf("Auto sync : %s\n", config->sync.autoSync ? "Activé" : "Désactivé");
    if (config->sync.lastSync != 0) {
        char dateStr[30];
        strftime(dateStr, sizeof(dateStr), "%d/%m/%Y %H:%M", localtime(&config->sync.lastSync));
        printf("Dernière synchronisation : %s\n", dateStr);
    } else {
        printf("Dernière synchronisation : jamais\n");
    }
    printf("Service cloud : %s\n", config->sync.cloudService);
}