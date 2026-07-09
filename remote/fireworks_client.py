# remote/fireworks_client.py

import os
import re
import requests
from dotenv import load_dotenv

load_dotenv()

PREAMBULES = re.compile(
    r"^(here (are|is)|named entities( extracted)?|sure[,!]?|certainly[,!]?)[^:\n]{0,60}:\s*",
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

    # Sortie NER : si le premier bloc est une liste 'Entité: Type',
    # on supprime tout paragraphe explicatif qui suivrait.
    ligne_entite = re.compile(r"^.{1,60}:\s*(Person|Organization|Location|Date)\s*$", re.IGNORECASE)
    blocs_texte = texte.split("\n\n")
    lignes = [l for l in blocs_texte[0].splitlines() if l.strip()]
    if len(lignes) >= 2 and all(ligne_entite.match(l.strip()) for l in lignes):
        return blocs_texte[0].strip()

    return texte

def _appel_api(url, headers, payload):
    """Retourne (content, reasoning) — le contenu final SEULEMENT dans content."""
    reponse = requests.post(url, headers=headers, json=payload, timeout=30)
    reponse.raise_for_status()
    message = reponse.json()["choices"][0].get("message", {})
    return message.get("content") or "", message.get("reasoning_content") or ""

def repondre_fireworks(question: str, modele: str, mode: str = "standard") -> str:
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
        "For sentiment classification: choose among Positive, Negative, Neutral, or Mixed, then give one short justification. Purely factual or descriptive statements with no emotional language are Neutral, not Positive. "
        "For math word problems: solve carefully, verify your arithmetic, and give the final numeric answer with a brief explanation. "
        "For named entity recognition: output ONLY the list of entities with their types (Person, Organization, Location, Date), one per line, format 'Entity: Type'. No introduction, no explanation, no numbering. Temporal expressions like 'last March' or 'two years ago' count as Date entities. "
        "For code debugging: briefly state what the bug is, then provide the complete corrected code. "
        "For code generation: provide the complete working code only. "
        "For summaries with a word limit: write ONE grammatical summary of exactly that length, then stop. Never count out loud, never show drafts. "
        "For summaries in one sentence: one clear, reasonably short sentence. "
        "Never invent information."
    )

    user_content = question
    max_tokens = 1500
    if mode == "raisonnement":
        max_tokens = 3000
        user_content = (
            question + "\n\nSolve step by step internally and verify your arithmetic or logic. "
            "Then output ONLY the final answer with a brief 1-2 sentence explanation."
        )

    payload = {
        "model": modele,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ],
        "max_tokens": max_tokens,
        "temperature": 0
    }
    url_complete = f"{base_url}/v1/chat/completions"
    limite = _contrainte_mots(question)
    dernier_raisonnement = ""

    for tentative in range(3):
        try:
            contenu, raisonnement = _appel_api(url_complete, headers, payload)
            dernier_raisonnement = raisonnement or dernier_raisonnement

            # Contenu vide = tokens épuisés en réflexion -> on RÉESSAIE avec plus de budget
            if not contenu.strip():
                if tentative < 2:
                    payload["max_tokens"] = min(payload["max_tokens"] * 2 + 1000, 6000)
                    continue
                contenu = dernier_raisonnement
                if not contenu.strip():
                    return "[ERROR] Empty model response"

            reponse = _nettoyer_reponse(contenu.strip())

            # Contrainte de mots : une réécriture guidée si le compte est faux
            if limite and len(reponse.split()) != limite:
                correction = {
                    "model": modele,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": question},
                        {"role": "assistant", "content": reponse},
                        {"role": "user", "content": f"Rewrite your summary as ONE grammatical sentence of EXACTLY {limite} words. Output only the sentence, nothing else."}
                    ],
                    "max_tokens": 300,
                    "temperature": 0
                }
                try:
                    c2, _ = _appel_api(url_complete, headers, correction)
                    reecrit = _nettoyer_reponse(c2.strip())
                    if reecrit and abs(len(reecrit.split()) - limite) <= abs(len(reponse.split()) - limite):
                        reponse = reecrit
                except Exception:
                    pass

            return reponse

        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            if tentative < 2:
                continue
            return f"[ERROR] Fireworks connection failed: {str(e)}"
        except requests.exceptions.RequestException as e:
            detail = ""
            if hasattr(e, 'response') and e.response is not None:
                detail = f" | Server detail: {e.response.text}"
            return f"[ERROR Fireworks] URL: {url_complete} | Problem: {str(e)}{detail}"
        except Exception as e:
            return f"[ERROR Fireworks] {str(e)}"