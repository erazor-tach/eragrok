#!/bin/bash
# Compilation CGI pour Apache

echo "🔨 Compilation API CGI Threshold..."

cd /mnt/e/Projet/GIT/C

# Compiler l'API CGI
g++ -std=c++17 \
    cgi/api.cpp \
    src/threshold_types.cpp \
    src/db_wrapper.cpp \
    src/meal_engine.cpp \
    src/food_data.cpp \
    src/exercise_data.cpp \
    src/utils.cpp \
    -I./include \
    -lsqlite3 -lpthread \
    -o cgi/threshold.cgi

if [ $? -eq 0 ]; then
    chmod +x cgi/threshold.cgi
    echo "✅ Compilation réussie : cgi/threshold.cgi"
    echo ""
    echo "📋 Installation Apache :"
    echo "sudo cp cgi/threshold.cgi /usr/lib/cgi-bin/"
    echo "sudo chmod 755 /usr/lib/cgi-bin/threshold.cgi"
else
    echo "❌ Erreur de compilation"
    exit 1
fi
