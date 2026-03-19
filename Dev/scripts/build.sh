#!/bin/bash
# build.sh — Compilation THRESHOLD C++ sous WSL/Linux
# ─────────────────────────────────────────────────────────────────────────────
# Usage : ./build.sh
# ─────────────────────────────────────────────────────────────────────────────

set -e  # Arrêt si erreur

echo "════════════════════════════════════════════════════════════════════════════"
echo "  THRESHOLD C++ — Compilation WSL/Linux"
echo "════════════════════════════════════════════════════════════════════════════"
echo ""

# ═════════════════════════════════════════════════════════════════════════════
#  VÉRIFICATION DÉPENDANCES
# ═════════════════════════════════════════════════════════════════════════════

echo "[Vérification] Dépendances..."

# CMake
if ! command -v cmake &> /dev/null; then
    echo "❌ CMake non trouvé"
    echo "Installation : sudo apt update && sudo apt install cmake build-essential"
    exit 1
fi

# g++
if ! command -v g++ &> /dev/null; then
    echo "❌ g++ non trouvé"
    echo "Installation : sudo apt install build-essential"
    exit 1
fi

# SQLite3
if ! command -v sqlite3 &> /dev/null; then
    echo "⚠️  SQLite3 non trouvé — installation auto..."
    sudo apt update && sudo apt install -y sqlite3 libsqlite3-dev
fi

echo "✅ Toutes les dépendances présentes"
echo ""

# ═════════════════════════════════════════════════════════════════════════════
#  COMPILATION
# ═════════════════════════════════════════════════════════════════════════════

# Créer dossier build
mkdir -p build
cd build

echo "[1/3] Configuration CMake..."
cmake .. -DCMAKE_BUILD_TYPE=Release

echo ""
echo "[2/3] Compilation..."
make -j$(nproc)  # Utilise tous les cœurs CPU

echo ""
echo "[3/3] Succès !"
echo ""

cd ..

echo "════════════════════════════════════════════════════════════════════════════"
echo "  ✅ Compilation terminée !"
echo "════════════════════════════════════════════════════════════════════════════"
echo ""
echo "Exécutable créé : build/threshold_test"
echo ""
echo "Commandes :"
echo "  ./build/threshold_test          # Lancer les tests"
echo "  ./build.sh clean              # Nettoyer build/"
echo "  ./build.sh                    # Recompiler"
echo ""

# Option clean
if [[ "$1" == "clean" ]]; then
    echo "Nettoyage du dossier build/..."
    rm -rf build/
    echo "✅ Build/ supprimé"
fi
