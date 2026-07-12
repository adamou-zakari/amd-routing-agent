# Hybrid Token-Efficient Routing Agent

**AMD Developer Hackathon: ACT II — Track 1** · Team: Adam dev teams

An autonomous agent that routes each task to the cheapest Fireworks AI model capable of answering it correctly — minimizing token usage while holding **100% accuracy** on the evaluation set.

## Results

| Metric | Value |
|---|---|
| **Accuracy** | **100.0%** (19/19 tasks) |
| **Tokens** | 10,670 |
| Image size | 47 MB (linux/amd64) |
| Local validation | 16/16 on a custom adversarial test suite |

## Architecture

**1. Zero-cost local classification** (`router.py`)
Each task is classified *locally* — no extra API call, no extra tokens — into one of three routes:

| Route | Model | Task types |
|---|---|---|
| `code` | **Kimi K2.7 Code** | code generation, debugging |
| `raisonnement` | **MiniMax M3** (extended budget) | multi-step math, logic puzzles |
| `standard` | **MiniMax M3** | facts, sentiment, NER, summaries |

Model IDs are read from `ALLOWED_MODELS` at runtime — nothing hardcoded, per hackathon rules.

**2. Robust answer post-processing** (`remote/fireworks_client.py`)
Reasoning models are powerful but noisy. Our pipeline handles this:
- Strips `<think>` blocks, markdown fences, and preambles ("Here are…")
- Extracts raw code from fenced blocks for code tasks
- Enforces exact word-count constraints on summaries (prevents the model's counting loops)
- Normalizes NER output to clean `Entity: Type` lines
- Recovers gracefully when a reasoning model exhausts its budget before answering

**3. Reliability engineering**
- Automatic retry on empty responses (budget escalation) and transient network errors
- Base-URL normalization (tolerates `/v1` with or without trailing slash)
- 30s per-request timeout, well within grading constraints (2 vCPU / 4 GB RAM)

## Engineering methodology

We built a **token profiler** (`compter_tokens.py`) to measure per-task cost instead of guessing. It revealed that a single word-constrained summary was consuming **4,298 tokens** (41% of the total budget) due to the model's internal counting loop — a bug invisible without measurement. Capping that path cut the waste while preserving correctness.

We iterated with a strict protocol: **measure → change one variable → validate 16/16 locally → deploy → compare**. Configurations that reduced accuracy were rolled back immediately using a tagged safety image (`:v100-safe`).

## Compliance

- ✅ 100% of inference goes through the **Fireworks AI API** (`FIREWORKS_BASE_URL`) — no external routing, no local models, no hardcoded answers
- ✅ Reads `/input/tasks.json`, writes `/output/results.json` (standard schema)
- ✅ All credentials injected at runtime — no secrets in the image (`.env` excluded via `.dockerignore`)
- ✅ Deterministic (`temperature = 0`)

## Run it

```bash
docker pull adamou1/amd-routing-agent:latest

docker run --rm \
  -v ./input:/input -v ./output:/output \
  -e FIREWORKS_API_KEY=<key> \
  -e FIREWORKS_BASE_URL=https://api.fireworks.ai/inference \
  -e ALLOWED_MODELS=<comma-separated model ids> \
  adamou1/amd-routing-agent:latest
```

## Team

- **Adamou Zakari Issaka**
- **Alkassoum Mohamed Sallah**

Built in Niamey, Niger 🇳🇪