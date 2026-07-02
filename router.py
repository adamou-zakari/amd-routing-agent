# router.py
# Ce fichier contient le "cerveau" qui décide si une question 
# est FACILE (→ modèle local gratuit) ou DIFFICILE (→ modèle distant payant)


def classifier_difficulte(question: str) -> str:
    """
    Cette fonction reçoit une question (texte) 
    et retourne soit "FACILE" soit "DIFFICILE".
    """
    
    # On compte le nombre de mots dans la question.
    # Une question courte est souvent plus simple à traiter.
    nb_mots = len(question.split())
    
    # Liste de mots qui indiquent souvent une question complexe.
    # Si un de ces mots apparaît, on penche vers "DIFFICILE".
    mots_complexes = [
        "pourquoi", "explique", "analyse", 
        "compare", "implications", "stratégie"
    ]
    
    # On vérifie si un mot complexe est présent dans la question.
    # .lower() met tout en minuscule pour ne pas rater "Pourquoi" vs "pourquoi"
    contient_mot_complexe = any(
        mot in question.lower() for mot in mots_complexes
    )
    
    # RÈGLE DE DÉCISION :
    # Si la question est longue (+15 mots) OU contient un mot complexe
    # → DIFFICILE. Sinon → FACILE.
    if nb_mots > 15 or contient_mot_complexe:
        return "DIFFICILE"
    else:
        return "FACILE"


# Cette partie s'exécute UNIQUEMENT si on lance ce fichier directement
# (pas si un autre fichier l'importe)
if __name__ == "__main__":
    test1 = "Quelle est la capitale du Niger ?"
    test2 = "Explique-moi les implications économiques de la BCEAO sur l'inflation"
    test3 = "Salut"
    
    print(f"'{test1}' → {classifier_difficulte(test1)}")
    print(f"'{test2}' → {classifier_difficulte(test2)}")
    print(f"'{test3}' → {classifier_difficulte(test3)}")