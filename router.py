# router.py
# Ce fichier contient le "cerveau" qui décide si une question 
# est FACILE (→ modèle local gratuit) ou DIFFICILE (→ modèle distant payant)


def question_est_simple(question: str) -> bool:
    """
    Vérifie si une question est clairement simple malgré la présence de mots complexes.
    Exemples : "Pourquoi il pleut ?" → True (simple)
              "Pourquoi l'inflation augmente-t-elle au Niger ?" → False (complexe)
    """
    # Si la question est très courte (moins de 6 mots), on la considère simple
    if len(question.split()) <= 5:
        return True
    
    # Mots qui indiquent une question réellement complexe
    vrais_mots_complexes = [
        "économie", "inflation", "stratégie", "analyse",
        "comparer", "théorie", "mécanisme", "implication"
    ]
    
    # Si un vrai mot complexe est présent ET que la question fait plus de 5 mots
    for mot in vrais_mots_complexes:
        if mot in question.lower():
            return False
    
    return True


def classifier_difficulte(question: str) -> str:
    """
    Cette fonction reçoit une question (texte) 
    et retourne soit "FACILE" soit "DIFFICILE".
    """
    
    nb_mots = len(question.split())
    
    # D'abord, on vérifie si la question est clairement simple
    if question_est_simple(question):
        return "FACILE"
    
    # Liste de mots qui indiquent souvent une question complexe.
    mots_complexes = [
        "pourquoi", "explique", "analyse", 
        "compare", "implications", "stratégie"
    ]
    
    # On vérifie si un mot complexe est présent dans la question.
    contient_mot_complexe = any(
        mot in question.lower() for mot in mots_complexes
    )
    
    # RÈGLE DE DÉCISION :
    if nb_mots > 15 or contient_mot_complexe:
        return "DIFFICILE"
    else:
        return "FACILE"


# Zone de test
if __name__ == "__main__":
    tests = [
        "Quelle est la capitale du Niger ?",
        "Explique-moi les implications économiques de la BCEAO sur l'inflation",
        "Salut",
        "Pourquoi il pleut aujourd'hui ?",
        "Pourquoi l'inflation augmente-t-elle au Niger ?"
    ]
    
    for test in tests:
        print(f"'{test}' → {classifier_difficulte(test)}")