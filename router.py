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
    """Maths multi-étapes et puzzles logiques : réflexion approfondie + vérification."""
    q = question.lower()
    mots_math = ["%", "percent", "calculate", "how many", "how much", "total",
                 "remain", "liters", "grew", "declined", "increase", "decrease",
                 "price", "cost", "sum", "average", "rate", "years old", "per ",
                 "twice", "half", "ratio", "fraction", "speed", "distance",
                 "minutes", "hours", "kg", "grams", "meters", "km", "older",
                 "younger", "age", "profit", "discount", "interest", "legs",
                 "animals", "grows", "loses", "value"]
    mots_logique = ["sits in", "seat", "each own", "who owns", "taller", "shorter",
                    "constraint", "puzzle", "deduce", "must be", "immediately",
                    "next to", "logic", "exactly one", "finished before",
                    "finished after", "order from", "left of", "right of",
                    "who speaks", "each speak"]
    return any(m in q for m in mots_math + mots_logique)


def choisir_modele(question: str):
    """Retourne (modele, mode) : mode = 'code', 'raisonnement' ou 'standard'."""
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