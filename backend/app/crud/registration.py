import uuid
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.agent import Agent, AgentModelAccess
from app.models.registration import AgentRegistration, AgentCredential
from app.models.audit import AuditLog


def create_agent(db: Session, *, agent_name: str, department: str, owner_team: str,
                  intended_audience: str, description: Optional[str], visibility: str,
                  expected_user_count_per_month: int, use_case_business_need: Optional[str]) -> Agent:
    agent = Agent(
        agent_name=agent_name, department=department, owner_team=owner_team,
        intended_audience=intended_audience, description=description, visibility=visibility,
        expected_user_count_per_month=expected_user_count_per_month,
        use_case_business_need=use_case_business_need,
    )
    db.add(agent)
    db.flush()
    return agent


def add_model_access(db: Session, *, agent_id: uuid.UUID, models: List[str], kind: str) -> None:
    for model_name in models:
        db.add(AgentModelAccess(agent_id=agent_id, model_name=model_name, kind=kind))


def create_registration(db: Session, *, agent_id: uuid.UUID, raw_request: dict) -> AgentRegistration:
    registration = AgentRegistration(agent_id=agent_id, status="pending", raw_request=raw_request)
    db.add(registration)
    db.flush()
    return registration


def get_pending_registrations(db: Session) -> List[AgentRegistration]:
    return (
        db.query(AgentRegistration)
        .filter(AgentRegistration.status == "pending")
        .order_by(AgentRegistration.submitted_at.asc())
        .all()
    )


def get_registration(db: Session, registration_id: uuid.UUID) -> Optional[AgentRegistration]:
    return db.query(AgentRegistration).filter(
        AgentRegistration.registration_id == registration_id
    ).first()


def get_latest_registration_for_agent(db: Session, agent_id: uuid.UUID) -> Optional[AgentRegistration]:
    return (
        db.query(AgentRegistration)
        .filter(AgentRegistration.agent_id == agent_id)
        .order_by(AgentRegistration.submitted_at.desc())
        .first()
    )


def set_registration_decision(db: Session, *, registration: AgentRegistration, status: str,
                               reviewed_by: str, environment: Optional[str], raw_response: dict) -> None:
    registration.status = status
    registration.reviewed_by = reviewed_by
    registration.environment = environment
    registration.raw_response = raw_response
    registration.reviewed_at = func.now()


def create_credential(db: Session, *, agent_id: uuid.UUID, registration_id: uuid.UUID,
                       api_key_hash: str, api_key_ciphertext: str, api_key_last4: str) -> AgentCredential:
    credential = AgentCredential(
        agent_id=agent_id, registration_id=registration_id,
        api_key_hash=api_key_hash, api_key_ciphertext=api_key_ciphertext,
        api_key_last4=api_key_last4, status="active",
    )
    db.add(credential)
    db.flush()
    return credential


def get_latest_credential(db: Session, agent_id: uuid.UUID) -> Optional[AgentCredential]:
    return (
        db.query(AgentCredential)
        .filter(AgentCredential.agent_id == agent_id, AgentCredential.status == "active")
        .order_by(AgentCredential.created_at.desc())
        .first()
    )


def get_agent(db: Session, agent_id: uuid.UUID) -> Optional[Agent]:
    return db.query(Agent).filter(Agent.agent_id == agent_id).first()


def get_granted_models(db: Session, agent_id: uuid.UUID) -> List[str]:
    rows = (
        db.query(AgentModelAccess)
        .filter(AgentModelAccess.agent_id == agent_id, AgentModelAccess.kind == "granted")
        .all()
    )
    return [r.model_name for r in rows]


def write_audit_log(db: Session, *, endpoint: str, method: str, agent_id: Optional[uuid.UUID],
                     actor: Optional[str], payload: dict) -> None:
    db.add(AuditLog(endpoint=endpoint, method=method, agent_id=agent_id, actor=actor, payload=payload))