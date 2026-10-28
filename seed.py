import uuid
from app.core.database import SessionLocal, Base, engine
from app.core.security import get_password_hash
from app.models.models import User, StudentDetail, Course, FAQQuestion, Activity

def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # 1. Admin
    admin = db.query(User).filter(User.email == "admin@smartcampus.tn").first()
    if not admin:
        admin = User(
            id=str(uuid.uuid4()),
            email="admin@smartcampus.tn",
            hashed_password=get_password_hash("123456"),
            name="Directeur Administrateur",
            role="admin",
            university="ISB",
            field="Direction Générale"
        )
        db.add(admin)
        print("Created admin: admin@smartcampus.tn / 123456")

    # 2. Enseignant
    prof = db.query(User).filter(User.email == "enseignant@smartcampus.tn").first()
    if not prof:
        prof = User(
            id=str(uuid.uuid4()),
            email="enseignant@smartcampus.tn",
            hashed_password=get_password_hash("123456"),
            name="Prof. Ahmed Ben Ali",
            role="enseignant",
            university="IIT",
            field="Informatique"
        )
        db.add(prof)
        print("Created prof: enseignant@smartcampus.tn / 123456")

    # 3. Student
    student = db.query(User).filter(User.email == "etudiant@smartcampus.tn").first()
    if not student:
        student = User(
            id=str(uuid.uuid4()),
            email="etudiant@smartcampus.tn",
            hashed_password=get_password_hash("123456"),
            name="Yassine Mansour",
            role="student",
            university="ISB",
            field="Génie Logiciel"
        )
        db.add(student)
        db.flush()

        detail = StudentDetail(
            user_id=student.id,
            cin_passport="12345678",
            country="Tunisie",
            birth_date="2002-05-15",
            sex="Homme",
            phone="+216 98 123 456",
            address="Sfax, Tunisie",
            last_diploma="Baccalauréat",
            diploma_year="2020",
            desired_diploma="Licence en Informatique de Gestion (LIG)",
            level="3",
            course_time="Cours de jour",
            known_by="Réseaux sociaux"
        )
        db.add(detail)
        print("Created student: etudiant@smartcampus.tn / 123456")

    db.commit()

    # 4. Courses
    if db.query(Course).count() == 0:
        courses = [
            Course(code="INFO101", name="Algorithmique & Structures de données", teacher_id=prof.id, students_count=65, schedule="Lun 08:30 - 10:30", room="Amphi A"),
            Course(code="INFO203", name="Développement Web Moderne (Angular)", teacher_id=prof.id, students_count=45, schedule="Mar 10:45 - 12:45", room="Labo 3"),
            Course(code="INFO305", name="Bases de Données Relationnelles & SQL", teacher_id=prof.id, students_count=40, schedule="Jeu 14:00 - 16:00", room="Salle 204"),
            Course(code="INFO402", name="Génie Logiciel & Architecture", teacher_id=prof.id, students_count=35, schedule="Ven 09:00 - 12:00", room="Amphi B")
        ]
        db.add_all(courses)
        print("Created sample courses")

    db.commit()
    db.close()
    print("Database seeding completed successfully!")

if __name__ == "__main__":
    seed()

