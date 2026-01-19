# Test V2 - État Actuel

**Date** : 2026-01-12
**Status** : En cours de correction

---

## Ce Qui A Été Fait

### 1. Lancement V2 ✅
- Services V2 démarrés (API port 8000, Frontend port 8502)
- Health check OK : API répond correctement

### 2. Tests d'Upload  📝
-  Tenté upload fichier TXT → Erreur : format non supporté
- Problème identifié : Docker cache pas invalidé, ancien code dans le container
- Créé fichier DOCX de test → Upload réussi mais erreur embeddings

### 3. Bugs Identifiés et Corrigés

#### Bug 1: Support TXT absent dans container ❌ → En correction
**Cause** : Cache Docker, code source pas mis à jour dans le container
**Solution** : Rebuild sans cache en cours

#### Bug 2: Erreur Albert Embeddings ✅ → Corrigé
**Symptôme** : `Input should be 'float'` mais reçoit `'base64'`
**Cause** : SDK OpenAI envoie `encoding_format="base64"` par défaut mais Albert attend `"float"`
**Solution** : Ajouté `encoding_format="float"` dans `albert_embedding_adapter.py` ligne 66 et 106

### 4. État du Build
- Build Docker `--no-cache` lancé : en cours
- Téléchargement des dépendances : ~3-4 GB (PyTorch, CUDA, etc.)
- Durée estimée : 10-15 minutes

---

## Prochaines Étapes

### Immédiat (après build)
1. Rebuilder l'image avec les corrections
2. Redémarrer les services
3. Tester upload DOCX avec embeddings Albert
4. Tester requête RAG complète
5. Tester frontend Streamlit V2

### Test Windows 11
- Documenter la procédure Docker sur Windows
- Vérifier compatibilité WSL2 vs Docker Desktop
- Tester le workflow complet

---

## Commandes Rapides

### Vérifier l'état du build
```bash
ps aux | grep "docker" | grep "build"
```

### Une fois le build terminé
```bash
# Redémarrer la stack
./docker-manage-v2.sh restart

# Tester l'API
curl http://localhost:8000/health

# Upload test
curl -X POST http://localhost:8000/documents/upload \
  -F "file=@/tmp/test_v2.docx"
```

### Logs en temps réel
```bash
docker logs -f aristote-api-v2
```

---

## Bugs Restants

### Known Issues
1. ⏳ Ollama pas disponible (normal, pas installé dans container)
   - Fallback vers Albert : ✅ fonctionne
2. ✅ Albert embeddings corrigé
3. ⏳ Support TXT : rebuild en cours

### À Vérifier
- Frontend V2 (port 8502)
- Requête RAG end-to-end
- Multi-providers (Aristote vs Albert pour LLM)

---

## Notes Techniques

### Architecture Testée
- Domain Layer : ✅
- Application Layer (Use Cases) : ✅
- Infrastructure (Adapters) : ✅ (avec corrections)
- API (FastAPI) : ✅

### Providers Testés
- **Embeddings** : Ollama (indisponible) → Albert (corrigé) ✅
- **LLM** : Aristote (à tester), Albert (à tester)
- **Vector Store** : ChromaDB ✅

---

## Résumé

**État** : V2 architecture hexagonale opérationnelle avec corrections en cours

**Succès** :
- ✅ Services démarrent correctement
- ✅ Health check OK
- ✅ Parser documents fonctionne
- ✅ Bug embeddings identifié et corrigé

**En cours** :
- ⏳ Rebuild Docker pour intégrer corrections
- ⏳ Tests end-to-end

**Temps estimé avant tests complets** : 10-15 minutes (build en cours)

---

**Prochaine session** : Terminer tests V2 puis tester sur Windows 11
