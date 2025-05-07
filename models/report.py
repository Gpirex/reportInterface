"""Report model implementations."""
import enum
from typing import List, Union

from prettyconf import config
from sqlalchemy import Column, Integer, String, select, DateTime, distinct, ForeignKey
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import relationship

from models.abstract import BaseModel, FilteredListDTOMixin
from models.report_type import ReportType
from utils.common import database_commit


class Status(enum.Enum):
    """Status type enum class."""
    on_hold = 1
    processing = 2
    done = 3


class Report(BaseModel):
    """Report model."""
    __tablename__ = "report"
    __table_args__ = {"schema": config("POSTGRES_SCHEMA")}

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=True)
    status = Column(Integer, default=Status.on_hold.value, nullable=False)
    type = Column(Integer, ForeignKey("report_type.id"), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    tenant_id = Column(Integer, nullable=False)

    report_type = relationship(ReportType)


class ReportDTO(FilteredListDTOMixin):
    """Report data transfer object."""

    def __init__(self, session: AsyncSession, tenant_id: int) -> None:
        """Class initialization."""
        super().__init__()

        self.base_query = select(Report).where(Report.tenant_id == tenant_id)
        self.tenant_id = tenant_id
        self.session = session
        self.model = Report

    async def create(self, report: Report) -> None:
        """Create report."""
        await database_commit(self.session, report)

    async def get_all_with_filters(
            self,
            tenant_code: str = None,
            page: int = 0,
            page_size: int = 100,
            filters: Union[List[str], None] = None,
            sorts: Union[List[str], None] = None,
            *args,
            **kwargs
    ):
        """Overrides super().get_all_with_filters, w/ default filter by Tenant;
        """
        if filters is None:
            filters = []

        if tenant_code:
            filters.append(f"tenants.code:{tenant_code}")

        sorts.append('id:DESC')
        return await super().get_all_with_filters(page, page_size, filters, sorts)

    async def get_unique_created_by_values(self):
        query = select(distinct(Report.created_by)).where(Report.tenant_id == self.tenant_id)
        result = await self.session.execute(query)
        return result.scalars().unique().all()
