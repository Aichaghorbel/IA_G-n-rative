FROM python:3.12-slim

WORKDIR /app

# Les dépendances Python (psycopg2-binary, bcrypt, uvicorn...) disposent de wheels pré-compilés
# Aucun compilateur C ni libpq système n'est requis
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copie du code source backend
COPY . .

# Exposition du port FastAPI
EXPOSE 8000

# Commande de démarrage par défaut
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
