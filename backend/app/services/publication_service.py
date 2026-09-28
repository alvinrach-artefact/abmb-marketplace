import re
import uuid
from typing import List

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.crud import publication as pub_crud
from app.crud.registration import get_agent, write_audit_log
from app.schemas.publication import (
    PublicationRequest, PublicationRequestedOut, PendingPublicationOut,
    AccPublicationRequest, AccPublicationOut,
    PublicationStatusOut, ComplianceSignOffOut, ApproverOut, GoLiveResultOut,
    PublishAgentRequest, PublishAgentOut,
)

# publication_status lifecycle:
#   pending  --/acc-publication (approved)-->  approved  --/publish-agent-->  published
#   pending  --/acc-publication (rejected)-->  rejected   (Marketplace may send a new request)

VALID_STAGES = {"PROMOTE", "POC_DEV", "TESTING", "PILOT", "PRODUCTION"}


def _normalize_stage(label: str) -> str:
    """'POC / DEV' -> 'POC_DEV', 'Pilot' -> 'PILOT'."""
    key = re.sub(r"[^A-Za-z0-9]+", "_", label.strip()).strip("_").upper()
    if key not in VALID_STAGES:
        raise ValueError(f"unknown stage '{label}'")
    return key


# ---------- POST /request-publication ----------

def request_publication(db: Session, payload: PublicationRequest) -> PublicationRequestedOut:
    agent = get_agent(db, payload.agent_id)
    if agent is None:
        raise ValueError("agent not found")

    latest = pub_crud.get_latest_publication(db, agent.agent_id)
    if latest and latest.status in ("pending", "approved"):
        raise ValueError(f"a publication request is already {latest.status} for this agent")
    if latest and latest.status == "published":
        raise ValueError("agent is already published")

    stage = _normalize_stage(payload.current_stage)
    raw = payload.model_dump(mode="json")

    publication = pub_crud.create_publication(
        db, agent_id=agent.agent_id, use_case=payload.use_case, raw_request=raw,
    )
    pub_crud.update_agent_profile(
        db, agent, classification=payload.classification, tier=payload.tier,
        environment=payload.environment, current_stage=stage,
    )
    write_audit_log(db, endpoint="/request-publication", method="POST",
                    agent_id=agent.agent_id, actor=payload.owner, payload=raw)

    db.commit()
    db.refresh(publication)
    return PublicationRequestedOut(
        publication_id=publication.publication_id, agent_id=publication.agent_id,
        status=publication.status, submitted_at=publication.submitted_at,
    )


# ---------- GET /fetch-publication-request (Control Tower queue) ----------

def list_pending_publications(db: Session) -> List[PendingPublicationOut]:
    return [
        PendingPublicationOut(
            publication_id=p.publication_id, status=p.status,
            submitted_at=p.submitted_at, **p.raw_request,
        )
        for p in pub_crud.get_pending_publications(db)
    ]


# ---------- POST /acc-publication (Control Tower decision) ----------

def approve_publication(db: Session, payload: AccPublicationRequest) -> AccPublicationOut:
    publication = pub_crud.get_publication(db, payload.publication_id)
    if publication is None:
        raise ValueError("publication not found")
    if publication.status != "pending":
        raise ValueError(f"publication already {publication.status}")

    approved = payload.decision == "approved"

    pub_crud.create_signoff(
        db, publication_id=publication.publication_id,
        approver_name=payload.approver_name, approver_role=payload.approver_role,
        approval_rule=payload.approval_rule, evidence_pack=payload.evidence_pack,
        promotion_gate="unblocked" if approved else "blocked",
        decision_status=payload.decision,
        retained_evidence_complete=payload.retained_evidence_complete,
        final_review_package_attached=payload.final_review_package_attached,
        compliance_approver_assigned=payload.compliance_approver_assigned,
    )
    if approved:
        # Prepared now, switched on by /publish-agent -- so the registry stays
        # 'pending_publish' until the Marketplace user actually clicks Publish.
        pub_crud.create_go_live(
            db, publication_id=publication.publication_id,
            marketplace_registry_status="pending_publish",
            unified_chat_access=payload.go_live.unified_chat_access,
            telemetry_streaming=payload.go_live.telemetry_streaming,
            monitoring=payload.go_live.monitoring,
            production_environment=payload.go_live.production_environment,
        )

    publication.status = "approved" if approved else "rejected"

    write_audit_log(db, endpoint="/acc-publication", method="POST",
                    agent_id=publication.agent_id, actor=payload.approver_name,
                    payload=payload.model_dump(mode="json"))
    db.commit()
    return AccPublicationOut(
        publication_id=publication.publication_id, agent_id=publication.agent_id,
        publication_status=publication.status,
    )


# ---------- GET /fetch-acc-public-agent (Marketplace) ----------

def fetch_public_agent(db: Session, agent_id: uuid.UUID) -> PublicationStatusOut:
    if get_agent(db, agent_id) is None:
        raise ValueError("agent not found")

    publication = pub_crud.get_latest_publication(db, agent_id)
    if publication is None:
        return PublicationStatusOut(agent_id=agent_id, publication_status="not_requested")

    out = PublicationStatusOut(
        agent_id=agent_id, publication_id=publication.publication_id,
        publication_status=publication.status,
    )

    s = publication.signoff
    if s is not None:
        out.compliance_sign_off = ComplianceSignOffOut(
            required=True,
            approver=ApproverOut(name=s.approver_name, role=s.approver_role),
            approval_rule=s.approval_rule, evidence_pack=s.evidence_pack or [],
            promotion_gate=s.promotion_gate, decision_status=s.decision_status,
            upon_approval="publish_to_production",
            retained_evidence_complete=bool(s.retained_evidence_complete),
            final_review_package_attached=bool(s.final_review_package_attached),
            compliance_approver_assigned=bool(s.compliance_approver_assigned),
        )

    g = publication.go_live
    if g is not None:
        out.go_live_result = GoLiveResultOut(
            marketplace_registry_status=g.marketplace_registry_status,
            unified_chat_access=g.unified_chat_access,
            telemetry_streaming=g.telemetry_streaming,
            monitoring=g.monitoring,
            production_environment=g.production_environment,
        )
    return out


# ---------- POST /publish-agent (Marketplace final action) ----------

def publish_agent(db: Session, payload: PublishAgentRequest) -> PublishAgentOut:
    agent = get_agent(db, payload.agent_id)
    if agent is None:
        raise ValueError("agent not found")

    publication = pub_crud.get_latest_publication(db, agent.agent_id)
    if publication is None:
        raise ValueError("no publication request found for this agent")
    if publication.status == "published":
        raise ValueError("agent is already published")
    if publication.status != "approved":
        raise ValueError(
            f"publication is '{publication.status}' -- Control Tower approval is required before publishing"
        )

    publication.status = "published"
    pub_crud.set_agent_stage(db, agent, "PRODUCTION")
    if publication.go_live is not None:
        publication.go_live.marketplace_registry_status = "active"
        publication.go_live.activated_at = func.now()

    write_audit_log(db, endpoint="/publish-agent", method="POST",
                    agent_id=agent.agent_id, actor=agent.owner_team,
                    payload=payload.model_dump(mode="json"))
    db.commit()
    return PublishAgentOut(
        agent_id=agent.agent_id, publication_id=publication.publication_id,
        publication_status="published", current_stage="PRODUCTION",
    )