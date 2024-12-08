from starlette import status

from src.core.utils.api.http_exceptions import AuthenticationFailedError


class JWTTokenError(AuthenticationFailedError):
    message = "Invalid JWT Token."
    code = "JWT_TOKEN_ERROR"


class JWTInvalidTokenError(JWTTokenError):
    status_code = status.HTTP_401_UNAUTHORIZED
    code = "JWT_INVALID_TOKEN"


class JWTExpiredSignatureError(JWTTokenError):
    status_code = status.HTTP_401_UNAUTHORIZED
    message = "Expired JWT Signature."
    code = "JWT_EXPIRED_TOKEN"
