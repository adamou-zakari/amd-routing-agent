# remote/fireworks_client.py

import os
import re
import requests
from dotenv import load_dotenv

load_dotenv()

def _contrainte_mots(question: str):
    """Détecte 'exactly N words' / 'in N words' dans la tâche."""
    m = re.search(r"(?:exactly|in)\s+(\d+)\s+words", question, re.IGNORECASE)
    return int(m.group(1)) if m else None

def _nettoyer_reponse(texte: str, question: str = "") -> str:
    """Retire <think>, extrait le code des balises, gère les fuites de raisonnement
    et applique les contraintes de nombre de mots de façon déterministe."""
    texte = re.sub(r"<think>.*?</think>", "", texte, flags=re.DOTALL).strip()
    
    blocs = re.findall(r"```(?:python|\w+)?\s*\n(.*?)```", texte, re.DOTALL)
    if blocs:
        return blocs[0].strip()
    
    limite = _contrainte_mots(question)
    
    # Fuite de raisonnement (le modèle pense à voix haute) :
    # on récupère la dernière proposition entre guillemets
    marqueurs = ("Let me", "The user wants", "Try:", "Count:")
    if any(m in texte for m in marqueurs):
        candidats = re.findall(r'"([^"]{20,300})"', texte)
        if candidats:
            if limite:
                exacts = [c for c in candidats if len(c.split()) == limite]
                texte = exacts[-1] if exacts else candidats[-1]
            else:
                texte = candidats[-1]
    
    # Application stricte de la contrainte de mots
    if limite:
        mots = texte.split()
        if len(mots) > limite:
            texte = " ".join(mots[:limite]).rstrip(",;:") + "."
    
    return texte.strip()

def repondre_fireworks(question: str, modele: str) -> str:
    """Appelle Fireworks AI avec le modèle spécifié."""
    
    api_key = os.environ.get("FIREWORKS_API_KEY")
    base_url = os.environ.get("FIREWORKS_BASE_URL")
    
    if not api_key or not base_url:
        return "[ERROR] Missing Fireworks API key or base URL. Check environment variables."
    
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
                    "For summaries with a word or sentence limit: write ONE good summary close to the limit and stop. Do not count words out loud, do not revise repeatedly, never show drafts. "
                    "Never invent information. Double-check math before answering."
                )
            },
            {"role": "user", "content": question}
        ],
        "max_tokens": 1500,
        "temperature": 0
    }
    
    url_complete = f"{base_url}/v1/chat/completions"
    
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
            message = data["choices"][0].get("message", {})
            contenu = message.get("content")
            
            if not contenu or not contenu.strip():
                if tentative < 1:
                    payload["max_tokens"] = 3000
                    continue
                contenu = message.get("reasoning_content") or ""
                if not contenu.strip():
                    return "[ERROR] Empty model response"
            
            return _nettoyer_reponse(contenu.strip(), question)
            
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            if tentative < 1:
                continue
            return f"[ERROR] Fireworks connection failed after 2 attempts: {str(e)}"
        except requests.exceptions.RequestException as e:
            detail = ""
            if hasattr(e, 'response') and e.response is not None:
                detail = f" | Server detail: {e.response.text}"
            return f"[ERROR Fireworks] URL: {url_complete} | Problem: {str(e)}{detail}"
        except Exception as e:
            return f"[ERROR Fireworks] {str(e)}"