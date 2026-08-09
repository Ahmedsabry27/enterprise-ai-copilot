from __future__ import annotations

import json

from app.auth.e2e import verify_e2e_token
from scripts.seed_live_e2e import main


def test_seed_writes_restricted_signed_tenant_state(tmp_path, monkeypatch):
    state_path = tmp_path / "state.json"
    monkeypatch.setenv("APP_ENV", "e2e")
    monkeypatch.setenv("E2E_AUTH_ENABLED", "true")
    monkeypatch.setenv("E2E_AUTH_SECRET", "0123456789abcdef0123456789abcdef")
    monkeypatch.setenv("E2E_STATE_PATH", str(state_path))

    main()

    state = json.loads(state_path.read_text())
    assert set(state) == {
        "token",
        "cross_tenant_token",
        "tenant",
        "actor",
        "agent_id",
    }
    assert state_path.stat().st_mode & 0o777 == 0o600
    owner = verify_e2e_token(state["token"])
    outsider = verify_e2e_token(state["cross_tenant_token"])
    assert owner["custom:tenant_id"] == state["tenant"]
    assert owner["sub"] == state["actor"]
    assert outsider["custom:tenant_id"] != state["tenant"]
