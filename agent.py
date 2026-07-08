# agent.py
import os
import json
from dotenv import load_dotenv
from router import choisir_modele
from remote.fireworks_client import repondre_fireworks

load_dotenv()

def traiter_question(question: str) -> dict:
    """
    Choisit le modèle Fireworks le moins cher adapté à la tâche,
    puis envoie la question et retourne la réponse.
    """
    modele = choisir_modele(question)
    reponse = repondre_fireworks(question, modele)
    
    return {
        "question": question,
        "modele_utilise": modele,
        "reponse": reponse
    }


def traiter_depuis_fichier():
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
    if traiter_depuis_fichier():
        print("✅ Traitement terminé. Résultats dans /output/results.json")
    else:
        print("🔧 Mode test interactif\n")
        tests = [
            "Quelle est la capitale du Niger ?",
            "Corrige ce bug : def add(a, b) return a+b",
            "Explique-moi les implications économiques de la BCEAO sur l'inflation"
        ]
        for q in tests:
            r = traiter_question(q)
            print(f"QUESTION: {r['question']}")
            print(f"MODELE: {r['modele_utilise']}")
            print(f"REPONSE: {r['reponse'][:200]}...\n")