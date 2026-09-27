from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.registration import (
    RegistrationRequest, RegistrationSubmittedOut, PendingRegistrationOut,
    AccRegistrationRequest, AccRegistrationOut, RegisteredAgentOut,
)
from app.services import registration_service

router = APIRouter(tags=["registration"])


@router.post("/input-register", response_model=RegistrationSubmittedOut, status_code=201)
def input_register(payload: RegistrationRequest, db: Session = Depends(get_db)):
    return registration_service.submit_registration(db, payload)


@router.get("/fetch-submitted-agent", response_model=list[PendingRegistrationOut])
def fetch_submitted_agent(db: Session = Depends(get_db)):
    return registration_service.list_pending_registrations(db)


@router.post("/acc-registration", response_model=AccRegistrationOut)
def acc_registration(payload: AccRegistrationRequest, db: Session = Depends(get_db)):
    try:
        return registration_service.approve_registration(db, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/fetch-acc-registered-agent", response_model=RegisteredAgentOut)
def fetch_acc_registered_agent(agent_id: UUID, reveal: bool = False, db: Session = Depends(get_db)):
    try:
        return registration_service.fetch_registered_agent(db, agent_id, reveal=reveal)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))