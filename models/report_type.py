from prettyconf import config
from sqlalchemy import Column, Integer, String

from models.abstract import BaseModel


class ReportType(BaseModel):
    __tablename__ = 'report_type'
    __table_args__ = {"schema": config("POSTGRES_SCHEMA")}

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=True)
    code_name = Column(String(30), nullable=True)
