from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt
from jwt import ExpiredSignatureError, InvalidTokenError, PyJWTError

from src.core.conf.settings import get_settings
from src.core.utils.api.http_exceptions import AuthenticationFailedError
from src.core.utils.api.jwt_exceptions import (
    JWTExpiredSignatureError,
    JWTInvalidTokenError,
    JWTTokenError,
)

SETTINGS = get_settings()
JWT_SECRET = SETTINGS.JWT.JWT_ACCESS_SECRET
# JWT_SECRET = "test"
ALGORITHM = SETTINGS.JWT.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = (
    REFRESH_TOKEN_EXPIRE_DAYS
) = SETTINGS.JWT.VERIFICATION_MINUTES
AUDIENCE = SETTINGS.JWT.AUDIENCE


def jwt_exception_handler(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ExpiredSignatureError as ex:
            raise JWTExpiredSignatureError from ex
        except InvalidTokenError as ex:
            raise JWTInvalidTokenError from ex
        except PyJWTError as ex:
            raise JWTTokenError from ex
        except Exception as ex:
            # Exception unrelated to JWT
            raise AuthenticationFailedError from ex

    return wrapper


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(tz=timezone.utc) + expires_delta
    else:
        expire = datetime.now(tz=timezone.utc) + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire})
    return jwt_encode(to_encode)


def create_refresh_token(data: dict):
    return create_access_token(
        data, expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )


@jwt_exception_handler
def jwt_decode(token: str) -> dict:
    return jwt.decode(
        token, JWT_SECRET.get_secret_value(), algorithms=[ALGORITHM], audience=AUDIENCE
    )


@jwt_exception_handler
def jwt_encode(data: dict):
    return jwt.encode(data, JWT_SECRET.get_secret_value(), algorithm=ALGORITHM)
