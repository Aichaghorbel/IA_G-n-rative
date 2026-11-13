# 📘 Guide Complet d'Installation, Configuration et Démarrage — SmartCampus AI

Ce guide détaille l'ensemble des étapes nécessaires pour préparer l'environnement de développement local, configurer les services associés (PostgreSQL + pgvector, MinIO, Redis, Mailpit), initialiser le backend FastAPI, exécuter le frontend Angular et peupler la base avec les données de démonstration.

---

## 1. Prérequis Système

| Composant | Version recommandée | Vérification |
| :--- | :--- | :--- |
| **Python** | 3.11 ou 3.12+ | `python --version` |
| **Node.js** | 18.x ou 20.x | `node --version` |
| **npm** | 9.x ou 10.x | `npm --version` |
| **Docker & Docker Compose** | 24.x+ | `docker compose version` |
| **Git** | 2.x+ | `git --version` |

---

## 2. Architecture des Services Locaux & Ports

| Service | Port Local | Description | Interface / Accès |
| :--- | :---: | :--- | :--- |
| **Backend FastAPI** | `8000` | API REST, WebSocket, Casbin RBAC, LangGraph | `http://localhost:8000/docs` |
| **Frontend Angular** | `4200` | Application Web (Proxy `/api` -> `8000`) | `http://localhost:4200` |
| **PostgreSQL + pgvector** | `5432` | Base de données relationnelle + recherche vectorielle | `localhost:5432` |
| **MinIO S3 API** | `9000` | Stockage objet pour documents PDF et audio | `localhost:9000` |
| **MinIO Web Console** | `9001` | Interface graphique de gestion des buckets | `http://localhost:9001` |
| **Redis** | `6379` | Cache de session et rate limiting | `localhost:6379` |
| **Mailpit (Web UI)** | `8025` | Boîte de réception locale pour les OTP et relances | `http://localhost:8025` |
| **Mailpit (SMTP)** | `1025` | Serveur SMTP pour FastAPI | `localhost:1025` |

---

## 3. Configuration des Variables d'Environnement

Un fichier `.env.example` est fourni à la racine et dans le dossier `backend/`.

Copiez le fichier d'exemple pour créer votre configuration locale :
```bash
cp backend/.env.example backend/.env
```

### Paramètres principaux dans `backend/.env` :
```env
# Mode et Débogage
ENVIRONMENT=development
DEBUG=True
APP_NAME="SmartCampus AI"
API_V1_STR="/api/v1"

# Base de données
# Option A : SQLite local sans Docker (actif par défaut)
DATABASE_URL=sqlite:///./smartcampus.db
# Option B : PostgreSQL Docker avec pgvector
# DATABASE_URL=postgresql+psycopg2://smartcampus:smartcampus_password@localhost:5432/smartcampus

# Stockage MinIO S3
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin_secret
MINIO_BUCKET_DOCS=smartcampus-docs
MINIO_BUCKET_AUDIO=smartcampus-audio

# Sécurité & Tokens JWT (Conformes Section 6.4)
SECRET_KEY=smartcampus-super-secret-key-change-me-in-production-2026!
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
VISITOR_SESSION_EXPIRE_DAYS=30

# CORS
CORS_ORIGINS=["http://localhost:4200","http://127.0.0.1:4200","http://localhost:8000"]

# IA & LLM (Qwen2.5 / OpenAI compatible / Ollama)
LLM_PROVIDER=openai_compatible
LLM_API_BASE=http://localhost:11434/v1
LLM_MODEL=qwen2.5-7b-instruct
WHISPER_MODEL=base

# Email SMTP (Mailpit local)
SMTP_HOST=localhost
SMTP_PORT=1025
EMAILS_FROM_EMAIL=contact@smartcampus.tn
```

---

## 4. Démarrage des Services d'Infrastructure (Docker)

Lancez les conteneurs PostgreSQL (avec extension pgvector), MinIO, Redis et Mailpit en arrière-plan :
```bash
docker compose up -d postgres redis minio mailpit
```

Vérifiez l'état des conteneurs :
```bash
docker compose ps
```

Pour consulter la console MinIO :
- Rendez-vous sur `http://localhost:9001`
- Identifiant : `minioadmin` / Mot de passe : `minioadmin_secret`

Pour consulter les emails de test et codes OTP envoyés :
- Rendez-vous sur `http://localhost:8025` (Mailpit)

---

## 5. Initialisation et Démarrage du Backend (FastAPI)

### 5.1 Création et activation de l'environnement virtuel Python
```bash
# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### 5.2 Installation des dépendances
```bash
cd backend
pip install -r requirements.txt
```

### 5.3 Injection des Données de Démonstration (Seed)
Le script `seed_demo_data.py` crée automatiquement :
- Les formations de référence de l'IIT et de l'ISB
- Les comptes utilisateurs pour chaque rôle (Admin unifié, Enseignants IIT/ISB, Candidats)
- Des profils candidats types avec dossiers, préinscriptions, QCM et rendez-vous
- L'indexation initiale des documents RAG depuis `backend/data/sample_corpus/`

Exécutez :
```bash
python scripts/seed_demo_data.py
```

### 5.4 Démarrage du Serveur FastAPI
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Le serveur démarre avec rechargement automatique à chaque modification de code.

---

## 6. Documentation Automatique des API

Une fois le backend démarré, la documentation interactive est générée automatiquement à partir du code, des schémas Pydantic et des règles d'accès Casbin :

1. **Swagger UI interactive** : [http://localhost:8000/docs](http://localhost:8000/docs)
   - Permet de tester directement toutes les routes depuis le navigateur.
   - Bouton **Authorize** en haut à droite pour renseigner le token JWT (`Bearer <access_token>`) ou le jeton de session (`X-Session-Token`).
2. **ReDoc (Vue technique détaillée)** : [http://localhost:8000/redoc](http://localhost:8000/redoc)
3. **Schéma brut OpenAPI 3.1 (JSON)** : [http://localhost:8000/api/v1/openapi.json](http://localhost:8000/api/v1/openapi.json)

---

## 7. Configuration et Démarrage du Frontend (Angular)

### 7.1 Configuration du Proxy
Le fichier `frontend/proxy.conf.json` redirige automatiquement les appels relatifs `/api` et `/ws` vers le serveur FastAPI local (`http://localhost:8000`), évitant ainsi les problèmes de CORS en développement local.

### 7.2 Installation et Lancement
```bash
cd frontend
npm install
npm start
```
L'application web sera disponible sur : **http://localhost:4200**

---

## 8. Comptes de Test et Données de Démonstration

| Rôle | Email | Mot de passe | Description & Droits |
| :--- | :--- | :--- | :--- |
| **Admin unifié (A)** | `admin@smartcampus.tn` | `AdminSmartCampus2026!` | Accès total IIT & ISB, documents RAG, validation affectations, supervision IA |
| **Enseignant IIT (E)** | `enseignant.iit@smartcampus.tn` | `TeacherPassword2026!` | Responsable entretien IIT, consultation des candidats affectés, saisie d'entretien |
| **Enseignant ISB (E)** | `enseignant.isb@smartcampus.tn` | `TeacherPassword2026!` | Responsable entretien ISB, gestion des dossiers Business Analytics |
| **Candidat (C)** | `sarra.benali@gmail.com` | `CandidatePassword2026!` | Dossier préinscrit, QCM passé, entretien planifié avec l'IIT |
| **Candidat (C)** | `youssef.trabelsi@gmail.com` | `CandidatePassword2026!` | Profil enrichi, orienté vers la Licence Business Analytics de l'ISB |

---

## 9. Nomenclature des Erreurs et Codes Métier

Toute réponse d'erreur (4xx et 5xx) retourne le schéma JSON standardisé :
```json
{
  "error": {
    "code": "AUTH_INVALID_CREDENTIALS",
    "message": "Email ou mot de passe incorrect",
    "details": { "field": "email" },
    "timestamp": "2026-10-27T14:30:00Z",
    "request_id": "req_abc123"
  }
}
```

### Principaux codes métier configurés :
- `AUTH_001` (401) : Jeton d'accès expiré (déclenche le refresh token côté Angular)
- `AUTH_002` (401) : Jeton invalide
- `AUTH_003` (403) : Rôle insuffisant (violation des règles Casbin)
- `CANDIDATE_001` (409) : Transition de statut de dossier interdite
- `CANDIDATE_002` (422) : Consentement explicite RGPD manquant
- `CANDIDATE_003` (403) : Enseignant tentant d'accéder à un candidat non affecté
- `DOC_001` (415) : Document PDF corrompu ou type MIME non autorisé
- `DOC_002` (409) : Document déjà indexé (détecté via empreinte SHA-256)
- `RATE_LIMIT_EXCEEDED` (429) : Trop de requêtes par minute (en-tête `Retry-After`)

---

## 10. Exécution des Tests Automatisés

Pour valider le bon fonctionnement de la plateforme en local :
```bash
python backend/tests/run_tests.py
```
Ce script exécute une suite de tests complète couvrant :
- L'authentification et les sessions anonymes
- Les permissions RBAC (Casbin)
- La machine à états des candidats (transitions autorisées et interdites)
- La conformité RGPD
- La détection de langues (français, tunisien, Arabizi)
- L'anti-doublon SHA-256 des documents RAG
- L'admissibilité du schéma OpenAPI
