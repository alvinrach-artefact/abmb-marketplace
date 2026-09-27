import uuid

from sqlalchemy.orm import Session

from app.core.security import generate_api_key, hash_api_key, encrypt_api_key, decrypt_api_key
from app.crud import registration as registration_crud
from app.schemas.registration import (
    RegistrationRequest, RegistrationSubmittedOut, PendingRegistrationOut,
    AccRegistrationRequest, AccRegistrationOut, RegisteredAgentOut,
    AccessCredentialsOut, ApiKeyOut, AgentDetails, PublicationAccess, SupportingInformation,
)


def submit_registration(db: Session, payload: RegistrationRequest) -> RegistrationSubmittedOut:
    details = payload.agent_details
    access = payload.publication_access

    agent = registration_crud.create_agent(
        db,
        agent_name=details.agent_name, department=details.department,
        owner_team=details.owner_team, intended_audience=details.intended_audience,
        description=details.description, visibility=access.visibility,
        expected_user_count_per_month=access.expected_user_count_per_month,
        use_case_business_need=payload.supporting_information.use_case_business_need,
    )

    registration_crud.add_model_access(
        db, agent_id=agent.agent_id, models=payload.model_access, kind="requested"
    )

    registration = registration_crud.create_registration(
        db, agent_id=agent.agent_id, raw_request=payload.model_dump()
    )

    registration_crud.write_audit_log(
        db, endpoint="/input-register", method="POST",
        agent_id=agent.agent_id, actor=details.owner_team, payload=payload.model_dump(),
    )

    db.commit()
    db.refresh(registration)

    return RegistrationSubmittedOut(
        registration_id=registration.registration_id, agent_id=agent.agent_id,
        status=registration.status, submitted_at=registration.submitted_at,
    )


def list_pending_registrations(db: Session) -> list[PendingRegistrationOut]:
    pending = registration_crud.get_pending_registrations(db)
    out = []
    for reg in pending:
        raw = reg.raw_request
        out.append(PendingRegistrationOut(
            registration_id=reg.registration_id, agent_id=reg.agent_id,
            status=reg.status, submitted_at=reg.submitted_at,
            agent_details=AgentDetails(**raw["agent_details"]),
            publication_access=PublicationAccess(**raw["publication_access"]),
            model_access=raw["model_access"],
            supporting_information=SupportingInformation(**raw["supporting_information"]),
        ))
    return out


def approve_registration(db: Session, payload: AccRegistrationRequest) -> AccRegistrationOut:
    registration = registration_crud.get_registration(db, payload.registration_id)
    if registration is None:
        raise ValueError("registration not found")
    if registration.status != "pending":
        raise ValueError(f"registration already {registration.status}")

    if payload.decision == "rejected":
        registration_crud.set_registration_decision(
            db, registration=registration, status="rejected",
            reviewed_by=payload.reviewed_by, environment=payload.environment,
            raw_response=payload.model_dump(),
        )
        registration_crud.write_audit_log(
            db, endpoint="/acc-registration", method="POST",
            agent_id=registration.agent_id, actor=payload.reviewed_by, payload=payload.model_dump(),
        )
        db.commit()
        return AccRegistrationOut(
            registration_id=registration.registration_id, agent_id=registration.agent_id,
            registration_status="rejected",
        )

    # approved path — server generates the secret; never trust a client-supplied key
    plaintext_key = generate_api_key()
    api_key_hash = hash_api_key(plaintext_key)
    api_key_ciphertext = encrypt_api_key(plaintext_key)
    api_key_last4 = plaintext_key[-4:]

    registration_crud.set_registration_decision(
        db, registration=registration, status="approved",
        reviewed_by=payload.reviewed_by, environment=payload.environment,
        raw_response=payload.model_dump(),
    )
    registration_crud.add_model_access(
        db, agent_id=registration.agent_id, models=payload.granted_models, kind="granted"
    )
    registration_crud.create_credential(
        db, agent_id=registration.agent_id, registration_id=registration.registration_id,
        api_key_hash=api_key_hash, api_key_ciphertext=api_key_ciphertext, api_key_last4=api_key_last4,
    )
    registration_crud.write_audit_log(
        db, endpoint="/acc-registration", method="POST",
        agent_id=registration.agent_id, actor=payload.reviewed_by, payload=payload.model_dump(),
    )

    db.commit()

    return AccRegistrationOut(
        registration_id=registration.registration_id, agent_id=registration.agent_id,
        registration_status="approved",
        access_credentials=AccessCredentialsOut(api_key=ApiKeyOut(status="active", value=plaintext_key)),
    )


def fetch_registered_agent(db: Session, agent_id: uuid.UUID, reveal: bool = False) -> RegisteredAgentOut:
    agent = registration_crud.get_agent(db, agent_id)
    if agent is None:
        raise ValueError("agent not found")

    registration = registration_crud.get_latest_registration_for_agent(db, agent_id)
    if registration is None:
        raise ValueError("no registration found for this agent")

    credential = registration_crud.get_latest_credential(db, agent_id)
    granted_models = registration_crud.get_granted_models(db, agent_id)

    api_key_out = ApiKeyOut(status="active")
    if credential:
        api_key_out.status = credential.status
        if reveal:
            # TODO: gate this behind a real RBAC check (role claim from auth
            # middleware) — right now it's just a query flag, not enforced.
            api_key_out.value = decrypt_api_key(credential.api_key_ciphertext)
        else:
            api_key_out.value = f"abmb_live_{'•' * 20}"

    registration_crud.write_audit_log(
        db, endpoint="/fetch-acc-registered-agent", method="GET",
        agent_id=agent_id, actor=None, payload={"reveal": reveal},
    )
    db.commit()

    return RegisteredAgentOut(
        agent_name=agent.agent_name, registration_status=registration.status,
        owner=agent.owner_team, intended_audience=agent.intended_audience,
        granted_models=granted_models, environment=registration.environment or "production",
        access_credentials=AccessCredentialsOut(api_key=api_key_out),
    )