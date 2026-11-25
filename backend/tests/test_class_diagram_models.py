import pytest
from datetime import date, datetime
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models import (
    Utilisateur,
    Enseignant,
    Responsable,
    Visiteur,
    Candidat,
    ProfilCandidat,
    Formation,
    Tarif,
    Equivalence,
    Specialite,
    ProgrammeEtude,
    Matiere,
    Preinscription,
    QCM,
    Question,
    ReponseQuestion,
    Recommandation,
    Conversation,
    Message,
    Reponse,
    RendezVous,
    Entretien,
    Notification,
    Document,
    VersionDocument,
    TraitementDocument,
    Diplome,
    Universite,
    Sexe,
    Niveau,
    Cours,
    TypeTarif,
    Devise,
    Source,
    DiplomeSouhaite,
    StatutRDV,
    StatutPreinscription,
    StatutRecommandation,
    NiveauQSM,
    Categorie,
    Avis,
    Departement,
    SatutEntretien,
    CategorieDoc,
    TypeNotif,
    TraitementType,
    StautDoc,
    Grade,
)


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_classes_exist_and_attributes(db: Session):
    """Vérifie l'existence et les attributs conformes des classes du diagramme DrawIO."""
    # 1. Utilisateur & Enseignant & Responsable
    resp = db.query(Responsable).first()
    assert resp is not None
    assert hasattr(resp, "id")
    assert hasattr(resp, "nom")
    assert hasattr(resp, "prenom")
    assert hasattr(resp, "email")
    assert hasattr(resp, "motDePasse")
    assert hasattr(resp, "telephone")
    assert hasattr(resp, "universite")

    ens = db.query(Enseignant).first()
    assert ens is not None
    assert hasattr(ens, "departement")
    assert hasattr(ens, "gradAcademique")
    assert hasattr(ens, "specialite")
    assert hasattr(ens, "universite")

    # 2. Visiteur & Candidat & ProfilCandidat
    visiteur = db.query(Visiteur).first()
    assert visiteur is not None
    assert hasattr(visiteur, "id")
    assert hasattr(visiteur, "sessionToken")
    assert hasattr(visiteur, "ip_address")
    assert hasattr(visiteur, "dateVisite")

    candidat = db.query(Candidat).first()
    assert candidat is not None
    assert hasattr(candidat, "id")
    assert hasattr(candidat, "CIN")
    assert hasattr(candidat, "passport")
    assert hasattr(candidat, "pays")
    assert hasattr(candidat, "dateNaissance")
    assert hasattr(candidat, "sexe")
    assert hasattr(candidat, "adresse")
    assert hasattr(candidat, "universite")

    profil = db.query(ProfilCandidat).first()
    assert profil is not None
    assert hasattr(profil, "id")
    assert hasattr(profil, "dernierDiplomeObtenu")
    assert hasattr(profil, "anneeObtention")
    assert hasattr(profil, "diplomeSouhaite")
    assert hasattr(profil, "niveau")
    assert hasattr(profil, "cours")
    assert hasattr(profil, "sourceConnaissanceUniversite")

    # 3. Formation, Tarif, Equivalence, Specialite, ProgrammeEtude, Matiere
    formation = db.query(Formation).first()
    assert formation is not None
    assert hasattr(formation, "id")
    assert hasattr(formation, "nom")
    assert hasattr(formation, "universite")
    assert hasattr(formation, "description")
    assert hasattr(formation, "objectif")
    assert hasattr(formation, "duree")
    assert hasattr(formation, "debouches")
    assert hasattr(formation, "conditionsAdmission")
    assert hasattr(formation, "prerequis")

    tarif = db.query(Tarif).first()
    assert tarif is not None
    assert hasattr(tarif, "id")
    assert hasattr(tarif, "montant_9mois")
    assert hasattr(tarif, "type")
    assert hasattr(tarif, "Annee")
    assert hasattr(tarif, "devise")

    equiv = db.query(Equivalence).first()
    assert equiv is not None
    assert hasattr(equiv, "id")
    assert hasattr(equiv, "desciption")
    assert hasattr(equiv, "conditions")
    assert hasattr(equiv, "formation_Origine")

    spec = db.query(Specialite).first()
    assert spec is not None
    assert hasattr(spec, "id")
    assert hasattr(spec, "nom")
    assert hasattr(spec, "description")

    prog = db.query(ProgrammeEtude).first()
    assert prog is not None
    assert hasattr(prog, "id")
    assert hasattr(prog, "nom")
    assert hasattr(prog, "description")
    assert hasattr(prog, "semestre")

    matiere = db.query(Matiere).first()
    assert matiere is not None
    assert hasattr(matiere, "id")
    assert hasattr(matiere, "nom")
    assert hasattr(matiere, "description")
    assert hasattr(matiere, "coefficient")
    assert hasattr(matiere, "volumeHoraire")


def test_qcm_and_reponse_question_relationships(db: Session):
    """
    Vérification stricte de la hiérarchie QCM :
    Preinscription (1) -> (1) QCM
    QCM (1) -> (1..*) Question
    Question (1) -> (1..*) ReponseQuestion
    IMPORTANT : ReponseQuestion est liée UNIQUEMENT à Question, PAS à QCM.
    """
    preinscr = db.query(Preinscription).first()
    assert preinscr is not None
    assert preinscr.qcm is not None

    qcm = preinscr.qcm
    assert hasattr(qcm, "score")
    assert hasattr(qcm, "datePassation")
    assert hasattr(qcm, "niveau")
    assert qcm.preinscription_id == preinscr.id

    # QCM -> Question
    assert len(qcm.questions) >= 1
    question = qcm.questions[0]
    assert hasattr(question, "contenu")
    assert hasattr(question, "correctReponse")
    assert hasattr(question, "niveau")
    assert hasattr(question, "categorie")
    assert question.qcm_id == qcm.id

    # Question -> ReponseQuestion
    assert len(question.reponses) >= 1
    reponse = question.reponses[0]
    assert hasattr(reponse, "estSelectionne")
    assert hasattr(reponse, "question_id")
    # ReponseQuestion ne doit PAS posséder de qcm_id !
    assert not hasattr(reponse, "qcm_id")
    assert reponse.question_id == question.id


def test_formation_specialite_programme_hierarchy(db: Session):
    """
    Vérification de la chaîne de composition :
    Formation (1) -> (1..*) Specialite -> (1..*) ProgrammeEtude -> (1..*) Matiere
    """
    formation = db.query(Formation).filter(Formation.nom.ilike("%Génie Logiciel%")).first()
    assert formation is not None
    assert len(formation.specialites) >= 1

    spec = formation.specialites[0]
    assert spec.formation_id == formation.id
    assert len(spec.programmes) >= 1

    prog = spec.programmes[0]
    assert prog.specialite_id == spec.id
    assert len(prog.matieres) >= 1

    mat = prog.matieres[0]
    assert mat.programme_id == prog.id


def test_rendezvous_and_entretien(db: Session):
    """
    Vérification des associations RendezVous & Entretien :
    RendezVous (1) -> (0..1) Entretien
    Enseignant (1) -> (0..1) Entretien
    Responsable (1) -> (0..*) RendezVous
    Enseignant (1) -> (0..*) RendezVous
    Candidat (1) -> (0..*) RendezVous
    """
    rdv = db.query(RendezVous).first()
    assert rdv is not None
    assert hasattr(rdv, "dateHeure")
    assert hasattr(rdv, "statut")
    assert hasattr(rdv, "salleOuLien")
    assert rdv.candidat is not None
    assert rdv.enseignant is not None

    if rdv.entretien:
        entretien = rdv.entretien
        assert hasattr(entretien, "avisEnseignant")
        assert hasattr(entretien, "notes")
        assert hasattr(entretien, "oriantationFinale")
        assert hasattr(entretien, "staut")
        assert entretien.rendezvous_id == rdv.id


def test_conversation_message_reponse(db: Session):
    """
    Vérification de la conversation :
    Conversation (1) -> (1..*) Message (1) -> (1) Reponse (ReponseGeneree)
    """
    conv = db.query(Conversation).first()
    assert conv is not None
    assert hasattr(conv, "idConversation")
    assert hasattr(conv, "titre")
    assert hasattr(conv, "estFavori")
    assert hasattr(conv, "dateDernierModification")

    assert len(conv.messages) >= 1
    msg = conv.messages[0]
    assert hasattr(msg, "idMessage")
    assert hasattr(msg, "contenu")
    assert hasattr(msg, "dateEnvoi")
    assert msg.conversation_id == conv.idConversation

    assert msg.reponse is not None
    rep = msg.reponse
    assert hasattr(rep, "contenu")
    assert hasattr(rep, "date")
    assert hasattr(rep, "source")
    assert rep.message_id == msg.idMessage


def test_documents_and_traitements(db: Session):
    """
    Vérification du sous-système Document :
    Document (1) -> (1..*) VersionDocument
    Document (1) -> (1..*) TraitementDocument
    """
    doc = db.query(Document).first()
    assert doc is not None
    assert hasattr(doc, "nom")
    assert hasattr(doc, "description")
    assert hasattr(doc, "categorie")

    assert len(doc.versions) >= 1
    v = doc.versions[0]
    assert hasattr(v, "nomFichier")
    assert hasattr(v, "cheminFichier")
    assert hasattr(v, "taille")
    assert hasattr(v, "dateAjout")
    assert v.document_id == doc.id

    assert len(doc.traitements) >= 1
    t = doc.traitements[0]
    assert hasattr(t, "type")
    assert hasattr(t, "date")
    assert hasattr(t, "statut")
    assert t.document_id == doc.id
