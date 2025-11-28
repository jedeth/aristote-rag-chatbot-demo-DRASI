"""
Test du RAG avec Albert - debug du probleme de reponse
"""

import json
import sys
sys.stdout.reconfigure(encoding='utf-8')

from openai import OpenAI

# Charger config
import os
config_path = os.path.join(os.path.dirname(__file__), "dev_config.json")
with open(config_path, "r", encoding="utf-8") as f:
    config = json.load(f)

ALBERT_API_KEY = config["api_keys"]["albert_api_key"]

client = OpenAI(
    api_key=ALBERT_API_KEY,
    base_url="https://albert.api.etalab.gouv.fr/v1",
)

# Simuler un contexte RAG simple
CONTEXT = """[DOCUMENT 1 - Source: RGPD.pdf]
Article 26 - Responsables conjoints du traitement

1. Lorsque deux responsables du traitement ou plus determinent conjointement
les finalites et les moyens du traitement, ils sont les responsables conjoints
du traitement. Les responsables conjoints du traitement definissent de maniere
transparente leurs obligations respectives aux fins d'assurer le respect des
exigences du present reglement.

La protection des droits et libertes des personnes concernees, de meme que la
responsabilite des responsables du traitement et des sous-traitants, y compris
dans le cadre de la surveillance exercee par les autorites de controle et des
mesures prises par celles-ci, exige une repartition claire des responsabilites
au titre du present reglement, y compris lorsque le responsable du traitement
determine les finalites et les moyens du traitement conjointement avec d'autres
responsables du traitement.
[FIN DOCUMENT 1]

[DOCUMENT 2 - Source: RGPD.pdf]
Le present reglement compte 99 articles et 173 considerants. Il est entre en
vigueur le 25 mai 2018.
[FIN DOCUMENT 2]"""

QUESTION = "Quel article parle de la repartition des responsabilites entre responsables conjoints ?"

# Test 1: Prompt simple
print("=" * 60)
print("TEST 1: Prompt simple")
print("=" * 60)

messages = [
    {"role": "system", "content": "Tu es un assistant qui repond aux questions en utilisant les documents fournis. Reponds en francais."},
    {"role": "user", "content": f"""Voici des extraits de documents :

{CONTEXT}

Question : {QUESTION}

Reponds a la question en te basant sur les documents ci-dessus."""}
]

response = client.chat.completions.create(
    model="albert-large",
    messages=messages,
    temperature=0.3,
    max_tokens=500,
)

print(f"\nReponse: {response.choices[0].message.content}")

# Test 2: Sans system prompt
print("\n" + "=" * 60)
print("TEST 2: Sans system prompt")
print("=" * 60)

messages2 = [
    {"role": "user", "content": f"""Voici des extraits de documents :

{CONTEXT}

Question : {QUESTION}

Reponds a la question."""}
]

response2 = client.chat.completions.create(
    model="albert-large",
    messages=messages2,
    temperature=0.3,
    max_tokens=500,
)

print(f"\nReponse: {response2.choices[0].message.content}")

# Test 3: Question directe apres contexte
print("\n" + "=" * 60)
print("TEST 3: Format question directe")
print("=" * 60)

messages3 = [
    {"role": "user", "content": f"""{CONTEXT}

{QUESTION}"""}
]

response3 = client.chat.completions.create(
    model="albert-large",
    messages=messages3,
    temperature=0.3,
    max_tokens=500,
)

print(f"\nReponse: {response3.choices[0].message.content}")

# Test 4: Avec albert-small
print("\n" + "=" * 60)
print("TEST 4: Avec albert-small")
print("=" * 60)

response4 = client.chat.completions.create(
    model="albert-small",
    messages=messages,
    temperature=0.3,
    max_tokens=500,
)

print(f"\nReponse: {response4.choices[0].message.content}")

print("\n" + "=" * 60)
print("FIN DES TESTS")
print("=" * 60)
