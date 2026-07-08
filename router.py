# router.py
import os

def _modeles_autorises() -> list:
    """Lit la liste des modèles depuis ALLOWED_MODELS (injectée par le harnais)."""
    raw = os.environ.get("ALLOWED_MODELS", "")
    return [m.strip() for m in raw.split(",") if m.strip()]


def est_tache_code(question: str) -> bool:
    """Détecte si la question concerne du CODE."""
    mots_code = [
        "code", "fonction", "python", "javascript", "bug", "debug",
        "erreur", "compile", "programme", "script", "algorithme",
        "classe", "variable", "syntax", "def ", "function", "class "
    ]
    question_lower = question.lower()
    return any(mot in question_lower for mot in mots_code)


def choisir_modele(question: str) -> str:
    """
    Routage conforme aux règles : les IDs viennent de ALLOWED_MODELS.
    Fallback sur les IDs complets uniquement en dev local (variable absente).
    """
    modeles = _modeles_autorises()
    
    if not modeles:
        # Dev local uniquement (ALLOWED_MODELS non défini)
        if est_tache_code(question):
            return "accounts/fireworks/models/kimi-k2p7-code"
        return "accounts/fireworks/models/minimax-m3"
    
    if est_tache_code(question):
        for m in modeles:
            if "kimi" in m.lower() or "code" in m.lower():
                return m
    
    for m in modeles:
        if "minimax" in m.lower():
            return m
    
    return modeles[0]