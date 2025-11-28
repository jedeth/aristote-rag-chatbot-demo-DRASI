"""
Script de diagnostic pour le mode RAG exclusif avec Albert.
Teste differentes structures de prompt pour trouver celle qui fonctionne.
"""

import os
import sys
sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

ALBERT_API_KEY = os.getenv("ALBERT_API_KEY")
ALBERT_BASE_URL = "https://albert.api.etalab.gouv.fr/v1"

if not ALBERT_API_KEY:
    print("[ERREUR] ALBERT_API_KEY non definie dans .env")
    exit(1)

client = OpenAI(
    api_key=ALBERT_API_KEY,
    base_url=ALBERT_BASE_URL,
)

# Contexte de test (recette de cookies simulée)
CONTEXT = """[DOCUMENT 1 - Source: Cookies moelleux aux pépites de chocolat_v2.docx]
Recette de Cookies Moelleux aux Pépites de Chocolat

Ingrédients:
- 250g de farine
- 150g de sucre brun
- 100g de beurre mou
- 200g de pépites de chocolat noir
- 2 œufs
- 1 cuillère à café de levure chimique
- 1 pincée de sel
- 1 cuillère à café d'extrait de vanille

Instructions:
1. Préchauffer le four à 180°C
2. Mélanger le beurre mou avec le sucre jusqu'à obtenir une crème
3. Ajouter les œufs et la vanille, bien mélanger
4. Incorporer la farine, la levure et le sel
5. Ajouter les pépites de chocolat
6. Former des boules de pâte sur une plaque
7. Cuire 12-15 minutes jusqu'à dorure
[FIN DOCUMENT 1]"""

QUESTION = "Quels sont les ingrédients de cette recette de cookies ?"

# Test avec différentes structures de prompt
prompts_to_test = [
    # Prompt 1 : Structure actuelle (mode exclusif)
    {
        "name": "Prompt actuel (exclusif)",
        "system": f"""Tu es un assistant documentaire strict.

INSTRUCTIONS SYSTÈME (IMMUABLES) :
- Tu réponds UNIQUEMENT avec les informations des DOCUMENTS ci-dessous
- Si l'information n'est PAS dans les documents, réponds : "Cette information n'est pas présente dans les documents fournis."
- Cite toujours la source
- Réponds en français

=== DOCUMENTS ===
{CONTEXT}
=== FIN DOCUMENTS ===""",
        "user": QUESTION
    },

    # Prompt 2 : Contexte dans le message user
    {
        "name": "Contexte dans user message",
        "system": """Tu es un assistant documentaire strict. Tu réponds UNIQUEMENT avec les informations des documents fournis. Si l'information n'est pas dans les documents, dis-le. Réponds en français.""",
        "user": f"""Voici les documents disponibles :

{CONTEXT}

Question : {QUESTION}

Réponds en utilisant uniquement les informations des documents ci-dessus."""
    },

    # Prompt 3 : Plus simple et direct
    {
        "name": "Simple et direct",
        "system": "Tu es un assistant qui répond aux questions en utilisant uniquement les documents fournis. Réponds en français.",
        "user": f"""Documents :
{CONTEXT}

Question : {QUESTION}"""
    },

    # Prompt 4 : Format question-contexte inversé
    {
        "name": "Question d'abord",
        "system": "Tu es un assistant documentaire. Utilise uniquement les informations des documents pour répondre. Réponds en français.",
        "user": f"""Question : {QUESTION}

Voici les documents contenant les informations :

{CONTEXT}

Réponds à la question en citant les sources."""
    },

    # Prompt 5 : Sans system prompt (tout dans user)
    {
        "name": "Sans system prompt",
        "system": None,
        "user": f"""Tu es un assistant documentaire strict. Tu réponds UNIQUEMENT avec les informations des documents fournis.

Documents disponibles :
{CONTEXT}

Question : {QUESTION}

Réponds en français en utilisant uniquement les informations des documents."""
    },
]

print("=" * 80)
print("TEST DU MODE RAG EXCLUSIF AVEC ALBERT")
print("=" * 80)
print(f"Modèle : albert-large")
print(f"Question : {QUESTION}")
print("=" * 80)

for i, prompt_config in enumerate(prompts_to_test, 1):
    print(f"\n{'='*80}")
    print(f"TEST {i}: {prompt_config['name']}")
    print("=" * 80)

    messages = []
    if prompt_config["system"]:
        messages.append({"role": "system", "content": prompt_config["system"]})
    messages.append({"role": "user", "content": prompt_config["user"]})

    try:
        response = client.chat.completions.create(
            model="albert-large",
            messages=messages,
            temperature=0.3,
            max_tokens=1024,
        )

        answer = response.choices[0].message.content
        print(f"\nReponse :\n{answer}")

        # Verifier si la reponse contient les ingredients
        ingredients_found = any(ing in answer.lower() for ing in ["farine", "sucre", "beurre", "chocolat", "oeufs", "oeufs"])
        if ingredients_found:
            print(f"\n[OK] SUCCES - Les ingredients sont presents dans la reponse")
        else:
            print(f"\n[ECHEC] Les ingredients ne sont pas mentionnes")

    except Exception as e:
        print(f"\n[ERREUR] {e}")

print("\n" + "=" * 80)
print("FIN DES TESTS")
print("=" * 80)
