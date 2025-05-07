"""OpenSearch connection management and utilities."""
import requests
import json
from utils.common import http_exception
from aiohttp import ClientSession, client_exceptions
from settings import OPENSEARCH_TOKEN

headers = {
    'content-type': 'application/json',
    'Authorization': f'Basic {OPENSEARCH_TOKEN}'
}


async def get_open_search_data(payload, url, client_session: ClientSession) -> dict:
    """Send requests to open search."""
    try:
        async with await client_session.post(
                url = f"{url}report-search-*/_search",
                headers=headers,
                data=json.dumps(payload)) as response:
                return await response.json()

    except client_exceptions.ClientResponseError as e:
        raise http_exception(message=e.message,
                             status=e.status)
