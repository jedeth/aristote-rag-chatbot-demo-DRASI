@echo off
chcp 65001 > nul
echo Ouverture du fichier de configuration...
echo.
echo Remplacez "votre_token_ici" par votre cle API Aristote.
echo Sauvegardez (Ctrl+S) puis fermez le Bloc-notes.
echo.
start notepad "%~dp0app\.env"
