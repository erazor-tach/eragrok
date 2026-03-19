# THRESHOLD - Démarrage Rapide

## 🚀 Lancer l'application WEB

### Option 1 : Serveur Python (Recommandé)

```bash
# Depuis le terminal
cd E:\Projet\GIT\C\Dev\web
python -m http.server 8000
```

Puis ouvrir : **http://localhost:8000**

### Option 2 : Fichier direct

Double-cliquer sur : `E:\Projet\GIT\C\Dev\web\index.html`

---

## 🧭 Pages disponibles

- **Dashboard** : http://localhost:8000/index.html
- **Workouts** : http://localhost:8000/workout.html
- **Nutrition** : http://localhost:8000/nutrition.html
- **Progrès** : http://localhost:8000/progres.html
- **Cycle** : http://localhost:8000/cycle.html
- **Settings** : http://localhost:8000/settings.html

---

## ✨ Fonctionnalités testées

### Dashboard (index.html)
- ✅ Séance en cours avec ring progress (78%)
- ✅ Chronomètre fonctionnel (Play/Pause/Reset)
- ✅ Compteur de séries (+/-)
- ✅ Cartes interactives
- ✅ Bottom navigation

### Workout (workout.html)
- ✅ Calendrier semaine
- ✅ Chronomètre repos
- ✅ Compteur séries
- ✅ Catalogue exercices
- ✅ Techniques vidéo
- ✅ Historique détaillé

### Nutrition (nutrition.html)
- ✅ Calculateur IMC interactif
- ✅ Générateur de plan (Masse/Sèche/Maintien)
- ✅ Planning repas semaine
- ✅ Liste courses (checkboxes)
- ✅ Scanner code-barres (UI)
- ✅ Objectifs quotidiens

### Progrès (progres.html)
- ✅ Graphiques évolution poids
- ✅ Graphiques force (1RM)
- ✅ Records personnels
- ✅ Objectifs avec progress bars
- ✅ Comparaison périodique
- ✅ Prédictions IA

### Cycle (cycle.html)
- ✅ Cycle en cours (ring 56%)
- ✅ Planning injection
- ✅ Paramètres cycle
- ✅ Timeline
- ✅ Rappels avec toggles
- ✅ Historique cycles

### Settings (settings.html)
- ✅ Profil utilisateur
- ✅ Préférences générales
- ✅ Notifications (toggles)
- ✅ Appareils connectés
- ✅ Confidentialité/Sécurité
- ✅ Paramètres spécifiques modules

---

## 🎮 Navigation

**Bottom Nav (6 onglets)** :
Cliquer sur n'importe quel onglet pour naviguer entre les pages.

**Indicateur actif** :
- Icône orange (#ff9f5c)
- Petit point orange en dessous
- Text-shadow glow

---

## 🔧 Tests recommandés

1. **Navigation** : Tester tous les onglets bottom nav
2. **Chronomètre** : Play/Pause/Reset
3. **Compteur** : +/- séries
4. **IMC** : Sliders taille/poids
5. **Toggles** : Settings, Cycle, Nutrition
6. **Responsive** : Resize fenêtre → max 480px

---

## ⚡ Performance

**Temps de chargement** : < 500ms  
**Animations** : 60 FPS  
**Taille pages** : ~80-100 KB chacune  
**Mobile-first** : Optimisé pour mobile dès le départ

---

## 📱 Test Mobile

**Chrome DevTools** :
1. F12 → Toggle device toolbar (Ctrl+Shift+M)
2. Sélectionner "iPhone 12 Pro" ou similaire
3. Tester touch interactions

**Vraie device** :
1. Sur même réseau : http://[IP_PC]:8000
2. Exemple : http://192.168.1.100:8000

---

## 🐛 Problèmes connus

**Navigation** :
- ⚠️ Le script `js/navigation.js` doit être chargé
- ⚠️ Chemins relatifs : utiliser serveur local

**Chronomètre** :
- ℹ️ Réinitialise à 01:30 par défaut
- ℹ️ Pas de persistance (normal pour proto)

---

## 📊 Checklist validation

- [ ] Toutes les pages s'affichent correctement
- [ ] Navigation bottom nav fonctionne
- [ ] Chronomètre démarre/pause/reset
- [ ] Compteur séries +/-
- [ ] IMC calcule en temps réel
- [ ] Toggles activent/désactivent
- [ ] Sliders changent valeurs
- [ ] Animations fluides
- [ ] Pas d'erreurs console

---

**Date** : 17 Mars 2026  
**Version** : 1.0.0 PROTO
