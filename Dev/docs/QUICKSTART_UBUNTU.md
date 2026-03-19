# ⚡ THRESHOLD C++ — Quick Start Ubuntu WSL

## 📦 Installation (une fois)
```bash
# Mise à jour des paquets
sudo apt update

# Installation complète
sudo apt install -y \
    build-essential \
    cmake \
    libsqlite3-dev \
    sqlite3

# Vérification
cmake --version      # Doit afficher >= 3.10
g++ --version        # Doit afficher g++ (Ubuntu...)
sqlite3 --version    # Doit afficher 3.x.x
```

## 🚀 Compilation

### Méthode 1 : Script automatique (recommandé)
```bash
# 1. Aller dans le projet
cd /mnt/e/Projet/GIT/C

# 2. Rendre le script exécutable
chmod +x build.sh

# 3. Compiler
./build.sh
```

### Méthode 2 : Makefile
```bash
cd /mnt/e/Projet/GIT/C
make run  # Compile + exécute
```

## ⚡ Exécution
```bash
./build/threshold_test
```

---

## 🔧 Commandes utiles

```bash
# Recompiler après modification
./build.sh

# Nettoyer et recompiler
./build.sh clean
./build.sh

# Ou avec make
make clean
make run
```

---

## ✅ **Sortie attendue**

```
════════════════════════════════════════════════════════════════════════════
  THRESHOLD C++ — Compilation WSL/Linux
════════════════════════════════════════════════════════════════════════════

[Vérification] Dépendances...
✅ Toutes les dépendances présentes

[1/3] Configuration CMake...
-- Build type : Release
-- Compiler   : /usr/bin/c++
-- SQLite3    : sqlite3

[2/3] Compilation...
[ 20%] Building CXX object CMakeFiles/threshold_test.dir/src/threshold_types.cpp.o
[ 40%] Building CXX object CMakeFiles/threshold_test.dir/src/db_wrapper.cpp.o
[ 60%] Building CXX object CMakeFiles/threshold_test.dir/src/meal_engine.cpp.o
[ 80%] Building CXX object CMakeFiles/threshold_test.dir/src/utils.cpp.o
[100%] Building CXX object CMakeFiles/threshold_test.dir/test/main_test.cpp.o
[100%] Linking CXX executable threshold_test

[3/3] Succès !

════════════════════════════════════════════════════════════════════════════
  ✅ Compilation terminée !
════════════════════════════════════════════════════════════════════════════

Exécutable créé : build/threshold_test
```

Puis en exécutant :
```
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║   THRESHOLD C++ — Tests Module                                     ║
║   Version squelette 1.0                                          ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝

🧪 TEST 1 : Base de données SQLite
──────────────────────────────────────────────────────────────
✅ Connexion DB établie
✅ Settings : test_key = test_value
✅ Base de données fonctionnelle

🧪 TEST 2 : Calculs nutrition
──────────────────────────────────────────────────────────────
  Profil : Homme, 80kg, 30 ans, 180cm
  Objectif : Prise de masse (+20%)

  Résultats :
    TDEE        : 2960 kcal
    Calories    : 3552 kcal
    Protéines   : 160 g
    Glucides    : 417 g
    Lipides     : 90 g
✅ Calculs nutrition OK

🧪 TEST 3 : Générateur de plans
──────────────────────────────────────────────────────────────
✅ Catalogue aliments chargé
✅ Génération réussie

[... plan alimentaire affiché ...]

╔═══════════════════════════════════════════════════════════════════╗
║ ✅ TOUS LES TESTS PASSÉS                                         ║
╚═══════════════════════════════════════════════════════════════════╝
```

---

## 🐛 Dépannage Ubuntu

### ❌ `cmake: command not found`
```bash
sudo apt install cmake
```

### ❌ `sqlite3.h: No such file or directory`
```bash
sudo apt install libsqlite3-dev
```

### ❌ `Permission denied: ./build.sh`
```bash
chmod +x build.sh
```

---

📖 **Guide complet** : README_WSL.md (fonctionne aussi pour Ubuntu)
