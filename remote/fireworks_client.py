# remote/fireworks_client.py

import os
import requests
from dotenv import load_dotenv

# Charge les variables du fichier .env dès que ce fichier est importé
load_dotenv()

def repondre_fireworks(question: str, modele: str) -> str:
    """
    Appelle Fireworks AI avec le modèle spécifié pour les questions complexes.
    Utilise les variables d'environnement FIREWORKS_API_KEY et FIREWORKS_BASE_URL.
    """
    
    api_key = os.environ.get("FIREWORKS_API_KEY")
    base_url = os.environ.get("FIREWORKS_BASE_URL")
    
    if not api_key or not base_url:
        return "[ERREUR] Clé API ou URL Fireworks non trouvée. Vérifie ton fichier .env"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": modele,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant that answers questions precisely and concisely."},
            {"role": "user", "content": question}
        ],
        "max_tokens": 200
    }
    
    url_complete = f"{base_url}/v1/chat/completions"
    
    try:
        reponse = requests.post(
            url_complete,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        reponse.raise_for_status()
        
        data = reponse.json()
        reponse_texte = data["choices"][0]["message"]["content"].strip()
        
        return reponse_texte
        
    except requests.exceptions.Timeout:
        return "[ERREUR] La requête Fireworks a expiré (30 secondes)"
    except requests.exceptions.RequestException as e:
        detail = ""
        if hasattr(e, 'response') and e.response is not None:
            detail = f" | Détail serveur : {e.response.text}"
        return f"[ERREUR Fireworks] URL appelée : {url_complete} | Problème : {str(e)}{detail}"
    except Exception as e:
        return f"[ERREUR Fireworks] {str(e)}"