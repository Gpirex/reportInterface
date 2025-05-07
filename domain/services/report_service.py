"""Report Service."""
from datetime import datetime
import oci
from oci.object_storage import UploadManager
from sqlalchemy.ext.asyncio import AsyncSession

from db.oci import oci_config
from domain.utils.format_date import formate_date
from models.report import ReportDTO, Report
from settings.__init__ import ENVIRONMENT


async def save_report(report_name, report_id):
    """Save report in OCI."""

    object_storage = oci.object_storage.ObjectStorageClient(oci_config)
    namespace = object_storage.get_namespace().data
    bucket_name = "report-blob-storage"
    object_name = f"{ENVIRONMENT}/REPORTS/report_{report_name}_{report_id}.pdf"

    upload_manager = UploadManager(object_storage, allow_parallel_uploads=True)
    response = upload_manager.upload_file(
        namespace, bucket_name, object_name,
        f"./reports/report_{report_name}_{report_id}.pdf")

    return response


class ReportService:
    """Report service."""

    def __init__(self, session: AsyncSession, tenant_id) -> None:
        """Class initialization."""

        self.report_dto = ReportDTO(session, tenant_id)

    async def create_report(self, report_data: dict) -> Report:
        """Create report."""
        report_data["start_date"] = report_data["start_date"].replace(
            tzinfo=None)
        report_data["end_date"] = report_data["end_date"].replace(tzinfo=None)
        report_data["created_at"] = datetime.utcnow()
        report_data["updated_at"] = datetime.utcnow()

        new_report = Report(**report_data)

        await self.report_dto.create(new_report)

        return new_report

    async def get_all_reports(self, report_parameters) -> dict:
        """Get all the reports according to the given parameters."""
        reports = await self.report_dto.get_all_with_filters(
            **report_parameters)

        # Add available values for filters
        filter_created_by = await self.report_dto.get_unique_created_by_values()

        reports["available_filters"] = {"created_by": filter_created_by}

        return reports

    @staticmethod
    def builds_and_formats_start_and_end_date(
            start_date: datetime,
            end_date: datetime,
            user_timezone: str
    ):
        format_data = "%Y-%m-%d %H:%M:%S"
        user_timezone = user_timezone.replace("@", "/") if user_timezone.find(
            "@") else user_timezone

        start_date_formatted = datetime.strptime(
            formate_date(start_date, user_timezone, format_data), format_data)
        end_date_formatted = datetime.strptime(
            formate_date(end_date, user_timezone, format_data), format_data)

        response = {
            "start_date": start_date_formatted,
            "end_date": end_date_formatted,
            "user_timezone": user_timezone
        }

        return response
