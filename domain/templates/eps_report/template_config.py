import base64
import copy

import plotly.graph_objects as go
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

from domain.utils.format_date import formate_date

# TEMPLATE INFO
report_config = {
    "en-US": {
        "report_name": "Registered Events",
        "description_title": "Registered Events",
        "description": "This report aims to present data and metrics related to \
        the registered events in report during a designated time range. It includes \
        the licensed events per secund (EPS), consumed EPS consisting of total \
        and average, and EPS peak detailed by date and time of registration.",
        "results_title": "Results",
        "time_range_title": "Time range",
        "consumed_EPS_title": "Consumed EPS",
        "consumed_EPS_description": "This section presents bar charts of the data \
        related to the registered events and the EPS peaks.",
        "table_EPS_description": "This section presents the overview of the consumption \
        of EPS containing all the data referring.",
        "contains_data": "There were no events in the designated time range."
    }
}


async def report_render_content(data):
    report_info = report_config[data['language']]
    env = Environment(loader=FileSystemLoader(''))
    html = env.get_template("domain/templates/" + data[
        'report_template'] + "/template_no_results.html")

    start_date = data['data']['start_date'].strftime("%m/%d/%Y %H:%M")
    end_date = data['data']['end_date'].strftime("%m/%d/%Y %H:%M")

    date_generate = formate_date(data['generate_date'], data['user_timezone'],
                                 "%m/%d/%Y - %H:%M")

    template_vars = {
        "report_name": report_info['report_name'],
        "date_generate": date_generate,
        "description_title": report_info['description_title'],
        "description": report_info['description'],
        "results_title": report_info['results_title'],
        "time_range_title": report_info['time_range_title'],
        "consumed_EPS_title": report_info['consumed_EPS_title'],
        "contains_data": report_info['contains_data'],
        "start_date": start_date,
        "end_date": end_date
    }

    if data['contains_data']:
        html = env.get_template(
            "domain/templates/" + data['report_template'] + "/template.html")

        graphic_events = await __create_graphic_events(data)
        table_events = await __create_table_events(data, graphic_events['eps'])

        template_vars = {
            "report_name": report_info['report_name'],
            "date_generate": date_generate,
            "description_title": report_info['description_title'],
            "description": report_info['description'],
            "results_title": report_info['results_title'],
            "time_range_title": report_info['time_range_title'],
            "consumed_EPS_title": report_info['consumed_EPS_title'],
            "consumed_EPS_description": report_info['consumed_EPS_description'],
            "table_EPS_description": report_info['table_EPS_description'],
            "total_events": table_events['total_events'],
            "eps_table": table_events['data_table'],
            "chart_EPS": graphic_events['png_base64'],
            "chart_EPS_peak": graphic_events['png_base64_peach'],
            "start_date": start_date,
            "end_date": end_date,
            "eps": table_events['eps']
        }

    html = html.render(template_vars)
    html = HTML(string=html)

    return html


async def __create_graphic_events(data):
    x = copy.copy(data['data']['table_metrics']['dates'])
    y = copy.copy(data['data']['table_metrics']['events'])

    for index, date in enumerate(x):
        data_formated = formate_date(date, "America/Sao_Paulo", "%m/%d/%Y")
        x[index] = data_formated

    fig = go.Figure(data=[go.Bar(x=x, y=y)],
                    layout={
                        'paper_bgcolor': 'rgba(0,0,0,0)',
                        'plot_bgcolor': 'rgba(0,0,0,0)',
                        'showlegend': False,
                        'yaxis': dict(
                            showline=False,
                            showgrid=False,
                            zeroline=False)
                    })
    fig.update_layout(legend=dict(x=0.46, orientation="h"), width=1200,
                      height=400, margin_t=0, margin_r=0, margin_l=0,
                      font_size=18)
    fig.update_traces(marker_color='rgb(223,244,247)',
                      marker_line_color='rgb(0,146,176)', marker_line_width=2.5)
    png_bytes = fig.to_image(format="png")
    png_base64 = base64.b64encode(png_bytes).decode('ascii')

    y = copy.copy(data['data']['table_metrics']['peak_eps'])

    eps = data['data']['eps_contracted']
    percent70 = ((70 / 100) * eps)
    percent100 = ((100 / 100) * eps)
    percent115 = ((115 / 100) * eps)

    marker_line_color = []
    marker_color = []
    standard_colors = {
        "low": "rgb(229,244,247)",
        "normal": "rgb(255,246,226)",
        "medium": "rgb(255,234,210)",
        "high": "rgb(254,236,236)"
    }
    standard_borders = {
        "low": "rgb(3,150,166)",
        "normal": "rgb(251,191,108)",
        "medium": "rgb(242,135,41)",
        "high": "rgb(242,65,80)"
    }
    for i in y:
        if i < percent70:
            marker_line_color.append(standard_borders["low"])
            marker_color.append(standard_colors["low"])
        elif percent70 <= i < percent100:
            marker_line_color.append(standard_borders["normal"])
            marker_color.append(standard_colors["normal"])
        elif percent100 <= i < percent115:
            marker_line_color.append(standard_borders["medium"])
            marker_color.append(standard_colors["medium"])
        else:
            marker_line_color.append(standard_borders["high"])
            marker_color.append(standard_colors["high"])

    fig2 = go.Figure(data=[go.Bar(x=x, y=y, marker={'color': y})],
                     layout={
                         'paper_bgcolor': 'rgba(0,0,0,0)',
                         'plot_bgcolor': 'rgba(0,0,0,0)',
                         'showlegend': False,
                         'yaxis': dict(
                             showline=False,
                             showgrid=False,
                             zeroline=False)
                     })
    fig2.update_layout(width=1200, height=400, margin_t=0, margin_r=0,
                       margin_l=0, font_size=18)
    fig2.update_traces(marker_color=marker_color,
                       marker_line_color=marker_line_color,
                       marker_line_width=2.5)

    png_bytes = fig2.to_image(format="png")
    png_base64_peach = base64.b64encode(png_bytes).decode('ascii')

    return {
        'png_base64': png_base64,
        'png_base64_peach': png_base64_peach,
        'eps': eps
    }


async def __create_table_events(data, eps):
    data_table = ""
    index = 0
    total_events = 0

    for line in data['data']['table_metrics']["events"]:

        data_print = data['data']['table_metrics']['dates'][index]
        data_print = data_print.strftime("%m/%d/%Y")

        eps_hours_print = formate_date(
            data['data']['table_metrics']['peak_eps_moment'][index],
            "America/Sao_Paulo",
            "%H:%M:%S")

        event_format = data['data']['table_metrics']['events'][index]
        event_format = '{:,}'.format(event_format)
        average = data['data']['table_metrics']['average_eps'][index]
        average = '{:,}'.format(average)
        peak_eps = data['data']['table_metrics']['peak_eps'][index]
        peak_eps = '{:,}'.format(peak_eps)

        line = '<tr>'
        line += '<td>' + str(data_print) + '</td>'
        line += '<td class="textRigth">' + event_format + '</td>'

        line += '<td class="textRigth">' + average + '</td>'
        line += '<td class="textRigth">' + peak_eps + '</td>'
        line += '<td class="textRigth">' + str(eps_hours_print) + '</td>'
        line += '</tr>'

        data_table += line
        total_events += data['data']['table_metrics']['events'][index]
        index = index + 1

    total_events = '{:,}'.format(total_events)
    eps = '{:,}'.format(eps)

    return {
        'total_events': total_events,
        'eps': eps,
        'data_table': data_table
    }
