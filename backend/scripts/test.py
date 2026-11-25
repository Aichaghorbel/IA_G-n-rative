from app.core.database import SessionLocal
from app.core.exceptions import RateLimitExceededException
from app.models.visitor_session import ConversationMessage
from app.services.session_memory_service import session_memory_service as mem
from app.services.session_service import session_service

db = SessionLocal()


def new_session():
    s, _ = session_service.create_session(db, None)  # None = pas de limite IP
    return s


def check(name, cond):
    print(("OK   " if cond else "ECHEC"), name)


# 1. Messages et contexte dans l'ordre
s = new_session()
mem.add_message(db, s, "user", "Je veux faire informatique")
mem.add_message(db, s, "assistant", "L'IIT propose une Licence Informatique")
mem.add_message(db, s, "user", "Et les frais ?")
ctx = mem.get_context(db, s)
check("3 messages dans le contexte", len(ctx["messages"]) == 3)
check("ordre chronologique", ctx["messages"][0]["content"].startswith("Je veux"))
check("compteur de messages user = 2", s.user_message_count == 2)

# 2. Profil
mem.update_profile(db, s, {"niveau": "Bac Maths", "interets": ["informatique"]})
mem.update_profile(db, s, {"interets": ["gestion", "informatique"]})
p = mem.get_context(db, s)["profile"]
check("profil fusionné sans doublon", p["interets"] == ["informatique", "gestion"])

# 3. Expiration glissante
old = s.expires_at
mem.add_message(db, s, "assistant", "test")
check("expiration renouvelée", s.expires_at >= old)

# 4. Limite de stockage (50) et de contexte (20)
s2 = new_session()
for i in range(60):
    mem.add_message(db, s2, "assistant", f"msg {i}")
n = db.query(ConversationMessage).filter_by(session_id=s2.id).count()
check(f"stockage limité à 50 (trouvé {n})", n == 50)
check("contexte limité à 20", len(mem.get_context(db, s2)["messages"]) == 20)
check("les plus récents sont gardés",
      mem.get_context(db, s2)["messages"][-1]["content"] == "msg 59")

# 5. Rate limiting (20 messages user / minute)
s3 = new_session()
try:
    for i in range(25):
        mem.add_message(db, s3, "user", f"spam {i}")
    check("rate limit déclenché", False)
except RateLimitExceededException:
    check(f"rate limit déclenché au message {s3.user_message_count + 1}", True)

# 6. Suppression RGPD (cascade)
sid = s.id
session_service.delete_session(db, s)
left = db.query(ConversationMessage).filter_by(session_id=sid).count()
check("messages supprimés avec la session", left == 0)

# Nettoyage des sessions de test
for x in (s2, s3):
    session_service.delete_session(db, x)
db.close()