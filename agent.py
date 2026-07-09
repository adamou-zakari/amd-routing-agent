# agent.py
import os
import json
from dotenv import load_dotenv
from router import choisir_modele
from remote.fireworks_client import repondre_fireworks

load_dotenv()

def traiter_question(question: str) -> dict:
    """
    Picks the cheapest suitable Fireworks model for the task,
    with a reasoning mode for math/logic tasks, then returns the answer.
    """
    modele, mode = choisir_modele(question)
    reponse = repondre_fireworks(question, modele, mode)

    return {
        "question": question,
        "modele_utilise": modele,
        "mode": mode,
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
        print("Done. Results written to /output/results.json")
    else:
        print("Interactive test mode\n")
        tests = [
            "What is the capital of Niger?",
            "Fix this bug: def add(a, b) return a+b",
            "A store has 240 items. It sells 15% on Monday and 60 more on Tuesday. How many items remain?",
            "Three friends, Sam, Jo, and Lee, each own a different pet: cat, dog, bird. Sam does not own the bird. Jo owns the dog. Who owns the cat?"
        ]
        for q in tests:
            r = traiter_question(q)
            print(f"QUESTION: {r['question']}")
            print(f"MODEL: {r['modele_utilise']} (mode: {r['mode']})")
            print(f"ANSWER: {r['reponse'][:250]}...\n")