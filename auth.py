"""
Module d'authentification pour Aristote RAG Chatbot.

Supporte plusieurs modes :
- none : Pas d'authentification (collection partagée)
- simple : Login/mot de passe basique
- cas : SSO CAS académique (à implémenter)
"""

import hashlib
import secrets
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Tuple
import streamlit as st

import config


# =============================================================================
# GESTION DES UTILISATEURS (mode simple)
# =============================================================================

USERS_FILE = config.DATA_DIR / "users.json"


def _load_users() -> dict:
    """Charge la base d'utilisateurs."""
    if USERS_FILE.exists():
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save_users(users: dict):
    """Sauvegarde la base d'utilisateurs."""
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


def _hash_password(password: str, salt: str = None) -> Tuple[str, str]:
    """Hash un mot de passe avec un sel."""
    if salt is None:
        salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode(),
        salt.encode(),
        100000
    ).hex()
    return hashed, salt


def create_user(username: str, password: str, display_name: str = None) -> bool:
    """Crée un nouvel utilisateur."""
    users = _load_users()
    if username in users:
        return False  # Utilisateur déjà existant

    hashed, salt = _hash_password(password)
    users[username] = {
        "password_hash": hashed,
        "salt": salt,
        "display_name": display_name or username,
        "created_at": datetime.now().isoformat(),
    }
    _save_users(users)
    return True


def verify_user(username: str, password: str) -> bool:
    """Vérifie les credentials d'un utilisateur."""
    users = _load_users()
    if username not in users:
        return False

    user = users[username]
    hashed, _ = _hash_password(password, user["salt"])
    return hashed == user["password_hash"]


def get_user_info(username: str) -> Optional[dict]:
    """Récupère les infos d'un utilisateur."""
    users = _load_users()
    return users.get(username)


# =============================================================================
# GESTION DE SESSION
# =============================================================================

def get_user_id() -> Optional[str]:
    """
    Retourne l'ID de l'utilisateur connecté.

    En mode 'none': retourne None (collection partagée)
    En mode 'simple' ou 'cas': retourne l'ID de l'utilisateur authentifié
    """
    if config.AUTH_MODE == "none":
        return None

    return st.session_state.get("user_id")


def get_user_display_name() -> str:
    """Retourne le nom d'affichage de l'utilisateur."""
    if config.AUTH_MODE == "none":
        return "Invité"

    user_id = get_user_id()
    if user_id:
        user_info = get_user_info(user_id)
        if user_info:
            return user_info.get("display_name", user_id)
    return "Non connecté"


def is_authenticated() -> bool:
    """Vérifie si l'utilisateur est authentifié."""
    if config.AUTH_MODE == "none":
        return True  # Pas d'auth requise

    return get_user_id() is not None


def login(username: str, password: str) -> bool:
    """Connecte un utilisateur."""
    if config.AUTH_MODE == "none":
        return True

    if verify_user(username, password):
        st.session_state.user_id = username
        st.session_state.auth_time = datetime.now().isoformat()
        return True
    return False


def logout():
    """Déconnecte l'utilisateur."""
    if "user_id" in st.session_state:
        del st.session_state.user_id
    if "auth_time" in st.session_state:
        del st.session_state.auth_time


# =============================================================================
# INTERFACE STREAMLIT
# =============================================================================

def render_login_form() -> bool:
    """
    Affiche le formulaire de connexion si nécessaire.

    Returns:
        True si l'utilisateur est authentifié, False sinon
    """
    if config.AUTH_MODE == "none":
        return True

    if is_authenticated():
        return True

    st.title("🔐 Connexion")
    st.caption("Aristote RAG Chatbot - Authentification requise")

    with st.form("login_form"):
        username = st.text_input("Identifiant")
        password = st.text_input("Mot de passe", type="password")
        submitted = st.form_submit_button("Se connecter")

        if submitted:
            if login(username, password):
                st.success(f"Bienvenue {get_user_display_name()} !")
                st.rerun()
            else:
                st.error("Identifiant ou mot de passe incorrect")

    # Option d'inscription si activée
    if config.AUTH_MODE == "simple":
        with st.expander("Créer un compte"):
            with st.form("register_form"):
                new_username = st.text_input("Nouvel identifiant")
                new_password = st.text_input("Nouveau mot de passe", type="password")
                new_password2 = st.text_input("Confirmer le mot de passe", type="password")
                display_name = st.text_input("Nom d'affichage (optionnel)")
                register = st.form_submit_button("Créer le compte")

                if register:
                    if not new_username or not new_password:
                        st.error("Identifiant et mot de passe requis")
                    elif new_password != new_password2:
                        st.error("Les mots de passe ne correspondent pas")
                    elif len(new_password) < 6:
                        st.error("Le mot de passe doit faire au moins 6 caractères")
                    elif create_user(new_username, new_password, display_name):
                        st.success("Compte créé ! Vous pouvez maintenant vous connecter.")
                    else:
                        st.error("Cet identifiant existe déjà")

    return False


def render_user_menu():
    """Affiche le menu utilisateur dans la sidebar."""
    if config.AUTH_MODE == "none":
        return

    if is_authenticated():
        st.sidebar.markdown(f"👤 **{get_user_display_name()}**")
        if st.sidebar.button("🚪 Déconnexion"):
            logout()
            st.rerun()


# =============================================================================
# ISOLATION DES COLLECTIONS CHROMADB
# =============================================================================

def get_collection_name(base_name: str = "documents", embedding_provider: str = "ollama") -> str:
    """
    Génère le nom de collection ChromaDB en fonction de l'utilisateur.

    En mode 'none': collection partagée ({base_name}_{provider})
    En mode authentifié: collection isolée (user_{hash}_{provider})
    """
    user_id = get_user_id()

    if user_id:
        # Collection isolée par utilisateur
        user_hash = hashlib.sha256(user_id.encode()).hexdigest()[:12]
        return f"user_{user_hash}_{embedding_provider}"
    else:
        # Collection partagée
        return f"{base_name}_{embedding_provider}"


def get_user_data_dir() -> Path:
    """
    Retourne le répertoire de données de l'utilisateur.

    En mode 'none': répertoire partagé
    En mode authentifié: répertoire isolé par utilisateur
    """
    user_id = get_user_id()

    if user_id:
        user_hash = hashlib.sha256(user_id.encode()).hexdigest()[:12]
        user_dir = config.DATA_DIR / "users" / user_hash
        user_dir.mkdir(parents=True, exist_ok=True)
        return user_dir
    else:
        return config.DATA_DIR
