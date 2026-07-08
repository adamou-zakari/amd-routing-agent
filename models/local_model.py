# models/local_model.py
# Ce modèle local est utilisé UNIQUEMENT pour le développement/debug.
# Il ne compte pas dans le score du hackathon (seul Fireworks est noté).

def repondre_local(question: str) -> str:
    """
    Réponse simulée basique, utile uniquement pour tester rapidement
    le flux du programme sans consommer de tokens Fireworks.
    """
    return f"[Réponse locale simulée, pour test uniquement] Question reçue : '{question}'"