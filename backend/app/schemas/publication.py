import uuid
from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


# ---------- Marketplace -> POST /request-publication ----------

class PublicationRequest(BaseModel):
    agent_id: uuid.UUID                       # real identity key; name/owner/audience are informational
    name: str
    owner: str
    audience: str
    classification: Literal["Internal", "Confidential", "Restricted"]
    tier: str
    environment: str
    current_stage: str                        # "POC / DEV", "Pilot", ... normalised server-side
    use_case: Optional[str] = None


class PublicationRequestedOut(BaseModel):
    publication_id: uuid.UUID
    agent_id: uuid.UUID
    status: str
    submitted_at: datetime


# ---------- Control Tower: GET /fetch-publication-request ----------

class PendingPublicationOut(PublicationRequest):
    publication_id: uuid.UUID
    status: str
    submitted_at: datetime


# ---------- Control Tower -> POST /acc-publication ----------
# Everything except publication_id has a default, so a demo call can be just:
#   {"publication_id": "<uuid>"}

class GoLivePlan(BaseModel):
    unified_chat_access: str = "available_to_authorized_users"
    telemetry_streaming: str = "finops_and_security_to_bigquery"
    monitoring: str = "continuous_monitoring_enabled"
    production_environment: str = "provisioned"


class AccPublicationRequest(BaseModel):
    publication_id: uuid.UUID
    decision: Literal["approved", "rejected"] = "approved"
    approver_name: str = "Alex Chen"
    approver_role: str = "Head of Financial Crime Compliance"
    approval_rule: str = "mandatory_final_sign_off_required"
    evidence_pack: List[str] = Field(default_factory=lambda: [
        "pilot_telemetry", "hitl_escalation_log", "risk_fairness_review", "security_evidence",
    ])
    retained_evidence_complete: bool = True
    final_review_package_attached: bool = True
    compliance_approver_assigned: bool = True
    go_live: GoLivePlan = Field(default_factory=GoLivePlan)


class AccPublicationOut(BaseModel):
    publication_id: uuid.UUID
    agent_id: uuid.UUID
    publication_status: str


# ---------- Marketplace: GET /fetch-acc-public-agent ----------

class ApproverOut(BaseModel):
    name: str
    role: str


class ComplianceSignOffOut(BaseModel):
    required: bool = True
    approver: ApproverOut
    approval_rule: str
    evidence_pack: List[str]
    promotion_gate: str
    decision_status: str
    upon_approval: str
    retained_evidence_complete: bool
    final_review_package_attached: bool
    compliance_approver_assigned: bool


class GoLiveResultOut(BaseModel):
    marketplace_registry_status: str
    unified_chat_access: str
    telemetry_streaming: str
    monitoring: str
    production_environment: str


class PublicationStatusOut(BaseModel):
    agent_id: uuid.UUID
    publication_id: Optional[uuid.UUID] = None
    # not_requested | pending | approved | published | rejected
    publication_status: str
    compliance_sign_off: Optional[ComplianceSignOffOut] = None
    go_live_result: Optional[GoLiveResultOut] = None


# ---------- Marketplace: POST /publish-agent ----------

class PublishAgentRequest(BaseModel):
    agent_id: uuid.UUID


class PublishAgentOut(BaseModel):
    agent_id: uuid.UUID
    publication_id: uuid.UUID
    publication_status: str
    current_stage: str