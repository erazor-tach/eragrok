# THRESHOLD - Interface Web

## 📁 Structure du projet

```
E:\Projet\GIT\C\Dev\web\
├── index.html          # Dashboard (page d'accueil)
├── workout.html        # Workouts / Entraînements
├── nutrition.html      # Nutrition
├── progres.html        # Progrès / Statistiques
├── cycle.html          # Cycle (PEDs tracking)
├── settings.html       # Paramètres
├── css/
│   └── common.css      # Styles communs (WIP)
└── js/
    └── navigation.js   # Système de navigation
```

## 🎨 Design System

**Palette de couleurs** :
- Primary: `#ff8c42` (Orange feu)
- Primary dark: `#e0662a`
- Primary light: `#ffb88c`
- Background root: `#0a0c0e`
- Background card: `#1a1e26`
- Background input: `#0f131a`
- Text: `#e8eef2`
- Text muted: `#8e9fb1`
- Border: `#2e353f`
- Success: `#8bc34a`

**Polices** :
- Interface: Inter (Google Fonts)
- Titres/Chiffres: Archivo Black (Google Fonts)

**Principe mobile-first** :
- Largeur max: 480px
- Border-radius: 28px (très moderne)
- Tous les éléments tactiles bien dimensionnés (min 40x40px)

## 🔗 Navigation

Le fichier `js/navigation.js` gère automatiquement la navigation entre les pages.

**Bottom nav (6 onglets)** :
1. Dashboard → index.html
2. Workouts → workout.html
3. Nutrition → nutrition.html
4. Progrès → progres.html
5. Cycle → cycle.html
6. Settings → settings.html

## 🚀 Démarrage

**Méthode simple** :
Ouvrir `index.html` directement dans un navigateur.

**Serveur local (recommandé)** :
```bash
# Python 3
cd E:\Projet\GIT\C\Dev\web
python -m http.server 8000
```

Puis ouvrir : http://localhost:8000

## ⚙️ État d'implémentation

✅ **Complété** :
- [x] 6 pages HTML complètes
- [x] Design mobile-first orange
- [x] Animations (fadeIn, pulse)
- [x] Navigation bottom nav
- [x] Chronomètres/compteurs fonctionnels
- [x] IMC calculateur interactif
- [x] Toggles (settings, cycle)
- [x] Sliders (settings, nutrition)
- [x] Charts/graphiques (CSS)

🔄 **En cours** :
- [ ] Extraction CSS commun (optimisation)
- [ ] Intégration avec backend C++
- [ ] Persistence SQLite via API

📋 **Prévu** :
- [ ] Responsive desktop
- [ ] PWA (offline, installable)
- [ ] Sync avec appareils connectés
- [ ] Export PDF/CSV

## 📝 Notes techniques

**CSS inline vs externe** :
Actuellement, chaque page a son CSS inline pour faciliter le prototypage.
Pour la production, le CSS sera extrait dans `css/common.css`.

**JavaScript** :
Chaque page a son JS inline (chrono, compteur, etc.).
Le fichier `js/navigation.js` est partagé.

**Compatibilité** :
- Chrome/Edge : ✅
- Firefox : ✅
- Safari : ✅
- Mobile : ✅ (Design mobile-first)

## 🔧 Prochaines étapes

1. **Intégration C++** : Connecter l'interface aux bindings JNI
2. **Base de données** : Implémenter la persistence via SQLite
3. **Tests** : Tester sur différents devices
4. **Optimisation** : Minifier CSS/JS

---

**Version** : 1.0.0 (Mars 2026)  
**Auteur** : Erazor (avec Claude Sonnet 4.5)
