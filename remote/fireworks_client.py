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
                    "You are an evaluation agent. Always answer in English, in plain text only (no markdown, no asterisks, no bullet points). "
                    "Be concise but COMPLETE: answer exactly what the task asks, nothing more. "
                    "If the task asks to explain, justify, or describe how something works, include a brief 1-2 sentence explanation. "
                    "For sentiment classification: give the label (Positive, Negative, Neutral, or Mixed) followed by a one-sentence justification. "
                    "For math word problems: solve carefully and give the final numeric answer. "
                    "For named entity recognition: list each entity with its type. "
                    "For code debugging: briefly state what the bug is, then provide the complete corrected code. "
                    "For code generation: provide the complete working code only. "
                    "For summaries: strictly respect the exact length or format constraint given in the task. "
                    "Never invent information. Double-check math before answering."
                )
            },
            {"role": "user", "content": question}
        ],
        "max_tokens": 900,
        "temperature": 0
    }
    
    url_complete = f"{base_url}/v1/chat/completions"
    
    # 2 tentatives, timeout 30s (règle du hackathon : réponse < 30s par requête)
    for tentative in range(2):
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
            return _nettoyer_reponse(reponse_texte)
            
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            if tentative < 1:
                continue  # on réessaie une fois
            return f"[ERROR] Fireworks connection failed after 2 attempts: {str(e)}"
        except requests.exceptions.RequestException as e:
            detail = ""
            if hasattr(e, 'response') and e.response is not None:
                detail = f" | Server detail: {e.response.text}"
            return f"[ERROR Fireworks] URL: {url_complete} | Problem: {str(e)}{detail}"
        except Exception as e:
            return f"[ERROR Fireworks] {str(e)}"