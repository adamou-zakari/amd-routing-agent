# Hybrid Token-Efficient Routing Agent

Agent intelligent qui route dynamiquement les questions vers le modèle 
Fireworks AI le moins cher et adapté à la tâche, afin de minimiser le 
coût en tokens tout en préservant la précision des réponses.

## Contexte
Développé pour le Track 1 du AMD Developer Hackathon: ACT II.

## Architecture
- `router.py` : détecte le type de tâche (général vs code) et choisit le modèle Fireworks adapté
- `remote/fireworks_client.py` : appelle l'API Fireworks AI
- `models/local_model.py` : modèle local simulé, utilisé uniquement en développement (ne compte pas dans le score)
- `agent.py` : orchestrateur principal, lit `/input/tasks.json` et écrit `/output/results.json`

## Modèles utilisés
- **MiniMax M3** (accounts/fireworks/models/minimax-m3) : tâches générales
- **Kimi K2.7 Code** (accounts/fireworks/models/kimi-k2p7-code) : tâches de code

## Installation

\`\`\`bash
git clone https://github.com/adamou-zakari/amd-routing-agent.git
cd amd-routing-agent
pip install -r requirements.txt
\`\`\`

Crée un fichier `.env` à la racine avec :
\`\`\`
FIREWORKS_API_KEY=ta_clé_ici
FIREWORKS_BASE_URL=https://api.fireworks.ai/inference
ALLOWED_MODELS=accounts/fireworks/models/minimax-m3,accounts/fireworks/models/kimi-k2p7-code
\`\`\`

## Utilisation

\`\`\`bash
python agent.py
\`\`\`

## Tests

\`\`\`bash
python -m pytest tests/
\`\`\`

## Avec Docker

\`\`\`bash
docker build -t amd-routing-agent .
docker run --env-file .env -v ${PWD}/input:/input -v ${PWD}/output:/output amd-routing-agent
\`\`\`