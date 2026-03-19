#include "workout_tracks.h"
#include <stdio.h>
#include <string.h>

void initTracks(Playlist *playlist) {
    strcpy(playlist->nom, "Focus Mix");
    playlist->nbPistes = 0;

    ajouterPiste(playlist, "Until I Collapse", "Eminem", 277, 90);
    ajouterPiste(playlist, "Stronger", "Kanye West", 312, 104);
    ajouterPiste(playlist, "Eye of the Tiger", "Survivor", 244, 109);
    ajouterPiste(playlist, "Lose Yourself", "Eminem", 326, 80);
    ajouterPiste(playlist, "Remember the Name", "Fort Minor", 230, 85);
}

void ajouterPiste(Playlist *playlist, const char *titre, const char *artiste, int duree, int bpm) {
    if (playlist->nbPistes >= MAX_TRACKS) return;
    Track *t = &playlist->pistes[playlist->nbPistes];
    strcpy(t->titre, titre);
    strcpy(t->artiste, artiste);
    t->duree = duree;
    t->bpm = bpm;
    t->favori = 0;
    playlist->nbPistes++;
}

void afficherPlaylist(const Playlist *playlist) {
    printf("\n=== Playlist : %s ===\n", playlist->nom);
    for (int i = 0; i < playlist->nbPistes; i++) {
        Track t = playlist->pistes[i];
        printf("%d. %s - %s (%02d:%02d) %d bpm %s\n",
               i+1,
               t.titre,
               t.artiste,
               t.duree / 60,
               t.duree % 60,
               t.bpm,
               t.favori ? "[Favori]" : "");
    }
}

void toggleFavori(Track *piste) {
    piste->favori = !piste->favori;
    printf("Piste %s %s favoris.\n", piste->titre, piste->favori ? "ajoutée aux" : "retirée des");
}

void jouerPiste(const Track *piste) {
    printf("▶ Lecture : %s - %s (%02d:%02d)\n",
           piste->titre,
           piste->artiste,
           piste->duree / 60,
           piste->duree % 60);
}

void afficherFavoris(Playlist playlists[], int nbPlaylists) {
    printf("\n=== Favoris ===\n");
    for (int i = 0; i < nbPlaylists; i++) {
        for (int j = 0; j < playlists[i].nbPistes; j++) {
            if (playlists[i].pistes[j].favori) {
                Track t = playlists[i].pistes[j];
                printf("%s - %s (%s)\n", t.titre, t.artiste, playlists[i].nom);
            }
        }
    }
}