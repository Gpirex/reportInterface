"""Common function for all system."""
import json
import logging
import secrets
import string
from typing import List

from aiohttp import ClientSession
from fastapi import HTTPException, Request, Query
from sqlalchemy.exc import SQLAlchemyError

from db.postgres import SessionLocal as postgres_async
from utils.datetime_encoder import DateTimeEncoder


def secret_key_generator():
    """ If there is no reference to an environment variable named SECRET KEY,
    it will generate a default for the user.
    """
    generate = string.ascii_letters + string.digits + string.punctuation
    secret_key = ''.join(secrets.choice(generate) for _ in range(50))
    return secret_key


async def get_db_postgres():
    """Dependency function that yields db sessions."""
    async with postgres_async() as session:
        yield session


def http_exception(message, status, headers=None):
    """
    :param message: {"name_error" : True or False}
    :param status: http response status code.
    :param headers:
    :return: exception error
    """
    return HTTPException(
        status_code=status,
        detail=message,
        headers=headers
    )


async def database_commit(session, model) -> None:
    """Generalized commit for used in the system."""
    try:
        session.add(model)
        await session.commit()
        await session.refresh(model)
    except SQLAlchemyError as err:
        await session.rollback()
        logging.error(f"Error on database_commit: {type(err)} {err}")
        raise err


def data_to_open_search(data_open):
    # tratamento separado de sql/json
    data = {
        'start_date_query': data_open[0],
        'end_date_query': data_open[1],
    }

    data = json.dumps(data, indent=4, cls=DateTimeEncoder)

    return data


def aiohttp_client_session(request: Request) -> ClientSession:
    """Instance for Async Client Requests"""
    return request.app.state.client_session


PAGE_SIZE_DESC = "The max quantity of records to be returned in a single page"
FILTERS_DESC = """This filter can accept search query's like `key:value` and 
will split on the `:` char.<br/><br/>
**key:** If it detects one `.` char inside the `key` 
element (like `name:ABC`), it will treat `key` as a relationship. If it 
detects one or more `,` char inside the `key` element (like `name,code:abc`), 
it will treat `key` as a list of fields, like an `or` comparison.<br/><br/>
**value:** If it detects one `,` char inside the `value` element (like 
`name:AB,XZ`), it will treat `value` as a list of values, like an `or` 
comparison.<br/><br/>
Multiple filters in different fields are joined as `and` conditions;<br>
Multiple values in the same field are joined as `or` conditions."""
SORTS_DESC = """The sort will accept parameters like `col:ASC` or `col:DESC` 
and will split on the `:` char. 
If it does not find a `:` it will sort ascending on that column."""


async def common_filter_parameters(
        page: int = Query(1, title="Page", description="The requested page"),  # NOQA
        page_size: int = Query(100, title="Page size", description=PAGE_SIZE_DESC),  # NOQA
        filters: List[str] = Query(list(), title="Filter fields", description=FILTERS_DESC),  # NOQA
        sorts: List[str] = Query(list(), title="Sort fields", description=SORTS_DESC)  # NOQA
) -> dict:
    return {
        "page": page,
        "page_size": page_size,
        "filters": filters,
        "sorts": sorts
    }
