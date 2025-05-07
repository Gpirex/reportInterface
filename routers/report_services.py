import logging
import os
from collections import defaultdict
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from domain.report_render import report_render
from domain.services import report_service
from domain.services.report_service import ReportService
from domain.services.rules_service import RuleService
from domain.services.user_profiles_service import UserService
from utils.common import get_db_postgres

router = APIRouter(tags=["Report Service"])


@router.get(
    "/v1/registered_incidents/{tenant_id}/{report_id}/{start_date}/{end_date}/{user_timezone}")
async def report_registered_incidents(
        report_id: int,
        start_date: datetime,
        end_date: datetime,
        tenant_id: int,
        user_timezone: str,
        db: AsyncSession = Depends(get_db_postgres)
):
    """Get Registered Incidents for Tenant based on period."""

    formatted_dates_and_timezone = ReportService.builds_and_formats_start_and_end_date(
        start_date=start_date,
        end_date=end_date,
        user_timezone=user_timezone
    )

    model_pattern = {
        "report_name": "Registered Incidents",
        "report_template": "incident_alerts_report",
        "generate_date": datetime.utcnow(),
        "user_timezone": formatted_dates_and_timezone["user_timezone"],
        "language": "en-US",
        "utc": "0",
        'contains_data': False,
        "data": {
            'start_date': formatted_dates_and_timezone["start_date"],
            'end_date': formatted_dates_and_timezone["end_date"],
        }
    }

    query_result_graphic_and_table = await RuleService.get_alerts_and_rules(
        start_date=formatted_dates_and_timezone["start_date"],
        end_date=formatted_dates_and_timezone["end_date"],
        tenant_id=tenant_id,
        db=db
    )

    result_table = query_result_graphic_and_table["result_table"]
    result_graphic = query_result_graphic_and_table["result_graphic"]

    if len(result_graphic) > 0 and len(result_table) > 0:
        model_pattern['contains_data'] = True

        res = defaultdict(list)

        for data in result_table:
            res[data[2]].append((data[0], data[1], data[3]))

        model_pattern["data"]['data_graphic'] = {
            "dates": [data[0] for data in result_graphic],
            "sum_incidents": [data[1] if data[0] else 0 for data in
                              result_graphic],
            "sum_alerts": [data[2] if data[0] else 0 for data in
                           result_graphic],
            "list_incidents_by_dates": [incident for incident in
                                        list(res.values())]
        }

    await report_render(model_pattern, report_id)

    is_exist = os.path.exists(
        f'./reports/report_incident_alerts_report_{report_id}.pdf')

    if is_exist:
        try:
            await report_service.save_report(model_pattern["report_template"],
                                             report_id)
        except IOError as e:
            logging.error(f"IOError writing to file: {e}")


@router.get(
    "/v1/registered_events/{tenant_id}/{report_id}/{start_date}/{end_date}/{user_timezone}")
async def report_registered_events(
        tenant_id: int,
        report_id: int,
        start_date: datetime,
        end_date: datetime,
        user_timezone: str,
        db: AsyncSession = Depends(get_db_postgres)
):
    """Get Registered Event Metrics for Tenant based on period."""

    formatted_dates_and_timezone = ReportService.builds_and_formats_start_and_end_date(
        start_date=start_date,
        end_date=end_date,
        user_timezone=user_timezone
    )

    model_pattern = {
        "report_name": "Registered Events",
        "report_template": "eps_report",
        "generate_date": datetime.utcnow(),
        "user_timezone": formatted_dates_and_timezone["user_timezone"],
        "language": "en-US",
        "utc": "0",
        'contains_data': False,
        "data": {
            'start_date': formatted_dates_and_timezone["start_date"],
            'end_date': formatted_dates_and_timezone["end_date"],
            'eps_contracted': None
        }
    }

    events = await UserService.get_events_by_time_interval_and_tenant_id(
        start_date=formatted_dates_and_timezone["start_date"],
        end_date=formatted_dates_and_timezone["end_date"],
        tenant_id=tenant_id,
        db=db
    )

    if len(events) > 0:
        model_pattern['contains_data'] = True

        events.sort(key=lambda x: x[0]["eps_date"].date(), reverse=False)

        model_pattern["data"]["eps_contracted"] = events[0]["eps_licensed"]
        model_pattern["data"]['table_metrics'] = {
            "dates": [event[0]["eps_date"] for event in events],
            "events": [event[0]["eps_total"] if event[0]["eps_total"] else 0 for
                       event in events],
            "average_eps": [event[0]["eps_avg"] if event[0]["eps_avg"] else 0
                            for event in events],
            "peak_eps": [event[0]["eps"] if event[0]["eps"] else 0 for event in
                         events],
            "peak_eps_moment": [event[0]["eps_date"] for event in events],
        }

    await report_render(model_pattern, report_id)

    is_exist = os.path.exists(f'./reports/report_eps_report_{report_id}.pdf')
    if is_exist:
        try:
            await report_service.save_report(model_pattern["report_template"],
                                             report_id)
        except IOError as e:
            logging.error(f"IOError writing to file: {e}")


@router.get(
    "/v1/top_10_rules/{tenant_id}/{report_id}/{start_date}/{end_date}/{user_timezone}")
async def report_top_10_rules(
        tenant_id: int,
        report_id: int,
        start_date: datetime,
        end_date: datetime,
        user_timezone: str,
        db: AsyncSession = Depends(get_db_postgres)
):
    """Get Top 10 Rules with more alerts for Tenant based on period."""

    formatted_dates_and_timezone = ReportService.builds_and_formats_start_and_end_date(
        start_date=start_date,
        end_date=end_date,
        user_timezone=user_timezone
    )

    model_pattern = {
        "report_name": "Top 10 Rules",
        "report_template": "top_10_rules_report",
        "generate_date": datetime.utcnow(),
        "user_timezone": formatted_dates_and_timezone["user_timezone"],
        "language": "en-US",
        "utc": "0",
        "data": {
            'start_date': formatted_dates_and_timezone["start_date"],
            'end_date': formatted_dates_and_timezone["end_date"]
        }
    }
    top_10_rules = await RuleService.get_top_10_rules(
        start_date=formatted_dates_and_timezone["start_date"],
        end_date=formatted_dates_and_timezone["end_date"],
        tenant_id=tenant_id,
        db=db
    )

    model_pattern["data"]['table_rules'] = {
        "general": [list(result) for result in top_10_rules['result_general']],
        "match": [list(result) for result in top_10_rules['result_match']],
        "threshold": [list(result) for result in
                      top_10_rules['result_threshold']],
        "correlated": [list(result) for result in
                       top_10_rules['result_correlated']],
        "_advanced": [list(result) for result in
                      top_10_rules['result_advanced']]
    }

    await report_render(model_pattern, report_id)

    is_exist = os.path.exists(
        f'./reports/report_top_10_rules_report_{report_id}.pdf')

    if is_exist:
        try:
            await report_service.save_report(model_pattern["report_template"],
                                             report_id)
        except IOError as e:
            logging.error(f"IOError writing to file: {e}")
