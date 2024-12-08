from typing import Optional

from dependency_injector.wiring import inject
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.security.utils import get_authorization_scheme_param

from src.core.conf.settings import get_settings
from src.core.utils.api.http_exceptions import AuthenticationFailedError
from src.core.utils.api.security import jwt_decode

SETTINGS = get_settings()


class CustomHTTPAuthorizationCredentials(HTTPAuthorizationCredentials):
    organization_id: str | None = None


class CustomHTTPBearer(HTTPBearer):
    async def __call__(
        self, request: Request
    ) -> Optional[CustomHTTPAuthorizationCredentials]:
        authorization = request.headers.get("Authorization")
        scheme, credentials = get_authorization_scheme_param(authorization)
        if not (authorization and scheme and credentials):
            if self.auto_error:
                raise AuthenticationFailedError
            else:
                return None
        if scheme.lower() != "bearer":
            if self.auto_error:
                raise AuthenticationFailedError(
                    message="Invalid authentication credentials"
                )
            else:
                return None
        return CustomHTTPAuthorizationCredentials(
            scheme=scheme, credentials=credentials
        )


security_bearer = CustomHTTPBearer()


@inject
async def _create_organization_if_not_exist_set_scope(
    organization_id: str,
    request: Request,
):
    try:
        organization_id = int(organization_id)
    except Exception as ex:
        raise AuthenticationFailedError(message="Invalid Organization-Id") from ex
    request.scope["X-User-ID"] = organization_id
    return organization_id


async def get_user_organization_by_auth_token(
    request: Request,
    credentials: CustomHTTPAuthorizationCredentials = Depends(security_bearer),
):
    jwt_decode(credentials.credentials).get("organizationId")
