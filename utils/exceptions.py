"""Exceptions implementation."""

from fastapi_jwt_auth.exceptions import AuthJWTException


class AuthException(AuthJWTException):
    """JWT Token Exceptions."""

    def __init__(self, status_code: int, message: str):
        """Start variables."""
        self.status_code = status_code
        self.message = message
