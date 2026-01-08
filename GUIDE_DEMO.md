# Guide de Démo - Applications Streamlit
## Date : 9 janvier 2026

---

## 🖥️ Configuration des Serveurs

### Serveur 1 : 10.22.200.36 (ia-raidf2.in.ac-paris.fr)
- **Application** : RAG Chatbot (Aristote)
- **Port serveur** : 8501
- **Chemin** : `/home/iarag/ChatBot_multiProvider/aristote-rag-chatbot-demo-DRASI/`
- **Statut** : ✅ ACTIF

### Serveur 2 : 10.22.200.35
- **Application 1** : [À compléter]
- **Port serveur** : 8502 (recommandé)
- **Application 2** : [À compléter]
- **Port serveur** : 8503 (recommandé)

---

## 🔐 ÉTAPE 0 : Connexion VPN (OBLIGATOIRE)

### ⚠️ CRITIQUE : Sans VPN, rien ne fonctionne !

Les serveurs 10.22.200.36 et 10.22.200.35 sont sur le réseau interne du rectorat.

**AVANT TOUTE CHOSE** :
1. Lancez le **client VPN Cisco** du rectorat
2. Connectez-vous avec vos identifiants
3. Attendez que le VPN soit **connecté** (voyant vert)
4. SEULEMENT APRÈS, passez aux tunnels SSH

### ⚠️ En cas de déconnexion VPN (CRITIQUE) :

**Symptômes** :
- Page blanche dans Chrome
- "Connection refused" ou pas de réponse
- Les tunnels SSH semblent ouverts mais ne fonctionnent plus

**Ce qui se passe** :
- Le VPN se déconnecte (timeout sécurité après inactivité)
- Les tunnels SSH restent "ouverts" mais sont MORTS
- Chrome essaie d'accéder à localhost:8501 → tunnel mort → page blanche

**✅ SOLUTION (ordre strict)** :
1. **FERMER tous les terminaux SSH** (les anciens tunnels sont morts !)
2. Reconnecter le VPN Cisco
3. Ouvrir 3 NOUVEAUX terminaux
4. Recréer les 3 tunnels SSH
5. Rafraîchir Chrome (Ctrl+Shift+R)

**Si ça ne marche toujours pas** : Redémarrer le PC (repart à zéro)

---

## 🔌 Tunnels SSH depuis votre PC

### ⚠️ PRÉREQUIS : VPN Cisco connecté (voir ci-dessus)

### Commandes à exécuter AVANT la démo :

```bash
# Terminal 1 : RAG Chatbot (Serveur 1)
ssh -L 8501:localhost:8501 iarag@10.22.200.36

# Terminal 2 : Application 1 (Serveur 2)
ssh -L 8502:localhost:8502 iarag@10.22.200.35

# Terminal 3 : Application 2 (Serveur 2)
ssh -L 8503:localhost:8503 iarag@10.22.200.35
```

**IMPORTANT** :
- VPN doit être actif en permanence
- Gardez ces 3 terminaux ouverts pendant toute la démo !

---

## 🌐 URLs pour le Navigateur

### RAG Chatbot Aristote
- **URL** : http://localhost:8501
- **Serveur** : 10.22.200.36
- **Description** : Chatbot avec RAG, multi-provider (Aristote/Albert)

### Application 1
- **URL** : http://localhost:8502
- **Serveur** : 10.22.200.35
- **Description** : [À compléter]

### Application 2
- **URL** : http://localhost:8503
- **Serveur** : 10.22.200.35
- **Description** : [À compléter]

---

## ✅ Checklist Avant Démo

### Veille de la démo (ce soir)
- [ ] Vérifier que les 3 applications tournent sur leurs serveurs respectifs
- [ ] **Tester la connexion VPN Cisco** (identifiants OK)
- [ ] Tester les tunnels SSH depuis votre PC (avec VPN actif)
- [ ] Vider le cache du navigateur (Ctrl+Shift+Suppr)
- [ ] Ouvrir 3 onglets avec les 3 URLs
- [ ] Préparer les documents de test pour le RAG

### Le matin de la démo (30 minutes avant)
- [ ] **ÉTAPE 1 : Connecter le VPN Cisco** (attendre voyant vert)
- [ ] ÉTAPE 2 : Relancer les applications si les serveurs ont redémarré
- [ ] ÉTAPE 3 : Établir les 3 tunnels SSH (un terminal par tunnel)
- [ ] ÉTAPE 4 : Ouvrir Chrome et tester rapidement chaque application
- [ ] ÉTAPE 5 : Fermer tous les autres onglets/applications inutiles
- [ ] **Vérifier que l'icône VPN reste verte pendant toute la démo**

---

## 🆘 Résolution de Problèmes

### ⚠️ Problème : "Connection refused" ou "ERR_CONNECTION_REFUSED"

**Cause la plus fréquente** : VPN Cisco déconnecté
**Solution** :
1. Vérifier l'icône VPN (doit être verte)
2. Reconnecter le VPN si nécessaire
3. Relancer les 3 tunnels SSH
4. Rafraîchir les pages (Ctrl+R)

---

### Problème : "Connection timed out" lors du tunnel SSH

**Cause** : VPN non connecté ou mal configuré
**Solution** :
```bash
# 1. Vérifier que le VPN est actif
# 2. Tester la connectivité
ping 10.22.200.36
# Si pas de réponse → VPN déconnecté
```

---

### Problème : Page blanche sur http://localhost:850X

**Solution 1** : Vérifier le tunnel SSH
```bash
# Sur votre PC, vérifier les tunnels actifs
netstat -an | findstr "850"
```

**Solution 2** : Vérifier l'application côté serveur
```bash
# SSH vers le serveur concerné (VPN doit être actif)
lsof -i :850X
# Si rien, relancer l'application
```

**Solution 3** : Cache navigateur
- Ctrl+Shift+R (rechargement forcé)
- Ou mode navigation privée (Ctrl+Shift+N)

### Problème : Mauvaise application qui s'affiche

**Cause** : Ports qui se mélangent
**Solution** :
1. Fermer TOUS les tunnels SSH
2. Vider le cache navigateur
3. Relancer les tunnels UN PAR UN
4. Tester chaque URL séparément

---

## 📋 Commandes Utiles

### Sur les serveurs (vérifier qu'une app tourne)
```bash
# Voir le processus Streamlit
ps aux | grep streamlit

# Voir quel port est utilisé
lsof -i :8501
lsof -i :8502
lsof -i :8503

# Relancer une application (exemple port 8501)
cd /chemin/vers/app
source venv/bin/activate
streamlit run app.py --server.port 8501 --server.address 0.0.0.0 > streamlit.log 2>&1 &
```

### Sur votre PC (vérifier les tunnels)
```bash
# Windows (PowerShell)
netstat -an | findstr "850"

# Linux/Mac
netstat -an | grep 850

# Voir les connexions SSH actives
ps aux | grep ssh
```

---

## 💡 Conseils pour la Démo

1. **Anticipation** : Testez tout 30 minutes avant
2. **Plan B** : Ayez les URLs des serveurs en direct (sans tunnel) au cas où
3. **Documentation** : Imprimez ce guide
4. **Navigateur** : Utilisez des onglets épinglés pour ne pas les perdre
5. **Présentation** : Commencez par l'app la plus stable

---

## 📞 Contact Urgence

Si problème technique pendant la démo :
- Serveur 10.22.200.36 : Application RAG Chatbot (la plus importante)
- En cas de crash : relancer avec `streamlit run app.py`

---

**Dernière mise à jour** : 8 janvier 2026 15:50
**Testé par** : Claude Code Assistant
**Statut** : ✅ Serveur 10.22.200.36 opérationnel sur port 8501
**Accès** : ⚠️ Nécessite VPN Cisco du rectorat actif
