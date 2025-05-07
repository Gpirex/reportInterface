"""Get tenant session info."""
import logging
from aiohttp import ClientSession, client_exceptions
import settings
from utils.common import http_exception


async def get_tenant_session_info(tenant_code, jwt_token,
                                  client_session: ClientSession):
    """Get tenant information from user_interface"""

    user_interface_tenant_session_info_url = \
        f'{settings.USER_INTERFACE_URL}/api/v1/tenants/{tenant_code}/info'

    try:
        logging.info(f"Getting info for tenant #{str(tenant_code)}")
        async with await client_session.get(
                url=user_interface_tenant_session_info_url,
                headers={"Authorization": f"Bearer {jwt_token}"}
        ) as response:
            return await response.json()

    except client_exceptions.ClientConnectorError as e:
        logging.exception(f"Error getting info for tenant #{str(tenant_code)}"
                          f" - {type(e)} {e}")
        raise http_exception(message=e, status=500)

    except client_exceptions.ClientResponseError as e:
        logging.exception(f"Error getting info for tenant #{str(tenant_code)}"
                          f" - {type(e)} {e.message}")
        raise http_exception(message=e.message, status=e.status)
