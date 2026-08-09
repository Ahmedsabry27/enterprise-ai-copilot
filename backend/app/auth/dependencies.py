from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.cognito import verify_token
from app.auth.e2e import verify_e2e_token

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),  # noqa: B008
):
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Bearer token",
        )

    try:
        if credentials.credentials.startswith("e2e."):
            return verify_e2e_token(credentials.credentials)
        return verify_token(credentials.credentials)

    except Exception:  # noqa: BLE001 - authentication boundary returns a safe error
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired bearer token",
        ) from None
