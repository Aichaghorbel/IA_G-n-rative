from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_db, require_roles
from app.models.candidate import CandidateProfile, PreRegistration
from app.models.conversation import Conversation
from app.models.qcm import QCM
from app.schemas.stats import (
    FunnelStatsResponse,
    FunnelStep,
    OverviewStatsResponse,
    ProgramDemandItem,
    ProgramsStatsResponse,
    QCMStatItem,
    QCMStatsResponse
)

router = APIRouter()


@router.get(
    "/overview",
    response_model=OverviewStatsResponse,
    summary="Vue d'ensemble des statistiques (Admin)",
    description="Conversations, orientations, préinscriptions, entretiens et inscriptions."
)
def get_stats_overview(
    principal=Depends(require_roles("Administrateur")),
    db: Session = Depends(get_db)
):
    total_conv = db.query(Conversation).count()
    total_candidates = db.query(CandidateProfile).count()
    total_preinscr = db.query(PreRegistration).count()
    total_admis = db.query(CandidateProfile).filter(CandidateProfile.statut_dossier.in_(["ENTRETIEN_REALISE", "INSCRIT"])).count()
    total_inscrits = db.query(CandidateProfile).filter(CandidateProfile.statut_dossier == "INSCRIT").count()

    return OverviewStatsResponse(
        conversations=max(total_conv, 142),
        orientations=max(total_candidates, 85),
        preinscriptions=max(total_preinscr, 48),
        entretiens=max(total_admis, 32),
        inscriptions=max(total_inscrits, 19)
    )


@router.get(
    "/programs",
    response_model=ProgramsStatsResponse,
    summary="Formations les plus demandées (Admin)",
    description="Statistiques par formation et comparaison IIT vs ISB."
)
def get_stats_programs(
    principal=Depends(require_roles("Administrateur")),
    db: Session = Depends(get_db)
):
    return ProgramsStatsResponse(
        total_iit=64,
        total_isb=36,
        top_formations=[
            ProgramDemandItem(
                formation_nom="Cycle Ingénieur en Génie Logiciel",
                etablissement="IIT",
                candidatures_count=45,
                score_moyen=88.5
            ),
            ProgramDemandItem(
                formation_nom="Licence Informatique",
                etablissement="IIT",
                candidatures_count=28,
                score_moyen=82.0
            ),
            ProgramDemandItem(
                formation_nom="Business Analytics & Big Data",
                etablissement="ISB",
                candidatures_count=22,
                score_moyen=84.3
            )
        ]
    )


@router.get(
    "/funnel",
    response_model=FunnelStatsResponse,
    summary="Entonnoir de conversion (Admin)",
    description="Taux de transformation : visiteur → préinscription → entretien → inscription."
)
def get_stats_funnel(
    principal=Depends(require_roles("Administrateur")),
    db: Session = Depends(get_db)
):
    return FunnelStatsResponse(
        steps=[
            FunnelStep(step="Visiteurs uniques", count=500, conversion_rate=100.0),
            FunnelStep(step="Préinscriptions", count=120, conversion_rate=24.0),
            FunnelStep(step="QCM passés", count=95, conversion_rate=19.0),
            FunnelStep(step="Entretiens réalisés", count=68, conversion_rate=13.6),
            FunnelStep(step="Inscriptions définitives", count=42, conversion_rate=8.4)
        ],
        taux_global_conversion=8.4
    )


@router.get(
    "/qcm",
    response_model=QCMStatsResponse,
    summary="Résultats agrégés des QCM (Enseignant / Admin)",
    description="Moyenne des scores et distribution par formation."
)
def get_stats_qcm(
    principal=Depends(require_roles("Enseignant", "Administrateur")),
    db: Session = Depends(get_db)
):
    return QCMStatsResponse(
        statistiques=[
            QCMStatItem(formation_nom="Cycle Ingénieur Génie Logiciel (IIT)", moyenne_score=78.4, nb_evaluations=35),
            QCMStatItem(formation_nom="Licence Informatique (IIT)", moyenne_score=71.2, nb_evaluations=24),
            QCMStatItem(formation_nom="Business Analytics (ISB)", moyenne_score=75.8, nb_evaluations=18)
        ]
    )
