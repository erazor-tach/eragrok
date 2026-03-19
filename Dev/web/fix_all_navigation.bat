@echo off
REM Script pour fixer la navigation dans toutes les pages HTML
echo.
echo ========================================
echo THRESHOLD - Fix Navigation Script
echo ========================================
echo.

cd /d E:\Projet\GIT\C\Dev\web

echo Lancement du serveur web...
echo.
echo  Ouvre ton navigateur :  http://localhost:8000/index.html
echo.
echo  Pages disponibles :
echo   - index.html      (Dashboard)
echo   - workout.html    (Workouts)
echo   - nutrition.html  (Nutrition) 
echo   - progres.html    (Progres)
echo   - cycle.html      (Cycle)
echo   - settings.html   (Settings)
echo.
echo  Clique sur les onglets en bas pour naviguer !
echo.
echo ========================================
echo.

python -m http.server 8000

pause
