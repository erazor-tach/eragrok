#ifndef WORKOUT_TRACKS_H
#define WORKOUT_TRACKS_H

#define MAX_TRACKS 100
#define MAX_PLAYLISTS 10
#define MAX_NAME_LEN 64
#define MAX_ARTIST_LEN 64

typedef struct {
    char titre[MAX_NAME_LEN];
    char artiste[MAX_ARTIST_LEN];
    int duree; // en secondes
    int bpm;
    int favori; // 0 ou 1
} Track;

typedef struct {
    char nom[MAX_NAME_LEN];
    Track pistes[MAX_TRACKS];
    int nbPistes;
} Playlist;

// Initialise quelques pistes d'exemple
void initTracks(Playlist *playlist);

// Ajoute une piste à une playlist
void ajouterPiste(Playlist *playlist, const char *titre, const char *artiste, int duree, int bpm);

// Affiche la playlist
void afficherPlaylist(const Playlist *playlist);

// Marque une piste comme favorite
void toggleFavori(Track *piste);

// Joue une piste (simulation)
void jouerPiste(const Track *piste);

// Affiche les pistes favorites (parcours toutes les playlists)
void afficherFavoris(Playlist playlists[], int nbPlaylists);

#endif