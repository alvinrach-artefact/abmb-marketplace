import uuid
from datetime import datetime
from typing import List, Optional, Literal

from pydantic import BaseModel, Field


# ---------- Marketplace -> Control Tower: POST /input-register ----------

class AgentDetails(BaseModel):
    agent_name: str
    department: str
    owner_team: str
    intended_audience: str
    description: Optional[str] = None


class PublicationAccess(BaseModel):
    visibility: Literal["personal", "team", "to_be_published"] = "team"
    expected_user_count_per_month: int = 0


class SupportingInformation(BaseModel):
    use_case_business_need: Optional[str] = None


class RegistrationRequest(BaseModel):
    agent_details: AgentDetails
    publication_access: PublicationAccess
    model_access: List[str] = Field(default_factory=list)
    supporting_information: SupportingInformation


class RegistrationSubmittedOut(BaseModel):
    registration_id: uuid.UUID
    agent_id: uuid.UUID
    status: str
    submitted_at: datetime

    class Config:
        from_attributes = True


# ---------- Control Tower: GET /fetch-submitted-agent ----------

class PendingRegistrationOut(BaseModel):
    registration_id: uuid.UUID
    agent_id: uuid.UUID
    status: str
    submitted_at: datetime
    agent_details: AgentDetails
    publication_access: PublicationAccess
    model_access: List[str]
    supporting_information: SupportingInformation

    class Config:
        from_attributes = True


# ---------- Control Tower -> DB: POST /acc-registration ----------

class ModelGrant(BaseModel):
    requested_capability: str
    granted_model_name: str

class AccRegistrationRequest(BaseModel):
    registration_id: uuid.UUID
    decision: Literal["approved", "rejected"]
    reviewed_by: str
    environment: Optional[str] = "production"
    model_grants: List[ModelGrant] = Field(default_factory=list)   # was: granted_models: List[str]


class ApiKeyOut(BaseModel):
    status: Literal["active", "revoked", "rotated"] = "active"
    value: Optional[str] = None  # plaintext — populated at issuance, or on explicit reveal
    display_policy: str = "hidden_by_default"
    copy_requires_rbac: bool = True


class AccessCredentialsOut(BaseModel):
    authentication: str = "rbac_protected"
    api_key: ApiKeyOut


class AccRegistrationOut(BaseModel):
    registration_id: uuid.UUID
    agent_id: uuid.UUID
    registration_status: str
    access_credentials: Optional[AccessCredentialsOut] = None


# ---------- Marketplace: GET /fetch-acc-registered-agent ----------

class RegisteredAgentOut(BaseModel):
    agent_name: str
    registration_status: str
    owner: str
    intended_audience: str
    granted_models: List[ModelGrant]   # was: List[str]
    environment: str
    access_credentials: AccessCredentialsOut