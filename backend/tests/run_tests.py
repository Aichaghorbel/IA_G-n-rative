import sys
from pathlib import Path
from datetime import datetime, timezone

# Add backend directory to path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.main import app
from app.core.database import Base, SessionLocal, engine
from app.core.exceptions import (
    ForbiddenStatusTransitionException,
    MissingRGPDConsentException,
    CandidateNotAssignedException,
    DocumentAlreadyIndexedException,
    InvalidCredentialsException,
    TokenInvalidException
)
from app.services.auth_service import auth_service
from app.services.candidate_service import candidate_service
from app.services.conversation_service import conversation_service
from app.services.document_service import document_service
from app.services.qcm_service import qcm_service
from app.services.appointment_service import appointment_service
from app.api.deps import VisitorSession, PaginationQuery
from app.models.candidate import CandidateProfile
from app.models.user import User
from app.models.conversation import Conversation
from app.api.v1.endpoints.auth import create_anonymous_session, login, LoginRequest
from app.api.v1.endpoints.candidates import list_candidates
from app.api.v1.endpoints.preregistrations import create_preregistration, PreRegistrationCreate
from app.api.v1.endpoints.conversations import send_message, MessageCreate
from fastapi import Response


def run_all_tests():
    print("=" * 70)
    print("  SUITE DE TESTS UNITAIRES ET D'INTÉGRATION — SMARTCAMPUS AI")
    print("=" * 70)

    db = SessionLocal()
    passed = 0
    total = 0

    def test(name, func):
        nonlocal passed, total
        total += 1
        try:
            func()
            print(f"  [PASS] {name}")
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {name}: {e}")

    # --- 1. Tests Authentification & Sessions ---
    def t_anon_session():
        resp = Response()
        anon = create_anonymous_session(response=resp)
        assert anon.session_id.startswith("sess_")
        assert anon.role == "Visiteur"
    test("Auth: Création de session anonyme (Visiteur)", t_anon_session)

    def t_login_admin():
        resp = Response()
        token = login(LoginRequest(email="admin@smartcampus.tn", password="AdminSmartCampus2026!"), response=resp, db=db)
        assert token.role == "Administrateur"
        assert token.access_token is not None
    test("Auth: Connexion Administrateur unifié (Rôle Administrateur)", t_login_admin)

    def t_login_bad_password():
        resp = Response()
        try:
            login(LoginRequest(email="admin@smartcampus.tn", password="WrongPassword123!"), response=resp, db=db)
            assert False, "Devrait échouer avec 401"
        except InvalidCredentialsException as e:
            assert e.code == "AUTH_INVALID_CREDENTIALS"
            assert e.status_code == 401
    test("Auth: Erreur d'identifiants renvoie AUTH_INVALID_CREDENTIALS (401)", t_login_bad_password)

    def t_otp_flow():
        code = auth_service.request_otp("etudiant.test@iit.tn")
        assert len(code) == 6
        assert auth_service.verify_otp("etudiant.test@iit.tn", code) is True
        assert auth_service.verify_otp("etudiant.test@iit.tn", "000000") is False
    test("Auth: Flux OTP email (génération 6 chiffres et vérification)", t_otp_flow)

    # --- 2. Tests Candidats & Machine à états ---
    def t_status_transition_forbidden():
        profile = db.query(CandidateProfile).first()
        try:
            candidate_service.validate_and_update_status(profile, "EXPLORATION")
            assert False, "Transition interdite"
        except ForbiddenStatusTransitionException as e:
            assert e.code == "CANDIDATE_001"
            assert e.status_code == 409
    test("Candidat: Transition de statut interdite renvoie CANDIDATE_001 (409)", t_status_transition_forbidden)

    def t_rgpd_consent():
        v = VisitorSession("sess_unit_test")
        try:
            create_preregistration(PreRegistrationCreate(formation_id=1, consent_rgpd=False), principal=v, db=db)
            assert False, "Consentement RGPD obligatoire"
        except MissingRGPDConsentException as e:
            assert e.code == "CANDIDATE_002"
            assert e.status_code == 422
    test("Préinscription: Consentement RGPD manquant renvoie CANDIDATE_002 (422)", t_rgpd_consent)

    def t_teacher_unassigned_access():
        profile = db.query(CandidateProfile).first()
        other_teacher = db.query(User).filter(User.role.in_(["Enseignant", "enseignant", "E"]), User.id != profile.enseignant_affecte_id).first()
        if other_teacher:
            try:
                candidate_service.verify_teacher_access(other_teacher.id, profile)
                assert False, "Accès interdit à un candidat non affecté"
            except CandidateNotAssignedException as e:
                assert e.code == "CANDIDATE_003"
                assert e.status_code == 403
    test("RBAC: Enseignant accédant à un candidat non affecté renvoie CANDIDATE_003 (403)", t_teacher_unassigned_access)

    # --- 3. Tests Multimodal & RAG ---
    def t_language_detection():
        assert conversation_service.detect_language("Bonjour, je souhaite m'inscrire à l'IIT") == "fr"
        assert conversation_service.detect_language("3aslema chnowa les formations fi Sfax ?") == "arabizi"
        assert conversation_service.detect_language("عسلامة نحب نسأل على التسجيل") == "tn"
    test("Langage: Détection automatique Français / Tunisien / Arabizi", t_language_detection)

    def t_document_duplicate_sha():
        with open(BASE_DIR / "data" / "sample_corpus" / "iit_brochure_2026_2027.txt", "rb") as f:
            content = f.read()
        try:
            document_service.process_and_index_document(db, "iit_brochure_2026_2027.txt", content, "brochure", "IIT", "text/plain", 1)
            assert False, "Doublon SHA-256 non détecté"
        except DocumentAlreadyIndexedException as e:
            assert e.code == "DOC_002"
            assert e.status_code == 409
    test("RAG: Doublon de document détecté par SHA-256 renvoie DOC_002 (409)", t_document_duplicate_sha)

    # --- 4. Tests QCM & Entretien ---
    def t_qcm_generation():
        qcm = qcm_service.generate_qcm(db, candidate_id=1, formation_id=1)
        assert qcm.id is not None
        assert len(qcm.questions) >= 3
    test("QCM: Génération automatique et adaptative de questions", t_qcm_generation)

    def t_openapi_schema():
        schema = app.openapi()
        assert schema["info"]["title"].startswith("SmartCampus AI")
        assert len(schema["paths"]) >= 20
    test("Documentation: Génération automatique OpenAPI 3.1 & Swagger", t_openapi_schema)

    db.close()
    print("=" * 70)
    print(f"  RÉSULTAT : {passed}/{total} tests réussis avec succès ({round((passed/total)*100)}%) !")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
