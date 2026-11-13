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
from app.api.deps import PaginationQuery, get_current_principal, get_db, require_roles
from app.core.exceptions import (
    DocumentAlreadyIndexedException,
    DocumentCorruptedException,
    ResourceNotFoundException
)
from app.models.document import Document
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
        filename=file.filename,
        content=content,
        doc_type=doc_type,
        etablissement=etablissement,
        mime_type=file.content_type or "application/octet-stream",
        uploaded_by=principal.id
    )
    if parcours_id:
        doc.parcours_id = parcours_id
        db.commit()
    return doc


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
        query = query.filter(Document.etablissement == etablissement)
    if doc_type and isinstance(doc_type, str):
        query = query.filter(Document.type == doc_type)

    total = query.count()
    response.headers["X-Total-Count"] = str(total)
    return query.offset(pagination.offset).limit(pagination.limit).all()


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
    return doc


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
    doc.status = "INDEXED"
    db.commit()
    return {"message": "Document réindexé avec succès", "document_id": doc.id, "status": doc.status}


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
    return DocumentStatusResponse(
        id=doc.id,
        status=doc.status,
        chunks_count=doc.chunks_count,
        indexed_at=doc.indexed_at
    )


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
