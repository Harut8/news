from src.core.utils.api.http_exceptions import RequestError


class UrlExistsError(RequestError):
    code = "URL_EXISTS"
    message = "URL already exists"
