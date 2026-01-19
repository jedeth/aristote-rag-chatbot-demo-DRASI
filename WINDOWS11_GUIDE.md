# 🪟 Guide Docker sur Windows 11

**Date** : 2026-01-12
**Objectif** : Faire tourner la V2 sur Windows 11

---

## Prérequis Windows 11

### 1. WSL2 (Windows Subsystem for Linux)

**Vérifier si installé** :
```powershell
wsl --status
```

**Si pas installé** :
```powershell
# En tant qu'administrateur
wsl --install
# Redémarrer Windows
```

**Choisir une distribution** :
```powershell
wsl --list --online
wsl --install -d Ubuntu-24.04
```

### 2. Docker Desktop pour Windows

**Télécharger** : https://www.docker.com/products/docker-desktop/

**Installation** :
1. Télécharger Docker Desktop installer
2. Lancer l'installation
3. Cocher "Use WSL 2 instead of Hyper-V" (recommandé)
4. Redémarrer si demandé

**Configuration** :
- Ouvrir Docker Desktop
- Settings → Resources → WSL Integration
- Activer l'intégration avec Ubuntu

---

## Option A : Via WSL2 (Recommandé)

### Avantages
- ✅ Performance optimale
- ✅ Compatibilité totale avec les scripts Bash
- ✅ Partage de fichiers facile

### Installation dans WSL

```bash
# 1. Ouvrir WSL (Ubuntu)
wsl

# 2. Cloner le projet
cd ~
git clone https://github.com/votre-user/aristote-rag-chatbot-demo-DRASI.git
cd aristote-rag-chatbot-demo-DRASI

# 3. Configurer les variables
cp .env.docker .env
nano .env  # Ajouter vos clés API

# 4. Lancer la V2
./docker-manage-v2.sh start

# 5. Accès depuis Windows
# → http://localhost:8000/docs (API)
# → http://localhost:8502 (Frontend)
```

### Accéder aux fichiers Windows depuis WSL
```bash
# Depuis WSL, vos fichiers Windows sont dans :
cd /mnt/c/Users/VotreNom/Documents
```

### Accéder aux fichiers WSL depuis Windows
```
Explorer Windows → Barre d'adresse :
\\wsl$\Ubuntu\home\votreuser\aristote-rag-chatbot-demo-DRASI
```

---

## Option B : PowerShell + Docker Desktop

### Si vous voulez rester sur PowerShell

**Limitations** :
- ❌ Scripts Bash ne fonctionnent pas directement
- ⚠️ Syntaxe différente

**Commandes PowerShell équivalentes** :

```powershell
# 1. Cloner le projet
git clone https://github.com/votre-user/aristote-rag-chatbot-demo-DRASI.git
cd aristote-rag-chatbot-demo-DRASI

# 2. Configuration
copy .env.docker .env
notepad .env  # Éditer les clés API

# 3. Lancer V2 manuellement (car docker-manage-v2.sh est un script Bash)
docker-compose -f docker-compose-v2.yml up -d

# 4. Voir les logs
docker-compose -f docker-compose-v2.yml logs -f

# 5. Arrêter
docker-compose -f docker-compose-v2.yml down
```

**Alternative** : Utiliser Git Bash (installé avec Git pour Windows)

```bash
# Dans Git Bash
./docker-manage-v2.sh start
```

---

## Option C : Git Bash (Compromis)

### Installation Git Bash
1. Télécharger Git for Windows : https://git-scm.com/download/win
2. Installer avec les options par défaut
3. Ouvrir Git Bash depuis le menu Démarrer

### Utilisation
```bash
# Fonctionne comme sur Linux
cd /c/Users/VotreNom/Documents/aristote-rag-chatbot-demo-DRASI
./docker-manage-v2.sh start
```

---

## Vérification de l'Installation

### 1. Docker fonctionne ?
```powershell
# PowerShell
docker --version
docker ps

# WSL
wsl docker --version
```

### 2. Ports accessibles ?
```powershell
# PowerShell : Vérifier les ports ouverts
netstat -an | findstr "8000 8502"
```

### 3. Test des services
```powershell
# PowerShell : Test API
Invoke-WebRequest -Uri http://localhost:8000/health

# Ou depuis le navigateur
start http://localhost:8000/docs
start http://localhost:8502
```

---

## Problèmes Courants Windows

### Problème 1 : WSL2 non activé
**Symptôme** : Docker Desktop dit "WSL 2 backend not installed"

**Solution** :
```powershell
# PowerShell Admin
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
# Redémarrer
wsl --set-default-version 2
```

### Problème 2 : Port déjà utilisé
**Symptôme** : "port is already allocated"

**Solution** :
```powershell
# PowerShell : Trouver le processus
netstat -ano | findstr :8000
# Tuer le processus (remplacer PID)
taskkill /PID 1234 /F
```

### Problème 3 : Permissions Docker
**Symptôme** : "permission denied"

**Solution** :
```bash
# Dans WSL
sudo usermod -aG docker $USER
# Déconnecter/reconnecter WSL
wsl --shutdown
wsl
```

### Problème 4 : Fichiers line endings
**Symptôme** : Scripts shell ne fonctionnent pas (`\r\n` vs `\n`)

**Solution** :
```bash
# Dans WSL
dos2unix docker-manage-v2.sh
# Ou
sed -i 's/\r$//' docker-manage-v2.sh
chmod +x docker-manage-v2.sh
```

---

## Performance Windows

### Optimisations Docker Desktop

**Settings → Resources** :
- CPUs : Au moins 4
- Memory : Au moins 8 GB (recommandé 16 GB)
- Swap : 2 GB
- Disk image size : 100 GB+

### Emplacements des fichiers

**Meilleure performance** :
```
✅ Bon : Fichiers dans WSL (~/projet)
❌ Moyen : Fichiers dans /mnt/c (Windows C:)
```

**Raison** : L'accès aux fichiers Windows depuis WSL est plus lent que les fichiers natifs WSL.

---

## Commandes Utiles Windows

### PowerShell

```powershell
# Informations système
systeminfo | findstr /C:"OS Name"
wsl --status

# Docker
docker ps -a
docker images
docker system df

# Réseau
ipconfig
netstat -an | findstr LISTEN
```

### WSL

```bash
# Infos WSL
cat /etc/os-release
uname -a

# Docker dans WSL
docker compose ps
docker logs aristote-api-v2

# Espace disque
df -h
```

---

## Accès depuis d'autres Machines

### Trouver votre IP Windows
```powershell
ipconfig
# Noter l'adresse IPv4 (ex: 192.168.1.100)
```

### Configurer le firewall
```powershell
# PowerShell Admin : Autoriser les ports
New-NetFirewallRule -DisplayName "Aristote API" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "Aristote Frontend" -Direction Inbound -LocalPort 8502 -Protocol TCP -Action Allow
```

### Accès depuis le réseau local
```
http://192.168.1.100:8000/docs
http://192.168.1.100:8502
```

---

## Recommandation Finale

**Pour développement** : Option A (WSL2) → Meilleure expérience

**Pour démo rapide** : Option B (PowerShell + Docker Compose manuel)

**Pour scripts Bash** : Option A (WSL2) ou C (Git Bash)

---

## Checklist de Test Windows

- [ ] WSL2 installé et configuré
- [ ] Docker Desktop installé et démarré
- [ ] Projet cloné (WSL ou Windows)
- [ ] Variables d'environnement configurées (.env)
- [ ] `docker compose up` réussit
- [ ] API accessible (http://localhost:8000/health)
- [ ] Frontend accessible (http://localhost:8502)
- [ ] Upload de document fonctionne
- [ ] Requête RAG fonctionne

---

## Support

**Documentation Docker** :
- https://docs.docker.com/desktop/windows/wsl/
- https://learn.microsoft.com/fr-fr/windows/wsl/

**Si problème** :
1. Vérifier logs : `docker compose -f docker-compose-v2.yml logs`
2. Redémarrer Docker Desktop
3. Redémarrer WSL : `wsl --shutdown` puis `wsl`
4. Vérifier `TEST_V2_STATUS.md` pour l'état actuel

---

**Date de ce guide** : 2026-01-12
**Testé sur** : Windows 11 22H2, Docker Desktop 4.x, WSL2 Ubuntu 24.04
