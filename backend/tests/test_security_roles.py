"""
Tests de l'authentification, des rôles et du contrôle d'accès.
Visiteur (sans compte) / Candidat / Enseignant / Administrateur.
"""
import uuid

import pytest

from app.core.config import settings
from app.services.otp_service import otp_service

API = "/api/v1"
STRONG = "Str0ngPassw0rd!"


@pytest.fixture(autouse=True)
def _relax_limits_and_reset_otp():
    old = settings.SESSION_CREATE_PER_IP_PER_HOUR
    settings.SESSION_CREATE_PER_IP_PER_HOUR = 10_000
    otp_service.clear()
    yield
    settings.SESSION_CREATE_PER_IP_PER_HOUR = old


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


def login(client, email, password):
    return client.post(f"{API}/auth/login", json={"email": email, "password": password})


def create_staff(client, admin_token, role="Enseignant", password=STRONG):
    """Crée un compte enseignant et le rend utilisable (changement du mot de passe initial)."""
    email = f"{role.lower()}.{uuid.uuid4().hex[:8]}@smartcampus.tn"
    res = client.post(f"{API}/auth/users", headers=bearer(admin_token), json={
        "email": email, "password": password, "nom": "Test", "prenom": role, "role": role,
    })
    assert res.status_code == 201, res.text
    return email, res.json()["id"]


def ready_user(client, admin_token, role="Enseignant"):
    """Compte du personnel avec mot de passe définitif -> (email, password, access, refresh, id)."""
    email, uid = create_staff(client, admin_token, role)
    tok = login(client, email, STRONG).json()
    assert tok["must_change_password"] is True
    new_pw = "N3wStr0ngPass!"
    r = client.post(f"{API}/auth/change-password", headers=bearer(tok["access_token"]),
                    json={"current_password": STRONG, "new_password": new_pw})
    assert r.status_code == 204, r.text
    tok = login(client, email, new_pw).json()
    return email, new_pw, tok["access_token"], tok["refresh_token"], uid


# ------------------------------------------------------------------ jetons
def test_refresh_token_cannot_be_used_as_access_token(client):
    tok = login(client, "admin@smartcampus.tn", "AdminSmartCampus2026!").json()
    res = client.get(f"{API}/auth/me", headers=bearer(tok["refresh_token"]))
    assert res.status_code == 401


def test_garbage_and_malformed_authorization_rejected(client):
    assert client.get(f"{API}/auth/me", headers=bearer("not.a.jwt")).status_code == 401
    assert client.get(f"{API}/auth/me", headers={"Authorization": "Basic abc"}).status_code == 401


def test_refresh_rotation_and_reuse_detection(client):
    tok = login(client, "admin@smartcampus.tn", "AdminSmartCampus2026!").json()
    r1 = client.post(f"{API}/auth/refresh", json={"refresh_token": tok["refresh_token"]})
    assert r1.status_code == 200
    body = r1.json()
    assert body["role"] == "Administrateur" and body["user_id"] > 0
    # L'ancien refresh token est consommé : le rejouer est refusé...
    r2 = client.post(f"{API}/auth/refresh", json={"refresh_token": tok["refresh_token"]})
    assert r2.status_code == 401
    # ... et coupe toutes les sessions du compte (vol présumé)
    assert client.get(f"{API}/auth/me", headers=bearer(body["access_token"])).status_code == 401


def test_logout_revokes_access_token(client, admin_token):
    email, pw, access, refresh, _ = ready_user(client, admin_token)
    assert client.get(f"{API}/auth/me", headers=bearer(access)).status_code == 200
    out = client.post(f"{API}/auth/logout", headers=bearer(access), json={"refresh_token": refresh})
    assert out.status_code == 204
    assert client.get(f"{API}/auth/me", headers=bearer(access)).status_code == 401
    assert client.post(f"{API}/auth/refresh", json={"refresh_token": refresh}).status_code == 401


# ------------------------------------------------------------------ connexion
def test_login_unknown_email_same_error_as_bad_password(client):
    a = login(client, "inconnu@nowhere.tn", "Whatever123")
    b = login(client, "admin@smartcampus.tn", "WrongPassword123")
    assert a.status_code == b.status_code == 401
    assert a.json()["error"]["code"] == b.json()["error"]["code"] == "AUTH_INVALID_CREDENTIALS"


def test_account_lockout_after_repeated_failures(client, admin_token):
    email, _ = create_staff(client, admin_token)
    for _ in range(settings.LOGIN_MAX_ATTEMPTS):
        assert login(client, email, "bad-password").status_code == 401
    locked = login(client, email, STRONG)  # même le bon mot de passe est refusé
    assert locked.status_code == 423
    assert locked.json()["error"]["code"] == "AUTH_005"
    assert "Retry-After" in locked.headers


def test_deactivated_account_loses_access_immediately(client, admin_token):
    email, pw, access, _, uid = ready_user(client, admin_token)
    res = client.patch(f"{API}/auth/users/{uid}", headers=bearer(admin_token), json={"is_active": False})
    assert res.status_code == 200 and res.json()["is_active"] is False
    assert client.get(f"{API}/auth/me", headers=bearer(access)).status_code == 401
    assert login(client, email, pw).status_code == 401


def test_admin_cannot_deactivate_self(client, admin_token):
    me = client.get(f"{API}/auth/me", headers=bearer(admin_token)).json()
    res = client.patch(f"{API}/auth/users/{me['id']}", headers=bearer(admin_token), json={"is_active": False})
    assert res.status_code == 409


# ------------------------------------------------------------------ comptes
def test_create_user_validation(client, admin_token, teacher_token):
    h = bearer(admin_token)
    base = {"email": f"x{uuid.uuid4().hex[:6]}@smartcampus.tn", "nom": "A", "prenom": "B"}
    # rôle Candidat interdit via cette route
    assert client.post(f"{API}/auth/users", headers=h, json={**base, "password": STRONG, "role": "Candidat"}).status_code == 422
    # mot de passe faible
    weak = client.post(f"{API}/auth/users", headers=h, json={**base, "password": "alllowercase", "role": "Enseignant"})
    assert weak.status_code == 422
    # doublon
    ok = client.post(f"{API}/auth/users", headers=h, json={**base, "password": STRONG, "role": "Enseignant"})
    assert ok.status_code == 201
    dup = client.post(f"{API}/auth/users", headers=h, json={**base, "password": STRONG, "role": "Enseignant"})
    assert dup.status_code == 409
    # administrateur unique : impossible d'en créer un second, même en étant admin
    second_admin = client.post(f"{API}/auth/users", headers=h,
                               json={**base, "email": "autre.admin@smartcampus.tn", "password": STRONG, "role": "Administrateur"})
    assert second_admin.status_code == 422
    # un enseignant ne peut pas créer de comptes
    forbidden = client.post(f"{API}/auth/users", headers=bearer(teacher_token),
                            json={**base, "email": "y@smartcampus.tn", "password": STRONG, "role": "Enseignant"})
    assert forbidden.status_code == 403


def test_temporary_password_must_be_changed_first(client, admin_token):
    email, _ = create_staff(client, admin_token)
    tok = login(client, email, STRONG).json()
    assert tok["must_change_password"] is True
    # bloqué partout sauf /me, /logout, /change-password
    blocked = client.get(f"{API}/candidates", headers=bearer(tok["access_token"]))
    assert blocked.status_code == 403
    assert blocked.json()["error"]["code"] == "AUTH_010"
    assert client.get(f"{API}/auth/me", headers=bearer(tok["access_token"])).status_code == 200


def test_change_password_invalidates_old_tokens(client, admin_token):
    email, uid = create_staff(client, admin_token)
    tok = login(client, email, STRONG).json()
    bad = client.post(f"{API}/auth/change-password", headers=bearer(tok["access_token"]),
                      json={"current_password": "wrong", "new_password": "N3wStr0ngPass!"})
    assert bad.status_code == 401
    ok = client.post(f"{API}/auth/change-password", headers=bearer(tok["access_token"]),
                     json={"current_password": STRONG, "new_password": "N3wStr0ngPass!"})
    assert ok.status_code == 204
    assert client.get(f"{API}/auth/me", headers=bearer(tok["access_token"])).status_code == 401


# ------------------------------------------------------------------ rôles
def test_role_matrix_on_protected_routes(client, admin_token, teacher_token, candidate_token):
    # sans jeton : 401 (authentification requise), jamais 403
    assert client.get(f"{API}/candidates").status_code == 401
    assert client.get(f"{API}/admin/metrics").status_code == 401

    # visiteur avec session : authentifié mais rôle insuffisant -> 403
    sess = client.post(f"{API}/auth/sessions/anonymous").json()
    vis = {"X-Session-Token": sess["session_token"]}
    assert client.get(f"{API}/candidates", headers=vis).status_code == 403
    assert client.get(f"{API}/candidates/me", headers=vis).status_code == 403

    # candidat
    assert client.get(f"{API}/admin/metrics", headers=bearer(candidate_token)).status_code == 403
    assert client.get(f"{API}/candidates", headers=bearer(candidate_token)).status_code == 403

    # enseignant
    assert client.get(f"{API}/admin/metrics", headers=bearer(teacher_token)).status_code == 403
    assert client.get(f"{API}/candidates/me", headers=bearer(teacher_token)).status_code == 403
    assert client.get(f"{API}/candidates", headers=bearer(teacher_token)).status_code not in (401, 403)

    # administrateur
    assert client.get(f"{API}/admin/metrics", headers=bearer(admin_token)).status_code not in (401, 403)


def test_me_returns_role_permissions(client, candidate_token, admin_token):
    c = client.get(f"{API}/auth/me", headers=bearer(candidate_token)).json()
    assert c["role"] == "Candidat" and "chat" in c["permissions"] and "*" not in c["permissions"]
    a = client.get(f"{API}/auth/me", headers=bearer(admin_token)).json()
    assert a["permissions"] == ["*"]


# ------------------------------------------------------------------ chat libre
def test_visitor_chat_is_free_without_any_account_or_token(client):
    res = client.post(f"{API}/conversations")  # aucun en-tête
    assert res.status_code == 201, res.text
    token = res.headers.get("X-Session-Token")
    assert token, "le jeton de session doit être renvoyé au visiteur"
    conv_id = res.json()["conversation_id"]

    msg = client.post(f"{API}/conversations/{conv_id}/messages",
                      headers={"X-Session-Token": token},
                      json={"message": "Quelles sont les formations de l'IIT ?"})
    assert msg.status_code == 200, msg.text
    assert msg.json()["response"]

    history = client.get(f"{API}/conversations/{conv_id}/messages", headers={"X-Session-Token": token})
    assert history.status_code == 200
    assert [m["role"] for m in history.json()] == ["user", "assistant"]


def test_visitor_with_anonymous_session_can_chat(client):
    sess = client.post(f"{API}/auth/sessions/anonymous").json()
    h = {"X-Session-Token": sess["session_token"]}
    conv = client.post(f"{API}/conversations", headers=h)
    assert conv.status_code == 201
    assert "X-Session-Token" not in conv.headers  # déjà identifié : pas de nouvelle session
    assert client.get(f"{API}/conversations", headers=h).json()[0]["conversation_id"] == conv.json()["conversation_id"]


def test_conversations_are_private_between_visitors(client):
    a = client.post(f"{API}/conversations")
    client.cookies.clear()
    b = client.post(f"{API}/conversations")
    client.cookies.clear()
    ha = {"X-Session-Token": a.headers["X-Session-Token"]}
    hb = {"X-Session-Token": b.headers["X-Session-Token"]}
    cid = a.json()["conversation_id"]
    # B ne peut ni lire, ni écrire, ni supprimer la conversation de A (404 : on ne révèle rien)
    assert client.get(f"{API}/conversations/{cid}", headers=hb).status_code == 404
    assert client.post(f"{API}/conversations/{cid}/messages", headers=hb, json={"message": "salut"}).status_code == 404
    assert client.get(f"{API}/conversations/{cid}/messages", headers=hb).status_code == 404
    assert client.delete(f"{API}/conversations/{cid}", headers=hb).status_code == 404
    # A garde l'accès
    assert client.get(f"{API}/conversations/{cid}", headers=ha).status_code == 200


def test_teacher_cannot_chat_or_read_unrelated_conversation(client, teacher_token):
    conv = client.post(f"{API}/conversations")
    cid = conv.json()["conversation_id"]
    assert client.post(f"{API}/conversations", headers=bearer(teacher_token)).status_code == 403
    # conversation anonyme : sans lien candidat -> invisible pour l'enseignant
    assert client.get(f"{API}/conversations/{cid}/messages", headers=bearer(teacher_token)).status_code == 404


def test_visitor_session_token_is_tied_to_database(client):
    sess = client.post(f"{API}/auth/sessions/anonymous").json()
    token = sess["session_token"]
    assert client.get(f"{API}/sessions/me", headers={"X-Session-Token": token}).status_code == 200
    assert client.delete(f"{API}/sessions/me", headers={"X-Session-Token": token}).status_code == 204
    # session supprimée (RGPD) : le jeton ne vaut plus rien
    assert client.get(f"{API}/sessions/me", headers={"X-Session-Token": token}).status_code == 401


def test_websocket_chat_open_to_visitors_but_rejects_bad_token(client):
    with client.websocket_connect(f"{API}/conversations/ws/chat") as ws:
        ws.send_text('{"message": "bonjour"}')
        chunks = []
        while True:
            data = ws.receive_json()
            if data.get("done"):
                break
            chunks.append(data["token"])
        assert chunks
    with pytest.raises(Exception):
        with client.websocket_connect(f"{API}/conversations/ws/chat?token=garbage"):
            pass


# ------------------------------------------------------------------ OTP
def test_otp_single_use_and_attempt_limit(client):
    email = "otp.test@gmail.com"
    code = client.post(f"{API}/auth/otp/request", json={"email": email}).json()["dev_code"]

    ok = client.post(f"{API}/auth/otp/verify", json={"email": email, "otp_code": code})
    assert ok.status_code == 200 and ok.json()["verification_token"]
    # usage unique
    assert client.post(f"{API}/auth/otp/verify", json={"email": email, "otp_code": code}).status_code == 400

    # trop d'essais
    otp_service.clear()
    code = client.post(f"{API}/auth/otp/request", json={"email": email}).json()["dev_code"]
    wrong = "000000" if code != "000000" else "111111"
    statuses = [client.post(f"{API}/auth/otp/verify", json={"email": email, "otp_code": wrong}).status_code
                for _ in range(settings.OTP_MAX_ATTEMPTS)]
    assert statuses[-1] == 429
    # le bon code ne marche plus : il faut redemander un OTP
    assert client.post(f"{API}/auth/otp/verify", json={"email": email, "otp_code": code}).status_code == 400


def test_otp_resend_cooldown(client):
    email = "cooldown@gmail.com"
    assert client.post(f"{API}/auth/otp/request", json={"email": email}).status_code == 200
    assert client.post(f"{API}/auth/otp/request", json={"email": email}).status_code == 429


def test_otp_code_format_validated(client):
    res = client.post(f"{API}/auth/otp/verify", json={"email": "a@b.tn", "otp_code": "12ab"})
    assert res.status_code == 422


# ------------------------------------------------------------------ conversion visiteur -> candidat
def test_convert_requires_staff_and_forces_password_change(client, admin_token, teacher_token):
    payload = {"session_id": "sess_x", "email": f"new{uuid.uuid4().hex[:6]}@gmail.com",
               "nom": "Nouveau", "prenom": "Candidat"}
    # anonyme / visiteur : refusé
    assert client.post(f"{API}/auth/convert", json=payload).status_code == 401
    sess = client.post(f"{API}/auth/sessions/anonymous").json()
    assert client.post(f"{API}/auth/convert", json=payload,
                       headers={"X-Session-Token": sess["session_token"]}).status_code == 403

    res = client.post(f"{API}/auth/convert", json=payload, headers=bearer(teacher_token))
    assert res.status_code == 201, res.text
    temp = res.json()["temporary_password"]
    assert temp and len(temp) >= 12

    tok = login(client, payload["email"], temp).json()
    assert tok["role"] == "Candidat" and tok["must_change_password"] is True
    assert client.get(f"{API}/candidates/me", headers=bearer(tok["access_token"])).json()["error"]["code"] == "AUTH_010"


def test_convert_never_downgrades_staff_account(client, admin_token):
    res = client.post(f"{API}/auth/convert", headers=bearer(admin_token), json={
        "session_id": "sess_y", "email": "admin@smartcampus.tn", "nom": "X", "prenom": "Y"})
    assert res.status_code == 409


# ------------------------------------------------------------------ transition visiteur -> candidat (cookies + X-Session-Token)
def test_visitor_becomes_candidate_with_cookie_and_session_header(client):
    """
    Régression : un visiteur qui s'inscrit tout en gardant X-Session-Token (en-tête ou cookie)
    et s'appuie sur le cookie access_token ne doit pas retomber en rôle Visiteur (403).
    """
    # 1. Visiteur démarre une conversation (reçoit X-Session-Token + cookie session_token)
    conv = client.post(f"{API}/conversations")
    assert conv.status_code == 201
    vis_token = conv.headers["X-Session-Token"]
    cid = conv.json()["conversation_id"]
    msg = client.post(f"{API}/conversations/{cid}/messages", headers={"X-Session-Token": vis_token},
                      json={"message": "Je veux faire Génie Logiciel à l'IIT"})
    assert msg.status_code == 200

    # 2. Visiteur vérifie son e-mail et crée son compte candidat (avec X-Session-Token)
    email = f"vis.to.cand.{uuid.uuid4().hex[:8]}@gmail.com"
    code = client.post(f"{API}/auth/otp/request", json={"email": email}).json()["dev_code"]
    verif = client.post(f"{API}/auth/otp/verify", json={"email": email, "otp_code": code}).json()["verification_token"]

    reg = client.post(
        f"{API}/auth/register",
        headers={"X-Session-Token": vis_token},
        json={"verification_token": verif, "password": STRONG, "nom": "Ben", "prenom": "Ali"},
    )
    assert reg.status_code == 201, reg.text
    body = reg.json()
    assert body["role"] == "Candidat"
    assert body["session_link"] and body["session_link"]["available"] is True
    sid = body["session_link"]["session_id"]

    # 3. Même avec X-Session-Token encore présent et authentification par cookie access_token,
    #    les routes Candidat et /auth/session-link doivent reconnaître le rôle Candidat (pas 403 Visiteur).
    prop = client.get(f"{API}/auth/session-link/proposal", headers={"X-Session-Token": vis_token})
    assert prop.status_code == 200, prop.text
    assert prop.json()["available"] is True

    linked = client.post(
        f"{API}/auth/session-link",
        headers={"X-Session-Token": vis_token},
        json={"session_id": sid, "consent": True},
    )
    assert linked.status_code == 200, linked.text
    assert linked.json()["linked"] is True

    me = client.get(f"{API}/auth/me", headers={"X-Session-Token": vis_token})
    assert me.status_code == 200 and me.json()["role"] == "Candidat"

    prof = client.get(f"{API}/candidates/me", headers={"X-Session-Token": vis_token})
    assert prof.status_code == 200, prof.text

    upd = client.patch(
        f"{API}/candidates/me/profile",
        headers={"X-Session-Token": vis_token},
        json={"universite": "IIT", "dernierDiplomeObtenu": "Baccalauréat", "niveau": 1},
    )
    assert upd.status_code == 200, upd.text
    assert upd.json()["universite"] == "IIT"

    recs = client.get(f"{API}/recommendations/me", headers={"X-Session-Token": vis_token})
    assert recs.status_code == 200 and len(recs.json()) >= 1


def test_visitor_preregistration_and_qcm_carried_over_on_register(client):
    """Un visiteur peut se préinscrire, passer un QCM puis s'inscrire et associer sa session sans conflit 409."""
    sess = client.post(f"{API}/auth/sessions/anonymous").json()
    vis_h = {"X-Session-Token": sess["session_token"]}

    prereg = client.post(f"{API}/preregistrations", headers=vis_h, json={"formation_id": 1, "consent_rgpd": True})
    assert prereg.status_code == 201, prereg.text
    prereg_id = prereg.json()["id"]

    assert client.get(f"{API}/preregistrations/{prereg_id}", headers=vis_h).status_code == 200

    qcm = client.post(f"{API}/qcm?preinscription_id={prereg_id}", headers=vis_h)
    assert qcm.status_code == 201, qcm.text
    qcm_id = qcm.json()["id"]
    q_id = qcm.json()["questions"][0]["id"]

    ans = client.post(f"{API}/qcm/{qcm_id}/answers", headers=vis_h,
                      json={"reponses": [{"question_id": q_id, "estSelectionne": True}]})
    assert ans.status_code == 200

    email = f"prereg.vis.{uuid.uuid4().hex[:8]}@gmail.com"
    code = client.post(f"{API}/auth/otp/request", json={"email": email}).json()["dev_code"]
    verif = client.post(f"{API}/auth/otp/verify", json={"email": email, "otp_code": code}).json()["verification_token"]
    reg = client.post(
        f"{API}/auth/register",
        headers=vis_h,
        json={"verification_token": verif, "password": STRONG, "nom": "Trabelsi", "prenom": "Yassine"},
    )
    assert reg.status_code == 201
    acc = reg.json()["access_token"]

    linked = client.post(
        f"{API}/auth/session-link",
        headers={**bearer(acc), **vis_h},
        json={"session_id": sess["session_id"], "consent": True},
    )
    assert linked.status_code == 200, linked.text

    # La préinscription et le résultat du QCM appartiennent maintenant au candidat
    assert client.get(f"{API}/preregistrations/{prereg_id}", headers=bearer(acc)).status_code == 200
    assert client.get(f"{API}/qcm/{qcm_id}/result", headers=bearer(acc)).status_code == 200


def test_admin_stats_documents_and_notifications_work(client, admin_token, candidate_token):
    assert client.get(f"{API}/stats/overview", headers=bearer(admin_token)).status_code == 200
    notifs = client.get(f"{API}/notifications", headers=bearer(candidate_token))
    assert notifs.status_code == 200, notifs.text
    if notifs.json():
        nid = notifs.json()[0]["id"]
        assert client.patch(f"{API}/notifications/{nid}/read", headers=bearer(candidate_token)).status_code == 200

    up = client.post(
        f"{API}/documents",
        headers=bearer(admin_token),
        data={"doc_type": "brochure", "etablissement": "IIT"},
        files={"file": (f"doc_{uuid.uuid4().hex[:6]}.txt", b"Programme Ingenieur IIT 2026", "text/plain")},
    )
    assert up.status_code == 201, up.text
    doc_id = up.json()["id"]
    assert client.get(f"{API}/documents/{doc_id}/status", headers=bearer(admin_token)).status_code == 200
    assert client.post(f"{API}/documents/rag/search", json={"query": "IIT", "top_k": 3}).status_code == 200


def test_sa29_session_link_consent_ownership_and_convert_flow(client, teacher_token):
    """Vérifie le flux SA-29 complet (consentement, propriété, idempotence, vol 409) + /auth/convert."""
    s = client.post(f"{API}/sessions").json()
    tok, sid = s["session_token"], s["session_id"]
    cid = client.post(f"{API}/conversations", headers={"X-Session-Token": tok}).json()["conversation_id"]
    client.post(f"{API}/conversations/{cid}/messages", headers={"X-Session-Token": tok},
                json={"message": "Quelles formations en informatique ?"})
    client.cookies.clear()

    email = f"sa29.{uuid.uuid4().hex[:8]}@gmail.com"
    code = client.post(f"{API}/auth/otp/request", json={"email": email}).json()["dev_code"]
    verif = client.post(f"{API}/auth/otp/verify", json={"email": email, "otp_code": code}).json()["verification_token"]
    reg = client.post(
        f"{API}/auth/register",
        headers={"X-Session-Token": tok},
        json={"verification_token": verif, "password": STRONG, "nom": "Ben Salah", "prenom": "Amira"},
    ).json()
    acc = reg["access_token"]
    client.cookies.clear()

    # Consentement refusé -> 422 SESSION_LINK_001
    r_no = client.post(f"{API}/auth/session-link", headers={**bearer(acc), "X-Session-Token": tok},
                       json={"session_id": sid, "consent": False})
    assert r_no.status_code == 422 and r_no.json()["error"]["code"] == "SESSION_LINK_001"

    # Mauvais session_id -> 403 SESSION_LINK_003
    r_bad = client.post(f"{API}/auth/session-link", headers={**bearer(acc), "X-Session-Token": tok},
                        json={"session_id": str(uuid.uuid4()), "consent": True})
    assert r_bad.status_code == 403 and r_bad.json()["error"]["code"] == "SESSION_LINK_003"

    # Association + idempotence
    r_ok = client.post(f"{API}/auth/session-link", headers={**bearer(acc), "X-Session-Token": tok},
                       json={"session_id": sid, "consent": True})
    assert r_ok.status_code == 200 and r_ok.json()["linked"] is True
    r_dup = client.post(f"{API}/auth/session-link", headers={**bearer(acc), "X-Session-Token": tok},
                        json={"session_id": sid, "consent": True})
    assert r_dup.status_code == 200 and r_dup.json()["already_linked"] is True

    # Candidat retrouve et continue la conversation ; visiteur anonyme ne la voit plus (404)
    assert cid in [c["conversation_id"] for c in client.get(f"{API}/conversations", headers=bearer(acc)).json()]
    assert client.post(f"{API}/conversations/{cid}/messages", headers=bearer(acc),
                       json={"message": "Et le master ?"}).status_code == 200
    assert client.get(f"{API}/conversations/{cid}", headers={"X-Session-Token": tok}).status_code == 404

    # Autre candidat ne peut pas voler la session -> 409 SESSION_LINK_002
    email2 = f"thief.{uuid.uuid4().hex[:8]}@gmail.com"
    code2 = client.post(f"{API}/auth/otp/request", json={"email": email2}).json()["dev_code"]
    verif2 = client.post(f"{API}/auth/otp/verify", json={"email": email2, "otp_code": code2}).json()["verification_token"]
    thief = client.post(
        f"{API}/auth/register",
        json={"verification_token": verif2, "password": STRONG, "nom": "Other", "prenom": "User"},
    ).json()["access_token"]
    client.cookies.clear()
    r_steal = client.post(f"{API}/auth/session-link", headers={**bearer(thief), "X-Session-Token": tok},
                          json={"session_id": sid, "consent": True})
    assert r_steal.status_code == 409 and r_steal.json()["error"]["code"] == "SESSION_LINK_002"

    # Conversion par un enseignant (/auth/convert) rattache les conversations du visiteur
    s2 = client.post(f"{API}/sessions").json()
    cid2 = client.post(f"{API}/conversations", headers={"X-Session-Token": s2["session_token"]}).json()["conversation_id"]
    c_email = f"conv.{uuid.uuid4().hex[:8]}@gmail.com"
    conv_res = client.post(
        f"{API}/auth/convert",
        headers=bearer(teacher_token),
        json={"session_id": s2["session_id"], "email": c_email, "nom": "Converted", "prenom": "Vis"},
    )
    assert conv_res.status_code == 201
    temp_pw = conv_res.json()["temporary_password"]
    t1 = login(client, c_email, temp_pw).json()["access_token"]
    client.post(f"{API}/auth/change-password", headers=bearer(t1),
                json={"current_password": temp_pw, "new_password": "N3wStr0ngPass!"})
    t2 = login(client, c_email, "N3wStr0ngPass!").json()["access_token"]
    client.cookies.clear()
    assert cid2 in [c["conversation_id"] for c in client.get(f"{API}/conversations", headers=bearer(t2)).json()]
