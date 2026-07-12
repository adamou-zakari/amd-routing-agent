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

MARQUEURS_BROUILLON = ("Let me count", "Let me try", "Let me craft", "Try:", "Count:", "The user wants", "That's too many", "words. Still", "words. Too")

MOTS_ORPHELINS = {"and", "or", "the", "a", "an", "of", "into", "with", "to", "for", "as", "by", "in", "on", "at", "but"}

SYSTEM_PROMPT = (
    "Answer in English, plain text, no markdown. Give the correct final answer as briefly as possible. "
    "Explanations, definitions, 'how it works' questions: answer in 2-3 short sentences maximum, no more. "
    "Sentiment (ONLY when the task explicitly asks to classify sentiment): one label (Positive/Negative/Neutral/Mixed) + ONE short sentence of justification. "
    "Math/logic: give the final answer + one short line of reasoning, nothing more. "
    "NER: only 'Entity: Type' lines (Person/Organization/Location/Date); relative dates are Dates. "
    "Debug: state the bug in one short line, then the corrected code only. Codegen: code only, no comments. "
    "Word-limited summary: write it in ONE attempt, never count aloud, never show drafts."
)

def _contrainte_mots(question: str):
    m = re.search(r"(?:exactly|in)\s+(\d+)\s+words", question, re.IGNORECASE)
    return int(m.group(1)) if m else None

def _extraire_candidat_brouillon(texte: str, limite=None):
    candidats = re.findall(r'"([^"]{20,400})"', texte)
    if not candidats:
        return None
    if limite:
        exacts = [c for c in candidats if len(c.split()) == limite]
        if exacts:
            return exacts[-1]
        return min(candidats, key=lambda c: abs(len(c.split()) - limite))
    return candidats[-1]

def _forcer_limite(texte: str, limite: int) -> str:
    mots = texte.split()
    if len(mots) <= limite:
        return texte
    mots = mots[:limite]
    while mots and mots[-1].strip(",;:.").lower() in MOTS_ORPHELINS:
        mots.pop()
    coupe = " ".join(mots).rstrip(",;:—-")
    if not coupe.endswith("."):
        coupe += "."
    return coupe

def _nettoyer_reponse(texte: str, limite=None) -> str:
    texte = re.sub(r"<think>.*?</think>", "", texte, flags=re.DOTALL).strip()
    blocs = re.findall(r"```(?:python|\w+)?\s*\n(.*?)```", texte, re.DOTALL)
    if blocs:
        return blocs[0].strip()
    texte = PREAMBULES.sub("", texte).strip()

    if any(m in texte for m in MARQUEURS_BROUILLON):
        candidat = _extraire_candidat_brouillon(texte, limite)
        if candidat:
            texte = candidat

    ligne_entite = re.compile(r"^.{1,60}:\s*(Person|Organization|Location|Date)\s*$", re.IGNORECASE)
    blocs_texte = texte.split("\n\n")
    lignes = [l for l in blocs_texte[0].splitlines() if l.strip()]
    if len(lignes) >= 2 and all(ligne_entite.match(l.strip()) for l in lignes):
        return blocs_texte[0].strip()

    return texte

def _appel_api(url, headers, payload):
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
    url_complete = f"{base_url}/v1/chat/completions"
    limite = _contrainte_mots(question)

    max_tokens = 600
    if mode == "raisonnement":
        max_tokens = 1200
    if limite:
        max_tokens = 500

    payload = {
        "model": modele,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question}
        ],
        "max_tokens": max_tokens,
        "temperature": 0
    }
    dernier_raisonnement = ""

    for tentative in range(3):
        try:
            contenu, raisonnement = _appel_api(url_complete, headers, payload)
            dernier_raisonnement = raisonnement or dernier_raisonnement

            if not contenu.strip():
                if tentative < 2:
                    payload["max_tokens"] = min(payload["max_tokens"] * 2, 5000)
                    continue
                contenu = dernier_raisonnement
                if not contenu.strip():
                    return "[ERROR] Empty model response"

            reponse = _nettoyer_reponse(contenu.strip(), limite)

            if limite and len(reponse.split()) != limite:
                correction = {
                    "model": modele,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": f"Task: {question}\n\nDraft: {_forcer_limite(reponse, limite + 10)}\n\nRewrite as ONE complete grammatical sentence of EXACTLY {limite} words. Output only the sentence."}
                    ],
                    "max_tokens": 150,
                    "temperature": 0
                }
                try:
                    c2, _ = _appel_api(url_complete, headers, correction)
                    reecrit = _nettoyer_reponse(c2.strip(), limite)
                    if reecrit and abs(len(reecrit.split()) - limite) <= abs(len(reponse.split()) - limite):
                        reponse = reecrit
                except Exception:
                    pass
                if len(reponse.split()) > limite:
                    reponse = _forcer_limite(reponse, limite)

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