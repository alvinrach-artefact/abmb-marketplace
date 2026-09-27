import uuid
from sqlalchemy import Column, Text, Boolean, TIMESTAMP, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, ENUM, JSONB
from sqlalchemy.orm import relationship

from app.db.base import Base

PublicationStatus = ENUM('pending', 'compliance_review', 'approved', 'published', 'rejected',
                          name='publication_status', create_type=False)


class AgentPublication(Base):
    __tablename__ = "agent_publications"

    publication_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.agent_id", ondelete="CASCADE"), nullable=False)
    status = Column(PublicationStatus, nullable=False, default="pending")
    submitted_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    use_case = Column(Text)
    raw_request = Column(JSONB, nullable=False)

    agent = relationship("Agent", back_populates="publications")
    signoff = relationship("ComplianceSignoff", back_populates="publication", uselist=False)
    go_live = relationship("GoLiveResult", back_populates="publication", uselist=False)


class ComplianceSignoff(Base):
    __tablename__ = "compliance_signoffs"

    signoff_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    publication_id = Column(UUID(as_uuid=True), ForeignKey("agent_publications.publication_id", ondelete="CASCADE"), nullable=False)
    approver_name = Column(Text)
    approver_role = Column(Text)
    approval_rule = Column(Text)
    evidence_pack = Column(JSONB)
    promotion_gate = Column(Text)
    decision_status = Column(Text)
    retained_evidence_complete = Column(Boolean, default=False)
    final_review_package_attached = Column(Boolean, default=False)
    compliance_approver_assigned = Column(Boolean, default=False)
    decided_at = Column(TIMESTAMP(timezone=True))

    publication = relationship("AgentPublication", back_populates="signoff")


class GoLiveResult(Base):
    __tablename__ = "go_live_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    publication_id = Column(UUID(as_uuid=True), ForeignKey("agent_publications.publication_id", ondelete="CASCADE"), nullable=False)
    marketplace_registry_status = Column(Text)
    unified_chat_access = Column(Text)
    telemetry_streaming = Column(Text)
    monitoring = Column(Text)
    production_environment = Column(Text)
    activated_at = Column(TIMESTAMP(timezone=True))

    publication = relationship("AgentPublication", back_populates="go_live")