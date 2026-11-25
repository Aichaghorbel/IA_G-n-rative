# SmartCampus AI — Authentification & autorisations

## 1. Les 4 rôles

| Rôle | Comment il s'identifie | Ce qu'il peut faire |
|---|---|---|
| **Visiteur** (sans compte) | `X-Session-Token` — ou **aucun jeton** : une session est créée automatiquement | Chat libre, catalogue des formations, OTP e-mail |
| **Candidat** | `Authorization: Bearer <access_token>` | Son profil, ses conversations, QCM, recommandations, rendez-vous, notifications |
| **Enseignant** | idem | Lecture des candidats avec lesquels il a un rendez-vous, décisions de préinscription, résultats d'entretien |
| **Administrateur** (responsable, **unique**, créé automatiquement au démarrage) | idem | Accès transverse : comptes, formations, documents RAG, statistiques, supervision |

## 2. Flux

**Visiteur (chat libre)**
1. `POST /api/v1/conversations` sans en-tête → `201`, jeton dans l'en-tête de réponse **`X-Session-Token`** (+ cookie httpOnly).
2. Le front renvoie ce jeton à chaque appel (`X-Session-Token`). Session valide 30 jours glissants, stockée en base, supprimable (`DELETE /sessions/me`, RGPD).
3. Alternative explicite : `POST /auth/sessions/anonymous`.
4. WebSocket : `/api/v1/conversations/ws/chat` (jeton optionnel `?token=`, jeton invalide → fermeture 1008).

**Vérification d'e-mail (OTP)** : `POST /auth/otp/request` → `POST /auth/otp/verify` → `verification_token` (30 min).
Code à 6 chiffres haché, 10 min, 5 essais, usage unique, 1 envoi/min. `dev_code` renvoyé **uniquement** si `DEBUG=True` et hors production.

**Visiteur → Candidat** : `POST /auth/convert` (réservé Enseignant/Administrateur) crée le compte avec un mot de passe temporaire aléatoire ; `must_change_password=true` bloque tout (`AUTH_010`) sauf `/auth/change-password`, `/auth/me`, `/auth/logout`.

**Connexion** : `POST /auth/login` → access (15 min) + refresh (7 j).
`POST /auth/refresh` fait une **rotation** (l'ancien refresh est révoqué ; le rejouer coupe toutes les sessions).
`POST /auth/logout` révoque access + refresh (`all_devices=true` pour tous les appareils).

## 2 bis. Conserver la conversation du visiteur après connexion (SA-29)

| Étape | Appel | Détail |
|---|---|---|
| 1 | `POST /auth/register` (après OTP) **ou** `POST /auth/login` | Envoyer aussi `X-Session-Token`. Si une conversation peut être conservée, la réponse contient `session_link` (proposition). |
| 2 | `GET /auth/session-link/proposal` | `Authorization: Bearer` **+** `X-Session-Token`. Lecture seule : nombre de conversations/messages, aperçu. |
| 3 | `POST /auth/session-link` `{"session_id": "...", "consent": true}` | Association réelle. Refus sans accord (`422 SESSION_LINK_001`). |

Vérifications avant association : accord explicite · jeton de session valide (signature, hash en base, non expiré) ·
`session_id` identique à celui du jeton (`403 SESSION_LINK_003`) · session/visiteur non déjà lié à un autre candidat
(`409 SESSION_LINK_002`). Idempotent (rejouer renvoie `already_linked=true`), transaction unique avec verrou de ligne.
Après association : le candidat retrouve ses conversations (`GET /conversations`) et peut les continuer ;
le jeton visiteur ne les voit plus (`404`). Aucune migration SQL (colonnes `visitor_sessions.candidate_id` et `conversations.candidat_id` déjà présentes).

## 3. Règles de sécurité implémentées

- Jetons **typés** (`access`, `refresh`, `session`, `email_verified`) : un refresh token n'ouvre aucune API.
- Liste noire des `jti` révoqués + `token_version` par utilisateur (changement de mot de passe, désactivation → anciens jetons invalides).
- Rôle relu en base à chaque requête.
- Verrouillage 15 min après 5 échecs de connexion (`423 AUTH_005`) ; même message d'erreur que l'e-mail existe ou non.
- Politique de mot de passe : 8+ caractères, majuscule, minuscule, chiffre.
- `require_roles` : **refus par défaut** — `401` si non authentifié, `403` si rôle insuffisant.
- **Propriété des ressources** (`app/api/ownership.py`) : conversations, recommandations, préinscriptions, rendez-vous, QCM, notifications. Accès à la ressource d'un tiers → `404`.
- Enseignant limité aux candidats liés par un `RendezVous`.
- **Administrateur unique** : créé au démarrage (`INITIAL_ADMIN_EMAIL` / `INITIAL_ADMIN_PASSWORD`) ; `POST /auth/users` ne crée que des enseignants.
- Un candidat ne peut plus s'auto-attribuer le statut de sa préinscription.
- Refus de démarrer en `ENVIRONMENT=production` avec la `SECRET_KEY`/le mot de passe admin par défaut ou `COOKIE_SECURE=False`.
- En-têtes `nosniff`, `X-Frame-Options`, `Cache-Control: no-store` sur `/auth`.

## 4. Codes d'erreur d'authentification

`AUTH_001` jeton expiré · `AUTH_002` jeton invalide/révoqué · `AUTH_003` rôle insuffisant · `AUTH_004` refresh invalide ·
`AUTH_005` compte verrouillé · `AUTH_006` e-mail déjà utilisé · `AUTH_007` OTP invalide · `AUTH_008` trop d'essais OTP ·
`AUTH_009` mot de passe faible · `AUTH_010` changement de mot de passe requis · `AUTH_011` auto-désactivation interdite · `AUTH_012` administrateur unique.

## 5. Mise en route

```bash
# Base existante : appliquer la migration (idempotente)
psql -U smartcampus -d smartcampus -f init-scripts/04-auth-security.sql

cd backend
pip install -r requirements.txt
pytest tests/test_security_roles.py -v
```

Variables : voir `.env.example` (section « Authentification & sécurité »).
Comptes de démo : `admin@smartcampus.tn`, `enseignant.iit@smartcampus.tn`, `sarra.benali@gmail.com`.

## 6. Limites connues

- OTP en mémoire (un seul worker). Pour plusieurs workers : brancher Redis derrière `otp_service`.
- La réponse du chat reste une réponse de démonstration (LLM/RAG à brancher) ; la propriété et l'accès sont, eux, en place.
- Le diagramme de classes UML n'a pas de colonne d'affectation enseignant : l'accès enseignant s'appuie sur `RendezVous.enseignant_id`.
