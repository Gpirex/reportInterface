import base64

import plotly.graph_objects as go
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

from domain.utils.format_date import formate_date

# TEMPLATE INFO
report_config = {
    "en-US": {
        "report_name": "Registered Incidents",
        "description_title": "Summary introduction",
        "description": "This report aims to present data and metrics related to the registered incidents in report "
                       "during a designated time range. It includes the total number of incidents, consisting of the"
                       " name and number of alerts for each incident, detailed by registration date.",
        "results_title": "Results",
        "time_range_title": "Time range",
        "consumed_incident_alert_title": "Registered Incidents",
        "consumed_incident_alert_description": "This section presents a chart of the data related to the registered"
                                               " incidents and their alerts.",
        "table_incident_alert_description": "This section presents in a table the registered incidents for each day and"
                                            " the total number of alerts corresponding to each incident.",
        "contains_data": "There were no incidents in the designated time range."
    }
}


async def report_render_content(data):
    report_info = report_config[data['language']]
    env = Environment(loader=FileSystemLoader(''))

    start_date = data['data']['start_date'].strftime("%m/%d/%Y %H:%M")
    end_date = data['data']['end_date'].strftime("%m/%d/%Y %H:%M")
    date_generate = formate_date(data['generate_date'], data['user_timezone'], "%m/%d/%Y - %H:%M")

    html = env.get_template("domain/templates/" + data['report_template'] + "/template_no_results.html")

    template_vars = {
        "report_name": report_info['report_name'],
        "date_generate": date_generate,
        "description_title": report_info['description_title'],
        "description": report_info['description'],
        "results_title": report_info['results_title'],
        "contains_data": report_info['contains_data'],
        "time_range_title": report_info['time_range_title'],
        "start_date": start_date,
        "end_date": end_date
    }

    if data['contains_data']:
        html = env.get_template("domain/templates/" + data['report_template'] + "/template.html")

        png_base64 = await __create_graphic_incidents(data)

        data_table_incidents = await __create_table_incidents(data)

        template_vars = {
            "report_name": report_info['report_name'],
            "date_generate": date_generate,
            "description_title": report_info['description_title'],
            "description": report_info['description'],
            "results_title": report_info['results_title'],
            "time_range_title": report_info['time_range_title'],
            "consumed_incident_alert_title": report_info['consumed_incident_alert_title'],
            "consumed_incident_alert_description": report_info['consumed_incident_alert_description'],
            "table_incident_alert_description": report_info['table_incident_alert_description'],
            "total_incidents": data_table_incidents['total_incidents'],
            "total_alerts": data_table_incidents['total_alerts'],
            "incidents_alerts_table": data_table_incidents['data_table'],
            "chart_incident_alert": png_base64,
            "start_date": start_date,
            "end_date": end_date
        }

    html = html.render(template_vars)
    html = HTML(string=html)

    return html


async def __create_graphic_incidents(data):
    x2 = data['data']['data_graphic']['dates']
    y2 = data['data']['data_graphic']['sum_incidents']
    z2 = data['data']['data_graphic']['sum_alerts']

    fig2 = go.Figure(
        data=[go.Bar(x=x2, y=y2, marker_color='rgb(230, 244, 247)', marker_line_color='rgb(8, 145, 178)')],
        layout={'paper_bgcolor': 'rgba(0,0,0,0)', 'plot_bgcolor': 'rgba(0,0,0,0)', 'showlegend': False,
                'yaxis': dict(showline=False, showgrid=False, zeroline=False)})

    fig2.add_trace(
        go.Scatter(
            x=x2,
            y=z2,
            yaxis="y2",
            mode='lines',
            marker_color='rgb(167, 139, 250)',
            marker_line_width=2.5
        )
    )

    fig2.update_layout(
        width=1200,
        height=600,
        legend=dict(orientation="h"),
        margin_t=0,
        margin_r=0,
        margin_l=0,
        font_size=25,
        yaxis=dict(
            side="left"
        ),
        yaxis2=dict(
            side="right",
            overlaying="y",
            tickmode="sync"
        ),
    )

    png_bytes = fig2.to_image(format="png")
    png_base64 = base64.b64encode(png_bytes).decode('ascii')

    return png_base64


async def __create_table_incidents(data):
    data_table = ""
    index = 0
    total_incidents = 0
    total_alerts = 0

    for value in data["data"]["data_graphic"]["dates"]:
        total_alert_day = 0
        data_print = value

        line_date = '<tr class="dateDay">'
        line_date += '<td colspan="2"> <span class="small"> DATE </span> <span> ' + str(
            data_print) + ' </span></td>'
        line = ' '
        for incident in data["data"]["data_graphic"]["list_incidents_by_dates"][index]:
            line += '<tr class="incidentTd">'
            line += '<td>' + str(incident[0]) + '</td>'
            line += '<td>' + incident[1] + '</td>'
            line += '<td class="total">' + str(incident[2]) + '</td>'
            total_alert_day += incident[2]
            line += '</tr>'
        line_date += '<td class="total"> <span class="small"> TOTAL DAY </span> <span>' \
                     + str(total_alert_day) + '</span> </td>'
        line_date += '</tr>'

        index = index + 1
        data_table += line_date + line

    for incident in data["data"]["data_graphic"]["sum_incidents"]:
        total_incidents += incident

    for alert in data["data"]["data_graphic"]["sum_alerts"]:
        total_alerts += alert

    total_incidents = '{:,}'.format(total_incidents)
    total_alerts = '{:,}'.format(total_alerts)

    return {
        'total_incidents': total_incidents,
        'total_alerts': total_alerts,
        'data_table': data_table
    }
