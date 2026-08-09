from __future__ import annotations

import json
import os
from pathlib import Path
from uuid import uuid4

from app.agents.application_service import AgentApplicationService, AgentIdentity
from app.auth.e2e import issue_e2e_token
from app.database.session import SessionLocal


def main() -> None:
    output = Path(os.environ["E2E_STATE_PATH"]).resolve()
    tenant = f"e2e-{uuid4()}"
    actor = f"platform-admin-{uuid4()}"
    claims = {
        "sub": actor,
        "custom:tenant_id": tenant,
        "cognito:groups": ["platform-admin"],
        "permissions": ["agents.list", "agents.read", "agents.create"],
    }
    cross_tenant_claims = {
        "sub": f"cross-tenant-admin-{uuid4()}",
        "custom:tenant_id": f"e2e-other-{uuid4()}",
        "cognito:groups": ["platform-admin"],
        "permissions": ["agents.admin"],
    }
    identity = AgentIdentity.from_claims(claims)
    with SessionLocal() as database:
        agent = AgentApplicationService().create(
            database,
            identity,
            {
                "name": "Live E2E Agent",
                "description": "Deterministic disposable browser verification Agent",
                "instructions": "Return only safe deterministic test evidence.",
                "model_configuration": {
                    "provider": "fake-e2e-provider",
                    "model": "deterministic-model",
                },
                "environment_restrictions": ["test"],
            },
        )
    output.write_text(
        json.dumps(
            {
                "token": issue_e2e_token(claims, lifetime_seconds=900),
                "cross_tenant_token": issue_e2e_token(
                    cross_tenant_claims, lifetime_seconds=900
                ),
                "tenant": tenant,
                "actor": actor,
                "agent_id": agent.uuid,
            }
        )
    )
    output.chmod(0o600)


if __name__ == "__main__":
    main()
