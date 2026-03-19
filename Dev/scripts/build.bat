@echo off
REM build.bat — Compilation rapide THRESHOLD C++
REM ─────────────────────────────────────────────────────────────────────────────
REM Usage : double-clic sur ce fichier → compile → threshold_test.exe créé
REM ─────────────────────────────────────────────────────────────────────────────

echo ════════════════════════════════════════════════════════════════════════════
echo   THRESHOLD C++ — Compilation Windows
echo ════════════════════════════════════════════════════════════════════════════
echo.

REM Vérifier si CMake est installé
where cmake >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERREUR] CMake non trouvé !
    echo.
    echo Installe CMake depuis : https://cmake.org/download/
    echo Ou via chocolatey : choco install cmake
    pause
    exit /b 1
)

REM Créer dossier build
if not exist build mkdir build
cd build

echo [1/3] Configuration CMake...
cmake .. -G "MinGW Makefiles"
if %errorlevel% neq 0 (
    echo [ERREUR] Configuration échouée
    pause
    exit /b 1
)

echo.
echo [2/3] Compilation...
cmake --build . --config Release
if %errorlevel% neq 0 (
    echo [ERREUR] Compilation échouée
    pause
    exit /b 1
)

echo.
echo [3/3] Succès !
echo.
echo ════════════════════════════════════════════════════════════════════════════
echo   threshold_test.exe créé dans : build\Release\
echo ════════════════════════════════════════════════════════════════════════════
echo.

cd ..
pause
