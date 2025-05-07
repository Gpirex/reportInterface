"""ReportDownload schemas implementation."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class ReportDownload(BaseModel):
    """ReportDownload schema."""

    report_id: int
    report_type: int

    class Config:
        orm_mode = True


class ReportCreate(BaseModel):
    """Base Model for daily time recurrence intervals."""
    name: str
    type: int
    start_date: datetime
    end_date: datetime

    class Config:
        orm_mode = True


class ReportOutput(BaseModel):
    id: int
    type: int
    status: int
    name: Optional[str]
    start_date: datetime
    end_date: Optional[datetime]
    created_by: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True


class PaginatedReportListOutput(BaseModel):
    current_page: int
    page_size: int
    number_pages: int
    count: int
    available_filters: Optional[dict[str, list]]
    records: List[ReportOutput]
