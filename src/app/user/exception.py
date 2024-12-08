from src.core.utils.api.http_exceptions import NotFound


class UserNotFoundError(NotFound):
    code = "USER_NOT_FOUND"
    message = "User not found"
