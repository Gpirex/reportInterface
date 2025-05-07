"""Rule Services."""
from datetime import datetime

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text

from utils.common import get_db_postgres


class RuleService:
    """Rule Services."""

    @staticmethod
    async def get_alerts_and_rules(
            start_date: datetime,
            end_date: datetime,
            tenant_id: int,
            db: AsyncSession = Depends(get_db_postgres)
    ):
        query_graphic = text(
            """select 
                    to_char(alert.created_at, 'MM/DD/YYYY') as created_date, 
                    count(alert.id) as incidents_day,
                    sum(alert.triggers) as sum_triggers
                from rule_interface.alert as alert
                where alert.tenant_id=:tenant_id and alert.trial = false and alert.created_at between \
                :start_date and :end_date group by created_date"""
        )

        query_table = text(
            """select alert.id, rule.name,
                    to_char(alert.created_at, 'MM/DD/YYYY') as created_date, alert.triggers
                from rule_interface.alert as alert
                    inner join rule_interface.rule as rule on rule.id=alert.rule_id
                where alert.tenant_id=:tenant_id and alert.trial = false and alert.created_at between \
                :start_date and :end_date order by created_date, alert.id"""
        )

        params = {
            "start_date": start_date.replace(tzinfo=None),
            "end_date": end_date.replace(tzinfo=None),
            "tenant_id": tenant_id
        }

        result_graphic = await db.execute(query_graphic, params)
        result_graphic = result_graphic.fetchall()

        result_table = await db.execute(query_table, params)
        result_table = result_table.fetchall()

        response = {
            "result_graphic": result_graphic,
            "result_table": result_table
        }

        return response

    @staticmethod
    async def get_top_10_rules(
            start_date: datetime,
            end_date: datetime,
            tenant_id: int,
            db: AsyncSession = Depends(get_db_postgres)
    ):
        query_general = text("""SELECT rule.id, rule.name, \
              CASE WHEN rule.rule_type=1 THEN 'Match' WHEN rule.rule_type=2 THEN 'Threshold' \
              WHEN rule.rule_type=3 THEN 'Correlation' WHEN rule.rule_type=4 THEN 'Advanced' END as type, \
              sum(alert.triggers) as alerts FROM rule_interface.rule as rule \
              INNER JOIN rule_interface.alert as alert on alert.rule_id = rule.id \
              WHERE alert.tenant_id =:tenant_id and alert.created_at between :start_date and :end_date \
              GROUP BY rule.id ORDER BY alerts DESC limit 10""")

        query_match = text("""SELECT rule.id, rule.name, sum(alert.triggers) as alerts,
              CASE WHEN rule.severity=1 THEN 'Info' WHEN rule.severity=2 THEN 'Low' 
              WHEN rule.severity=3 THEN 'Medium' WHEN rule.severity=4 THEN 'High' 
              WHEN rule.severity=5 THEN 'Critical' END,
              CASE WHEN rule.source=0 THEN 'Default' WHEN rule.source=1 THEN 'Tenant' WHEN rule.source=2 THEN 'Channel' END
              FROM rule_interface.rule as rule 
              INNER JOIN rule_interface.alert as alert on alert.rule_id = rule.id 
              WHERE alert.tenant_id =:tenant_id and rule.rule_type = 1 and alert.created_at between :start_date and :end_date 
              GROUP BY rule.id ORDER BY alerts DESC limit 10""")

        query_threshold = text("""SELECT rule.id, rule.name, sum(alert.triggers) as alerts,
              CASE WHEN rule.severity=1 THEN 'Info' WHEN rule.severity=2 THEN 'Low' 
              WHEN rule.severity=3 THEN 'Medium' WHEN rule.severity=4 THEN 'High' 
              WHEN rule.severity=5 THEN 'Critical' END,
              CASE WHEN rule.source=0 THEN 'Default' WHEN rule.source=1 THEN 'Tenant' WHEN rule.source=2 THEN 'Channel' END
              FROM rule_interface.rule as rule 
              INNER JOIN rule_interface.alert as alert on alert.rule_id = rule.id 
              WHERE alert.tenant_id =:tenant_id and rule.rule_type = 2 and alert.created_at between :start_date and :end_date 
              GROUP BY rule.id ORDER BY alerts DESC limit 10""")

        query_correlated = text("""SELECT rule.id, rule.name, sum(alert.triggers) as alerts,
              CASE WHEN rule.severity=1 THEN 'Info' WHEN rule.severity=2 THEN 'Low' 
              WHEN rule.severity=3 THEN 'Medium' WHEN rule.severity=4 THEN 'High' 
              WHEN rule.severity=5 THEN 'Critical' END,
              CASE WHEN rule.source=0 THEN 'Default' WHEN rule.source=1 THEN 'Tenant' WHEN rule.source=2 THEN 'Channel' END
              FROM rule_interface.rule as rule 
              INNER JOIN rule_interface.alert as alert on alert.rule_id = rule.id 
              WHERE alert.tenant_id =:tenant_id and rule.rule_type = 3 and alert.created_at between :start_date and :end_date 
              GROUP BY rule.id ORDER BY alerts DESC limit 10""")

        query_advanced = text("""SELECT rule.id, rule.name, sum(alert.triggers) as alerts,
              CASE WHEN rule.severity=1 THEN 'Info' WHEN rule.severity=2 THEN 'Low' 
              WHEN rule.severity=3 THEN 'Medium' WHEN rule.severity=4 THEN 'High' 
              WHEN rule.severity=5 THEN 'Critical' END,
              CASE WHEN rule.source=0 THEN 'Default' WHEN rule.source=1 THEN 'Tenant' WHEN rule.source=2 THEN 'Channel' END
              FROM rule_interface.rule as rule 
              INNER JOIN rule_interface.alert as alert on alert.rule_id = rule.id 
              WHERE alert.tenant_id =:tenant_id and rule.rule_type = 4 and alert.created_at between :start_date and :end_date 
              GROUP BY rule.id ORDER BY alerts DESC limit 10""")

        params = {
            "start_date": start_date.replace(tzinfo=None),
            "end_date": end_date.replace(tzinfo=None),
            "tenant_id": tenant_id
        }

        result_general = await db.execute(query_general, params)
        result_general = result_general.fetchall()

        result_match = await db.execute(query_match, params)
        result_match = result_match.fetchall()

        result_threshold = await db.execute(query_threshold, params)
        result_threshold = result_threshold.fetchall()

        result_correlated = await db.execute(query_correlated, params)
        result_correlated = result_correlated.fetchall()

        result_advanced = await db.execute(query_advanced, params)
        result_advanced = result_advanced.fetchall()

        response = {
            "result_general": result_general,
            "result_match": result_match,
            "result_threshold": result_threshold,
            "result_correlated": result_correlated,
            "result_advanced": result_advanced
        }

        return response
