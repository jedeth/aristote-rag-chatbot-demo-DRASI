"""
Frontend Streamlit V2 - Architecture Hexagonale
Client pur qui appelle l'API FastAPI
"""

import streamlit as st
import requests
from typing import List, Dict

# Configuration de la page
st.set_page_config(
    page_title="Aristote RAG - V2 Hexagonale",
    page_icon="🤖",
    layout="wide"
)

# URL de l'API (configurable via variable d'environnement)
import os
API_URL = os.getenv("API_URL", "http://localhost:8000")


def call_api_health() -> Dict:
    """Appel API : Health check."""
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"status": "error", "detail": str(e)}


def call_api_query(query: str, n_results: int = 5, temperature: float = 0.7) -> Dict:
    """Appel API : Requête RAG."""
    try:
        payload = {
            "query": query,
            "n_results": n_results,
            "temperature": temperature,
            "max_tokens": 1000
        }
        response = requests.post(
            f"{API_URL}/query",
            json=payload,
            timeout=60
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        return {"error": f"Erreur API ({e.response.status_code})", "detail": e.response.text}
    except Exception as e:
        return {"error": "Erreur de connexion", "detail": str(e)}


def call_api_documents() -> Dict:
    """Appel API : Liste des documents."""
    try:
        response = requests.get(f"{API_URL}/documents", timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}


# Interface utilisateur
st.title("🤖 Aristote RAG - Architecture Hexagonale V2")
st.caption("Frontend Streamlit découplé - Appelle l'API FastAPI")

# Sidebar - Configuration
with st.sidebar:
    st.header("⚙️ Configuration")

    # Health check de l'API
    with st.expander("🏥 Statut de l'API", expanded=True):
        health = call_api_health()
        if health.get("status") == "healthy":
            st.success(f"✅ API opérationnelle")
            st.caption(f"Version: {health.get('version', 'N/A')}")
            st.caption(f"Architecture: {health.get('architecture', 'N/A')}")
        else:
            st.error(f"❌ API indisponible")
            st.caption(f"URL: {API_URL}")
            if "detail" in health:
                st.caption(f"Erreur: {health['detail']}")

    st.divider()

    # Paramètres RAG
    st.subheader("🎛️ Paramètres RAG")
    n_results = st.slider("Nombre de sources", 1, 10, 5)
    temperature = st.slider("Température LLM", 0.0, 1.0, 0.7, 0.1)

    st.divider()

    # Documents indexés
    st.subheader("📚 Documents indexés")
    if st.button("🔄 Actualiser"):
        st.rerun()

    docs_data = call_api_documents()
    if "error" in docs_data:
        st.error(f"Erreur: {docs_data['error']}")
    else:
        st.metric("Documents", docs_data.get("total_documents", 0))
        st.metric("Chunks", docs_data.get("total_chunks", 0))

        if docs_data.get("documents"):
            with st.expander("📄 Liste des documents"):
                for doc in docs_data["documents"]:
                    st.caption(f"• {doc}")

# Zone principale - Chat
st.header("💬 Chat RAG")

# Initialisation de l'historique
if "messages_v2" not in st.session_state:
    st.session_state.messages_v2 = []

# Affichage de l'historique
for message in st.session_state.messages_v2:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant" and "sources" in message:
            with st.expander("📚 Sources utilisées"):
                for source in message["sources"]:
                    st.caption(
                        f"**{source['filename']}** (score: {source['score']:.2f})"
                    )
                    st.text(source['text'][:200] + "...")

# Zone de saisie
if prompt := st.chat_input("Posez votre question..."):
    # Afficher le message utilisateur
    with st.chat_message("user"):
        st.markdown(prompt)

    st.session_state.messages_v2.append({"role": "user", "content": prompt})

    # Appeler l'API
    with st.chat_message("assistant"):
        with st.spinner("Interrogation de l'API..."):
            result = call_api_query(prompt, n_results, temperature)

        if "error" in result:
            st.error(f"❌ {result['error']}")
            if "detail" in result:
                st.caption(f"Détail: {result['detail']}")
            response_text = f"Erreur: {result['error']}"
        else:
            response_text = result.get("response_text", "Aucune réponse")
            st.markdown(response_text)

            # Afficher les sources
            sources = result.get("sources", [])
            if sources:
                with st.expander(f"📚 {len(sources)} source(s) utilisée(s)"):
                    for source in sources:
                        st.caption(
                            f"**{source['filename']}** (score: {source['score']:.2f})"
                        )
                        st.text(source['text'][:200] + "...")

            # Métriques
            col1, col2 = st.columns(2)
            with col1:
                st.caption(f"🤖 Modèle: {result.get('model_name', 'N/A')}")
            with col2:
                st.caption(f"📊 {len(sources)} source(s)")

        # Sauvegarder dans l'historique
        st.session_state.messages_v2.append({
            "role": "assistant",
            "content": response_text,
            "sources": result.get("sources", []) if "error" not in result else []
        })

# Footer
st.divider()
st.caption(
    "🏗️ Architecture Hexagonale V2 | "
    f"API: {API_URL} | "
    "Frontend Streamlit découplé"
)
