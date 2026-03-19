# THRESHOLD - Backend CGI Apache

## 🎯 Architecture

```
Interface Web (HTML/JS)
         ↓
    Apache CGI
         ↓
  Backend C++ (threshold.cgi)
         ↓
      SQLite
```

## 📋 Installation Apache + CGI (WSL Ubuntu)

### Étape 1 : Installer Apache
```bash
sudo apt update
sudo apt install apache2
sudo a2enmod cgid
sudo systemctl restart apache2
```

### Étape 2 : Vérifier Apache
```bash
# Apache doit tourner
sudo systemctl status apache2

# Tester dans navigateur
# http://localhost
```

### Étape 3 : Compiler le CGI
```bash
cd /mnt/e/Projet/GIT/C
chmod +x Dev/scripts/build_cgi.sh
./Dev/scripts/build_cgi.sh
```

### Étape 4 : Installer le CGI
```bash
sudo cp cgi/threshold.cgi /usr/lib/cgi-bin/
sudo chmod 755 /usr/lib/cgi-bin/threshold.cgi
```

### Étape 5 : Tester l'API
```bash
# Test dans navigateur ou curl
curl "http://localhost/cgi-bin/threshold.cgi?action=tdee&age=30&poids=85&taille=180&sexe=homme&activite=actif"
```

Résultat attendu :
```json
{
  "tdee": 2873,
  "calories": 2873,
  "proteines": 160,
  "glucides": 405,
  "lipides": 88
}
```

## 🚀 Utilisation depuis JavaScript

### Inclure le script API
```html
<script src="js/api.js"></script>
```

### Appeler l'API
```javascript
// Calculer TDEE
const result = await calculateTDEE(30, 85, 180, 'homme', 'actif');
console.log('TDEE:', result.tdee);

// Afficher dans l'interface
document.getElementById('tdee-value').textContent = result.tdee;
```

## 📁 Structure fichiers

```
E:/Projet/GIT/C/
├── cgi/
│   ├── api.cpp              # Source API CGI
│   └── threshold.cgi        # Exécutable compilé
├── Dev/
│   ├── scripts/
│   │   └── build_cgi.sh     # Script compilation
│   └── web/
│       └── js/
│           └── api.js       # Client JavaScript
└── /usr/lib/cgi-bin/        # Apache CGI (WSL)
    └── threshold.cgi        # Installé ici
```

## 🔧 Endpoints disponibles

### `/cgi-bin/threshold.cgi?action=tdee`
**Paramètres** :
- `age` (int)
- `poids` (double) kg
- `taille` (double) cm
- `sexe` (string) "homme" ou "femme"
- `activite` (string) "sedentaire", "leger", "modere", "actif", "tres_actif"

**Retour** :
```json
{
  "tdee": 2873.0,
  "calories": 2873.0,
  "proteines": 160.0,
  "glucides": 405.0,
  "lipides": 88.0
}
```

### `/cgi-bin/threshold.cgi?action=meal` (TODO)
**Paramètres** :
- `nb_repas` (int)
- `calories` (double)

**Retour** : Plan repas complet

## ⚡ Avantages de cette approche

✅ **Simple** : Apache standard + CGI standard  
✅ **Pas de lib externe** : Pur C++ standard  
✅ **Déjà dispo** : Apache sur WSL  
✅ **Testable** : curl, navigateur  
✅ **Performant** : C++ natif compilé  

## 🐛 Debugging

### Logs Apache
```bash
sudo tail -f /var/log/apache2/error.log
```

### Test direct CGI
```bash
# En ligne de commande
REQUEST_METHOD=GET QUERY_STRING="action=tdee&age=30&poids=85&taille=180&sexe=homme&activite=actif" ./cgi/threshold.cgi
```

### Permissions
```bash
# Vérifier
ls -la /usr/lib/cgi-bin/threshold.cgi

# Devrait afficher
-rwxr-xr-x 1 root root ... threshold.cgi
```

## 📝 Prochaines étapes

1. ✅ API TDEE fonctionnelle
2. ⏳ API génération repas
3. ⏳ API historique nutrition
4. ⏳ API cycle
5. ⏳ API workout

---

**Date** : 18 Mars 2026  
**Version** : 1.0.0 CGI
