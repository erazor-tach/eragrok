@echo off
echo.
echo ========================================
echo   THRESHOLD - Navigation Test
echo ========================================
echo.
echo Lancement du serveur web...
echo.
cd /d E:\Projet\GIT\C\Dev\web
echo.
echo OUVRE TON NAVIGATEUR :
echo.
echo   http://localhost:8000/index.html
echo.
echo Clique sur les onglets en bas pour tester !
echo.
echo ========================================
echo.
python -m http.server 8000
