"""Triggered rules report implementations."""
from sqlalchemy.sql import text
from datetime import datetime
import pandas as pd


async def get_triggered_rules(report_id, tenant_id, session):
    """Get list of triggered rules."""
    query = text(f"""select rl.id, rl.name, count(alert.triggers) as triggers, sum(alert.logs) as logs, 
                        rl.severity, rl.threat, tenant.name, concat_ws('-', rl.id, rl.name) as rule_data, 
                        rl.source, tenant.cluster_url from rule_interface.report 
                        inner join user_interface.tenants as tenant on report.tenant_id=tenant.id 
                        inner join rule_interface.alert on tenant.id=alert.tenant_id 
                        inner join rule_interface.rule as rl on alert.rule_id=rl.id 
                        inner join rule_interface.trigger as trigg on alert.id = trigg.alert_id  
                        where report.id={report_id} and report.tenant_id={tenant_id} and trigg.start_date_query
                        between report.start_date and report.end_date group by rl.id,
                        tenant.name, tenant.cluster_url order by count(alert.triggers) desc;""")  # NOQA

    result = await session.execute(query)
    rules = result.fetchall()
    return rules


async def get_triggers(report_id, tenant_id, session):
    """Get list of all trigger objects."""
    query = text(f"""select trigg.start_date_query, count(trigg.id) as triggers,
                        concat_ws('-', rl.id, rl.name) as rule, sum(trigg.logs) as logs
                        from rule_interface.report 
                        inner join user_interface.tenants as tenant on report.tenant_id=tenant.id 
                        inner join rule_interface.alert on tenant.id=alert.tenant_id 
                        inner join rule_interface.rule as rl on alert.rule_id=rl.id 
                        inner join rule_interface.trigger as trigg on
                        alert.id = trigg.alert_id  
                        where report.id={report_id} and report.tenant_id={tenant_id} and trigg.start_date_query 
                        between report.start_date and
                        report.end_date group by trigg.start_date_query, rl.id,
                        rl.name, tenant.name order by trigg.start_date_query;""")  # NOQA

    result = await session.execute(query)
    triggers = result.fetchall()
    return triggers


def get_fixed_intervals(start_date, end_date):
    """Handle start and final dates to set the better gap time."""
    diff = end_date - start_date
    d1 = datetime.strftime(start_date, "%Y-%m-%d")
    d2 = datetime.strftime(end_date, "%Y-%m-%d")

    if diff.days == 0:
        gap = "1H"
        format_date = "%H:%M"
    elif 0 < diff.days <= 3:
        gap = "6H"
        format_date = "%m/%d %H:%M"
    elif diff.days <= 90:
        gap = "1d"
        format_date = "%d/%m"
    elif diff.days <= 365:
        gap = "1M"
        format_date = "%B"
    else:
        gap = "1Y"
        format_date = "%Y"

    fixed_intervals = pd.date_range(
        f"{d1} 00:00:00",
        f"{d2} 00:00:00",
        freq=gap
    )
    return gap, format_date, fixed_intervals


async def get_triggered_rules_chart_series(
        start_date, end_date, hank, report_id, tenant_id, session):
    """Mount triggered rules chart series."""
    triggers = await get_triggers(report_id, tenant_id, session)
    intervals = get_fixed_intervals(start_date, end_date)
    # Convert the triggers SQL result in panda data frame.
    df = pd.DataFrame(
        triggers,
        columns=['date', 'triggers', 'rule', 'hits']
    )
    # Indexes the date field, creates a pivot making the list of rules as
    # columns relating the number of triggers in each one.
    pivot_df = df.pivot(values=['triggers'], index='date', columns='rule')
    # Resizes the previous dataframe (pivot) following the correct time range.
    pivot_df.index = pd.to_datetime(pivot_df.index)
    pivot_df_by_freq = pivot_df.resample(intervals[0]).sum()
    # Re-index the data frame containing the data already in the due intervals
    # with all the intervals in the series, getting the intervals without data
    # in the same sequence
    pivot_df_by_freq = pivot_df_by_freq.reindex(intervals[2], fill_value=0)

    # Handle triggered rule chart information's
    datasets = []
    colors = [
        "#0A7261", "#24B47E", "#B1E2C5", "#126098", "#5B82CE", "#B4D7EB",
        "#573E8E", "#8F6ED5", "#D8CDF7", "#8A3A78", "#C46ABB", "#787B7D"
    ]
    # Set the chart labels following the format_date generated.
    labels = list(
        map(lambda x: datetime.strftime(pd.to_datetime(x[0]), intervals[1]),
            pivot_df_by_freq.to_records())
    )
    # Used when exists more than 10 lines in report.
    others_data = []
    # Variable to control the color from chart lines.
    cont = 0
    # Handle dataframes to mount the dataset chart.
    for idx_h, h in enumerate(hank):
        for idx, df in enumerate(pivot_df_by_freq.keys()):
            if h == df[1]:
                data = []
                if len(datasets) < 10:
                    for value in pivot_df_by_freq.values:
                        data.append(value[idx])
                    datasets.append(
                        {
                            "label": h,
                            "fill": False,
                            "backgroundColor": colors[cont],
                            "borderColor": colors[cont],
                            "pointStrokeColor": "#fff",
                            "borderCapStyle": 'butt',
                            "data": data,
                        }
                    )
                    cont += 1

                else:
                    for value in pivot_df_by_freq.values:
                        data.append(value[idx])
                        others_data.append(data)
    # Used to group other results in chart after 10 first lines.
    if len(others_data) > 0:
        data = [sum(x) for x in zip(*others_data)]
        datasets.append(
            {
                "label": "Others",
                "fill": False,
                "backgroundColor": colors[cont],
                "borderColor": colors[cont],
                "data": data,
            }
        )

    return labels, datasets


def get_triggered_rules_table(rules):
    """Handle rules SQL result to set main triggered rules table."""
    main_rules_triggered = []
    for idx, rule in enumerate(rules):
        obj = {
            "id": rule[0],
            "name": rule[1] if rule[8] == 0 else f"*{rule[1]}",
            "triggers": rule[2],
            "hits": rule[3],
            "severity": rule[4],
            "threat_names": [{"threatName": "---------"}],
            "threat_tech": [{"technique": "---------"}]
        }
        # threat_names = []
        #     if rule[5] != "[]":
        #         threat = ast.literal_eval(rules[idx][5])
        #         for t in threat:
        #             threat_tech = []
        #             threat_names.append({"threatName": t['tactic']['name']})
        #             obj['threat_names'] = threat_names
        #             techniques = t['technique']
        #             for technique in techniques:
        #                 threat_tech.append(
        #                     {
        #                         "technique": technique['id'],
        #                         "reference": technique['reference']
        #                     })
        #             obj['threat_tech'] = threat_tech
        #
        main_rules_triggered.append(obj)
    return main_rules_triggered


def get_formatted_payload(
        start_date,
        end_date,
        triggered_rules_chart,
        main_rules_triggered,
        events_series,
        rule_name
):
    """Format the jsreport data payload."""
    if events_series is None:
        events_series = ['-----', '-----']

    start = datetime.strftime(start_date, "%Y-%m-%d %H:%M:%S")
    end = datetime.strftime(end_date, "%Y-%m-%d %H:%M:%S")
    payload = {
        "template": {"name": "/report/triggered_rule/main"},
        "data": {
            "companies": [{
                "company": {
                    "fullName": rule_name,
                    "business": "report Query Report"
                },
                "scoreHighlights": [
                    "This section shows a timeline graph that references "
                    "the number of triggers of all enabled rules and the "
                    "relevance between them."
                ],
                "businessSummary": f"This document details all triggers "
                                   f"identified from {start} to "
                                   f"{end} in relation to the enabled "
                                   "rules.",
                "eventChart": "This section shows a timeline graph "
                              "which makes reference to all events processed."
                              " In total report processed events.",
                "tableMainTriggeredRules": (
                    "This section summarizes in a "
                    "table format the relation of events and triggers of each"
                    "enabled rule. It is important to understand the difference"
                    " between events and triggers, the first refers to the total"
                    " of logs received, while the second refers to the number of"
                    " identified matches referenced for each rule. Triggered"
                    " rules are sorted according to their respective number of"
                    " triggers. Rules whose names start with * indicate that"
                    " they are custom rules for the client. The other rules make"
                    " up the report rules baseline."),
                # NOQA
                "triggeredRulesChart": {
                    "labels": triggered_rules_chart[0],
                    "datasets": triggered_rules_chart[1]
                },
                "allProcessedEvents": {
                    "labels": events_series[0],
                    "datasets": events_series[1]
                },
                "mainRulesTriggered": main_rules_triggered,
                "count": len(main_rules_triggered)

            }],
            "options": {"reports": {"save": "true"}}
        }
    }

    return payload
