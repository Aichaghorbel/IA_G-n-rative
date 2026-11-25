--
-- PostgreSQL database dump
--

\restrict 50fOiO7hmFiHF8bjAsfTZdAmr7qGutGgLgtZmBvJhmtvi0HK5XKDupWMdgfLPSc

-- Dumped from database version 16.16 (Debian 16.16-1.pgdg12+1)
-- Dumped by pg_dump version 16.16 (Debian 16.16-1.pgdg12+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: public; Type: SCHEMA; Schema: -; Owner: -
--

-- *not* creating schema, since initdb creates it


--
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON SCHEMA public IS '';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: candidats; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.candidats (
    id integer NOT NULL,
    "CIN" character varying(50),
    passport character varying(50),
    pays character varying(100),
    "dateNaissance" date,
    sexe character varying(20),
    adresse character varying(255),
    universite character varying(50),
    visiteur_id integer,
    user_id integer
);


--
-- Name: candidats_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.candidats_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: candidats_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.candidats_id_seq OWNED BY public.candidats.id;


--
-- Name: conversations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.conversations (
    "idConversation" integer NOT NULL,
    titre character varying(200),
    "estFavori" boolean,
    "dateDernierModification" timestamp without time zone,
    visiteur_id integer,
    candidat_id integer,
    enseignant_id integer
);


--
-- Name: conversations_idConversation_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public."conversations_idConversation_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: conversations_idConversation_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public."conversations_idConversation_seq" OWNED BY public.conversations."idConversation";


--
-- Name: documents; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.documents (
    id integer NOT NULL,
    nom character varying(255) NOT NULL,
    description character varying(1000),
    categorie character varying(50) NOT NULL,
    responsable_id integer
);


--
-- Name: documents_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.documents_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: documents_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.documents_id_seq OWNED BY public.documents.id;


--
-- Name: entretiens; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.entretiens (
    id integer NOT NULL,
    "avisEnseignant" character varying(50),
    notes character varying(2000),
    "oriantationFinale" character varying(100),
    staut character varying(50) NOT NULL,
    rendezvous_id integer NOT NULL,
    enseignant_id integer
);


--
-- Name: entretiens_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.entretiens_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: entretiens_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.entretiens_id_seq OWNED BY public.entretiens.id;


--
-- Name: equivalences; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.equivalences (
    id integer NOT NULL,
    desciption character varying(1000),
    conditions character varying(1000),
    "formation_Origine" character varying(50) NOT NULL,
    formation_id integer NOT NULL
);


--
-- Name: equivalences_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.equivalences_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: equivalences_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.equivalences_id_seq OWNED BY public.equivalences.id;


--
-- Name: formation_candidat; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.formation_candidat (
    formation_id integer NOT NULL,
    candidat_id integer NOT NULL
);


--
-- Name: formations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.formations (
    id integer NOT NULL,
    nom character varying(200) NOT NULL,
    universite character varying(50) NOT NULL,
    description character varying(1000) NOT NULL,
    objectif character varying(1000),
    duree integer,
    debouches character varying(1000),
    "conditionsAdmission" character varying(1000),
    prerequis character varying(1000)
);


--
-- Name: formations_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.formations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: formations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.formations_id_seq OWNED BY public.formations.id;


--
-- Name: matieres; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.matieres (
    id integer NOT NULL,
    nom character varying(100) NOT NULL,
    description character varying(1000),
    coefficient integer NOT NULL,
    "volumeHoraire" integer NOT NULL,
    programme_id integer NOT NULL
);


--
-- Name: matieres_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.matieres_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: matieres_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.matieres_id_seq OWNED BY public.matieres.id;


--
-- Name: messages; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.messages (
    "idMessage" integer NOT NULL,
    contenu character varying(2000) NOT NULL,
    "dateEnvoi" timestamp without time zone,
    conversation_id integer NOT NULL
);


--
-- Name: messages_idMessage_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public."messages_idMessage_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: messages_idMessage_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public."messages_idMessage_seq" OWNED BY public.messages."idMessage";


--
-- Name: notifications; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.notifications (
    id integer NOT NULL,
    type character varying(50) NOT NULL,
    contenu character varying(1000) NOT NULL,
    "dateEnvoi" timestamp without time zone,
    envoyee boolean NOT NULL,
    user_id integer NOT NULL
);


--
-- Name: notifications_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.notifications_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: notifications_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.notifications_id_seq OWNED BY public.notifications.id;


--
-- Name: preinscriptions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.preinscriptions (
    id integer NOT NULL,
    "dateCreation" date,
    statut character varying(50) NOT NULL,
    candidat_id integer NOT NULL,
    formation_id integer NOT NULL
);


--
-- Name: preinscriptions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.preinscriptions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: preinscriptions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.preinscriptions_id_seq OWNED BY public.preinscriptions.id;


--
-- Name: profils_candidat; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.profils_candidat (
    id integer NOT NULL,
    candidat_id integer NOT NULL,
    "dernierDiplomeObtenu" character varying(50),
    "annéeObtention" character varying(20),
    "diplomeSouhaite" character varying(100),
    niveau integer,
    cours character varying(50),
    "sourceConnaissanceUniversité" character varying(50)
);


--
-- Name: profils_candidat_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.profils_candidat_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: profils_candidat_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.profils_candidat_id_seq OWNED BY public.profils_candidat.id;


--
-- Name: programmes_etude; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.programmes_etude (
    id integer NOT NULL,
    nom character varying(100) NOT NULL,
    description character varying(1000),
    semestre integer NOT NULL,
    specialite_id integer NOT NULL
);


--
-- Name: programmes_etude_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.programmes_etude_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: programmes_etude_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.programmes_etude_id_seq OWNED BY public.programmes_etude.id;


--
-- Name: qcms; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.qcms (
    id integer NOT NULL,
    score double precision,
    "datePassation" date,
    niveau character varying(50),
    preinscription_id integer NOT NULL
);


--
-- Name: qcms_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.qcms_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: qcms_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.qcms_id_seq OWNED BY public.qcms.id;


--
-- Name: questions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.questions (
    id integer NOT NULL,
    contenu character varying(1000) NOT NULL,
    "correctReponse" integer,
    niveau character varying(50) NOT NULL,
    categorie character varying(50) NOT NULL,
    qcm_id integer NOT NULL
);


--
-- Name: questions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.questions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: questions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.questions_id_seq OWNED BY public.questions.id;


--
-- Name: recommendations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.recommendations (
    id integer NOT NULL,
    nom character varying(200),
    "scoreComptabilite" double precision NOT NULL,
    justification character varying(2000) NOT NULL,
    "dateGeneration" timestamp without time zone,
    statut character varying(50) NOT NULL,
    candidat_id integer NOT NULL,
    formation_id integer NOT NULL
);


--
-- Name: recommendations_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.recommendations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: recommendations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.recommendations_id_seq OWNED BY public.recommendations.id;


--
-- Name: rendezvous; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.rendezvous (
    id integer NOT NULL,
    "dateHeure" timestamp without time zone,
    statut character varying(50) NOT NULL,
    "salleOuLien" character varying(255),
    responsable_id integer,
    enseignant_id integer,
    candidat_id integer NOT NULL
);


--
-- Name: rendezvous_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.rendezvous_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: rendezvous_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.rendezvous_id_seq OWNED BY public.rendezvous.id;


--
-- Name: reponses; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.reponses (
    id integer NOT NULL,
    contenu character varying(2000) NOT NULL,
    date timestamp without time zone,
    source character varying(500),
    message_id integer NOT NULL
);


--
-- Name: reponses_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.reponses_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: reponses_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.reponses_id_seq OWNED BY public.reponses.id;


--
-- Name: reponses_question; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.reponses_question (
    id integer NOT NULL,
    "estSélectionné" boolean NOT NULL,
    question_id integer NOT NULL
);


--
-- Name: reponses_question_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.reponses_question_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: reponses_question_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.reponses_question_id_seq OWNED BY public.reponses_question.id;


--
-- Name: specialites; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.specialites (
    id integer NOT NULL,
    nom character varying(100) NOT NULL,
    description character varying(1000),
    formation_id integer NOT NULL
);


--
-- Name: specialites_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.specialites_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: specialites_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.specialites_id_seq OWNED BY public.specialites.id;


--
-- Name: tarifs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tarifs (
    id integer NOT NULL,
    "montant/9mois" double precision NOT NULL,
    type character varying(50) NOT NULL,
    "Annee" character varying(50) NOT NULL,
    devise character varying(10) NOT NULL,
    formation_id integer NOT NULL
);


--
-- Name: tarifs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.tarifs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: tarifs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.tarifs_id_seq OWNED BY public.tarifs.id;


--
-- Name: traitement_documents; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.traitement_documents (
    id integer NOT NULL,
    type character varying(50) NOT NULL,
    date date,
    statut character varying(50) NOT NULL,
    document_id integer NOT NULL
);


--
-- Name: traitement_documents_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.traitement_documents_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: traitement_documents_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.traitement_documents_id_seq OWNED BY public.traitement_documents.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    id integer NOT NULL,
    nom character varying(100) NOT NULL,
    prenom character varying(100) NOT NULL,
    email character varying(255) NOT NULL,
    "motDePasse" character varying(255) NOT NULL,
    telephone character varying(30),
    type_user character varying(50) NOT NULL,
    departement character varying(100),
    "gradAcademique" character varying(100),
    specialite character varying(100),
    universite character varying(50)
);


--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: version_documents; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.version_documents (
    id integer NOT NULL,
    "nomFichier" character varying(255) NOT NULL,
    "cheminFichier" character varying(500) NOT NULL,
    taille double precision NOT NULL,
    "dateAjout" date,
    document_id integer NOT NULL
);


--
-- Name: version_documents_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.version_documents_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: version_documents_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.version_documents_id_seq OWNED BY public.version_documents.id;


--
-- Name: visiteurs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.visiteurs (
    id integer NOT NULL,
    "sessionToken" character varying(255) NOT NULL,
    ip_address character varying(50),
    "dateVisite" date
);


--
-- Name: visiteurs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.visiteurs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: visiteurs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.visiteurs_id_seq OWNED BY public.visiteurs.id;


--
-- Name: candidats id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.candidats ALTER COLUMN id SET DEFAULT nextval('public.candidats_id_seq'::regclass);


--
-- Name: conversations idConversation; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversations ALTER COLUMN "idConversation" SET DEFAULT nextval('public."conversations_idConversation_seq"'::regclass);


--
-- Name: documents id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documents ALTER COLUMN id SET DEFAULT nextval('public.documents_id_seq'::regclass);


--
-- Name: entretiens id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entretiens ALTER COLUMN id SET DEFAULT nextval('public.entretiens_id_seq'::regclass);


--
-- Name: equivalences id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.equivalences ALTER COLUMN id SET DEFAULT nextval('public.equivalences_id_seq'::regclass);


--
-- Name: formations id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.formations ALTER COLUMN id SET DEFAULT nextval('public.formations_id_seq'::regclass);


--
-- Name: matieres id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.matieres ALTER COLUMN id SET DEFAULT nextval('public.matieres_id_seq'::regclass);


--
-- Name: messages idMessage; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.messages ALTER COLUMN "idMessage" SET DEFAULT nextval('public."messages_idMessage_seq"'::regclass);


--
-- Name: notifications id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notifications ALTER COLUMN id SET DEFAULT nextval('public.notifications_id_seq'::regclass);


--
-- Name: preinscriptions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.preinscriptions ALTER COLUMN id SET DEFAULT nextval('public.preinscriptions_id_seq'::regclass);


--
-- Name: profils_candidat id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.profils_candidat ALTER COLUMN id SET DEFAULT nextval('public.profils_candidat_id_seq'::regclass);


--
-- Name: programmes_etude id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.programmes_etude ALTER COLUMN id SET DEFAULT nextval('public.programmes_etude_id_seq'::regclass);


--
-- Name: qcms id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.qcms ALTER COLUMN id SET DEFAULT nextval('public.qcms_id_seq'::regclass);


--
-- Name: questions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.questions ALTER COLUMN id SET DEFAULT nextval('public.questions_id_seq'::regclass);


--
-- Name: recommendations id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.recommendations ALTER COLUMN id SET DEFAULT nextval('public.recommendations_id_seq'::regclass);


--
-- Name: rendezvous id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rendezvous ALTER COLUMN id SET DEFAULT nextval('public.rendezvous_id_seq'::regclass);


--
-- Name: reponses id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reponses ALTER COLUMN id SET DEFAULT nextval('public.reponses_id_seq'::regclass);


--
-- Name: reponses_question id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reponses_question ALTER COLUMN id SET DEFAULT nextval('public.reponses_question_id_seq'::regclass);


--
-- Name: specialites id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.specialites ALTER COLUMN id SET DEFAULT nextval('public.specialites_id_seq'::regclass);


--
-- Name: tarifs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tarifs ALTER COLUMN id SET DEFAULT nextval('public.tarifs_id_seq'::regclass);


--
-- Name: traitement_documents id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.traitement_documents ALTER COLUMN id SET DEFAULT nextval('public.traitement_documents_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Name: version_documents id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.version_documents ALTER COLUMN id SET DEFAULT nextval('public.version_documents_id_seq'::regclass);


--
-- Name: visiteurs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.visiteurs ALTER COLUMN id SET DEFAULT nextval('public.visiteurs_id_seq'::regclass);


--
-- Name: candidats candidats_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.candidats
    ADD CONSTRAINT candidats_pkey PRIMARY KEY (id);


--
-- Name: conversations conversations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversations
    ADD CONSTRAINT conversations_pkey PRIMARY KEY ("idConversation");


--
-- Name: documents documents_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documents
    ADD CONSTRAINT documents_pkey PRIMARY KEY (id);


--
-- Name: entretiens entretiens_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entretiens
    ADD CONSTRAINT entretiens_pkey PRIMARY KEY (id);


--
-- Name: equivalences equivalences_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.equivalences
    ADD CONSTRAINT equivalences_pkey PRIMARY KEY (id);


--
-- Name: formation_candidat formation_candidat_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.formation_candidat
    ADD CONSTRAINT formation_candidat_pkey PRIMARY KEY (formation_id, candidat_id);


--
-- Name: formations formations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.formations
    ADD CONSTRAINT formations_pkey PRIMARY KEY (id);


--
-- Name: matieres matieres_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.matieres
    ADD CONSTRAINT matieres_pkey PRIMARY KEY (id);


--
-- Name: messages messages_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT messages_pkey PRIMARY KEY ("idMessage");


--
-- Name: notifications notifications_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT notifications_pkey PRIMARY KEY (id);


--
-- Name: preinscriptions preinscriptions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.preinscriptions
    ADD CONSTRAINT preinscriptions_pkey PRIMARY KEY (id);


--
-- Name: profils_candidat profils_candidat_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.profils_candidat
    ADD CONSTRAINT profils_candidat_pkey PRIMARY KEY (id);


--
-- Name: programmes_etude programmes_etude_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.programmes_etude
    ADD CONSTRAINT programmes_etude_pkey PRIMARY KEY (id);


--
-- Name: qcms qcms_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.qcms
    ADD CONSTRAINT qcms_pkey PRIMARY KEY (id);


--
-- Name: questions questions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.questions
    ADD CONSTRAINT questions_pkey PRIMARY KEY (id);


--
-- Name: recommendations recommendations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.recommendations
    ADD CONSTRAINT recommendations_pkey PRIMARY KEY (id);


--
-- Name: rendezvous rendezvous_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rendezvous
    ADD CONSTRAINT rendezvous_pkey PRIMARY KEY (id);


--
-- Name: reponses reponses_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reponses
    ADD CONSTRAINT reponses_pkey PRIMARY KEY (id);


--
-- Name: reponses_question reponses_question_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reponses_question
    ADD CONSTRAINT reponses_question_pkey PRIMARY KEY (id);


--
-- Name: specialites specialites_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.specialites
    ADD CONSTRAINT specialites_pkey PRIMARY KEY (id);


--
-- Name: tarifs tarifs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tarifs
    ADD CONSTRAINT tarifs_pkey PRIMARY KEY (id);


--
-- Name: traitement_documents traitement_documents_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.traitement_documents
    ADD CONSTRAINT traitement_documents_pkey PRIMARY KEY (id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: version_documents version_documents_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.version_documents
    ADD CONSTRAINT version_documents_pkey PRIMARY KEY (id);


--
-- Name: visiteurs visiteurs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.visiteurs
    ADD CONSTRAINT visiteurs_pkey PRIMARY KEY (id);


--
-- Name: ix_candidats_CIN; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_candidats_CIN" ON public.candidats USING btree ("CIN");


--
-- Name: ix_candidats_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_candidats_id ON public.candidats USING btree (id);


--
-- Name: ix_candidats_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_candidats_user_id ON public.candidats USING btree (user_id);


--
-- Name: ix_candidats_visiteur_id; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_candidats_visiteur_id ON public.candidats USING btree (visiteur_id);


--
-- Name: ix_conversations_candidat_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_conversations_candidat_id ON public.conversations USING btree (candidat_id);


--
-- Name: ix_conversations_enseignant_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_conversations_enseignant_id ON public.conversations USING btree (enseignant_id);


--
-- Name: ix_conversations_idConversation; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_conversations_idConversation" ON public.conversations USING btree ("idConversation");


--
-- Name: ix_conversations_visiteur_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_conversations_visiteur_id ON public.conversations USING btree (visiteur_id);


--
-- Name: ix_documents_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_documents_id ON public.documents USING btree (id);


--
-- Name: ix_documents_responsable_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_documents_responsable_id ON public.documents USING btree (responsable_id);


--
-- Name: ix_entretiens_enseignant_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_entretiens_enseignant_id ON public.entretiens USING btree (enseignant_id);


--
-- Name: ix_entretiens_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_entretiens_id ON public.entretiens USING btree (id);


--
-- Name: ix_entretiens_rendezvous_id; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_entretiens_rendezvous_id ON public.entretiens USING btree (rendezvous_id);


--
-- Name: ix_equivalences_formation_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_equivalences_formation_id ON public.equivalences USING btree (formation_id);


--
-- Name: ix_equivalences_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_equivalences_id ON public.equivalences USING btree (id);


--
-- Name: ix_formations_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_formations_id ON public.formations USING btree (id);


--
-- Name: ix_matieres_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_matieres_id ON public.matieres USING btree (id);


--
-- Name: ix_matieres_programme_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_matieres_programme_id ON public.matieres USING btree (programme_id);


--
-- Name: ix_messages_conversation_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_messages_conversation_id ON public.messages USING btree (conversation_id);


--
-- Name: ix_messages_idMessage; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_messages_idMessage" ON public.messages USING btree ("idMessage");


--
-- Name: ix_notifications_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_notifications_id ON public.notifications USING btree (id);


--
-- Name: ix_notifications_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_notifications_user_id ON public.notifications USING btree (user_id);


--
-- Name: ix_preinscriptions_candidat_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_preinscriptions_candidat_id ON public.preinscriptions USING btree (candidat_id);


--
-- Name: ix_preinscriptions_formation_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_preinscriptions_formation_id ON public.preinscriptions USING btree (formation_id);


--
-- Name: ix_preinscriptions_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_preinscriptions_id ON public.preinscriptions USING btree (id);


--
-- Name: ix_profils_candidat_candidat_id; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_profils_candidat_candidat_id ON public.profils_candidat USING btree (candidat_id);


--
-- Name: ix_profils_candidat_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_profils_candidat_id ON public.profils_candidat USING btree (id);


--
-- Name: ix_programmes_etude_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_programmes_etude_id ON public.programmes_etude USING btree (id);


--
-- Name: ix_programmes_etude_specialite_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_programmes_etude_specialite_id ON public.programmes_etude USING btree (specialite_id);


--
-- Name: ix_qcms_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_qcms_id ON public.qcms USING btree (id);


--
-- Name: ix_qcms_preinscription_id; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_qcms_preinscription_id ON public.qcms USING btree (preinscription_id);


--
-- Name: ix_questions_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_questions_id ON public.questions USING btree (id);


--
-- Name: ix_questions_qcm_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_questions_qcm_id ON public.questions USING btree (qcm_id);


--
-- Name: ix_recommendations_candidat_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_recommendations_candidat_id ON public.recommendations USING btree (candidat_id);


--
-- Name: ix_recommendations_formation_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_recommendations_formation_id ON public.recommendations USING btree (formation_id);


--
-- Name: ix_recommendations_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_recommendations_id ON public.recommendations USING btree (id);


--
-- Name: ix_rendezvous_candidat_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_rendezvous_candidat_id ON public.rendezvous USING btree (candidat_id);


--
-- Name: ix_rendezvous_enseignant_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_rendezvous_enseignant_id ON public.rendezvous USING btree (enseignant_id);


--
-- Name: ix_rendezvous_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_rendezvous_id ON public.rendezvous USING btree (id);


--
-- Name: ix_rendezvous_responsable_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_rendezvous_responsable_id ON public.rendezvous USING btree (responsable_id);


--
-- Name: ix_reponses_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_reponses_id ON public.reponses USING btree (id);


--
-- Name: ix_reponses_message_id; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_reponses_message_id ON public.reponses USING btree (message_id);


--
-- Name: ix_reponses_question_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_reponses_question_id ON public.reponses_question USING btree (id);


--
-- Name: ix_reponses_question_question_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_reponses_question_question_id ON public.reponses_question USING btree (question_id);


--
-- Name: ix_specialites_formation_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_specialites_formation_id ON public.specialites USING btree (formation_id);


--
-- Name: ix_specialites_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_specialites_id ON public.specialites USING btree (id);


--
-- Name: ix_tarifs_formation_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_tarifs_formation_id ON public.tarifs USING btree (formation_id);


--
-- Name: ix_tarifs_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_tarifs_id ON public.tarifs USING btree (id);


--
-- Name: ix_traitement_documents_document_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_traitement_documents_document_id ON public.traitement_documents USING btree (document_id);


--
-- Name: ix_traitement_documents_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_traitement_documents_id ON public.traitement_documents USING btree (id);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: ix_users_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_users_id ON public.users USING btree (id);


--
-- Name: ix_version_documents_document_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_version_documents_document_id ON public.version_documents USING btree (document_id);


--
-- Name: ix_version_documents_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_version_documents_id ON public.version_documents USING btree (id);


--
-- Name: ix_visiteurs_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_visiteurs_id ON public.visiteurs USING btree (id);


--
-- Name: ix_visiteurs_sessionToken; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX "ix_visiteurs_sessionToken" ON public.visiteurs USING btree ("sessionToken");


--
-- Name: candidats candidats_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.candidats
    ADD CONSTRAINT candidats_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: candidats candidats_visiteur_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.candidats
    ADD CONSTRAINT candidats_visiteur_id_fkey FOREIGN KEY (visiteur_id) REFERENCES public.visiteurs(id);


--
-- Name: conversations conversations_candidat_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversations
    ADD CONSTRAINT conversations_candidat_id_fkey FOREIGN KEY (candidat_id) REFERENCES public.candidats(id);


--
-- Name: conversations conversations_enseignant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversations
    ADD CONSTRAINT conversations_enseignant_id_fkey FOREIGN KEY (enseignant_id) REFERENCES public.users(id);


--
-- Name: conversations conversations_visiteur_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversations
    ADD CONSTRAINT conversations_visiteur_id_fkey FOREIGN KEY (visiteur_id) REFERENCES public.visiteurs(id);


--
-- Name: documents documents_responsable_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documents
    ADD CONSTRAINT documents_responsable_id_fkey FOREIGN KEY (responsable_id) REFERENCES public.users(id);


--
-- Name: entretiens entretiens_enseignant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entretiens
    ADD CONSTRAINT entretiens_enseignant_id_fkey FOREIGN KEY (enseignant_id) REFERENCES public.users(id);


--
-- Name: entretiens entretiens_rendezvous_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entretiens
    ADD CONSTRAINT entretiens_rendezvous_id_fkey FOREIGN KEY (rendezvous_id) REFERENCES public.rendezvous(id);


--
-- Name: equivalences equivalences_formation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.equivalences
    ADD CONSTRAINT equivalences_formation_id_fkey FOREIGN KEY (formation_id) REFERENCES public.formations(id);


--
-- Name: formation_candidat formation_candidat_candidat_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.formation_candidat
    ADD CONSTRAINT formation_candidat_candidat_id_fkey FOREIGN KEY (candidat_id) REFERENCES public.candidats(id);


--
-- Name: formation_candidat formation_candidat_formation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.formation_candidat
    ADD CONSTRAINT formation_candidat_formation_id_fkey FOREIGN KEY (formation_id) REFERENCES public.formations(id);


--
-- Name: matieres matieres_programme_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.matieres
    ADD CONSTRAINT matieres_programme_id_fkey FOREIGN KEY (programme_id) REFERENCES public.programmes_etude(id);


--
-- Name: messages messages_conversation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT messages_conversation_id_fkey FOREIGN KEY (conversation_id) REFERENCES public.conversations("idConversation");


--
-- Name: notifications notifications_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT notifications_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: preinscriptions preinscriptions_candidat_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.preinscriptions
    ADD CONSTRAINT preinscriptions_candidat_id_fkey FOREIGN KEY (candidat_id) REFERENCES public.candidats(id);


--
-- Name: preinscriptions preinscriptions_formation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.preinscriptions
    ADD CONSTRAINT preinscriptions_formation_id_fkey FOREIGN KEY (formation_id) REFERENCES public.formations(id);


--
-- Name: profils_candidat profils_candidat_candidat_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.profils_candidat
    ADD CONSTRAINT profils_candidat_candidat_id_fkey FOREIGN KEY (candidat_id) REFERENCES public.candidats(id);


--
-- Name: programmes_etude programmes_etude_specialite_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.programmes_etude
    ADD CONSTRAINT programmes_etude_specialite_id_fkey FOREIGN KEY (specialite_id) REFERENCES public.specialites(id);


--
-- Name: qcms qcms_preinscription_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.qcms
    ADD CONSTRAINT qcms_preinscription_id_fkey FOREIGN KEY (preinscription_id) REFERENCES public.preinscriptions(id);


--
-- Name: questions questions_qcm_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.questions
    ADD CONSTRAINT questions_qcm_id_fkey FOREIGN KEY (qcm_id) REFERENCES public.qcms(id);


--
-- Name: recommendations recommendations_candidat_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.recommendations
    ADD CONSTRAINT recommendations_candidat_id_fkey FOREIGN KEY (candidat_id) REFERENCES public.candidats(id);


--
-- Name: recommendations recommendations_formation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.recommendations
    ADD CONSTRAINT recommendations_formation_id_fkey FOREIGN KEY (formation_id) REFERENCES public.formations(id);


--
-- Name: rendezvous rendezvous_candidat_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rendezvous
    ADD CONSTRAINT rendezvous_candidat_id_fkey FOREIGN KEY (candidat_id) REFERENCES public.candidats(id);


--
-- Name: rendezvous rendezvous_enseignant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rendezvous
    ADD CONSTRAINT rendezvous_enseignant_id_fkey FOREIGN KEY (enseignant_id) REFERENCES public.users(id);


--
-- Name: rendezvous rendezvous_responsable_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rendezvous
    ADD CONSTRAINT rendezvous_responsable_id_fkey FOREIGN KEY (responsable_id) REFERENCES public.users(id);


--
-- Name: reponses reponses_message_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reponses
    ADD CONSTRAINT reponses_message_id_fkey FOREIGN KEY (message_id) REFERENCES public.messages("idMessage");


--
-- Name: reponses_question reponses_question_question_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reponses_question
    ADD CONSTRAINT reponses_question_question_id_fkey FOREIGN KEY (question_id) REFERENCES public.questions(id);


--
-- Name: specialites specialites_formation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.specialites
    ADD CONSTRAINT specialites_formation_id_fkey FOREIGN KEY (formation_id) REFERENCES public.formations(id);


--
-- Name: tarifs tarifs_formation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tarifs
    ADD CONSTRAINT tarifs_formation_id_fkey FOREIGN KEY (formation_id) REFERENCES public.formations(id);


--
-- Name: traitement_documents traitement_documents_document_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.traitement_documents
    ADD CONSTRAINT traitement_documents_document_id_fkey FOREIGN KEY (document_id) REFERENCES public.documents(id);


--
-- Name: version_documents version_documents_document_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.version_documents
    ADD CONSTRAINT version_documents_document_id_fkey FOREIGN KEY (document_id) REFERENCES public.documents(id);


--
-- PostgreSQL database dump complete
--

\unrestrict 50fOiO7hmFiHF8bjAsfTZdAmr7qGutGgLgtZmBvJhmtvi0HK5XKDupWMdgfLPSc
