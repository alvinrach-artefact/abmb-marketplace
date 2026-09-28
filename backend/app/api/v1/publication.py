from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.publication import (
    PublicationRequest, PublicationRequestedOut, PendingPublicationOut,
    AccPublicationRequest, AccPublicationOut, PublicationStatusOut,
    PublishAgentRequest, PublishAgentOut,
)
from app.services import publication_service

router = APIRouter(tags=["publication"])


@router.post("/request-publication", response_model=PublicationRequestedOut, status_code=201)
def request_publication(payload: PublicationRequest, db: Session = Depends(get_db)):
    try:
        return publication_service.request_publication(db, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/fetch-publication-request", response_model=list[PendingPublicationOut])
def fetch_publication_request(db: Session = Depends(get_db)):
    return publication_service.list_pending_publications(db)


@router.post("/acc-publication", response_model=AccPublicationOut)
def acc_publication(payload: AccPublicationRequest, db: Session = Depends(get_db)):
    try:
        return publication_service.approve_publication(db, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/fetch-acc-public-agent", response_model=PublicationStatusOut)
def fetch_acc_public_agent(agent_id: UUID, db: Session = Depends(get_db)):
    try:
        return publication_service.fetch_public_agent(db, agent_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/publish-agent", response_model=PublishAgentOut)
def publish_agent(payload: PublishAgentRequest, db: Session = Depends(get_db)):
    try:
        return publication_service.publish_agent(db, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))