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
    """
    Calls Fireworks AI with the specified model.
    mode: 'code' / 'standard' -> short, direct answers.
          'raisonnement' -> more tokens, careful step-by-step verification.
    Retries once on connection/timeout errors before giving up.
    """

    api_key = os.environ.get("FIREWORKS_API_KEY")
    base_url = os.environ.get("FIREWORKS_BASE_URL")

    if not api_key or not base_url:
        return "[ERROR] Missing Fireworks API key or base URL. Check environment variables."

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
            
            # === EXTRACTION ULTRA-ROBUSTE AVEC FALLBACK ===
            if "choices" in data and len(data["choices"]) > 0:
                message = data["choices"][0].get("message", {})
                
                # 1. Essayer content d'abord (format standard)
                if "content" in message and message["content"]:
                    return message["content"].strip()
                
                # 2. Fallback : reasoning_content (Gemma en mode raisonnement)
                if "reasoning_content" in message and message["reasoning_content"]:
                    return message["reasoning_content"].strip()
                
                # 3. Si rien, on retourne le message complet pour debug
                return f"[ERROR] Fireworks response structure: {message}"
            else:
                return f"[ERROR] Fireworks unexpected response: {data}"

        except requests.exceptions.Timeout:
            if tentative == 0:
                time.sleep(2)
                continue
            return "[ERROR] Fireworks request timed out after retry"

        except requests.exceptions.RequestException as e:
            if tentative == 0:
                time.sleep(2)
                continue
            detail = ""
            if hasattr(e, 'response') and e.response is not None:
                detail = f" | Server detail: {e.response.text}"
            return f"[ERROR Fireworks] URL: {url_complete} | Problem: {str(e)}{detail}"

        except Exception as e:
            return f"[ERROR Fireworks] {str(e)}"

    return "[ERROR] Unexpected failure after retry"