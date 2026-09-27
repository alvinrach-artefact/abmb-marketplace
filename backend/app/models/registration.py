import uuid
from sqlalchemy import Column, Text, Boolean, TIMESTAMP, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, ENUM, JSONB
from sqlalchemy.orm import relationship

from app.db.base import Base

RegistrationStatus = ENUM('pending', 'approved', 'rejected',
                           name='registration_status', create_type=False)
CredentialStatus = ENUM('active', 'revoked', 'rotated',
                         name='credential_status', create_type=False)


class AgentRegistration(Base):
    __tablename__ = "agent_registrations"

    registration_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.agent_id", ondelete="CASCADE"), nullable=False)
    status = Column(RegistrationStatus, nullable=False, default="pending")
    submitted_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    reviewed_at = Column(TIMESTAMP(timezone=True))
    reviewed_by = Column(Text)
    environment = Column(Text)
    raw_request = Column(JSONB, nullable=False)
    raw_response = Column(JSONB)

    agent = relationship("Agent", back_populates="registrations")
    credentials = relationship("AgentCredential", back_populates="registration")


class AgentCredential(Base):
    __tablename__ = "agent_credentials"

    credential_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.agent_id", ondelete="CASCADE"), nullable=False)
    registration_id = Column(UUID(as_uuid=True), ForeignKey("agent_registrations.registration_id"))
    api_key_hash = Column(Text, nullable=False)
    api_key_ciphertext = Column(Text, nullable=False)   # NEW
    api_key_last4 = Column(Text, nullable=False)
    status = Column(CredentialStatus, nullable=False, default="active")
    authentication_mode = Column(Text, default="rbac_protected")
    display_policy = Column(Text, default="hidden_by_default")
    copy_requires_rbac = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    last_rotated_at = Column(TIMESTAMP(timezone=True))

    registration = relationship("AgentRegistration", back_populates="credentials")