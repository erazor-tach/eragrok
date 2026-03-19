#!/bin/bash
# install_ubuntu.sh — Installation dépendances Ubuntu WSL (une seule fois)
# ─────────────────────────────────────────────────────────────────────────────
# Usage : ./install_ubuntu.sh
# ─────────────────────────────────────────────────────────────────────────────

set -e

echo "════════════════════════════════════════════════════════════════════════════"
echo "  THRESHOLD C++ — Installation dépendances Ubuntu"
echo "════════════════════════════════════════════════════════════════════════════"
echo ""

# Mise à jour
echo "[1/2] Mise à jour des paquets..."
sudo apt update

# Installation
echo ""
echo "[2/2] Installation outils de compilation..."
sudo apt install -y \
    build-essential \
    cmake \
    libsqlite3-dev \
    sqlite3 \
    git

echo ""
echo "════════════════════════════════════════════════════════════════════════════"
echo "  ✅ Installation terminée !"
echo "════════════════════════════════════════════════════════════════════════════"
echo ""
echo "Versions installées :"
cmake --version | head -n1
g++ --version | head -n1
sqlite3 --version
echo ""
echo "Prochaine étape : ./build.sh"
