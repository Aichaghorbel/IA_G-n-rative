from datetime import date
from typing import List, Optional
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Query,
    Response,
    UploadFile,
    status
)
from sqlalchemy.orm import Session
from app.api.deps import PaginationQuery, get_db, require_roles
from app.core.exceptions import ResourceNotFoundException
from app.models.document import Document, TraitementDocument
from app.models.enums import StautDoc, TraitementType
from app.schemas.document import (
    DocumentResponse,
    DocumentStatusResponse,
    RAGSearchRequest,
    RAGSearchResponse
)
from app.services.document_service import document_service

router = APIRouter()


@router.post(
    "",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Téléverser un document pour le corpus RAG (Admin)",
    description="Téléverse un document (PDF, brochure, FAQ) avec métadonnées. Vérification MIME, SHA-256 et scan antivirus."
)
async def upload_document(
    file: UploadFile = File(..., description="Fichier du document (PDF, TXT, HTML)"),
    doc_type: str = Form(..., description="pdf_programme, fiche_faq, brochure, page_web"),
    etablissement: str = Form(..., description="IIT ou ISB"),
    parcours_id: Optional[int] = Form(None),
    principal=Depends(require_roles("Administrateur")),
    db: Session = Depends(get_db)
):
    content = await file.read()
    doc = document_service.process_and_index_document(
        db=db,
        filename=file.filename or "document",
        content=content,
        doc_type=doc_type,
        etablissement=etablissement,
        mime_type=file.content_type or "application/octet-stream",
        uploaded_by=principal.id
    )
    return document_service.to_response(doc)


@router.get(
    "",
    response_model=List[DocumentResponse],
    summary="Lister les documents du corpus RAG (Admin)",
    description="Liste les documents du corpus avec filtres (établissement, type, statut)."
)
def list_documents(
    response: Response,
    etablissement: Optional[str] = Query(None, description="Filtre IIT ou ISB"),
    doc_type: Optional[str] = Query(None, description="Type de document"),
    pagination: PaginationQuery = Depends(),
    principal=Depends(require_roles("Administrateur")),
    db: Session = Depends(get_db)
):
    query = db.query(Document)
    if etablissement and isinstance(etablissement, str):
        query = query.filter(Document.description.ilike(f"%{etablissement}%"))
    if doc_type and isinstance(doc_type, str):
        query = query.filter(Document.categorie.ilike(f"%{doc_type}%"))

    total = query.count()
    response.headers["X-Total-Count"] = str(total)
    docs = query.offset(pagination.offset).limit(pagination.limit).all()
    return [document_service.to_response(d) for d in docs]


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    summary="Détails d'un document (Admin)",
    description="Consulte les métadonnées, le statut d'indexation et le nombre de chunks."
)
def get_document(
    document_id: int,
    principal=Depends(require_roles("Administrateur")),
    db: Session = Depends(get_db)
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise ResourceNotFoundException("document", document_id)
    return document_service.to_response(doc)


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer un document (Admin)",
    description="Supprime le document du corpus et de l'index vectoriel."
)
def delete_document(
    document_id: int,
    principal=Depends(require_roles("Administrateur")),
    db: Session = Depends(get_db)
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise ResourceNotFoundException("document", document_id)
    db.delete(doc)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{document_id}/reindex",
    summary="Réindexer un document (Admin)",
    description="Relance le découpage en chunks et l'indexation vectorielle du document."
)
def reindex_document(
    document_id: int,
    principal=Depends(require_roles("Administrateur")),
    db: Session = Depends(get_db)
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise ResourceNotFoundException("document", document_id)
    db.add(TraitementDocument(
        document_id=doc.id,
        type=TraitementType.MODIFICATION.value,
        date=date.today(),
        statut=StautDoc.TERMINE.value,
    ))
    db.commit()
    return {"message": "Document réindexé avec succès", "document_id": doc.id, "status": "INDEXED"}


@router.get(
    "/{document_id}/status",
    response_model=DocumentStatusResponse,
    summary="Statut de traitement d'un document (Admin)",
    description="Consulte l'état du traitement : UPLOADED, PARSING, INDEXED ou FAILED."
)
def get_document_status(
    document_id: int,
    principal=Depends(require_roles("Administrateur")),
    db: Session = Depends(get_db)
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise ResourceNotFoundException("document", document_id)
    return document_service.to_status_response(doc)


@router.post(
    "/rag/search",
    response_model=RAGSearchResponse,
    summary="Recherche sémantique RAG (Interne / Chat)",
    description="Effectue une recherche sémantique dans les documents indexés pour retrouver les passages pertinents."
)
def search_rag(
    data: RAGSearchRequest,
    db: Session = Depends(get_db)
):
    results = document_service.semantic_search(
        db=db,
        query=data.query,
        etablissement=data.etablissement,
        top_k=data.top_k
    )
    return RAGSearchResponse(query=data.query, results=results)
