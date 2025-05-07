"""User Service."""
from datetime import datetime

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text

from utils.common import get_db_postgres


class UserService:
    """User service."""

    @staticmethod
    async def get_events_by_time_interval_and_tenant_id(
            start_date: datetime,
            end_date: datetime,
            tenant_id: int,
            db: AsyncSession = Depends(get_db_postgres)
    ):
        query = text("""select event, tenant.eps_licensed from user_interface.event_metrics as event \
               inner join user_interface.tenants as tenant on event.tenant_code=tenant.code \
               where tenant.id =:tenant_id and CAST(event.eps_date AS DATE) >=:start
               and CAST(event.eps_date AS DATE) <=:end;""")

        params = {
            "start": start_date,
            "end": end_date,
            "tenant_id": tenant_id
        }

        result = await db.execute(query, params)
        events = result.fetchall()

        return events
