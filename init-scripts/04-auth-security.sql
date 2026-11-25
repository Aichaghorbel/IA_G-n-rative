-- ============================================================================
-- SmartCampus AI — Authentification & autorisations
-- Idempotent : peut être rejoué sur une base existante (create_all n'altère pas les tables).
-- ============================================================================

-- 1. Colonnes de sécurité sur users
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS is_active boolean NOT NULL DEFAULT true;
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS token_version integer NOT NULL DEFAULT 0;
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS failed_login_attempts integer NOT NULL DEFAULT 0;
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS locked_until timestamp without time zone;
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS must_change_password boolean NOT NULL DEFAULT false;
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS last_login_at timestamp without time zone;

-- 1 bis. Colonnes additionnelles sur formations / tarifs & compatibilité colonnes héritées
ALTER TABLE public.formations ADD COLUMN IF NOT EXISTS statut_publication character varying(50) NOT NULL DEFAULT 'publie';
ALTER TABLE public.formations ADD COLUMN IF NOT EXISTS date_debut_validite date;
ALTER TABLE public.formations ADD COLUMN IF NOT EXISTS date_fin_validite date;
ALTER TABLE public.tarifs ADD COLUMN IF NOT EXISTS modalites_paiement character varying(500);

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'candidats' AND column_name = 'statut_dossier'
    ) THEN
        ALTER TABLE public.candidats ALTER COLUMN statut_dossier SET DEFAULT 'EXPLORATION';
        ALTER TABLE public.candidats ALTER COLUMN statut_dossier DROP NOT NULL;
    END IF;
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'messages' AND column_name = 'role'
    ) THEN
        ALTER TABLE public.messages ALTER COLUMN role SET DEFAULT 'user';
        ALTER TABLE public.messages ALTER COLUMN role DROP NOT NULL;
    END IF;
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'recommendations' AND column_name = 'formation_id'
    ) THEN
        ALTER TABLE public.recommendations ALTER COLUMN formation_id DROP NOT NULL;
    END IF;
END $$;

-- 2. Jetons révoqués (déconnexion, rotation des refresh tokens)
CREATE TABLE IF NOT EXISTS public.revoked_tokens (
    jti        character varying(64) PRIMARY KEY,
    expires_at timestamp without time zone NOT NULL,
    revoked_at timestamp without time zone NOT NULL DEFAULT (now() at time zone 'utc')
);
CREATE INDEX IF NOT EXISTS ix_revoked_tokens_expires_at ON public.revoked_tokens (expires_at);

-- 3. Sessions visiteurs (chat sans compte)
CREATE TABLE IF NOT EXISTS public.visitor_sessions (
    id                 uuid PRIMARY KEY,
    token_hash         character varying(64) NOT NULL UNIQUE,
    created_at         timestamp without time zone NOT NULL,
    last_seen_at       timestamp without time zone NOT NULL,
    expires_at         timestamp without time zone NOT NULL,
    profile            jsonb NOT NULL DEFAULT '{}'::jsonb,
    candidate_id       integer REFERENCES public.candidats(id) ON DELETE SET NULL,
    ip_hash            character varying(64),
    user_message_count integer NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS ix_visitor_sessions_last_seen_at ON public.visitor_sessions (last_seen_at);
CREATE INDEX IF NOT EXISTS ix_visitor_sessions_expires_at ON public.visitor_sessions (expires_at);
CREATE INDEX IF NOT EXISTS ix_visitor_sessions_ip_hash ON public.visitor_sessions (ip_hash);

CREATE TABLE IF NOT EXISTS public.conversation_messages (
    id         bigserial PRIMARY KEY,
    session_id uuid NOT NULL REFERENCES public.visitor_sessions(id) ON DELETE CASCADE,
    role       character varying(16) NOT NULL CHECK (role IN ('user', 'assistant')),
    content    text NOT NULL,
    created_at timestamp without time zone NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_conv_messages_session_id_id ON public.conversation_messages (session_id, id);
