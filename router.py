# router.py
import os

def _modeles_autorises() -> list:
    raw = os.environ.get("ALLOWED_MODELS", "")
    return [m.strip() for m in raw.split(",") if m.strip()]


def est_tache_code(question: str) -> bool:
    mots_code = [
        "code", "fonction", "python", "javascript", "bug", "debug",
        "erreur", "compile", "programme", "script", "algorithme",
        "classe", "variable", "syntax", "def ", "function", "class ",
        "return", "lambda", "implement"
    ]
    q = question.lower()
    return any(mot in q for mot in mots_code)


def est_tache_raisonnement(question: str) -> bool:
    """Multi-step math and logic puzzles: need deeper reasoning."""
    q = question.lower()
    mots_math = ["%", "percent", "calculate", "how many", "how much", "total",
                 "remain", "liters", "employees", "grew", "declined", "increase",
                 "decrease", "price", "cost", "sum", "average", "rate", "per "]
    mots_logique = ["sits in", "seat", "each own", "who owns", "taller than",
                    "older than", "constraint", "puzzle", "deduce", "must be",
                    "immediately to", "next to", "logic"]
    return any(m in q for m in mots_math + mots_logique)


def choisir_modele(question: str):
    """
    Returns (model, mode) where mode is 'code', 'raisonnement', or 'standard'.
    Model IDs come from ALLOWED_MODELS (hackathon rule: never hardcode).
    """
    modeles = _modeles_autorises()

    def trouver(mots_cles, defaut):
        for m in modeles:
            if any(k in m.lower() for k in mots_cles):
                return m
        return modeles[0] if modeles else defaut

    if est_tache_code(question):
        return trouver(["kimi", "code"], "accounts/fireworks/models/kimi-k2p7-code"), "code"
    if est_tache_raisonnement(question):
        return trouver(["minimax"], "accounts/fireworks/models/minimax-m3"), "raisonnement"
    return trouver(["minimax"], "accounts/fireworks/models/minimax-m3"), "standard"


if __name__ == "__main__":
    tests = [
        "What is the capital of Niger?",
        "Fix this bug: def add(a, b) return a+b",
        "A store has 240 items. It sells 15% on Monday and 60 more on Tuesday. How many remain?",
        "Three friends each own a different pet: cat, dog, bird. Sam does not own the bird. Jo owns the dog. Who owns the cat?",
    ]
    for t in tests:
        modele, mode = choisir_modele(t)
        print(f"'{t}' -> model={modele} mode={mode}")