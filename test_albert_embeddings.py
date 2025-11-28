"""
Test de l'API embeddings Albert pour diagnostiquer les erreurs.
"""

import os
import sys
import json
import requests

sys.stdout.reconfigure(encoding='utf-8')

# Charger la config dev
config_file = os.path.join(os.path.dirname(__file__), "dev_config.json")
with open(config_file, "r", encoding="utf-8") as f:
    config = json.load(f)

ALBERT_API_KEY = config["api_keys"]["albert_api_key"]
ALBERT_BASE_URL = "https://albert.api.etalab.gouv.fr/v1"

print("=" * 60)
print("TEST API EMBEDDINGS ALBERT")
print("=" * 60)

# Test 1: Lister les modeles disponibles
print("\n1. Liste des modeles disponibles:")
try:
    response = requests.get(
        f"{ALBERT_BASE_URL}/models",
        headers={"Authorization": f"Bearer {ALBERT_API_KEY}"},
        timeout=30,
    )
    if response.status_code == 200:
        models = response.json()
        for model in models.get("data", []):
            print(f"   - {model.get('id', 'N/A')}")
    else:
        print(f"   Erreur {response.status_code}: {response.text}")
except Exception as e:
    print(f"   Erreur: {e}")

# Test 2: Appel embeddings avec model embeddings-small
print("\n2. Test embeddings avec model='embeddings-small':")
try:
    response = requests.post(
        f"{ALBERT_BASE_URL}/embeddings",
        headers={
            "Authorization": f"Bearer {ALBERT_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": "embeddings-small",
            "input": "Ceci est un test",
        },
        timeout=60,
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        embedding = data["data"][0]["embedding"]
        print(f"   [OK] Embedding dimension: {len(embedding)}")
    else:
        print(f"   Erreur: {response.text}")
except Exception as e:
    print(f"   Erreur: {e}")

# Test 3: Appel embeddings sans model specifie
print("\n3. Test embeddings sans model specifie:")
try:
    response = requests.post(
        f"{ALBERT_BASE_URL}/embeddings",
        headers={
            "Authorization": f"Bearer {ALBERT_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "input": "Ceci est un test",
        },
        timeout=60,
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        embedding = data["data"][0]["embedding"]
        print(f"   [OK] Embedding dimension: {len(embedding)}")
        print(f"   Model utilise: {data.get('model', 'N/A')}")
    else:
        print(f"   Erreur: {response.text}")
except Exception as e:
    print(f"   Erreur: {e}")

# Test 4: Avec encoding_format=float
print("\n4. Test avec encoding_format='float':")
try:
    response = requests.post(
        f"{ALBERT_BASE_URL}/embeddings",
        headers={
            "Authorization": f"Bearer {ALBERT_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": "embeddings-small",
            "input": "Ceci est un test",
            "encoding_format": "float",
        },
        timeout=60,
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        embedding = data["data"][0]["embedding"]
        print(f"   [OK] Embedding dimension: {len(embedding)}")
    else:
        print(f"   Erreur: {response.text}")
except Exception as e:
    print(f"   Erreur: {e}")

# Test 5: Liste de textes
print("\n5. Test avec liste de textes:")
try:
    response = requests.post(
        f"{ALBERT_BASE_URL}/embeddings",
        headers={
            "Authorization": f"Bearer {ALBERT_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": "embeddings-small",
            "input": ["Texte 1", "Texte 2", "Texte 3"],
        },
        timeout=60,
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   [OK] {len(data['data'])} embeddings retournes")
        for i, emb in enumerate(data["data"]):
            print(f"       - Index {emb['index']}: dim={len(emb['embedding'])}")
    else:
        print(f"   Erreur: {response.text}")
except Exception as e:
    print(f"   Erreur: {e}")

print("\n" + "=" * 60)
print("FIN DES TESTS")
print("=" * 60)
