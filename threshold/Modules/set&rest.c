#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <unistd.h> // pour sleep() sur Linux/Unix (ou <windows.h> pour Windows)

#ifdef _WIN32
#include <windows.h>
#define SLEEP(x) Sleep(x * 1000)
#else
#define SLEEP(x) sleep(x)
#endif

// Fonction pour afficher le menu
void afficherMenu() {
    printf("\n=== THRESHOLD - COMPTEURS ===\n");
    printf("1. Compteur de séries\n");
    printf("2. Chronomètre de récupération\n");
    printf("3. Quitter\n");
    printf("Choix : ");
}

// Compteur de séries
void compteurSeries() {
    int series = 0;
    char choix;
    printf("\n--- Compteur de séries ---\n");
    printf("Utilisez '+' pour augmenter, '-' pour diminuer, 'r' pour remettre à zéro, 'q' pour quitter.\n");
    while (1) {
        printf("\rSéries effectuées : %d   ", series);
        fflush(stdout);
        scanf(" %c", &choix);
        switch (choix) {
            case '+':
                series++;
                break;
            case '-':
                if (series > 0) series--;
                break;
            case 'r':
                series = 0;
                break;
            case 'q':
                return;
            default:
                printf("Commande non reconnue.\n");
        }
    }
}

// Chronomètre simple (compte à rebours depuis 90 secondes)
void chronometre() {
    int secondes = 90;
    char commande;
    int running = 0;
    time_t debut, maintenant;
    printf("\n--- Chronomètre de récupération (90s) ---\n");
    printf("Commandes : 's' start/pause, 'r' reset, 'q' quitter.\n");
    while (1) {
        if (running) {
            maintenant = time(NULL);
            int ecoule = (int)difftime(maintenant, debut);
            int reste = secondes - ecoule;
            if (reste < 0) reste = 0;
            printf("\rTemps restant : %02d:%02d   ", reste / 60, reste % 60);
            fflush(stdout);
            if (reste == 0) {
                printf("\nTemps écoulé !\n");
                running = 0;
            }
        } else {
            printf("\rTemps restant : %02d:%02d   ", secondes / 60, secondes % 60);
            fflush(stdout);
        }

        // Vérifie si une touche a été pressée (non bloquant)
        // Sur les systèmes Unix, on peut utiliser un select, mais pour simplifier on utilise une attente active avec getchar() bloquant.
        // Pour une version simple, on va rendre le menu séquentiel : on n'affiche le temps qu'après une commande.
        // Mais pour simuler un vrai chrono, il faudrait un thread. On va faire une version simplifiée où on entre les commandes et le temps s'écoule entre les commandes.
        // Pour garder le code simple, on va utiliser une approche avec scanf bloquant, donc le temps ne s'écoule que quand on ne tape pas.
        // Je vais plutôt faire un chronomètre pas à pas : on démarre, puis on entre 'p' pour mettre en pause et voir le temps.
        // Ce n'est pas parfait mais ça donne une idée.
        printf("\nCommande : ");
        scanf(" %c", &commande);
        if (commande == 's') {
            if (running) {
                running = 0;
                // on met à jour le temps écoulé
                int ecoule = (int)difftime(time(NULL), debut);
                secondes -= ecoule;
                if (secondes < 0) secondes = 0;
            } else {
                if (secondes > 0) {
                    running = 1;
                    debut = time(NULL);
                }
            }
        } else if (commande == 'r') {
            running = 0;
            secondes = 90;
        } else if (commande == 'q') {
            break;
        }
    }
}

int main() {
    int choix;
    while (1) {
        afficherMenu();
        scanf("%d", &choix);
        switch (choix) {
            case 1:
                compteurSeries();
                break;
            case 2:
                chronometre();
                break;
            case 3:
                printf("À bientôt !\n");
                exit(0);
            default:
                printf("Choix invalide.\n");
        }
    }
    return 0;
}