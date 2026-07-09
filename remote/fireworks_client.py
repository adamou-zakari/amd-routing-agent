# remote/fireworks_client.py

import os
import re
import requests
from dotenv import load_dotenv

load_dotenv()

def _nettoyer_reponse(texte: str, question: str = "") -> str:
    """Retire <think>, extrait le code des balises, applique les contraintes de mots."""
    texte = re.sub(r"<think>.*?</think>", "", texte, flags=re.DOTALL).strip()
    
    # Extraire le code des blocs markdown
    blocs = re.findall(r"```(?:python|\w+)?\s*\n(.*?)```", texte, re.DOTALL)
    if blocs:
        return blocs[0].strip()
    
    # Détecter la contrainte de mots
    m = re.search(r"(?:exactly|in)\s+(\d+)\s+words", question, re.IGNORECASE)
    limite = int(m.group(1)) if m else None
    
    # Si le modèle a laissé des guillemets, prendre la dernière proposition
    marqueurs = ("Let me", "The user wants", "Try:", "Count:", "Draft")
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

def repondre_fireworks(question: str, modele: str, mode: str = "standard") -> str:
    api_key = os.environ.get("FIREWORKS_API_KEY")
    base_url = os.environ.get("FIREWORKS_BASE_URL")
    
    if not api_key or not base_url:
        return "[ERROR] Missing Fireworks API key or base URL."
    
    base_url = base_url.rstrip("/")
    if base_url.endswith("/v1"):
        base_url = base_url[:-3].rstrip("/")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # === PROMPTS SYSTÈME PAR MODE ===
    if mode == "code":
        system_prompt = (
            "You are a coding expert. Give ONLY the corrected code. "
            "No explanations, no markdown, just the code. "
            "If there's a bug, fix it and output the complete corrected function."
        )
        max_tokens = 500
        
    elif mode == "resume":
        system_prompt = (
            "You are a summarization expert. "
            "Give ONLY the final summary, no explanations, no drafts. "
            "Count the words silently in your head. "
            "If the task says 'exactly N words', output EXACTLY that many words. "
            "If the task says 'in one sentence', output ONE sentence. "
            "Stop after the requested length."
        )
        max_tokens = 500
        
    elif mode == "raisonnement":
        system_prompt = (
            "You are a math and logic expert. "
            "Think through the problem step by step internally. "
            "Double-check your arithmetic and logic. "
            "Then give your final answer with a brief 1-2 sentence explanation. "
            "Do not show your intermediate reasoning in the final answer."
        )
        max_tokens = 4000
        
    else:  # standard
        system_prompt = (
            "You are a helpful assistant. Always respond in English. "
            "Give a direct, clean, final answer only. "
            "For sentiment: give ONE label (Positive/Negative/Neutral/Mixed). "
            "For NER: list each entity with its type. "
            "For facts: give the direct answer. "
            "Be concise and complete."
        )
        max_tokens = 300
    
    payload = {
        "model": modele,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ],
        "max_tokens": max_tokens,
        "temperature": 0
    }
    
    url_complete = f"{base_url}/v1/chat/completions"
    
    for tentative in range(2):
        try:
            reponse = requests.post(url_complete, headers=headers, json=payload, timeout=45)
            reponse.raise_for_status()
            data = reponse.json()
            message = data.get("choices", [{}])[0].get("message", {})
            
            contenu = message.get("content")
            if not contenu or not contenu.strip():
                if tentative < 1:
                    payload["max_tokens"] = 4000
                    continue
                contenu = message.get("reasoning_content")
                if not contenu or not contenu.strip():
                    return "[ERROR] Empty model response after retry"
            
            return _nettoyer_reponse(contenu.strip(), question)
            
        except requests.exceptions.Timeout:
            if tentative < 1:
                continue
            return "[ERROR] Fireworks timeout after 2 attempts"
        except requests.exceptions.RequestException as e:
            detail = ""
            if hasattr(e, 'response') and e.response is not None:
                detail = f" | Server: {e.response.text}"
            return f"[ERROR Fireworks] {str(e)}{detail}"
        except Exception as e:
            return f"[ERROR Fireworks] {str(e)}"
    
    return "[ERROR] Unexpected failure"