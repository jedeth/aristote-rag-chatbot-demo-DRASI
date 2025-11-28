"""
Script de test pour vérifier l'accès à l'API Albert.
Usage: python test_albert_api.py
"""

import os
from dotenv import load_dotenv

load_dotenv()

def test_albert_embeddings():
    """Teste l'API d'embeddings Albert."""
    print("=" * 60)
    print("Test de l'API Albert Embeddings")
    print("=" * 60)

    api_key = os.getenv("ALBERT_API_KEY")

    if not api_key:
        print("❌ ALBERT_API_KEY non définie dans .env")
        print("   Ajoutez: ALBERT_API_KEY=votre_cle_ici")
        return False

    print(f"✅ Clé API trouvée: {api_key[:10]}...{api_key[-4:] if len(api_key) > 14 else ''}")

    try:
        from openai import OpenAI

        # URL correcte de l'API Albert
        base_url = os.getenv("ALBERT_API_BASE", "https://albert.api.etalab.gouv.fr/v1")
        print(f"   URL API: {base_url}")

        client = OpenAI(
            api_key=api_key,
            base_url=base_url,
        )

        print("\n📡 Test de connexion à l'API...")

        # Test embeddings
        response = client.embeddings.create(
            model="embeddings-small",
            input="Ceci est un test d'embedding.",
        )

        embedding = response.data[0].embedding
        print(f"✅ Embeddings OK!")
        print(f"   Dimension: {len(embedding)}")
        print(f"   Premiers éléments: {embedding[:5]}")

        return True

    except Exception as e:
        print(f"\n❌ Erreur Embeddings: {type(e).__name__}")
        print(f"   Message: {e}")

        if "401" in str(e) or "Unauthorized" in str(e):
            print("\n💡 La clé API semble invalide ou expirée.")
        elif "404" in str(e):
            print("\n💡 Le modèle 'embeddings-small' n'existe peut-être pas.")
        elif "connection" in str(e).lower():
            print("\n💡 Problème de connexion réseau.")

        return False


def test_albert_llm():
    """Teste l'API LLM Albert (chat completion)."""
    print("\n" + "=" * 60)
    print("Test de l'API Albert LLM (Chat)")
    print("=" * 60)

    api_key = os.getenv("ALBERT_API_KEY")
    if not api_key:
        print("❌ ALBERT_API_KEY non définie")
        return False

    try:
        from openai import OpenAI

        # URL correcte de l'API Albert
        base_url = os.getenv("ALBERT_API_BASE", "https://albert.api.etalab.gouv.fr/v1")
        print(f"   URL API: {base_url}")

        client = OpenAI(
            api_key=api_key,
            base_url=base_url,
        )

        # Tester les différents modèles LLM
        models_to_test = ["albert-small", "albert-large", "albert-code"]

        for model_name in models_to_test:
            print(f"\n📡 Test du modèle: {model_name}")
            try:
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "user", "content": "Réponds juste 'OK' si tu fonctionnes."}
                    ],
                    max_tokens=10,
                )
                reply = response.choices[0].message.content
                print(f"   ✅ {model_name}: {reply[:50]}")
            except Exception as e:
                print(f"   ❌ {model_name}: {type(e).__name__} - {str(e)[:100]}")

        return True

    except Exception as e:
        print(f"\n❌ Erreur LLM: {type(e).__name__}")
        print(f"   Message: {e}")
        return False


def test_albert_models():
    """Liste les modèles disponibles sur Albert."""
    print("\n" + "=" * 60)
    print("Liste des modèles Albert disponibles")
    print("=" * 60)

    api_key = os.getenv("ALBERT_API_KEY")
    if not api_key:
        return []

    try:
        from openai import OpenAI

        # URL correcte de l'API Albert
        base_url = os.getenv("ALBERT_API_BASE", "https://albert.api.etalab.gouv.fr/v1")
        print(f"   URL API: {base_url}")

        client = OpenAI(
            api_key=api_key,
            base_url=base_url,
        )

        models = client.models.list()

        print(f"\n📋 {len(models.data)} modèle(s) disponible(s):\n")
        model_ids = []
        for model in models.data:
            print(f"   - {model.id}")
            model_ids.append(model.id)

        return model_ids

    except Exception as e:
        print(f"❌ Erreur liste modèles: {type(e).__name__}")
        print(f"   Message: {e}")
        return []


if __name__ == "__main__":
    print("\n🔧 Test complet de l'API Albert\n")

    # Test 1: Liste des modèles
    available_models = test_albert_models()

    # Test 2: Embeddings
    embeddings_ok = test_albert_embeddings()

    # Test 3: LLM Chat
    llm_ok = test_albert_llm()

    # Résumé
    print("\n" + "=" * 60)
    print("RÉSUMÉ")
    print("=" * 60)
    print(f"Modèles disponibles: {len(available_models)}")
    print(f"Embeddings: {'✅ OK' if embeddings_ok else '❌ ERREUR'}")
    print(f"LLM Chat: {'✅ OK' if llm_ok else '❌ ERREUR'}")

    if available_models:
        print(f"\n💡 Modèles détectés: {', '.join(available_models)}")

    print("=" * 60)
