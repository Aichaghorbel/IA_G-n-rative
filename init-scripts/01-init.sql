-- 1. Activer pgvector (CRITIQUE pour le RAG)
-- pgvector ajoute le type 'vector' pour stocker des embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. pg_trgm = recherche floue (utile pour "trouver candidats dont le nom ressemble à...")
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- 3. uuid-ossp = génère des UUID (pour les sessions visiteurs anonymes)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 4. pgcrypto = hachage (bcrypt-like) et chiffrement
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Utilisateur applicatif (privilèges CRUD seulement)
-- C'est l'utilisateur que le backend FastAPI utilisera
DO $$
BEGIN
    -- Vérifie si l'utilisateur existe déjà (au cas où tu relances le script)
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'smartcampus_app') THEN
        CREATE ROLE smartcampus_app WITH
            LOGIN                          -- peut se connecter
            PASSWORD 'app_password_2026'   -- son mot de passe
            NOSUPERUSER                    -- ⚠️ PAS superuser (sécurité)
            NOCREATEDB                     -- ne peut pas créer de bases
            NOCREATEROLE                   -- ne peut pas créer d'autres users
            NOREPLICATION                  -- ne peut pas répliquer
            CONNECTION LIMIT 50;           -- max 50 connexions simultanées
    END IF;
END
$$;

-- smartcampus_app peut se connecter à la base 'smartcampus'
GRANT CONNECT ON DATABASE smartcampus TO smartcampus_app;

-- Peut utiliser le schéma 'public' (le schéma par défaut)
GRANT USAGE ON SCHEMA public TO smartcampus_app;

-- Donner les privilèges CRUD (Create/Read/Update/Delete) sur TOUTES les tables
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO smartcampus_app;

-- ⚠️ CRITIQUE : les tables créées PLUS TARD auront aussi ces privilèges
-- Sans ALTER DEFAULT PRIVILEGES, les nouvelles tables créées par
-- smartcampus_migrate ne seraient PAS accessibles à smartcampus_app
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO smartcampus_app;