# compter_tokens.py
import os, json, requests, re
from dotenv import load_dotenv
from router import choisir_modele
from remote.fireworks_client import SYSTEM_PROMPT, _contrainte_mots

load_dotenv()
api_key = os.environ["FIREWORKS_API_KEY"]
base_url = os.environ["FIREWORKS_BASE_URL"].rstrip("/")
if base_url.endswith("/v1"):
    base_url = base_url[:-3].rstrip("/")
url = f"{base_url}/v1/chat/completions"
os.environ.setdefault("ALLOWED_MODELS",
    "accounts/fireworks/models/minimax-m3,accounts/fireworks/models/kimi-k2p7-code")

with open("input/tasks.json") as f:
    tasks = json.load(f)

headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
total = 0
print(f"{'TASK':<6}{'MODE':<14}{'MAXTOK':>8}{'TOTAL':>8}")
print("-" * 40)

for t in tasks:
    q = t["prompt"]
    modele, mode = choisir_modele(q)
    limite = _contrainte_mots(q)
    # REPRODUIT ta logique exacte
    mt = 600
    if mode == "raisonnement":
        mt = 1200
    if limite:
        mt = 700
    payload = {"model": modele,
               "messages": [{"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": q}],
               "max_tokens": mt, "temperature": 0}
    r = requests.post(url, headers=headers, json=payload, timeout=90)
    tt = r.json().get("usage", {}).get("total_tokens", 0)
    total += tt
    print(f"{t['task_id']:<6}{mode:<14}{mt:>8}{tt:>8}")

print("-" * 40)
print(f">>> TOTAL (1 appel/tache) : {total} tokens")
print(">>> Rappel : les taches 'raisonnement' font parfois 1 appel suffisant,")
print(">>>          le vrai total AMD sera proche de ce chiffre.")