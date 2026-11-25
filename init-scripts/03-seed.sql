--
-- PostgreSQL database dump
--

\restrict 5xNEpwLLnPn2X2bGfqIwJoorjixkYDkvMlP0TxByO1LiK9oYNMIP3WOmOCLyMGG

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
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.users (id, nom, prenom, email, "motDePasse", telephone, type_user, departement, "gradAcademique", specialite, universite) FROM stdin;
1	Ben Abdallah	Taoufik	admin@smartcampus.tn	$2b$12$69Si7r7rG/syOuaTFcCLR.puJ.TBfQq4I3EoO5/iVrdaqvVsCPRW2	+216 74 123 456	Responsable	\N	\N	\N	IIT
2	Gharbi	Mohamed	enseignant.iit@smartcampus.tn	$2b$12$5FrY.e3PiotXuI0zJ3jMVOSWXc0/7luGuPWYlNqDiPaPqJzYvWoGu	+216 74 234 567	Enseignant	Informatique	ProfesseurEnseignementSuperieur	Génie Logiciel & IA	IIT
3	Mezghani	Amel	enseignant.isb@smartcampus.tn	$2b$12$wR6WJhGBLUzndbvK7KRaseOO8cOTJ0LgwB9H.Yw7DIjrZGBpM8qxK	+216 74 345 678	Enseignant	Marketing et E-Business	MaitreConferences	Business Analytics & Finance	ISB
4	Ben Ali	Sarra	sarra.benali@gmail.com	$2b$12$s.7zOCceWfGJrOfKil53j.12gN6yqNBnGPyRr61jmJwGiUqTKR2ce	+216 21 000 111	Candidat	\N	\N	\N	\N
\.


--
-- Data for Name: visiteurs; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.visiteurs (id, "sessionToken", ip_address, "dateVisite") FROM stdin;
1	sess_demo_sarra	127.0.0.1	2026-11-19
\.


--
-- Data for Name: candidats; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.candidats (id, "CIN", passport, pays, "dateNaissance", sexe, adresse, universite, visiteur_id, user_id) FROM stdin;
1	12345678	TN987654	Tunisie	2003-05-14	Femme	Route de Téniour Km 4, Sfax	IIT	1	4
\.


--
-- Data for Name: conversations; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.conversations ("idConversation", titre, "estFavori", "dateDernierModification", visiteur_id, candidat_id, enseignant_id) FROM stdin;
1	Discussion orientation Cycle Ingénieur	t	2026-11-19 11:06:09.326142	1	1	2
\.


--
-- Data for Name: documents; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.documents (id, nom, description, categorie, responsable_id) FROM stdin;
1	Brochure Officielle IIT	Guide des formations et cursus de l'IIT 2026-2027	Guide	1
\.


--
-- Data for Name: rendezvous; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.rendezvous (id, "dateHeure", statut, "salleOuLien", responsable_id, enseignant_id, candidat_id) FROM stdin;
1	2026-11-21 11:06:09.321981	confirmé	Campus IIT - Salle B204	1	2	1
\.


--
-- Data for Name: entretiens; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.entretiens (id, "avisEnseignant", notes, "oriantationFinale", staut, rendezvous_id, enseignant_id) FROM stdin;
1	Favorable	Très bon niveau technique, esprit logique et forte motivation.	Génie Informatique	Planifié	1	2
\.


--
-- Data for Name: formations; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.formations (id, nom, universite, description, objectif, duree, debouches, "conditionsAdmission", prerequis) FROM stdin;
1	Cycle Ingénieur en Génie Logiciel & Informatique	IIT	Formation d'ingénieurs d'excellence formant des concepteurs logiciels, experts cloud et IA.	Former des ingénieurs aptes à concevoir des architectures distribuées modernes.	5	Architecte Logiciel, Ingénieur IA / Data, Lead Tech, Chef de projet	Bac Scientifique ou admission sur titre après Licence/Prépa	Mathématiques, Algorithmique, Notions de programmation
2	Licence Business Analytics & Intelligence des Données	ISB	Cursus alliant gestion d'entreprise, marketing digital et analyse décisionnelle.	Maîtriser la chaîne d'analyse de données d'entreprise pour la prise de décision stratégique.	3	Data Analyst Business, Consultant BI, Responsable CRM	Baccalauréat Economie & Gestion, Mathématiques ou Sciences	Bases en mathématiques et statistiques
\.


--
-- Data for Name: equivalences; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.equivalences (id, desciption, conditions, "formation_Origine", formation_id) FROM stdin;
1	Accès direct en 3ème année (1ère année cycle ingénieur)	Validation L2/L3 ou prépa	Licence	1
\.


--
-- Data for Name: formation_candidat; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.formation_candidat (formation_id, candidat_id) FROM stdin;
1	1
\.


--
-- Data for Name: specialites; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.specialites (id, nom, description, formation_id) FROM stdin;
1	Génie Logiciel & Cloud	Spécialisation ingénierie logicielle avancée	1
2	Business Analytics	Spécialité analytique appliquée	2
\.


--
-- Data for Name: programmes_etude; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.programmes_etude (id, nom, description, semestre, specialite_id) FROM stdin;
1	Programme Tronc Commun Ingénieur	Semestre S1 d'intégration	1	1
2	Fondamentaux de Business Intelligence	Semestre S1	1	2
\.


--
-- Data for Name: matieres; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.matieres (id, nom, description, coefficient, "volumeHoraire", programme_id) FROM stdin;
1	Algorithmique Avancée & Complexité	Structures de données complexes	3	42	1
2	Conception Orientée Objet & Design Patterns	Patterns GoF et SOLID	3	42	1
3	Bases de Données Relationnelles & NoSQL	PostgreSQL et architectures distribuées	2	35	1
4	Statistiques Décisionnelles	Modélisation statistique	3	42	2
5	Business Intelligence & Power BI	Tableaux de bord d'entreprise	3	42	2
\.


--
-- Data for Name: messages; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.messages ("idMessage", contenu, "dateEnvoi", conversation_id) FROM stdin;
1	Bonjour, je souhaite me renseigner sur le cycle ingénieur informatique.	2026-11-19 11:06:09.330335	1
\.


--
-- Data for Name: notifications; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.notifications (id, type, contenu, "dateEnvoi", envoyee, user_id) FROM stdin;
1	Confirmation	Votre préinscription en Cycle Ingénieur a été confirmée.	2026-11-19 11:06:09.330335	t	4
\.


--
-- Data for Name: preinscriptions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.preinscriptions (id, "dateCreation", statut, candidat_id, formation_id) FROM stdin;
1	2026-11-19	accepté	1	1
\.


--
-- Data for Name: profils_candidat; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.profils_candidat (id, candidat_id, "dernierDiplomeObtenu", "annéeObtention", "diplomeSouhaite", niveau, cours, "sourceConnaissanceUniversité") FROM stdin;
1	1	Baccalauréat	2024	Génie Informatique	1	cours de jour	Site Web
\.


--
-- Data for Name: qcms; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.qcms (id, score, "datePassation", niveau, preinscription_id) FROM stdin;
1	85	2026-11-19	Avancé	1
\.


--
-- Data for Name: questions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.questions (id, contenu, "correctReponse", niveau, categorie, qcm_id) FROM stdin;
1	Quelle structure de données est la plus adaptée pour une pile LIFO ?	1	moyenne	Algorithmique	1
\.


--
-- Data for Name: recommendations; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.recommendations (id, nom, "scoreComptabilite", justification, "dateGeneration", statut, candidat_id, formation_id) FROM stdin;
1	Orientation Ingénierie Logicielle	0.95	Excellente adéquation avec le profil mathématique et algorithmique.	2026-11-19 11:06:09.321981	validée	1	1
\.


--
-- Data for Name: reponses; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.reponses (id, contenu, date, source, message_id) FROM stdin;
1	Bonjour Sarra ! Le cycle ingénieur à l'IIT propose les filières Génie Logiciel, Télécom et IA.	2026-11-19 11:06:09.330335	Brochure IIT 2026-2027	1
\.


--
-- Data for Name: reponses_question; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.reponses_question (id, "estSélectionné", question_id) FROM stdin;
1	t	1
2	f	1
\.


--
-- Data for Name: tarifs; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.tarifs (id, "montant/9mois", type, "Annee", devise, formation_id) FROM stdin;
1	6500	fraisNational	2026-2027	DT	1
2	3200	frais international	2026-2027	€	1
3	5200	fraisNational	2026-2027	DT	2
\.


--
-- Data for Name: traitement_documents; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.traitement_documents (id, type, date, statut, document_id) FROM stdin;
1	Ajout	2026-11-19	Terminé	1
\.


--
-- Data for Name: version_documents; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.version_documents (id, "nomFichier", "cheminFichier", taille, "dateAjout", document_id) FROM stdin;
1	iit_brochure_2026_2027.pdf	/storage/docs/iit_brochure_2026_2027.pdf	2048.5	2026-11-19	1
\.


--
-- Name: candidats_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.candidats_id_seq', 1, true);


--
-- Name: conversations_idConversation_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."conversations_idConversation_seq"', 1, true);


--
-- Name: documents_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.documents_id_seq', 1, true);


--
-- Name: entretiens_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.entretiens_id_seq', 1, true);


--
-- Name: equivalences_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.equivalences_id_seq', 1, true);


--
-- Name: formations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.formations_id_seq', 2, true);


--
-- Name: matieres_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.matieres_id_seq', 5, true);


--
-- Name: messages_idMessage_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."messages_idMessage_seq"', 1, true);


--
-- Name: notifications_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.notifications_id_seq', 1, true);


--
-- Name: preinscriptions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.preinscriptions_id_seq', 1, true);


--
-- Name: profils_candidat_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.profils_candidat_id_seq', 1, true);


--
-- Name: programmes_etude_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.programmes_etude_id_seq', 2, true);


--
-- Name: qcms_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.qcms_id_seq', 1, true);


--
-- Name: questions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.questions_id_seq', 1, true);


--
-- Name: recommendations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.recommendations_id_seq', 1, true);


--
-- Name: rendezvous_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.rendezvous_id_seq', 1, true);


--
-- Name: reponses_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.reponses_id_seq', 1, true);


--
-- Name: reponses_question_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.reponses_question_id_seq', 2, true);


--
-- Name: specialites_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.specialites_id_seq', 2, true);


--
-- Name: tarifs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.tarifs_id_seq', 3, true);


--
-- Name: traitement_documents_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.traitement_documents_id_seq', 1, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.users_id_seq', 4, true);


--
-- Name: version_documents_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.version_documents_id_seq', 1, true);


--
-- Name: visiteurs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.visiteurs_id_seq', 1, true);


--
-- PostgreSQL database dump complete
--

\unrestrict 5xNEpwLLnPn2X2bGfqIwJoorjixkYDkvMlP0TxByO1LiK9oYNMIP3WOmOCLyMGG
