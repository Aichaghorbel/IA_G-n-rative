import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.core.database import Base, SessionLocal, engine
from app.core.security import get_password_hash
from app.models.appointment import Appointment, Notification
from app.models.candidate import CandidateProfile, PreRegistration
from app.models.conversation import Conversation, Message
from app.models.document import Document
from app.models.qcm import QCM, Question
from app.models.recommendation import Formation, Recommendation
from app.models.user import User
from app.services.document_service import document_service


def seed_database():
    print("=" * 70)
    print("  INITIALISATION DES DONNÉES DE DÉMONSTRATION SMARTCAMPUS AI")
    print("=" * 70)

    # 1. Création des tables
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Chargement du fichier JSON
        json_path = BASE_DIR / "data" / "demo_data.json"
        with open(json_path, "r", encoding="utf-8") as f:
            demo_data = json.load(f)

        # 2. Utilisateurs
        user_map = {}
        for u in demo_data.get("users", []):
            existing = db.query(User).filter(User.email == u["email"].lower()).first()
            if not existing:
                user = User(
                    email=u["email"].lower(),
                    hashed_password=get_password_hash(u["password"]),
                    role=u["role"],
                    nom=u["nom"],
                    prenom=u["prenom"],
                    telephone=u.get("telephone"),
                    is_active=True
                )
                db.add(user)
                db.flush()
                user_map[user.email] = user
                print(f"  [+] Utilisateur créé: {user.email} (Rôle: {user.role})")
            else:
                user_map[existing.email] = existing
                print(f"  [*] Utilisateur existant: {existing.email}")

        # 3. Formations
        formation_map = {}
        for f_data in demo_data.get("formations", []):
            existing = db.query(Formation).filter(Formation.code == f_data["code"]).first()
            if not existing:
                formation = Formation(
                    code=f_data["code"],
                    nom=f_data["nom"],
                    etablissement=f_data["etablissement"],
                    cycle=f_data["cycle"],
                    duree_annees=f_data["duree_annees"],
                    description=f_data["description"],
                    avantages=f_data["avantages"],
                    prerequis=f_data["prerequis"],
                    debouches=f_data["debouches"]
                )
                db.add(formation)
                db.flush()
                formation_map[formation.code] = formation
                print(f"  [+] Formation créée: {formation.nom} ({formation.etablissement})")
            else:
                formation_map[existing.code] = existing
                print(f"  [*] Formation existante: {existing.nom}")

        # 4. Profils Candidats & Affectation
        teacher_iit = user_map.get("enseignant.iit@smartcampus.tn")
        teacher_isb = user_map.get("enseignant.isb@smartcampus.tn")

        for cp in demo_data.get("candidate_profiles", []):
            email = cp["email"].lower()
            existing = db.query(CandidateProfile).filter(CandidateProfile.email == email).first()
            if not existing:
                user_acc = user_map.get(email)
                profile = CandidateProfile(
                    user_id=user_acc.id if user_acc else None,
                    nom=cp["nom"],
                    prenom=cp["prenom"],
                    email=email,
                    telephone=cp.get("telephone"),
                    niveau_etudes=cp.get("niveau_etudes"),
                    etablissement_origine=cp.get("etablissement_origine"),
                    specialites=cp.get("specialites", []),
                    interets=cp.get("interets", []),
                    matieres_preferees=cp.get("matieres_preferees", []),
                    objectif_professionnel=cp.get("objectif_professionnel"),
                    contraintes=cp.get("contraintes"),
                    etablissement_vise=cp.get("etablissement_vise"),
                    statut_dossier=cp.get("statut_dossier", "EXPLORATION"),
                    affectation_statut=cp.get("affectation_statut"),
                    enseignant_affecte_id=teacher_iit.id if cp.get("etablissement_vise") == "IIT" and teacher_iit else (teacher_isb.id if teacher_isb else None),
                    consent_rgpd=cp.get("consent_rgpd", True),
                    consent_timestamp=datetime.now(timezone.utc)
                )
                db.add(profile)
                db.flush()
                print(f"  [+] Profil candidat créé: {profile.prenom} {profile.nom} (Statut: {profile.statut_dossier})")

                # Préinscription associée
                target_form = formation_map.get("IIT-ING-GL") if cp.get("etablissement_vise") == "IIT" else formation_map.get("ISB-LIC-BA")
                prereg = PreRegistration(
                    candidate_id=profile.id,
                    formation_id=target_form.id if target_form else 1,
                    decision="en_attente",
                    observations="Dossier académique solide."
                )
                db.add(prereg)
                db.flush()

                # Recommandation IA associée
                rec = Recommendation(
                    candidate_id=profile.id,
                    formation_id=target_form.id if target_form else 1,
                    score_compatibilite=0.94 if cp.get("etablissement_vise") == "IIT" else 0.89,
                    justification="Forte affinité démontrée lors du parcours conversationnel.",
                    status="valide",
                    genere_par="agent_ia"
                )
                db.add(rec)
                db.flush()

                # QCM associé
                qcm = QCM(
                    candidate_id=profile.id,
                    formation_id=target_form.id if target_form else 1,
                    total_questions=3,
                    score=85.0 if cp.get("etablissement_vise") == "IIT" else 78.0,
                    completed=True,
                    result_summary={
                        "acquis": ["Algorithmique", "Raisonnement logique", "Conception d'APIs"],
                        "difficultes": ["Statistiques avancées"],
                        "motivations": "Très motivé par les projets appliqués et le travail en équipe."
                    }
                )
                db.add(qcm)
                db.flush()

                # Entretien / Rendez-vous associé
                apt = Appointment(
                    candidat_id=profile.id,
                    enseignant_id=profile.enseignant_affecte_id,
                    preinscription_id=prereg.id,
                    date_proposee=datetime.now(timezone.utc) + timedelta(days=2, hours=10),
                    date_confirmee=datetime.now(timezone.utc) + timedelta(days=2, hours=10),
                    status="confirme" if profile.statut_dossier == "ENTRETIEN_PLANIFIE" else "propose",
                    lieu="Campus IIT - Salle A102",
                    decision_finale="en_attente"
                )
                db.add(apt)

                # Conversation de démo
                conv = Conversation(
                    candidate_id=profile.id,
                    is_anonymous=False,
                    language_detected="arabizi",
                    intent_detected="info_programme",
                    memory_summary={"interets": profile.interets, "niveau": profile.niveau_etudes}
                )
                db.add(conv)
                db.flush()

                msg_user = Message(
                    conversation_id=conv.id,
                    role="user",
                    content="3aslema! N7eb na3ref akther 3la parcours Génie Logiciel fel IIT.",
                    language_detected="arabizi",
                    metadata_json={"intent": "info_programme"}
                )
                msg_bot = Message(
                    conversation_id=conv.id,
                    role="assistant",
                    content="Mar7ba bik Sarra ! L'IIT t9addem diplôme d'ingénieur en Génie Logiciel (5 snin ou 3 snin ba3d Licence). Famma barcha stages w des projets réels.",
                    language_detected="arabizi",
                    metadata_json={"latency_ms": 310, "tokens_used": 95, "model": "qwen2.5-7b-instruct"}
                )
                db.add_all([msg_user, msg_bot])

        # 5. Documents RAG depuis sample_corpus
        corpus_dir = BASE_DIR / "data" / "sample_corpus"
        if corpus_dir.exists():
            admin_user = user_map.get("admin@smartcampus.tn")
            admin_id = admin_user.id if admin_user else 1

            for doc_file in corpus_dir.glob("*.txt"):
                content = doc_file.read_bytes()
                sha = document_service.calculate_sha256(content)
                existing = db.query(Document).filter(Document.hash_content == sha).first()
                if not existing:
                    etab = "IIT" if "iit" in doc_file.name else ("ISB" if "isb" in doc_file.name else "IIT")
                    doc = Document(
                        filename=doc_file.name,
                        type="brochure" if "brochure" in doc_file.name else "fiche_faq",
                        etablissement=etab,
                        size_bytes=len(content),
                        mime_type="text/plain",
                        status="INDEXED",
                        chunks_count=max(2, len(content) // 400),
                        hash_content=sha,
                        uploaded_by=admin_id,
                        indexed_at=datetime.now(timezone.utc)
                    )
                    db.add(doc)
                    print(f"  [+] Document RAG indexé: {doc_file.name} ({etab})")

        # 6. Notification de bienvenue
        for email, user in user_map.items():
            notif = Notification(
                user_id=user.id,
                title="Bienvenue sur SmartCampus AI",
                message=f"Bonjour {user.prenom}, votre espace {user.role} est configuré et prêt pour l'année universitaire 2026-2027.",
                type="systeme"
            )
            db.add(notif)

        db.commit()
        print("\n" + "=" * 70)
        print("  SUCCÈS : Données de démonstration insérées avec succès !")
        print("=" * 70)
        print("\nComptes prêts pour tester la plateforme :")
        print("  1. Administrateur unifié : admin@smartcampus.tn       | Mot de passe: AdminSmartCampus2026!")
        print("  2. Enseignant (IIT)      : enseignant.iit@smartcampus.tn | Mot de passe: TeacherPassword2026!")
        print("  3. Enseignant (ISB)      : enseignant.isb@smartcampus.tn | Mot de passe: TeacherPassword2026!")
        print("  4. Candidat (IIT)        : sarra.benali@gmail.com       | Mot de passe: CandidatePassword2026!")
        print("  5. Candidat (ISB)        : youssef.trabelsi@gmail.com   | Mot de passe: CandidatePassword2026!")
        print("\nDocumentation Swagger : http://localhost:8000/docs")
        print("=" * 70)

    except Exception as e:
        db.rollback()
        print(f"\n[ERREUR] Échec du peuplement : {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
