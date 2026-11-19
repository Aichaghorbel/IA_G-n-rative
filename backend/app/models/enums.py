from enum import Enum


# ==============================================================================
# ENUMERATIONS STRICTEMENT CONFORMES AU DIAGRAMME DE CLASSES
# ==============================================================================

class Diplome(str, Enum):
    BACCALAUREAT = "Baccalauréat"
    PREPA = "Prépa"
    LICENCE = "Licence"
    MASTERE = "Mastère"


class Universite(str, Enum):
    IIT = "IIT"
    ISB = "ISB"


class Sexe(str, Enum):
    HOMME = "Homme"
    FEMME = "Femme"


class Niveau(int, Enum):
    NIVEAU_1 = 1
    NIVEAU_2 = 2
    NIVEAU_3 = 3


class Cours(str, Enum):
    COURS_DE_JOUR = "cours de jour"
    COURS_DE_SOIR = "cours de soir"


class TypeTarif(str, Enum):
    FRAIS_NATIONAL = "fraisNational"
    FRAIS_INTERNATIONAL = "frais international"


class Devise(str, Enum):
    DT = "DT"
    EUR = "€"


class Source(str, Enum):
    RESEAUX_SOCIAUX = "Réseaux sociaux"
    AMIS_PARENTS = "Amis/Parents"
    SITE_WEB = "Site Web"
    SMS = "SMS"
    PRESSE = "Presse"
    FOIRE = "Foire"
    TOURNEE_LYCEE = "Tourné Lycée"
    EVENEMENT = "Evenement"
    EMAIL = "Email"
    RADIO_TV = "Radio/TV"
    AUTRE = "Autre"


class DiplomeSouhaite(str, Enum):
    LICENCE_BUSINESS_ADMINISTRATION_ENG = "Licence in Business Administration(ENG)"
    LICENCE_BUSINESS_INTELLIGENCE_BILINGUE = "Licence en Business Intelligence(Bilingue)"
    LICENCE_NATIONALE_GESTION_FR = "Licence Nationale en Gestion(FR)"
    LICENCE_NATIONALE_COMPTABILITE_FR = "Licence Nationale en Comptabilité(FR)"
    LICENCE_NATIONALE_DROIT_PRIVE_FR = "Licence Nationale en Droit Privé(FR)"
    LICENCE_NATIONALE_DROIT_AFFAIRES_FR = "Licence Nationale en Droit des Affaires(FR)"
    LICENCE_SC_ECO_BUSINESS_ECONOMICS_AI_FR = "Licence en science économique : Business Economics (with AI)(FR)"
    LICENCE_SC_ECO_TRANSPORT_LOGISTIQUE_FR = "Licence en science économique : Transport et Logistique(FR)"
    MASTER_BUSINESS_ADMINISTRATION_MBA_ENG = "Master in Business Administration (MBA)(ENG)"
    MASTERE_MARKETING_DIGITAL_FR = "Mastère en Marketing Digital(FR)"
    MASTER_COMPTABILITE_FR = "Master en Comptabilité(FR)"
    MASTERE_FINANCE_ENTREPRISE_ING_FINANCIERE_FR = "Mastère Finance d'Entreprise et Ingénierie Financière(FR)"
    MSC_DIGITAL_MARKETING_ENG = "Master of Science (MSc) in Digital Marketing(ENG)"
    MSC_FINANCE_FR = "Master of Science (MSc) in Finance(FR)"
    MSC_FINANCE_ENG = "Master of Science (MSc) in Finance(ENG)"
    MASTER_DROIT_FR = "Master en Droit(FR)"
    CYCLE_PREPARATOIRE = "Cycle Préparatoire"
    LICENCE_INFO_GENIE_LOGICIEL_SYSTEME_INFO = "Licence en informatique : Génie Logiciel et Système d'Information"
    LICENCE_GENIE_INDUSTRIEL_MANAGEMENT = "Licence en Génie Industriel : Management des Systèmes Industriels"
    MASTER_INDUSTRIE_4_0 = "Master Industrie 4.0"
    GENIE_CIVIL = "Génie Civil"
    GENIE_DES_PROCEDES = "Génie des Procédés"
    GENIE_MECANIQUE = "Génie Mécanique"
    GENIE_DES_TELECOMMUNICATIONS = "Génie des Télécommunications"
    GENIE_INFORMATIQUE = "Génie Informatique"
    GENIE_INDUSTRIEL = "Génie Industriel"
    ARCHITECTURE = "Architecture"


class StatutRDV(str, Enum):
    CONFIRME = "confirmé"
    REPORTE = "reporté"
    ANNULE = "Annulé"


class StatutPreinscription(str, Enum):
    ACCEPTE = "accepté"
    REFUSE = "refusé"


class StatutRecommandation(str, Enum):
    VALIDEE = "validée"
    AJUSTEE = "ajustée"
    A_VALIDER = "à validée"


class NiveauQSM(str, Enum):
    FACILE = "facile"
    DIFFICILE = "difficile"
    MOYENNE = "moyenne"
    AVANCE = "Avancé"
    INTERMEDIAIRE = "Intermédiaire"
    A_CONSIDERER = "A considérer"


class Categorie(str, Enum):
    ALGORITHMIQUE = "Algorithmique"
    LOGIQUEMATH = "logiqueMath"
    GESTIONETECONOMIE = "gestionEtEconomie"


class Avis(str, Enum):
    FAVORABLE = "Favorable"
    DEFAVORABLE = "Défavorable"


class Departement(str, Enum):
    CIVIL = "Civil"
    INDUSTRIEL = "Industriel"
    INFORMATIQUE = "Informatique"
    PROCEDES = "Procédés"
    MECANIQUE = "Mécanique"
    TELECOMMUNICATIONS = "Télécommunications"
    COMPTABILITE_ET_FINANCE = "Comptabilité et Finance"
    MARKETING_ET_E_BUSINESS = "Marketing et E-Business"
    GESTION_DES_SYSTEMES_D_INFORMATION = "Gestion des Systèmes d'Information"
    INGENIERIE_DES_AFFAIRES = "Ingénierie des Affaires"
    GESTION_DES_RISQUES = "Gestion des Risques"
    ENTREPRENARIAT = "Entreprenariat"
    ADMINISTRATION_DES_AFFAIRES_MBA = "Administration des Affaires (MBA)"


class SatutEntretien(str, Enum):
    PLANIFIE = "Planifié"
    TERMINE = "Terminé"


class CategorieDoc(str, Enum):
    GUIDE = "Guide"
    FORMATION = "Formation"


class TypeNotif(str, Enum):
    CONFIRMATION = "Confirmation"
    ANNONCE = "Annonce"


class TraitementType(str, Enum):
    AJOUT = "Ajout"
    MODIFICATION = "Modification"
    SUPPRESSION = "Suppression"


class StautDoc(str, Enum):
    EN_COURS = "En cours"
    TERMINE = "Terminé"
    ERREUR = "Erreur"


class Grade(str, Enum):
    MAITRE_ASSISTANT = "MaitreAssistant"
    ASSISTANT = "Assistant"
    EXPERT_PROFESSIONNEL = "ExpertProfessionnel"
    PROFESSEUR_ENSEIGNEMENT_SUPERIEUR = "ProfesseurEnseignementSuperieur"
    MAITRE_CONFERENCES = "MaitreConferences"
