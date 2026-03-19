# Module SessionHelper

**Aide pour la séance d'entraînement**

---

## 📋 Description

Module autonome qui fournit un assistant de séance avec :
- ✅ Chronomètre (Play/Pause/Reset)
- ✅ Compteur de séries (+/- avec progression)
- ✅ Ring progress (indicateur % visuel)
- ✅ Actions (Modifier/Terminer)

---

## 📁 Fichiers

```
modules/SessionHelper/
├── SessionHelper.html    # Structure HTML
├── SessionHelper.css     # Styles
├── SessionHelper.js      # Logique (classe)
└── README.md             # Cette doc
```

---

## 🚀 Utilisation

### 1. Inclure les fichiers

```html
<!-- Dans votre page HTML -->
<link rel="stylesheet" href="modules/SessionHelper/SessionHelper.css">
```

### 2. Ajouter le HTML

```html
<!-- Copier le contenu de SessionHelper.html -->
<div class="session-card" id="sessionHelper">
  <!-- ... -->
</div>
```

### 3. Charger le script

```html
<script src="modules/SessionHelper/SessionHelper.js"></script>
```

### 4. Le module s'initialise automatiquement !

---

## 🎯 Fonctionnalités

### Chronomètre
- **Play** : Démarre le chrono
- **Pause** : Met en pause
- **Reset** : Remet à 00:00
- Format : MM:SS
- Sauvegarde de l'état

### Compteur de séries
- **Bouton +** : Incrémente le nombre de séries
- **Bouton -** : Décrémente le nombre de séries
- Plage : 0 → Total (configurable)
- Mise à jour automatique du ring progress
