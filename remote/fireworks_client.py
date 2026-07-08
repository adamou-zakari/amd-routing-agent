# remote/fireworks_client.py

import os
import re
import requests
from dotenv import load_dotenv

load_dotenv()

PREAMBULES = re.compile(
    r"^(here (are|is)|the (named )?entities( extracted)?|sure[,!]?|certainly[,!]?)[^:\n]*:\s*",
    re.IGNORECASE
)

def _contrainte_mots(question: str):
    m = re.search(r"(?:exactly|in)\s+(\d+)\s+words", question, re.IGNORECASE)
    return int(m.group(1)) if m else None

def _nettoyer_reponse(texte: str) -> str:
    texte = re.sub(r"<think>.*?</think>", "", texte, flags=re.DOTALL).strip()
    blocs = re.findall(r"```(?:python|\w+)?\s*\n(.*?)```", texte, re.DOTALL)
    if blocs:
        return blocs[0].strip()
    texte = PREAMBULES.sub("", texte).strip()
    return texte

def _appel_api(url, headers, payload):
    reponse = requests.post(url, headers=headers, json=payload, timeout=30)
    reponse.raise_for_status()
    message = reponse.json()["choices"][0].get("message", {})
    return message.get("content") or message.get("reasoning_content") or ""

def repondre_fireworks(question: str, modele: str) -> str:
    api_key = os.environ.get("FIREWORKS_API_KEY")
    base_url = os.environ.get("FIREWORKS_BASE_URL")
    if not api_key or not base_url:
        return "[ERROR] Missing Fireworks API key or base URL. Check environment variables."

    base_url = base_url.rstrip("/")
    if base_url.endswith("/v1"):
        base_url = base_url[:-3].rstrip("/")

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    system_prompt = (
        "You are an evaluation agent. Always answer in English, in plain text only (no markdown, no asterisks, no bullet points). "
        "Be concise but COMPLETE: answer exactly what the task asks, nothing more. Never add introductions like 'Here are'. "
        "If the task asks to explain, justify, or describe how something works, include a brief 1-2 sentence explanation. "
        "For sentiment classification: give the label (Positive, Negative, Neutral, or Mixed) followed by a one-sentence justification. "
        "For math word problems: solve carefully and give the final numeric answer. "
        "For named entity recognition: list each entity with its type, nothing else. "
        "For code debugging: briefly state what the bug is, then provide the complete corrected code. "
        "For code generation: provide the complete working code only. "
        "For summaries with a word limit: write ONE grammatical summary of exactly that length, then stop. Never count out loud, never show drafts. "
        "Never invent information. Double-check math before answering."
    )
    payload = {
        "model": modele,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ],
        "max_tokens": 1500,
        "temperature": 0
    }
    url_complete = f"{base_url}/v1/chat/completions"
    limite = _contrainte_mots(question)

    for tentative in range(2):
        try:
            contenu = _appel_api(url_complete, headers, payload)
            if not contenu.strip():
                if tentative < 1:
                    payload["max_tokens"] = 3000
                    continue
                return "[ERROR] Empty model response"

            reponse = _nettoyer_reponse(contenu.strip())

            # Validation de la contrainte de mots : une correction guidée, pas de troncature brute
            if limite and len(reponse.split()) != limite:
                correction = {
                    "model": modele,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": question},
                        {"role": "assistant", "content": reponse},
                        {"role": "user", "content": f"Rewrite your summary as ONE grammatical sentence of EXACTLY {limite} words. Output only the sentence."}
                    ],
                    "max_tokens": 200,
                    "temperature": 0
                }
                try:
                    reecrit = _nettoyer_reponse(_appel_api(url_complete, headers, correction).strip())
                    if reecrit and abs(len(reecrit.split()) - limite) <= abs(len(reponse.split()) - limite):
                        reponse = reecrit
                except Exception:
                    pass  # on garde la première réponse

            return reponse

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