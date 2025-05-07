"""System settings implementation."""

import inspect
import re
from typing import Any, Callable, Dict

import asyncio
from aiohttp import ClientSession
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from fastapi_jwt_auth import AuthJWT
from fastapi_jwt_auth.exceptions import AuthJWTException
from utils.exceptions import AuthException
from schemas.jwt_auth import AuthJwtSettings
import logger

from utils.requests.middleware import CORRELATION_ID_HEADER_KEY, correlation_id_context


@AuthJWT.load_config
def get_config():
    """JWT Token Configuration."""
    return AuthJwtSettings()


def customization_setup(app: FastAPI) -> None:
    """System customization configuration."""

    @app.exception_handler(AuthJWTException)
    def auth_jwt_exception_handler(exc: AuthException):
        """JWT Token custom Exceptions."""
        if exc.message == "Missing Authorization Header":
            exc.message = "api007"

        if exc.message == "Signature has expired":
            exc.status_code = 401
            exc.message = "api020"

        if exc.message == "Signature verification failed":
            exc.status_code = 401
            exc.message = "api007"

        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message}
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(exc: RequestValidationError):
        """Your custom validation exception."""
        error = exc.errors()[0]
        message = exc.errors()
        if error.get("type") == "value_error.missing":
            message = "api018"
        if error.get("type") == "value_error.email":
            message = "api019"

        return JSONResponse(
            status_code=422,
            content={"detail": message}
        )

    @app.on_event("startup")
    async def startup():
        """Creation of access limit to routes."""
        print("STARTUP APP")

        class CustomClientSession(ClientSession):
            """Custom ClientSession with integrated CorrelationID control."""

            async def _request(self, method, url, **kwargs):
                headers = kwargs.get("headers", {})
                if CORRELATION_ID_HEADER_KEY not in headers:
                    correlation_id = correlation_id_context.get()
                    headers.update({CORRELATION_ID_HEADER_KEY: correlation_id})
                    kwargs.update({"headers": headers})
                return await super()._request(method, url, **kwargs)

        setattr(app.state, "client_session",
                CustomClientSession(raise_for_status=True))

        # Logging configuration
        logger.config_log()

    @app.on_event("shutdown")
    async def shutdown():
        # Async Client Session Close
        await asyncio.wait((app.state.client_session.close()), timeout=5.0)


def harpia_openapi(
        app: FastAPI,
) -> Callable[[], Dict[str, Any]]:
    """
    Generate custom openAPI schema.

    This function generates openapi schema based on
    routes from FastAPI application.
    """

    def openapi_generator() -> Dict[str, Any]:
        """Swagger and bearer preview settings for authenticated routes."""
        if app.openapi_schema:
            return app.openapi_schema
        openapi_schema = get_openapi(
            title="HARPIA-REPORTS-INTERFACE",
            version="0.0.1",
            description="Reports management API",
            routes=app.routes,
        )

        # Adding the system logo in FastAPI.
        openapi_schema["info"]["x-logo"] = {
            "url": "https://fastapi.tiangolo.com/img/"
                   "logo-margin/logo-teal.png"
        }

        # Applying the bearer to the required token routes
        openapi_schema["components"]["securitySchemes"] = {
            "Bearer Auth": {
                "type": "apiKey",
                "in": "header",
                "name": "Authorization",
                "description": "Enter: **'Bearer &lt;JWT&gt;'**, "
                               "where JWT is the access token"
            }
        }

        # Get all routes where jwt_optional() or jwt_required
        api_router = [route for route in app.routes if
                      isinstance(route, APIRoute)]

        for route in api_router:
            path = getattr(route, "path")
            endpoint = getattr(route, "endpoint")
            methods = [
                method.lower() for method in getattr(route, "methods")]

            for method in methods:
                # access_token
                required = re.search(
                    "jwt_required", inspect.getsource(endpoint))

                refresh = re.search(
                    "jwt_refresh_token_required", inspect.getsource(endpoint))

                optional = re.search(
                    "jwt_optional", inspect.getsource(endpoint))

                must_validate = re.search(
                    "validate_jwt_access_token", inspect.getsource(endpoint))

                if required or refresh or optional or must_validate:
                    openapi_schema["paths"][path][method]["security"] = [
                        {
                            "Bearer Auth": []
                        }
                    ]
        app.openapi_schema = openapi_schema
        return app.openapi_schema

    return openapi_generator
