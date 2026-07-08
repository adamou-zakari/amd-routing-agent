# router.py
# Décide FACILE/DIFFICILE (pour tes tests locaux)
# ET détecte si la tâche est du CODE (pour choisir le bon modèle Fireworks)

def classifier_difficulte(question: str) -> str:
    """Utilisé en développement local uniquement (ne compte pas dans le score)."""
    score = 0
    nb_mots = len(question.split())
    
    if nb_mots > 20:
        score += 2
    elif nb_mots > 10:
        score += 1
    
    mots_forts = ["analyse", "compare", "stratégie", "implications", "démontre", "évalue", "conçois"]
    for mot in mots_forts:
        if mot in question.lower():
            score += 2
    
    mots_moyens = ["pourquoi", "explique", "comment"]
    for mot in mots_moyens:
        if mot in question.lower():
            score += 1
    
    if question.count("?") > 1:
        score += 2
    
    return "DIFFICILE" if score >= 3 else "FACILE"


def est_tache_code(question: str) -> bool:
    """
    Détecte si la question concerne du CODE.
    Si oui -> on utilise Kimi K2.7 Code (spécialisé, plus cher)
    Si non -> on utilise Minimax M3 (généraliste, moins cher)
    """
    mots_code = [
        "code", "fonction", "python", "javascript", "bug", "debug",
        "erreur", "compile", "programme", "script", "algorithme",
        "classe", "variable", "syntax", "def ", "function", "class "
    ]
    question_lower = question.lower()
    return any(mot in question_lower for mot in mots_code)


def choisir_modele(question: str) -> str:
    """
    LA vraie fonction de routage qui compte pour le score du hackathon.
    Retourne le nom complet du modèle Fireworks à utiliser.
    """
    if est_tache_code(question):
        return "accounts/fireworks/models/kimi-k2p7-code"
    else:
        return "accounts/fireworks/models/minimax-m3"


if __name__ == "__main__":
    tests = [
        "Quelle est la capitale du Niger ?",
        "Corrige ce bug dans ma fonction Python",
        "Explique-moi les implications économiques de la BCEAO",
        "Écris une fonction qui trie une liste",
    ]
    for t in tests:
        print(f"'{t}'")
        print(f"  → Difficulté (dev only) : {classifier_difficulte(t)}")
        print(f"  → Modèle choisi : {choisir_modele(t)}\n")