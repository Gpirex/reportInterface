import logging
from datetime import datetime

from aiohttp import ClientSession
from fastapi import APIRouter, Depends, Path, Request
from fastapi_jwt_auth import AuthJWT
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from domain.get_session_info import get_tenant_session_info
from domain.get_user_profiles import get_user_profiles_by_email
from domain.kafka_producer import publish_message
from domain.services.report_service import ReportService
from models.report import Report
from schemas.report import PaginatedReportListOutput, \
    ReportCreate as ReportCreateSchema
from utils.common import common_filter_parameters, get_db_postgres, \
    aiohttp_client_session, http_exception
from utils.fastapi_limiter import default_user_identifier
from utils.responses.report_responses import response_reports

router = APIRouter(tags=["Reports"])


@router.get("/v1/{tenant_code}/reports",
            responses=response_reports.get("list"),
            response_model=PaginatedReportListOutput
            )
async def list_reports(
        tenant_code: str = Path(
            None,
            title="Tenant code",
            description="Code of the tenant from which will display records"),
        filter_parameters: dict = Depends(common_filter_parameters),
        jwt_auth: AuthJWT = Depends(),
        session: AsyncSession = Depends(get_db_postgres),
        async_client: ClientSession = Depends(aiohttp_client_session)
):
    """List all match reports."""
    jwt_auth.jwt_required()

    # Validate Tenant access
    tenant = await get_tenant_session_info(
        tenant_code=tenant_code,
        jwt_token=jwt_auth.__dict__[
            "_token"],
        client_session=async_client
    )
    tenant_id = tenant["tenant_id"]

    report_parameters = {
        "tenant_id": tenant_id,
        "page": filter_parameters.get("page"),
        "page_size": filter_parameters.get("page_size"),
        "filters": filter_parameters.get("filters"),
        "sorts": filter_parameters.get("sorts")
    }

    report_service = ReportService(session, tenant_id)
    result = await report_service.get_all_reports(report_parameters)

    return result


@router.post("/v1/{tenant_code}/reports",
             responses=response_reports.get("register"))
async def register_report(
        request: Request,
        report_data: ReportCreateSchema,
        tenant_code: str = Path(
            None,
            title="Tenant code",
            description="Code of the tenant from which will display records"),
        jwt_auth: AuthJWT = Depends(),
        session: AsyncSession = Depends(get_db_postgres),
        async_client: ClientSession = Depends(aiohttp_client_session)
):
    """Register a match report."""
    jwt_auth.jwt_required()

    tenant = await get_tenant_session_info(
        tenant_code=tenant_code,
        jwt_token=jwt_auth.__dict__[
            "_token"],
        client_session=async_client
    )

    decoded = jwt_auth.get_raw_jwt(jwt_auth.__dict__["_token"])
    user_email = decoded.get("sub").split(":")[0]

    user = await get_user_profiles_by_email(
        email=user_email,
        tenant_code=tenant_code,
        jwt_token=jwt_auth.__dict__[
            "_token"],
        client_session=async_client
    )

    user_timezone = user["timezone"] if user["timezone"] != "Default device" else "UTC"
    user_timezone_ = user_timezone.replace("/", "@") if user_timezone.find(
        "/") else user_timezone

    tenant_id = tenant["tenant_id"]

    report_service = ReportService(session, tenant_id)

    report_data = report_data.dict()
    report_data["tenant_id"] = tenant_id
    report_data["created_by"] = user_email

    try:
        Report(**report_data)

    except Exception as e:
        raise http_exception(message=f"Invalid report data: {e}",
                             status=status.HTTP_422_UNPROCESSABLE_ENTITY)

    new_report = await report_service.create_report(report_data)

    publish_message(
        name="created_report_activity_history",
        topic="report.report.created",
        payload=send_payload(report_data, new_report.id, user_timezone_)
    )

    try:

        publish_message(
            name="report_activity_history",
            topic="report.user.activity.history",
            payload=await send_activity_payload(
                origin=[tenant_code],
                request=request,
                email=user_email,
                first_name=user["first_name"],
                last_name=user["last_name"],
                action="create_report",
                object_reference={
                    "id": new_report.id,
                    "report_type": new_report.type
                }
            )
        )
    except KeyError:
        logging.info(
            f"Failed to fetch user profile in report create. "
            f"tenant_code : {tenant_code}")

    return {
        "detail": "api072",
        "new_report_id": new_report.id
    }


def send_payload(report, report_id, user_timezone):
    return {
        "report_id": report_id,
        "type": report["type"],
        "start_date": report["start_date"].isoformat(),
        "end_date": report["end_date"].isoformat(),
        "tenant_id": report["tenant_id"],
        "user_timezone": user_timezone
    }


async def send_activity_payload(origin, request, email,
                                first_name, last_name, action,
                                object_reference):
    """Mount payload to send user activity history."""
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "email": email,
        "category": "report",
        "first_name": first_name,
        "last_name": last_name,
        "action": action,
        "object_reference": object_reference,
        "origin": origin,
        "ip": await default_user_identifier(request),
    }
