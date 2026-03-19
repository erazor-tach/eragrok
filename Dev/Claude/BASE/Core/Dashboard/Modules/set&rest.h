#ifndef SET_REST_H
#define SET_REST_H

/**
 * Lance le compteur de séries interactif.
 * L'utilisateur peut appuyer sur '+' pour incrémenter,
 * '-' pour décrémenter, 'r' pour remettre à zéro,
 * et 'q' pour quitter.
 */
void compteurSeries(void);

/**
 * Lance le chronomètre de récupération (90 secondes par défaut).
 * Commandes : 's' pour démarrer/pause, 'r' pour reset, 'q' pour quitter.
 */
void chronometre(void);

#endif