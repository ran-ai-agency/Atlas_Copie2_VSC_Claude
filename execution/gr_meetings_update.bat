@echo off
REM GR International - Mise a jour hebdomadaire des reunions
REM Execute chaque vendredi a 7h00 via tache planifiee Windows

cd /d "c:\Users\ranai\Documents\Atlas - Copie"

echo ============================================================
echo [%date% %time%] Debut de l'extraction des reunions GR
echo ============================================================

python execution/gr_meetings_scraper.py

echo ============================================================
echo [%date% %time%] Extraction terminee
echo ============================================================
