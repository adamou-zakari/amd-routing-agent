# remote/fireworks_client.py

import os
import re
import requests
from dotenv import load_dotenv

load_dotenv()

def _nettoyer_reponse(texte: str) -> str:
    """
    Post-traitement : si la réponse contient un bloc de code markdown,
    on extrait uniquement le code (élimine le raisonnement parasite
    et les balises ```).
    """
    blocs = re.findall(r"```(?:python|\w+)?\s*\n(.*?)```", texte, re.DOTALL)
    if blocs:
        return blocs[0].strip()
    return texte.strip()

def repondre_fireworks(question: str, modele: str) -> str:
    """
    Appelle Fireworks AI avec le modèle spécifié.
    """
    
    api_key = os.environ.get("FIREWORKS_API_KEY")
    base_url = os.environ.get("FIREWORKS_BASE_URL")
    
    if not api_key or not base_url:
        return "[ERROR] Missing Fireworks API key or base URL. Check environment variables."
    
    # Normalisation : accepte les URL avec ou sans /v1 à la fin
    # (évite le doublon /v1/v1 qui provoque une erreur 404)
    base_url = base_url.rstrip("/")
    if base_url.endswith("/v1"):
        base_url = base_url[:-3].rstrip("/")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": modele,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an evaluation agent. Always answer in English. "
                    "Give ONLY the final answer, as short as possible. "
                    "Never use markdown, asterisks, bold, bullet points, or headers. "
                    "Never explain your reasoning. Never think out loud. Never restate the question. "
                    "For factual questions: answer with just the fact. "
                    "For math: give only the final number. "
                    "For sentiment classification: answer with one word only (Positive, Negative, Neutral, or Mixed). "
                    "For named entity recognition: list only the entities, separated by commas. "
                    "For code tasks: output only the complete raw code, nothing else. "
                    "For summaries: 1-2 short plain sentences."
                )
            },
            {"role": "user", "content": question}
        ],
        "max_tokens": 900,
        "temperature": 0
    }
    
    url_complete = f"{base_url}/v1/chat/completions"
    
    # 3 tentatives : les modèles peuvent être lents ou la connexion instable
    for tentative in range(3):
        try:
            reponse = requests.post(
                url_complete,
                headers=headers,
                json=payload,
                timeout=90
            )
            reponse.raise_for_status()
            data = reponse.json()
            reponse_texte = data["choices"][0]["message"]["content"].strip()
            return _nettoyer_reponse(reponse_texte)
            
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            if tentative < 2:
                continue  # on réessaie
            return f"[ERROR] Fireworks connection failed after 3 attempts: {str(e)}"
        except requests.exceptions.RequestException as e:
            detail = ""
            if hasattr(e, 'response') and e.response is not None:
                detail = f" | Server detail: {e.response.text}"
            return f"[ERROR Fireworks] URL: {url_complete} | Problem: {str(e)}{detail}"
        except Exception as e:
            return f"[ERROR Fireworks] {str(e)}"