import os
import json
from dotenv import load_dotenv
from router import classifier_difficulte
from models.local_model import repondre_local
from remote.fireworks_client import repondre_fireworks

# Charger les variables depuis .env
load_dotenv()

def traiter_question(question: str) -> dict:
    """
    Traite une question :
    1. Classifie la difficulté (FACILE ou DIFFICILE)
    2. Appelle le bon modèle (local ou Fireworks)
    3. Retourne la réponse
    """
    difficulte = classifier_difficulte(question)
    
    if difficulte == "FACILE":
        reponse = repondre_local(question)
        modele = "local (GPT-2)"
    else:
        # Lire les modèles autorisés depuis l'environnement
        modeles = os.environ.get("ALLOWED_MODELS", "").split(",")
        modele = modeles[0] if modeles else "accounts/fireworks/models/gemma-4-31b-it"
        reponse = repondre_fireworks(question, modele)
        modele = f"fireworks ({modele})"
    
    return {
        "question": question,
        "difficulte": difficulte,
        "reponse": reponse,
        "modele": modele
    }

def traiter_depuis_fichier():
    """
    Mode hackathon officiel :
    Lit /input/tasks.json, traite chaque tâche, écrit /output/results.json
    """
    input_path = "/input/tasks.json"
    output_path = "/output/results.json"
    
    if not os.path.exists(input_path):
        return False
    
    with open(input_path, "r") as f:
        tasks = json.load(f)
    
    results = []
    for task in tasks:
        task_id = task.get("task_id")
        prompt = task.get("prompt")
        resultat = traiter_question(prompt)
        results.append({
            "task_id": task_id,
            "answer": resultat["reponse"]
        })
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    
    return True

if __name__ == "__main__":
    # Mode hackathon : lecture de /input/tasks.json
    if traiter_depuis_fichier():
        print("✅ Traitement terminé. Résultats dans /output/results.json")
    else:
        # Mode développement : tests interactifs
        print("🔧 Mode test interactif")
        tests = [
            "Quelle est la capitale du Niger ?",
            "Explique-moi les implications économiques de la BCEAO sur l'inflation"
        ]
        for q in tests:
            r = traiter_question(q)
            print(f"\nQUESTION: {r['question']}")
            print(f"DIFFICULTE: {r['difficulte']}")
            print(f"MODELE: {r['modele']}")
            print(f"REPONSE: {r['reponse']}")