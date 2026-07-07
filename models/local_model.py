from transformers import pipeline

# Charger le modèle GPT-2 une seule fois au démarrage
generateur = pipeline("text-generation", model="gpt2")

def repondre_local(question: str) -> str:
    """
    Répond à une question simple avec le modèle local GPT-2.
    """
    prompt = f"Question: {question}\nRéponse:"
    resultat = generateur(
        prompt,
        max_length=50,
        do_sample=False,
        pad_token_id=50256
    )
    reponse_complete = resultat[0]['generated_text']
    reponse = reponse_complete.split("Réponse:")[-1].strip()
    return reponse