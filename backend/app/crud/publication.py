import uuid
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.agent import Agent
from app.models.publication import AgentPublication, ComplianceSignoff, GoLiveResult


def get_latest_publication(db: Session, agent_id: uuid.UUID) -> Optional[AgentPublication]:
    return (
        db.query(AgentPublication)
        .filter(AgentPublication.agent_id == agent_id)
        .order_by(AgentPublication.submitted_at.desc())
        .first()
    )


def get_publication(db: Session, publication_id: uuid.UUID) -> Optional[AgentPublication]:
    return db.query(AgentPublication).filter(AgentPublication.publication_id == publication_id).first()


def get_pending_publications(db: Session) -> List[AgentPublication]:
    return (
        db.query(AgentPublication)
        .filter(AgentPublication.status == "pending")
        .order_by(AgentPublication.submitted_at.asc())
        .all()
    )


def create_publication(db: Session, *, agent_id: uuid.UUID, use_case: Optional[str],
                        raw_request: dict) -> AgentPublication:
    publication = AgentPublication(
        agent_id=agent_id, status="pending", use_case=use_case, raw_request=raw_request,
    )
    db.add(publication)
    db.flush()
    return publication


def update_agent_profile(db: Session, agent: Agent, *, classification: str, tier: str,
                          environment: str, current_stage: str) -> None:
    agent.classification = classification
    agent.tier = tier
    agent.environment = environment
    agent.current_stage = current_stage
    agent.updated_at = func.now()


def set_agent_stage(db: Session, agent: Agent, stage: str) -> None:
    agent.current_stage = stage
    agent.updated_at = func.now()


def create_signoff(db: Session, *, publication_id: uuid.UUID, **fields) -> ComplianceSignoff:
    signoff = ComplianceSignoff(publication_id=publication_id, decided_at=func.now(), **fields)
    db.add(signoff)
    db.flush()
    return signoff


def create_go_live(db: Session, *, publication_id: uuid.UUID, **fields) -> GoLiveResult:
    go_live = GoLiveResult(publication_id=publication_id, **fields)
    db.add(go_live)
    db.flush()
    return go_live