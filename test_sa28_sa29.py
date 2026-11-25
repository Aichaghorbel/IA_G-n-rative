#!/usr/bin/env python3
"""Test simple SA-28 + SA-29.   Usage : python test_sa28_sa29.py [http://localhost:8000]
Prerequis : backend demarre, DEBUG=True (dev_code OTP), comptes de demo charges."""
import json, sys, uuid, urllib.request, urllib.error

HOST = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000").rstrip("/")
B = HOST + "/api/v1"
ADMIN = ("admin@smartcampus.tn", "AdminSmartCampus2026!")
TEACHER = ("enseignant.iit@smartcampus.tn", "TeacherPassword2026!")
CAND = ("sarra.benali@gmail.com", "CandidatePassword2026!")
PWD = "Motdepasse123!"
ok = ko = 0


def call(method, path, body=None, token=None, session=None):
    h = {"Content-Type": "application/json"}
    if token:
        h["Authorization"] = "Bearer " + token
    if session:
        h["X-Session-Token"] = session
    req = urllib.request.Request(B + path, method=method, headers=h,
                                 data=json.dumps(body).encode() if body is not None else None)
    try:
        r = urllib.request.urlopen(req, timeout=120)
        code, raw, hd = r.status, r.read(), r.headers
    except urllib.error.HTTPError as e:
        code, raw, hd = e.code, e.read(), e.headers
    try:
        data = json.loads(raw)
    except Exception:
        data = {}
    return code, data, hd


def check(name, cond):
    global ok, ko
    ok, ko = (ok + 1, ko) if cond else (ok, ko + 1)
    print(("  [OK]   " if cond else "  [FAIL] ") + name)


def login(c, session=None):
    code, d, _ = call("POST", "/auth/login", {"email": c[0], "password": c[1]}, session=session)
    return code, d


def register(session=None):
    email = f"t.{uuid.uuid4().hex[:8]}@example.com"
    _, d, _ = call("POST", "/auth/otp/request", {"email": email})
    _, v, _ = call("POST", "/auth/otp/verify", {"email": email, "otp_code": d["dev_code"]})
    code, r, _ = call("POST", "/auth/register", {"verification_token": v["verification_token"],
                      "password": PWD, "nom": "Ben Salah", "prenom": "Amira"}, session=session)
    return code, r


# ============================== SA-28 ==============================
print("\nSA-28 : connexion, roles, autorisations, chat libre")
roles = {}
for label, c, role in (("admin", ADMIN, "Administrateur"), ("enseignant", TEACHER, "Enseignant"),
                       ("candidat", CAND, "Candidat")):
    code, d = login(c)
    check(f"connexion {label} -> role {role}", code == 200 and d.get("role") == role)
    roles[label] = d.get("access_token")

code, d, hd = call("POST", "/conversations")
check("chat libre : conversation sans aucun jeton (201)", code == 201)
check("chat libre : jeton de session renvoye", bool(hd.get("X-Session-Token")))
code, d2, _ = call("POST", f"/conversations/{d['conversation_id']}/messages",
                   {"message": "Bonjour"}, session=hd.get("X-Session-Token"))
check("chat libre : le visiteur peut ecrire (200)", code == 200)

_, s, _ = call("POST", "/sessions")
vis = s["session_token"]
check("sans jeton -> /admin/metrics = 401", call("GET", "/admin/metrics")[0] == 401)
check("visiteur -> /admin/metrics = 403", call("GET", "/admin/metrics", session=vis)[0] == 403)
check("visiteur -> /recommendations/me = 403", call("GET", "/recommendations/me", session=vis)[0] == 403)
check("candidat -> /admin/metrics = 403", call("GET", "/admin/metrics", token=roles["candidat"])[0] == 403)
check("candidat -> /auth/users = 403", call("GET", "/auth/users", token=roles["candidat"])[0] == 403)
check("enseignant -> /admin/metrics = 403", call("GET", "/admin/metrics", token=roles["enseignant"])[0] == 403)
check("enseignant -> /recommendations/me = 403", call("GET", "/recommendations/me", token=roles["enseignant"])[0] == 403)
check("enseignant -> /candidates autorise", call("GET", "/candidates", token=roles["enseignant"])[0] not in (401, 403))
check("admin -> /admin/metrics = 200", call("GET", "/admin/metrics", token=roles["admin"])[0] == 200)
check("admin -> /auth/users = 200", call("GET", "/auth/users", token=roles["admin"])[0] == 200)

forged = roles["candidat"][:-3] + "AAA"
check("jeton falsifie -> 401", call("GET", "/auth/me", token=forged)[0] == 401)
_, t, _ = call("POST", "/auth/login", {"email": CAND[0], "password": CAND[1]})
check("refresh token comme jeton d'acces -> 401", call("GET", "/auth/me", token=t["refresh_token"])[0] == 401)
call("POST", "/auth/logout", {"refresh_token": t["refresh_token"]}, token=t["access_token"])
check("apres deconnexion, ancien jeton -> 401", call("GET", "/auth/me", token=t["access_token"])[0] == 401)

# ============================== SA-29 ==============================
print("\nSA-29 : conserver la conversation du visiteur")
_, s, _ = call("POST", "/sessions")
tok, sid = s["session_token"], s["session_id"]
_, c, _ = call("POST", "/conversations", session=tok)
cid = c["conversation_id"]
call("POST", f"/conversations/{cid}/messages", {"message": "Quelles formations en informatique ?"}, session=tok)

code, r = register(session=tok)
acc = r.get("access_token")
check("inscription avec X-Session-Token (200/201)", code in (200, 201) and acc)
sl = r.get("session_link") or {}
check("proposition d'association (available, bon session_id)", sl.get("available") is True and sl.get("session_id") == sid)
check("accord requis (consent_required)", sl.get("consent_required") is True)
check("rien associe avant l'accord (conversation anonyme)",
      call("GET", f"/conversations/{cid}", session=tok)[1].get("is_anonymous") is True)

body = {"session_id": sid, "consent": True}
check("sans aucun jeton -> 401", call("POST", "/auth/session-link", body)[0] == 401)
check("jeton de session seul (pas connecte) -> 403", call("POST", "/auth/session-link", body, session=tok)[0] == 403)
code, d, _ = call("POST", "/auth/session-link", {"session_id": sid, "consent": False}, token=acc, session=tok)
check("sans accord (consent=false) -> 422 SESSION_LINK_001", code == 422 and d["error"]["code"] == "SESSION_LINK_001")
code, d, _ = call("POST", "/auth/session-link", {"session_id": str(uuid.uuid4()), "consent": True}, token=acc, session=tok)
check("mauvais session_id -> 403 SESSION_LINK_003", code == 403 and d["error"]["code"] == "SESSION_LINK_003")
check("jeton de session falsifie -> 401",
      call("POST", "/auth/session-link", body, token=acc, session=tok[:-3] + "AAA")[0] == 401)

code, d, _ = call("POST", "/auth/session-link", body, token=acc, session=tok)
check("association avec accord -> 200 linked", code == 200 and d.get("linked") is True)
code, d, _ = call("POST", "/auth/session-link", body, token=acc, session=tok)
check("rejouer -> idempotent (already_linked)", code == 200 and d.get("already_linked") is True)
_, lst, _ = call("GET", "/conversations", token=acc)
check("le candidat retrouve la conversation", cid in [x["conversation_id"] for x in lst])
_, conv, _ = call("GET", f"/conversations/{cid}", token=acc)
check("historique conserve (>= 2 messages)", len(conv.get("messages", [])) >= 2)
check("le candidat peut continuer la conversation",
      call("POST", f"/conversations/{cid}/messages", {"message": "Et le master ?"}, token=acc)[0] == 200)
check("cote visiteur anonyme : conversation introuvable (404)",
      call("GET", f"/conversations/{cid}", session=tok)[0] == 404)

_, r2 = register()
thief = r2["access_token"]
code, d, _ = call("POST", "/auth/session-link", body, token=thief, session=tok)
check("un autre candidat ne peut pas voler la session -> 409 SESSION_LINK_002",
      code == 409 and d["error"]["code"] == "SESSION_LINK_002")
check("l'autre candidat ne voit pas la conversation (404)",
      call("GET", f"/conversations/{cid}", token=thief)[0] == 404)

print(f"\nRESULTAT : {ok} reussis, {ko} echoues")
sys.exit(1 if ko else 0)
