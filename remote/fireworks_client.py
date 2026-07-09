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

SYSTEM_PROMPT = (
    "You are an evaluation agent. Always answer in English, in plain text only (no markdown, no asterisks, no bullet points). "
    "Be concise but COMPLETE: answer exactly what the task asks, nothing more. Never add introductions like 'Here are'. "
    "If the task asks to explain, justify, or describe how something works, include a brief 1-2 sentence explanation. "
    "For sentiment classification: choose among Positive, Negative, Neutral, or Mixed, then give one short justification. Purely factual or descriptive statements with no emotional language are Neutral, not Positive. "
    "For math word problems: solve carefully, verify your arithmetic, and give the final numeric answer with a brief explanation. "
    "For named entity recognition: output ONLY the list of entities with their types (Person, Organization, Location, Date), one per line, format 'Entity: Type'. No introduction, no explanation, no numbering. Temporal expressions like 'last March' or 'two years ago' count as Date entities. "
    "For code debugging: briefly state what the bug is, then provide the complete corrected code. "
    "For code generation: provide the complete working code only. "
    "For summaries with a word limit: write ONE grammatical summary of approximately that length in a single attempt, then stop immediately. Never count words out loud, never revise, never show drafts. "
    "For summaries in one sentence: one clear, reasonably short sentence. "
    "Never invent information."
)

def _contrainte_mots(question: str):
    m = re.search(r"(?:exactly|in)\s+(\d+)\s+words", question, re.IGNORECASE)
    return int(m.group(1)) if m else None

def _extraire_nombres(texte: str):
    return re.findall(r"-?\d[\d,]*\.?\d*", texte.replace(",", ""))

def _extraire_candidat_brouillon(texte: str, limite=None):
    """Si le texte est un brouillon de comptage, récupère la meilleure proposition entre guillemets."""
    candidats = re.findall(r'"([^"]{20,400})"', texte)
    if not candidats:
        return None
    if limite:
        exacts = [c for c in candidats if len(c.split()) == limite]
        if exacts:
            return exacts[-1]
        # sinon le plus proche du compte
        return min(candidats, key=lambda c: abs(len(c.split()) - limite))
    return candidats[-1]

def _forcer_limite(texte: str, limite: int) -> str:
    """Troncature dure en dernier recours : exactement `limite` mots, terminés proprement."""
    mots = texte.split()
    if len(mots) <= limite:
        return texte
    coupe = " ".join(mots[:limite]).rstrip(",;:—-")
    if not coupe.endswith("."):
        coupe += "."
    return coupe

def _nettoyer_reponse(texte: str, limite=None) -> str:
    texte = re.sub(r"<think>.*?</think>", "", texte, flags=re.DOTALL).strip()
    blocs = re.findall(r"```(?:python|\w+)?\s*\n(.*?)```", texte, re.DOTALL)
    if blocs:
        return blocs[0].strip()
    texte = PREAMBULES.sub("", texte).strip()

    # Fuite de brouillon (comptage à voix haute) : on repêche la meilleure proposition
    if any(m in texte for m in MARQUEURS_BROUILLON):
        candidat = _extraire_candidat_brouillon(texte, limite)
        if candidat:
            texte = candidat

    # Sortie NER : liste nue, on coupe toute explication qui suivrait
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

def _appel_simple(url, headers, modele, user_content, max_tokens=2000, limite=None):
    payload = {
        "model": modele,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content}
        ],
        "max_tokens": max_tokens,
        "temperature": 0
    }
    for tentative in range(2):
        try:
            contenu, _ = _appel_api(url, headers, payload)
            if contenu.strip():
                return _nettoyer_reponse(contenu.strip(), limite)
            payload["max_tokens"] = min(payload["max_tokens"] * 2 + 1000, 6000)
        except Exception:
            continue
    return ""

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

    user_content = question
    max_tokens = 1500
    if mode == "raisonnement":
        max_tokens = 3000
        user_content = (
            question + "\n\nSolve step by step internally and verify your arithmetic or logic. "
            "Then output ONLY the final answer with a brief 1-2 sentence explanation."
        )
    if limite:
        max_tokens = 4000  # gros budget d'emblée pour éviter la coupe en plein comptage
        user_content = (
            question + f"\n\nWrite the summary in ONE attempt, approximately {limite} words. "
            "Do not count words out loud. Do not show drafts. Output only the summary."
        )

    payload = {
        "model": modele,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content}
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
                    payload["max_tokens"] = min(payload["max_tokens"] * 2 + 1000, 6000)
                    continue
                contenu = dernier_raisonnement
                if not contenu.strip():
                    return "[ERROR] Empty model response"

            reponse = _nettoyer_reponse(contenu.strip(), limite)

            # AUTO-VERIFICATION des maths
            if mode == "raisonnement" and any(c.isdigit() for c in question):
                nombres_1 = _extraire_nombres(reponse)
                verif = _appel_simple(
                    url_complete, headers, modele,
                    question + "\n\nSolve this independently from scratch. Verify each step. "
                    "Output ONLY the final numeric answer, nothing else.",
                    max_tokens=3000
                )
                nombres_2 = _extraire_nombres(verif)
                if nombres_1 and nombres_2 and nombres_1[-1] != nombres_2[-1]:
                    arbitrage = _appel_simple(
                        url_complete, headers, modele,
                        question + f"\n\nTwo candidate answers were computed: '{nombres_1[-1]}' and '{nombres_2[-1]}'. "
                        "Carefully determine which is correct by re-solving. "
                        "Output the correct final answer with a brief 1-2 sentence explanation.",
                        max_tokens=4000
                    )
                    if arbitrage:
                        reponse = arbitrage

            # Contrainte de mots : réécriture guidée (avec réponse courte en contexte), puis troncature dure
            if limite and len(reponse.split()) != limite:
                base_courte = _forcer_limite(reponse, limite + 10)
                reecrit = _appel_simple(
                    url_complete, headers, modele,
                    f"Original task: {question}\n\nDraft summary: {base_courte}\n\n"
                    f"Rewrite it as ONE grammatical sentence of EXACTLY {limite} words. Output only the sentence.",
                    max_tokens=300, limite=limite
                )
                if reecrit and abs(len(reecrit.split()) - limite) <= abs(len(reponse.split()) - limite):
                    reponse = reecrit
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