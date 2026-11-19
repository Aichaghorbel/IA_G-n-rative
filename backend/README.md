# 🛠️ SmartCampus AI — Backend Architecture & Developer Guide

Documentation technique dédiée à la conception, aux modèles de données, aux patrons d'architecture logicielle et aux API REST de **SmartCampus AI**.

---

## 📂 Structure du Répertoire Backend

```text
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/            # Contrôleurs FastAPI par domaine métier
│   │       │   ├── admin.py          # Métriques et supervision
│   │       │   ├── appointments.py   # Rendez-vous et entretiens
│   │       │   ├── auth.py           # Authentification JWT, OTP, sessions anonymes
│   │       │   ├── candidates.py     # Gestion des profils de candidature
│   │       │   ├── conversations.py  # Chat contextuel et streaming SSE
│   │       │   ├── documents.py      # Ingestion documentaire et RAG
│   │       │   ├── formations.py     # Catalogue des formations, tarifs, spécialités
│   │       │   ├── notifications.py  # Alertes et notifications utilisateurs
│   │       │   ├── preregistrations.py # Candidatures et préinscriptions
│   │       │   ├── qcm.py            # Tests d'orientation et QCMs adaptatifs
│   │       │   ├── recommendations.py# Algorithme d'affinité académique
│   │       │   └── stats.py          # Statistiques et entonnoir de conversion
│   │       └── api_router.py         # Agrégation de tous les sous-routeurs
│   ├── core/                         # Configuration centrale et infrastructure
│   │   ├── config.py                 # Pydantic Settings & gestion des variables .env
│   │   ├── database.py               # Engine SQLAlchemy, Base et SessionLocal
│   │   ├── exceptions.py             # Exceptions typées et gestionnaires d'erreurs
│   │   └── security.py               # Cryptographie bcrypt, tokens JWT
│   ├── models/                       # Modèles de persistance relationnelle SQLAlchemy
│   │   ├── appointment.py            # RendezVous, Entretien, Notification
│   │   ├── candidate.py              # Visiteur, Candidat, ProfilCandidat
│   │   ├── conversation.py           # Conversation, Message, Reponse (ReponseGeneree)
│   │   ├── document.py               # Document, VersionDocument, TraitementDocument
│   │   ├── enums.py                  # Énumérations officielles du diagramme
│   │   ├── formation.py              # Formation, Tarif, Equivalence, Specialite, ProgrammeEtude, Matiere
│   │   ├── qcm.py                    # Preinscription, QCM, Question, ReponseQuestion
│   │   ├── recommendation.py         # Recommandation
│   │   ├── user.py                   # User (Utilisateur), Enseignant, Responsable
│   │   └── __init__.py               # Réexport unifié conforme au diagramme de classes
│   ├── schemas/                      # Schémas DTO Pydantic V2 (validation entrées/sorties)
│   └── services/                     # Logique métier et cas d'utilisation
├── scripts/
│   └── seed_demo_data.py             # Peuplement initial de la base PostgreSQL
├── tests/
│   ├── conftest.py                   # Fixtures de test pytest et client FastAPI
│   ├── test_api_docs.py              # Tests de Swagger UI et OpenAPI
│   ├── test_auth.py                  # Tests d'authentification et de rôles
│   ├── test_class_diagram_models.py  # Validation stricte du diagramme de classes
│   ├── test_error_handling.py        # Tests du format d'erreur JSON standardisé
│   └── test_formations.py            # Tests du catalogue de cours
├── Dockerfile                        # Image Docker optimisée Python 3.12-slim
├── requirements.txt                  # Dépendances Python
└── .env                              # Variables d'environnement locales
```

---

## 🧩 Patrons de Conception (Design Patterns)

### 1. Single Table Inheritance (STI) — Acteurs du Système
- **Fichier :** `app/models/user.py`
- **Pattern :** Tous les utilisateurs partagent la table PostgreSQL `users`. La colonne `type_user` sert de discriminateur polymorphique pour instancier `User` (`Utilisateur`), `Enseignant`, ou `Responsable`.
- **Avantage :** Authentification unifiée, performance optimale sans jointure, respect strict de la hiérarchie UML.

### 2. DDD Aggregate Pattern — Préinscription & QCM
- **Fichier :** `app/models/qcm.py`
- **Pattern :**
  ```text
  Preinscription (1) ──générer──> (1) QCM (1) ──composer──> (1..*) Question (1) ──composer──> (1..*) ReponseQuestion
  ```
- **Règle stricte du diagramme :** La classe `ReponseQuestion` est liée **uniquement à `Question`** via `question_id`. Aucune clé étrangère directe n'existe vers `QCM`.

### 3. Composite Pattern — Structure Académique
- **Fichier :** `app/models/formation.py`
- **Pattern :**
  ```text
  Formation (1) ──> (1..*) Specialite (1) ──> (1..*) ProgrammeEtude (1) ──> (1..*) Matiere
  ```
- **Avantage :** Permet une navigation descendante intuitive dans le cursus d'un étudiant.

---

## 🌐 Swagger UI & Documentation des API

FastAPI expose automatiquement les interfaces interactives :
- **Swagger UI :** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc :** [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Spécification OpenAPI (JSON) :** [http://localhost:8000/api/v1/openapi.json](http://localhost:8000/api/v1/openapi.json)

---

## 🚀 Exécution & Tests

### Lancement dans Docker Compose
```bash
# Démarrer le backend et ses dépendances (Postgres, Redis, pgAdmin)
docker compose up -d

# Initialiser la base de données de démo
docker compose exec backend python scripts/seed_demo_data.py

# Exécuter les tests unitaires et d'intégration
docker compose exec backend pytest
```

### Lancement en Local (hors Docker)
```bash
# Créer et activer l'environnement virtuel
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux / macOS

# Installer les dépendances
pip install -r requirements.txt

# Initialiser la base
python scripts/seed_demo_data.py

# Démarrer le serveur Uvicorn
uvicorn app.main:app --reload --port 8000
```
