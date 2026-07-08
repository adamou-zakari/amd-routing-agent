# remote/fireworks_client.py

import os
import requests
from dotenv import load_dotenv

load_dotenv()

def repondre_fireworks(question: str, modele: str) -> str:
    """
    Appelle Fireworks AI avec le modèle spécifié.
    """
    
    api_key = os.environ.get("FIREWORKS_API_KEY")
    base_url = os.environ.get("FIREWORKS_BASE_URL")
    
    if not api_key or not base_url:
        return "[ERROR] Missing Fireworks API key or base URL. Check environment variables."
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": modele,
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant. Always respond in English. Give a direct, clean, final answer only. Do not show your reasoning process, do not think out loud, and do not include phrases like 'Let's implement' or 'We need to'. Just provide the complete, correct answer immediately."
            },
            {"role": "user", "content": question}
        ],
        "max_tokens": 300
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
        return "[ERROR] Fireworks request timed out (30 seconds)"
    except requests.exceptions.RequestException as e:
        detail = ""
        if hasattr(e, 'response') and e.response is not None:
            detail = f" | Server detail: {e.response.text}"
        return f"[ERROR Fireworks] URL: {url_complete} | Problem: {str(e)}{detail}"
    except Exception as e:
        return f"[ERROR Fireworks] {str(e)}"