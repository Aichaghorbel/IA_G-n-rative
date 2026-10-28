from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import Base, engine
from app.api import auth, student, admin, enseignant

# Automatically create all tables in PostgreSQL
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"Database connection note: {e}")

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url="/api/openapi.json",
    docs_url="/docs"
)

# CORS Middleware for Angular frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",
        "http://127.0.0.1:4200"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(auth.router, prefix="/api")
app.include_router(student.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(enseignant.router, prefix="/api")

@app.get("/")
def root():
    return {
        "status": "online",
        "message": "Bienvenue sur l'API UniHelp / SmartCampus",
        "docs": "/docs"
    }

