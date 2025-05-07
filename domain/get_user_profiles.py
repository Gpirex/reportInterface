"""Get user profiles from user interface."""
import logging

from aiohttp import ClientSession, client_exceptions

import settings
from utils.common import http_exception


async def get_user_profiles_info(tenant_code, jwt_token,
                                 client_session: ClientSession):
    """Get user profiles from user_interface"""

    user_interface_user_profiles_info_url = \
        f'{settings.USER_INTERFACE_URL}/api/v1/{tenant_code}/user-profiles'

    try:
        logging.info(f"Getting user profiles info for tenant "
                     f"#{str(tenant_code)}")
        async with await client_session.get(
                url=user_interface_user_profiles_info_url,
                headers={"Authorization": f"Bearer {jwt_token}"}
        ) as response:
            return await response.json()

    except client_exceptions.ClientConnectorError as e:
        logging.exception(f"Error getting user profiles info for tenant "
                          f"#{str(tenant_code)} - {type(e)} {e}")
        raise http_exception(message=e, status=500)

    except client_exceptions.ClientResponseError as e:
        logging.exception(f"Error getting user profiles info for tenant "
                          f"#{str(tenant_code)} - {type(e)} {e.message}")
        raise http_exception(message=e.message, status=e.status)


async def get_user_profiles_by_email(tenant_code: str,
                                     jwt_token: str,
                                     email: str,
                                     client_session: ClientSession):
    """Get user profile from user_interface by email"""

    user_interface_user_profile_url = \
        f'{settings.USER_INTERFACE_URL}/api/v1/user-profiles/email/{email}'

    try:
        logging.info(f"Getting user profile info for tenant "
                     f"#{str(tenant_code)}")
        async with await client_session.get(
                url=user_interface_user_profile_url,
                headers={"Authorization": f"Bearer {jwt_token}"}
        ) as response:
            return await response.json()

    except client_exceptions.ClientConnectorError as e:
        logging.exception(f"Error getting user profile info for tenant "
                          f"#{str(tenant_code)} - {type(e)} {e}")
        raise http_exception(message=e, status=500)

    except client_exceptions.ClientResponseError as e:
        logging.exception(f"Error getting user profile info for tenant "
                          f"#{str(tenant_code)} - {type(e)} {e.message}")
        raise http_exception(message=e.message, status=e.status)
