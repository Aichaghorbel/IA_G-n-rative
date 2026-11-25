import json
import os
import sys
from datetime import datetime, date, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.core.database import Base, SessionLocal, engine
from app.core.security import get_password_hash
from app.models.enums import (
    Universite,
    Diplome,
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
from app.models.user import User, Enseignant, Responsable
from app.models.candidate import Visiteur, Candidat, ProfilCandidat
from app.models.formation import Formation, Tarif, Equivalence, Specialite, ProgrammeEtude, Matiere
from app.models.qcm import Preinscription, QCM, Question, ReponseQuestion
from app.models.recommendation import Recommandation
from app.models.appointment import RendezVous, Entretien, Notification
from app.models.document import Document, VersionDocument, TraitementDocument
from app.models.conversation import Conversation, Message, Reponse


def seed_database():
    print("=" * 70)
    print("  INITIALISATION DES DONNEES SMARTCAMPUS AI - DIAGRAMME DE CLASSES")
    print("=" * 70)

    db = SessionLocal()

    try:
        # 1. Responsable & Enseignants
        resp = db.query(Responsable).filter(Responsable.email == "admin@smartcampus.tn").first()
        if not resp:
            resp = Responsable(
                nom="Ben Abdallah",
                prenom="Taoufik",
                email="admin@smartcampus.tn",
                motDePasse=get_password_hash("AdminSmartCampus2026!"),
                telephone="+216 74 123 456",
                universite=Universite.IIT.value
            )
            db.add(resp)
            db.flush()
            print(f"  [+] Responsable créé: {resp.email}")

        ens_iit = db.query(Enseignant).filter(Enseignant.email == "enseignant.iit@smartcampus.tn").first()
        if not ens_iit:
            ens_iit = Enseignant(
                nom="Gharbi",
                prenom="Mohamed",
                email="enseignant.iit@smartcampus.tn",
                motDePasse=get_password_hash("TeacherPassword2026!"),
                telephone="+216 74 234 567",
                departement=Departement.INFORMATIQUE.value,
                gradAcademique=Grade.PROFESSEUR_ENSEIGNEMENT_SUPERIEUR.value,
                specialite="Génie Logiciel & IA",
                universite=Universite.IIT.value
            )
            db.add(ens_iit)
            db.flush()
            print(f"  [+] Enseignant IIT créé: {ens_iit.email}")

        ens_isb = db.query(Enseignant).filter(Enseignant.email == "enseignant.isb@smartcampus.tn").first()
        if not ens_isb:
            ens_isb = Enseignant(
                nom="Mezghani",
                prenom="Amel",
                email="enseignant.isb@smartcampus.tn",
                motDePasse=get_password_hash("TeacherPassword2026!"),
                telephone="+216 74 345 678",
                departement=Departement.MARKETING_ET_E_BUSINESS.value,
                gradAcademique=Grade.MAITRE_CONFERENCES.value,
                specialite="Business Analytics & Finance",
                universite=Universite.ISB.value
            )
            db.add(ens_isb)
            db.flush()
            print(f"  [+] Enseignant ISB créé: {ens_isb.email}")

        # 2. Formations, Tarifs, Equivalences, Specialites, Programmes, Matieres
        f_gl = db.query(Formation).filter(Formation.nom.ilike("%Génie Logiciel%")).first()
        if not f_gl:
            f_gl = Formation(
                nom="Cycle Ingénieur en Génie Logiciel & Informatique",
                universite=Universite.IIT.value,
                description="Formation d'ingénieurs d'excellence formant des concepteurs logiciels, experts cloud et IA.",
                objectif="Former des ingénieurs aptes à concevoir des architectures distribuées modernes.",
                duree=5,
                debouches="Architecte Logiciel, Ingénieur IA / Data, Lead Tech, Chef de projet",
                conditionsAdmission="Bac Scientifique ou admission sur titre après Licence/Prépa",
                prerequis="Mathématiques, Algorithmique, Notions de programmation"
            )
            db.add(f_gl)
            db.flush()

            # Tarifs
            t1 = Tarif(formation_id=f_gl.id, montant_9mois=6500.0, type=TypeTarif.FRAIS_NATIONAL.value, Annee="2026-2027", devise=Devise.DT.value)
            t2 = Tarif(formation_id=f_gl.id, montant_9mois=3200.0, type=TypeTarif.FRAIS_INTERNATIONAL.value, Annee="2026-2027", devise=Devise.EUR.value)
            db.add_all([t1, t2])

            # Equivalence
            eq1 = Equivalence(formation_id=f_gl.id, desciption="Accès direct en 3ème année (1ère année cycle ingénieur)", conditions="Validation L2/L3 ou prépa", formation_Origine=Diplome.LICENCE.value)
            db.add(eq1)

            # Specialite -> Programme -> Matieres
            spec_gl = Specialite(formation_id=f_gl.id, nom="Génie Logiciel & Cloud", description="Spécialisation ingénierie logicielle avancée")
            db.add(spec_gl)
            db.flush()

            prog1 = ProgrammeEtude(specialite_id=spec_gl.id, nom="Programme Tronc Commun Ingénieur", description="Semestre S1 d'intégration", semestre=1)
            db.add(prog1)
            db.flush()

            m1 = Matiere(programme_id=prog1.id, nom="Algorithmique Avancée & Complexité", description="Structures de données complexes", coefficient=3, volumeHoraire=42)
            m2 = Matiere(programme_id=prog1.id, nom="Conception Orientée Objet & Design Patterns", description="Patterns GoF et SOLID", coefficient=3, volumeHoraire=42)
            m3 = Matiere(programme_id=prog1.id, nom="Bases de Données Relationnelles & NoSQL", description="PostgreSQL et architectures distribuées", coefficient=2, volumeHoraire=35)
            db.add_all([m1, m2, m3])
            print(f"  [+] Formation complète IIT créée: {f_gl.nom}")

        f_ba = db.query(Formation).filter(Formation.nom.ilike("%Business Analytics%")).first()
        if not f_ba:
            f_ba = Formation(
                nom="Licence Business Analytics & Intelligence des Données",
                universite=Universite.ISB.value,
                description="Cursus alliant gestion d'entreprise, marketing digital et analyse décisionnelle.",
                objectif="Maîtriser la chaîne d'analyse de données d'entreprise pour la prise de décision stratégique.",
                duree=3,
                debouches="Data Analyst Business, Consultant BI, Responsable CRM",
                conditionsAdmission="Baccalauréat Economie & Gestion, Mathématiques ou Sciences",
                prerequis="Bases en mathématiques et statistiques"
            )
            db.add(f_ba)
            db.flush()

            t_isb = Tarif(formation_id=f_ba.id, montant_9mois=5200.0, type=TypeTarif.FRAIS_NATIONAL.value, Annee="2026-2027", devise=Devise.DT.value)
            db.add(t_isb)

            spec_ba = Specialite(formation_id=f_ba.id, nom="Business Analytics", description="Spécialité analytique appliquée")
            db.add(spec_ba)
            db.flush()

            prog_ba = ProgrammeEtude(specialite_id=spec_ba.id, nom="Fondamentaux de Business Intelligence", description="Semestre S1", semestre=1)
            db.add(prog_ba)
            db.flush()

            m_ba1 = Matiere(programme_id=prog_ba.id, nom="Statistiques Décisionnelles", description="Modélisation statistique", coefficient=3, volumeHoraire=42)
            m_ba2 = Matiere(programme_id=prog_ba.id, nom="Business Intelligence & Power BI", description="Tableaux de bord d'entreprise", coefficient=3, volumeHoraire=42)
            db.add_all([m_ba1, m_ba2])
            print(f"  [+] Formation complète ISB créée: {f_ba.nom}")

        # 3. Visiteur, Candidat & ProfilCandidat
        visiteur = db.query(Visiteur).filter(Visiteur.sessionToken == "sess_demo_sarra").first()
        if not visiteur:
            visiteur = Visiteur(
                sessionToken="sess_demo_sarra",
                ip_address="127.0.0.1",
                dateVisite=date.today()
            )
            db.add(visiteur)
            db.flush()

        cand_user = db.query(User).filter(User.email == "sarra.benali@gmail.com").first()
        if not cand_user:
            cand_user = User(
                nom="Ben Ali",
                prenom="Sarra",
                email="sarra.benali@gmail.com",
                motDePasse=get_password_hash("CandidatePassword2026!"),
                telephone="+216 21 000 111",
                type_user="Candidat"
            )
            db.add(cand_user)
            db.flush()

        candidat = db.query(Candidat).filter(Candidat.visiteur_id == visiteur.id).first()
        if not candidat:
            candidat = Candidat(
                visiteur_id=visiteur.id,
                user_id=cand_user.id,
                CIN="12345678",
                passport="TN987654",
                pays="Tunisie",
                dateNaissance=date(2003, 5, 14),
                sexe=Sexe.FEMME.value,
                adresse="Route de Téniour Km 4, Sfax",
                universite=Universite.IIT.value
            )
            db.add(candidat)
            db.flush()

            profil = ProfilCandidat(
                candidat_id=candidat.id,
                dernierDiplomeObtenu=Diplome.BACCALAUREAT.value,
                anneeObtention="2024",
                diplomeSouhaite=DiplomeSouhaite.GENIE_INFORMATIQUE.value,
                niveau=Niveau.NIVEAU_1.value,
                cours=Cours.COURS_DE_JOUR.value,
                sourceConnaissanceUniversite=Source.SITE_WEB.value
            )
            db.add(profil)
            print(f"  [+] Visiteur, Candidat et ProfilCandidat créés: {candidat.CIN}")

            # Association Candidat s'inscrire Formation
            candidat.formations.append(f_gl)

            # Preinscription
            preinscr = Preinscription(
                candidat_id=candidat.id,
                formation_id=f_gl.id,
                dateCreation=date.today(),
                statut=StatutPreinscription.ACCEPTE.value
            )
            db.add(preinscr)
            db.flush()

            # QCM généré par la préinscription
            qcm = QCM(
                preinscription_id=preinscr.id,
                score=85.0,
                datePassation=date.today(),
                niveau=NiveauQSM.AVANCE.value
            )
            db.add(qcm)
            db.flush()

            q1 = Question(
                qcm_id=qcm.id,
                contenu="Quelle structure de données est la plus adaptée pour une pile LIFO ?",
                correctReponse=1,
                niveau=NiveauQSM.MOYENNE.value,
                categorie=Categorie.ALGORITHMIQUE.value
            )
            db.add(q1)
            db.flush()

            rq1 = ReponseQuestion(question_id=q1.id, estSelectionne=True)
            rq2 = ReponseQuestion(question_id=q1.id, estSelectionne=False)
            db.add_all([rq1, rq2])

            # Recommandation (liée uniquement au Candidat — pas de formation_id selon le diagramme)
            rec = Recommandation(
                candidat_id=candidat.id,
                nom="Orientation Ingénierie Logicielle",
                scoreComptabilite=0.95,
                justification="Excellente adéquation avec le profil mathématique et algorithmique.",
                dateGeneration=datetime.now(),
                statut=StatutRecommandation.VALIDEE.value
            )
            db.add(rec)

            # RendezVous (lié à Enseignant + Candidat — pas de responsable_id selon le diagramme)
            rdv = RendezVous(
                candidat_id=candidat.id,
                enseignant_id=ens_iit.id,
                dateHeure=datetime.now() + timedelta(days=2),
                statut=StatutRDV.CONFIRME.value,
                salleOuLien="Campus IIT - Salle B204"
            )
            db.add(rdv)
            db.flush()

            # Entretien (lié uniquement au RendezVous — pas d'enseignant_id direct selon le diagramme)
            ent = Entretien(
                rendezvous_id=rdv.id,
                avisEnseignant=Avis.FAVORABLE.value,
                notes="Très bon niveau technique, esprit logique et forte motivation.",
                oriantationFinale=DiplomeSouhaite.GENIE_INFORMATIQUE.value,
                staut=SatutEntretien.PLANIFIE.value
            )
            db.add(ent)

            # Conversation (liée à Visiteur + Candidat — pas d'enseignant_id selon le diagramme)
            conv = Conversation(
                visiteur_id=visiteur.id,
                candidat_id=candidat.id,
                titre="Discussion orientation Cycle Ingénieur",
                estFavori=True,
                dateDernierModification=datetime.now()
            )
            db.add(conv)
            db.flush()

            msg = Message(
                conversation_id=conv.idConversation,
                contenu="Bonjour, je souhaite me renseigner sur le cycle ingénieur informatique.",
                dateEnvoi=datetime.now()
            )
            db.add(msg)
            db.flush()

            rep = Reponse(
                message_id=msg.idMessage,
                contenu="Bonjour Sarra ! Le cycle ingénieur à l'IIT propose les filières Génie Logiciel, Télécom et IA.",
                date=datetime.now(),
                source="Brochure IIT 2026-2027"
            )
            db.add(rep)

            # Notification
            notif = Notification(
                user_id=cand_user.id,
                type=TypeNotif.CONFIRMATION.value,
                contenu="Votre préinscription en Cycle Ingénieur a été confirmée.",
                dateEnvoi=datetime.now(),
                envoyee=True
            )
            db.add(notif)

        # 4. Documents, Versions & Traitements
        doc = db.query(Document).filter(Document.nom == "Brochure Officielle IIT").first()
        if not doc:
            doc = Document(
                nom="Brochure Officielle IIT",
                description="Guide des formations et cursus de l'IIT 2026-2027",
                categorie=CategorieDoc.GUIDE.value,
                responsable_id=resp.id
            )
            db.add(doc)
            db.flush()

            vdoc = VersionDocument(
                document_id=doc.id,
                nomFichier="iit_brochure_2026_2027.pdf",
                cheminFichier="/storage/docs/iit_brochure_2026_2027.pdf",
                taille=2048.5,
                dateAjout=date.today()
            )
            db.add(vdoc)

            tdoc = TraitementDocument(
                document_id=doc.id,
                type=TraitementType.AJOUT.value,
                date=date.today(),
                statut=StautDoc.TERMINE.value
            )
            db.add(tdoc)
            print(f"  [+] Document, Version et Traitement créés: {doc.nom}")

        db.commit()
        print("\n" + "=" * 70)
        print("  SUCCES : Base de données PostgreSQL initialisée avec succès !")
        print("=" * 70)

    except Exception as e:
        db.rollback()
        print(f"\n[ERREUR] Echec : {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
