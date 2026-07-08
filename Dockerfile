FROM python:3.10-slim

WORKDIR /app

# Copier et installer les dépendances (léger maintenant, plus de torch)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier tout le code
COPY . .

CMD ["python", "agent.py"]