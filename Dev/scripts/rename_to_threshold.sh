#!/bin/bash
# rename_threshold_to_threshold.sh — Renommage automatique complet
# ─────────────────────────────────────────────────────────────────────────────

cd /mnt/e/Projet/GIT/C

echo "🔄 Renommage THRESHOLD → THRESHOLD"
echo "════════════════════════════════════════════════════════════════"

# Renommer les fichiers
echo "[1/3] Renommage des fichiers..."
mv src/threshold_types.cpp src/threshold_types.cpp 2>/dev/null
mv test_threshold.db test_threshold.db 2>/dev/null
mv THRESHOLD_Architecture_C++.pdf THRESHOLD_Architecture_C++.pdf 2>/dev/null

# Remplacer dans tous les fichiers source/header
echo "[2/3] Remplacement dans les fichiers C++..."
find . -type f \( -name "*.h" -o -name "*.cpp" -o -name "*.txt" -o -name "*.md" -o -name "*.sh" -o -name "*.bat" -o -name "*.html" -o -name "*.css" \) -exec sed -i 's/THRESHOLD/THRESHOLD/g' {} \;
find . -type f \( -name "*.h" -o -name "*.cpp" -o -name "*.txt" -o -name "*.md" -o -name "*.sh" -o -name "*.bat" -o -name "*.html" -o -name "*.css" \) -exec sed -i 's/threshold/threshold/g' {} \;
find . -type f \( -name "*.h" -o -name "*.cpp" -o -name "*.txt" -o -name "*.md" -o -name "*.sh" -o -name "*.bat" -o -name "*.html" -o -name "*.css" \) -exec sed -i 's/Threshold/Threshold/g' {} \;

echo "[3/3] Nettoyage build..."
rm -rf build/

echo ""
echo "✅ Renommage terminé !"
echo "════════════════════════════════════════════════════════════════"
echo "Prochaine étape : ./build.sh"
