import uuid
from sqlalchemy import Column, String, Integer, Text, TIMESTAMP, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.orm import relationship

from app.db.base import Base

AgentClassification = ENUM('Internal', 'Confidential', 'Restricted',
                            name='agent_classification', create_type=False)
AgentVisibility = ENUM('personal', 'team', 'to_be_published',
                        name='agent_visibility', create_type=False)
AgentStage = ENUM('PROMOTE', 'POC_DEV', 'TESTING', 'PILOT', 'PRODUCTION',
                   name='agent_stage', create_type=False)
ModelAccessKind = ENUM('requested', 'granted',
                        name='model_access_kind', create_type=False)


class Agent(Base):
    __tablename__ = "agents"

    agent_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_name = Column(Text, nullable=False)
    department = Column(Text, nullable=False)
    owner_team = Column(Text, nullable=False)
    intended_audience = Column(Text, nullable=False)
    description = Column(Text)
    visibility = Column(AgentVisibility, nullable=False, default="team")
    expected_user_count_per_month = Column(Integer, default=0)
    use_case_business_need = Column(Text)
    classification = Column(AgentClassification)
    tier = Column(Text)
    environment = Column(Text)
    current_stage = Column(AgentStage, nullable=False, default="PROMOTE")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    model_access = relationship("AgentModelAccess", back_populates="agent", cascade="all, delete-orphan")
    registrations = relationship("AgentRegistration", back_populates="agent", cascade="all, delete-orphan")
    publications = relationship("AgentPublication", back_populates="agent", cascade="all, delete-orphan")


class AgentModelAccess(Base):
    __tablename__ = "agent_model_access"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.agent_id", ondelete="CASCADE"), nullable=False)
    requested_capability = Column(Text, nullable=False)   # e.g. "general-chat", "drafting", "image"
    granted_model_name = Column(Text, nullable=True)      # e.g. "Claude Opus 4.5" -- set at approval, not before
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    agent = relationship("Agent", back_populates="model_access")