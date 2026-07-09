# remote/fireworks_client.py

import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_SYSTEM_PROMPT = (
    "You are a helpful assistant. Always respond in English. "
    "Give a direct, clean, final answer only. Do not show your reasoning "
    "process, do not think out loud, and do not include phrases like "
    "'Let's implement' or 'We need to'. Just provide the complete, "
    "correct answer immediately."
)

REASONING_SYSTEM_PROMPT = (
    "You are a helpful assistant. Always respond in English. "
    "For this task, think through the problem step by step internally, "
    "double-check your arithmetic or logic carefully, then give your "
    "final answer clearly with a brief 1-2 sentence explanation. "
    "Do not show messy intermediate scratch work in the final answer — "
    "only the verified final reasoning and conclusion."
)

def repondre_fireworks(question: str, modele: str, mode: str = "standard") -> str:
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
    
    if mode == "raisonnement":
        system_prompt = REASONING_SYSTEM_PROMPT
        max_tokens = 4000
    else:
        system_prompt = BASE_SYSTEM_PROMPT
        max_tokens = 300
    
    payload = {
        "model": modele,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ],
        "max_tokens": max_tokens
    }
    
    url_complete = f"{base_url}/v1/chat/completions"
    
    for tentative in range(2):
        try:
            reponse = requests.post(
                url_complete,
                headers=headers,
                json=payload,
                timeout=45
            )
            reponse.raise_for_status()
            data = reponse.json()
            
            # Extraction robuste avec fallback reasoning_content
            message = data.get("choices", [{}])[0].get("message", {})
            
            if "content" in message and message["content"]:
                return message["content"].strip()
            
            if "reasoning_content" in message and message["reasoning_content"]:
                return message["reasoning_content"].strip()
            
            return f"[ERROR] Fireworks response structure: {message}"
            
        except requests.exceptions.Timeout:
            if tentative < 1:
                continue
            return "[ERROR] Fireworks request timed out after retry"
        except requests.exceptions.RequestException as e:
            detail = ""
            if hasattr(e, 'response') and e.response is not None:
                detail = f" | Server detail: {e.response.text}"
            return f"[ERROR Fireworks] URL: {url_complete} | Problem: {str(e)}{detail}"
        except Exception as e:
            return f"[ERROR Fireworks] {str(e)}"
    
    return "[ERROR] Unexpected failure after retry"