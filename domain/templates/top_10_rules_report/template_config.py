import base64
import io
from collections import defaultdict
from typing import Callable

import plotly.graph_objects as go
from PIL import Image
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

from domain.utils.format_date import formate_date

report_config = {
    "en-US": {
        "report_name": "Top 10 Rules",
        "description_title": "Summary introduction",
        "description": "This report aims to present data and metrics related to the registered rules in report that "
                       "generated the most alerts during a designated time range. It includes the top 10 rules "
                       "considering all types and the top 10 for each type of rule.",
        "results_title": "Results",
        "time_range_title": "Time range",
        "table_top_10_rules_title": "Top 10 Rules",
        "table_top_10_rules_title_description": "This section presents a ranking of the top 10 rules that generated the"
                                                " most alerts, considering all rule types.",
        "table_top_10_match_rules_title": "Top 10 Match rules",
        "table_top_10_match_rules_title_description": "This section presents a ranking of the top 10 Match rules that "
                                                      "generated the most alerts, detailed by origin and level of "
                                                      "criticality.",
        "table_top_10_threshold_rules_title": "Top 10 Threshold rules",
        "table_top_10_threshold_rules_title_description": "This section presents a ranking of the top 10 Threshold "
                                                          "rules that generated the most alerts, detailed by origin "
                                                          "and level of criticality.",
        "table_top_10_correlation_rules_title": "Top 10 Correlation rules",
        "table_top_10_correlation_rules_title_description": "This section presents a ranking of the top 10 Correlation "
                                                            "rules that generated the most alerts, detailed by origin "
                                                            "and level of criticality.",
        "table_top_10_advanced_rules_title": "Top 10 Advanced rules",
        "table_top_10_advanced_rules_title_description": "This section presents a ranking of the top 10 Advanced rules "
                                                         "that generated the most alerts, detailed by origin and level "
                                                         "of criticality.",
        "contains_data_rules": "There were no rules in the designated time range."
    }
}


async def report_render_content(data):
    data_table_rules = []
    data_graphic_rules = []
    report_info = report_config[data['language']]
    env = Environment(loader=FileSystemLoader(''))

    start_date = data['data']['start_date'].strftime("%m/%d/%Y %H:%M")
    end_date = data['data']['end_date'].strftime("%m/%d/%Y %H:%M")
    date_generate = formate_date(data['generate_date'], data['user_timezone'],
                                 "%m/%d/%Y - %H:%M")

    html = env.get_template("domain/templates/" + data['report_template'] + "/template.html")

    for key, value in data['data']['table_rules'].items():
        result_table = await __create_table_rules(key, value)
        data_table_rules.append(result_table)

        if key != 'general':
            result_graphic = await __create_graphic_rules(key, value)
            data_graphic_rules.append(result_graphic)

    template_vars = {
        "report_name": report_info['report_name'],
        "date_generate": date_generate,
        "description_title": report_info['description_title'],
        "description": report_info['description'],
        "results_title": report_info['results_title'],
        "contains_data_rules": report_info['contains_data_rules'],
        "time_range_title": report_info['time_range_title'],
        "table_top_10_rules_title": report_info['table_top_10_rules_title'],
        "table_top_10_rules_title_description": report_info['table_top_10_rules_title_description'],
        "table_top_10_match_rules_title": report_info['table_top_10_match_rules_title'],
        "table_top_10_match_rules_title_description": report_info['table_top_10_match_rules_title_description'],
        "table_top_10_threshold_rules_title": report_info['table_top_10_threshold_rules_title'],
        "table_top_10_threshold_rules_title_description": report_info['table_top_10_threshold_rules_title_description'],
        "table_top_10_correlation_rules_title": report_info['table_top_10_correlation_rules_title'],
        "table_top_10_correlation_rules_title_description": report_info[
            'table_top_10_correlation_rules_title_description'],
        "table_top_10_advanced_rules_title": report_info['table_top_10_advanced_rules_title'],
        "table_top_10_advanced_rules_title_description": report_info['table_top_10_advanced_rules_title_description'],
        "top_10_table_general": data_table_rules[0]['general'] if data_table_rules[0] else '',
        "top_10_table_match": data_table_rules[1]['match'] if data_table_rules[1] else '',

        "top_10_graphic_match_rules_origin": data_graphic_rules[0]['rules_origin']['png_base64'] if data_graphic_rules[
            0] else '',
        "percent_default_match": data_graphic_rules[0]['rules_origin']['percent_default'] if data_graphic_rules[
            0] else '0%',
        "percent_tenant_match": data_graphic_rules[0]['rules_origin']['percent_tenant'] if data_graphic_rules[0] else '0%',
        "percent_channel_match": data_graphic_rules[0]['rules_origin']['percent_channel'] if data_graphic_rules[0] else '0%',
        "count_default_match": data_graphic_rules[0]['rules_origin']['count_default'] if data_graphic_rules[0] else '0',
        "count_tenant_match": data_graphic_rules[0]['rules_origin']['count_tenant'] if data_graphic_rules[0] else '0',
        "count_channel_match": data_graphic_rules[0]['rules_origin']['count_channel'] if data_graphic_rules[0] else '0',

        "top_10_graphic_match_rules_severity": data_graphic_rules[0]['rules_severity']['png_base64'] if
        data_graphic_rules[0] else None,
        "percent_high_match": data_graphic_rules[0]['rules_severity']['percent_high'] if data_graphic_rules[
            0] else '0%',
        "percent_critical_match": data_graphic_rules[0]['rules_severity']['percent_critical'] if data_graphic_rules[
            0] else '0%',
        "percent_medium_match": data_graphic_rules[0]['rules_severity']['percent_medium'] if data_graphic_rules[
            0] else '0%',
        "percent_info_match": data_graphic_rules[0]['rules_severity']['percent_info'] if data_graphic_rules[
            0] else '0%',
        "percent_low_match": data_graphic_rules[0]['rules_severity']['percent_low'] if data_graphic_rules[0] else '0%',

        "count_high_match": data_graphic_rules[0]['rules_severity']['count_high'] if data_graphic_rules[0] else '0',
        "count_critical_match": data_graphic_rules[0]['rules_severity']['count_critical'] if data_graphic_rules[
            0] else '0',
        "count_medium_match": data_graphic_rules[0]['rules_severity']['count_medium'] if data_graphic_rules[0] else '0',
        "count_info_match": data_graphic_rules[0]['rules_severity']['count_info'] if data_graphic_rules[0] else '0',
        "count_low_match": data_graphic_rules[0]['rules_severity']['count_low'] if data_graphic_rules[0] else '0',

        "top_10_table_threshold": data_table_rules[2]['threshold'] if data_table_rules[2] else '',
        "top_10_graphic_threshold_rules_origin": data_graphic_rules[1]['rules_origin']['png_base64'] if
        data_graphic_rules[
            1] else None,
        "percent_default_threshold": data_graphic_rules[1]['rules_origin']['percent_default'] if data_graphic_rules[
            1] else '0%',
        "percent_tenant_threshold": data_graphic_rules[1]['rules_origin']['percent_tenant'] if data_graphic_rules[
            1] else '0%',
        "percent_channel_threshold": data_graphic_rules[1]['rules_origin']['percent_channel'] if data_graphic_rules[
            1] else '0%',
        "count_default_threshold": data_graphic_rules[1]['rules_origin']['count_default'] if data_graphic_rules[
            1] else '0',
        "count_tenant_threshold": data_graphic_rules[1]['rules_origin']['count_tenant'] if data_graphic_rules[1] else '0',
        "count_channel_threshold": data_graphic_rules[1]['rules_origin']['count_channel'] if data_graphic_rules[
            1] else '0',
        "top_10_graphic_threshold_rules_severity": data_graphic_rules[1]['rules_severity']['png_base64'] if
        data_graphic_rules[1] else None,
        "percent_high_threshold": data_graphic_rules[1]['rules_severity']['percent_high'] if data_graphic_rules[
            1] else '0%',
        "percent_critical_threshold": data_graphic_rules[1]['rules_severity']['percent_critical'] if data_graphic_rules[
            1] else '0%',
        "percent_medium_threshold": data_graphic_rules[1]['rules_severity']['percent_medium'] if data_graphic_rules[
            1] else '0%',
        "percent_info_threshold": data_graphic_rules[1]['rules_severity']['percent_info'] if data_graphic_rules[
            1] else '0%',
        "percent_low_threshold": data_graphic_rules[1]['rules_severity']['percent_low'] if data_graphic_rules[
            1] else '0%',

        "count_high_threshold": data_graphic_rules[1]['rules_severity']['count_high'] if data_graphic_rules[1] else '0',
        "count_critical_threshold": data_graphic_rules[1]['rules_severity']['count_critical'] if data_graphic_rules[
            1] else '0',
        "count_medium_threshold": data_graphic_rules[1]['rules_severity']['count_medium'] if data_graphic_rules[
            1] else '0',
        "count_info_threshold": data_graphic_rules[1]['rules_severity']['count_info'] if data_graphic_rules[1] else '0',
        "count_low_threshold": data_graphic_rules[1]['rules_severity']['count_low'] if data_graphic_rules[1] else '0',

        "top_10_table_correlated": data_table_rules[3]['correlated'] if data_table_rules[3] else '',
        "top_10_graphic_correlated_rules_severity": data_graphic_rules[2]['rules_severity']['png_base64'] if
        data_graphic_rules[2] else None,
        "percent_high_correlated": data_graphic_rules[2]['rules_severity']['percent_high'] if data_graphic_rules[
            2] else '0%',
        "percent_critical_correlated": data_graphic_rules[2]['rules_severity']['percent_critical'] if
        data_graphic_rules[2] else '0%',
        "percent_medium_correlated": data_graphic_rules[2]['rules_severity']['percent_medium'] if data_graphic_rules[
            2] else '0%',
        "percent_info_correlated": data_graphic_rules[2]['rules_severity']['percent_info'] if data_graphic_rules[
            2] else '0%',
        "percent_low_correlated": data_graphic_rules[2]['rules_severity']['percent_low'] if data_graphic_rules[
            2] else '0%',

        "count_high_correlated": data_graphic_rules[2]['rules_severity']['count_high'] if data_graphic_rules[
            2] else '0',
        "count_critical_correlated": data_graphic_rules[2]['rules_severity']['count_critical'] if data_graphic_rules[
            2] else '0',
        "count_medium_correlated": data_graphic_rules[2]['rules_severity']['count_medium'] if data_graphic_rules[
            2] else '0',
        "count_info_correlated": data_graphic_rules[2]['rules_severity']['count_info'] if data_graphic_rules[
            2] else '0',
        "count_low_correlated": data_graphic_rules[2]['rules_severity']['count_low'] if data_graphic_rules[2] else '0',

        "top_10_graphic_correlated_rules_origin": data_graphic_rules[2]['rules_origin']['png_base64'] if data_graphic_rules[
            2] else '',
        "percent_default_correlated": data_graphic_rules[2]['rules_origin']['percent_default'] if data_graphic_rules[
            2] else '0%',
        "percent_tenant_correlated": data_graphic_rules[2]['rules_origin']['percent_tenant'] if data_graphic_rules[
            2] else '0%',
        "count_channel_correlated": data_graphic_rules[2]['rules_origin']['percent_channel'] if data_graphic_rules[
            2] else '0%',
        "count_default_correlated": data_graphic_rules[2]['rules_origin']['count_default'] if data_graphic_rules[
            2] else '0',
        "count_tenant_correlated": data_graphic_rules[2]['rules_origin']['count_tenant'] if data_graphic_rules[2] else '0',
        "count_channel_correlated": data_graphic_rules[2]['rules_origin']['count_channel'] if data_graphic_rules[2] else '0',
        "top_10_table_advanced": data_table_rules[4]['_advanced'] if data_table_rules[4] else '',
        "top_10_graphic_advanced_rules_severity": data_graphic_rules[3]['rules_severity']['png_base64'] if
        data_graphic_rules[3] else None,
        "percent_high_advanced": data_graphic_rules[3]['rules_severity']['percent_high'] if data_graphic_rules[
            3] else '0%',
        "percent_critical_advanced": data_graphic_rules[3]['rules_severity']['percent_critical'] if data_graphic_rules[
            3] else '0%',
        "percent_medium_advanced": data_graphic_rules[3]['rules_severity']['percent_medium'] if data_graphic_rules[
            3] else '0%',
        "percent_info_advanced": data_graphic_rules[3]['rules_severity']['percent_info'] if data_graphic_rules[
            3] else '0%',
        "percent_low_advanced": data_graphic_rules[3]['rules_severity']['percent_low'] if data_graphic_rules[
            3] else '0%',

        "count_high_advanced": data_graphic_rules[3]['rules_severity']['count_high'] if data_graphic_rules[3] else '0',
        "count_critical_advanced": data_graphic_rules[3]['rules_severity']['count_critical'] if data_graphic_rules[
            3] else '0',
        "count_medium_advanced": data_graphic_rules[3]['rules_severity']['count_medium'] if data_graphic_rules[
            3] else '0',
        "count_info_advanced": data_graphic_rules[3]['rules_severity']['count_info'] if data_graphic_rules[3] else '0',
        "count_low_advanced": data_graphic_rules[3]['rules_severity']['count_low'] if data_graphic_rules[3] else '0',

        "top_10_graphic_advanced_rules_origin": data_graphic_rules[3]['rules_origin']['png_base64'] if
        data_graphic_rules[3] else '',
        "percent_default_advanced": data_graphic_rules[3]['rules_origin']['percent_default'] if data_graphic_rules[
            3] else '0%',
        "percent_tenant_advanced": data_graphic_rules[3]['rules_origin']['percent_tenant'] if data_graphic_rules[
            3] else '0%',
        "percent_channel_advanced": data_graphic_rules[3]['rules_origin']['percent_channel'] if data_graphic_rules[
            3] else '0%',
        "count_default_advanced": data_graphic_rules[3]['rules_origin']['count_default'] if data_graphic_rules[
            3] else '0',
        "count_tenant_advanced": data_graphic_rules[3]['rules_origin']['count_tenant'] if data_graphic_rules[3] else '0',
        "count_channel_advanced": data_graphic_rules[3]['rules_origin']['count_channel'] if data_graphic_rules[3] else '0',

        "icon_default": __get_icons_rules_by_origin("Default"),
        "icon_tenant": __get_icons_rules_by_origin("Tenant"),
        "icon_channel": __get_icons_rules_by_origin("Channel"),
        "icon_critical": __get_icons_rules_by_severity("Critical"),
        "icon_high": __get_icons_rules_by_severity("High"),
        "icon_medium": __get_icons_rules_by_severity("Medium"),
        "icon_low": __get_icons_rules_by_severity("Low"),
        "icon_info": __get_icons_rules_by_severity("Info"),
        "start_date": start_date,
        "end_date": end_date,

        "hide_general": 'hide' if not data_table_rules[0] else '',
        "hide_match": 'hide' if not data_table_rules[1] else '',
        "hide_threshold": 'hide' if not data_table_rules[2] else '',
        "hide_correlated": 'hide' if not data_table_rules[3] else '',
        "hide_advanced": 'hide' if not data_table_rules[4] else '',

        "not_rules_general": '<p> There were no general rules in the designated time range. </p>' if not
        data_table_rules[0] else '',
        "not_rules_match": '<p> There were no match rules in the designated time range. </p>' if not data_table_rules[
            1] else '',
        "not_rules_threshold": '<p> There were no threshold rules in the designated time range. </p>' if not
        data_table_rules[2] else '',
        "not_rules_correlated": '<p> There were no correlated rules in the designated time range. </p>' if not
        data_table_rules[3] else '',
        "not_rules_advanced": '<p> There were no advanced rules in the designated time range. </p>' if not
        data_table_rules[4] else ''
    }

    html = html.render(template_vars)
    html = HTML(string=html)

    return html


async def __create_table_rules(key, value):
    resolver_response = ''

    map_keys = {
        'general': __build_table_general,
        'match': __build_table_match,
        'threshold': __build_table_threshold,
        'correlated': __build_table_correlated,
        '_advanced': __build_table_advanced,
        None: ""
    }
    if len(value) > 0:
        resolver: Callable = map_keys.get(key)
        resolver_response = await resolver(value)

    return resolver_response


async def __build_table_general(value):
    count = 1
    data_table_general = ''

    for general_value in value:
        line_general = '<tr>'
        line_general += '<td>' + str(count) + '</td>'
        line_general += '<td>' + str(general_value[0]) + '</td>'
        line_general += '<td>' + general_value[1] + '</td>'
        line_general += '<td> <div class="boderSeverity"> <span>' + general_value[2] + '</span></div></td>'
        line_general += '<td>' + str(general_value[3]) + '</td>'
        line_general += '</tr>'

        data_table_general += line_general
        count = count + 1

    return {
        'general': data_table_general
    }


async def __build_table_match(value):
    count = 1
    data_table_match = ''

    for match_value in value:
        icon_origin = __get_icons_rules_by_origin(rule_icon=str(match_value[4]))
        icon_severity = __get_icons_rules_by_severity(rule_icon=str(match_value[3]))

        line_match = '<tr>'
        line_match += '<td>' + str(count) + '</td>'
        line_match += '<td> <span class="icon"> <img src="data:image/png;base64,' + icon_origin + '"></span> </td>'
        line_match += '<td>' + str(match_value[0]) + '</td>'
        line_match += '<td>' + str(match_value[1]) + '</td>'
        line_match += '<td> <span class="icon"> <img src="data:image/png;base64,' + icon_severity + '"></span> </td>'
        line_match += '<td>' + str(match_value[2]) + '</td>'
        line_match += '</tr>'

        data_table_match += line_match
        count = count + 1

    return {
        'match': data_table_match
    }


async def __build_table_threshold(value):
    count = 1
    data_table_threshold = ''

    for threshold_value in value:
        icon_origin = __get_icons_rules_by_origin(rule_icon=str(threshold_value[4]))
        icon_severity = __get_icons_rules_by_severity(rule_icon=str(threshold_value[3]))

        line_threshold = '<tr>'
        line_threshold += '<td>' + str(count) + '</td>'
        line_threshold += '<td> <span class="icon"> <img src="data:image/png;base64,' + icon_origin + '"></span> </td>'
        line_threshold += '<td>' + str(threshold_value[0]) + '</td>'
        line_threshold += '<td>' + str(threshold_value[1]) + '</td>'
        line_threshold += '<td> <span class="icon"> <img src="data:image/png;base64,' + icon_severity + '"></span> </td>'
        line_threshold += '<td>' + str(threshold_value[2]) + '</td>'
        line_threshold += '</tr>'

        data_table_threshold += line_threshold
        count = count + 1

    return {
        'threshold': data_table_threshold
    }


async def __build_table_correlated(value):
    count = 1
    data_table_correlated = ''

    for correlated_value in value:
        icon_origin = __get_icons_rules_by_origin(rule_icon=str(correlated_value[4]))
        icon_severity = __get_icons_rules_by_severity(rule_icon=str(correlated_value[3]))

        line_correlated = '<tr>'
        line_correlated += '<td>' + str(count) + '</td>'
        line_correlated += '<td> <span class="icon"> <img src="data:image/png;base64,' + icon_origin + '"></span> </td>'
        line_correlated += '<td>' + str(correlated_value[0]) + '</td>'
        line_correlated += '<td>' + str(correlated_value[1]) + '</td>'
        line_correlated += '<td> <span class="icon"> <img src="data:image/png;base64,' + icon_severity + '"></span> </td>'
        line_correlated += '<td>' + str(correlated_value[2]) + '</td>'
        line_correlated += '</tr>'

        data_table_correlated += line_correlated
        count = count + 1

    return {
        'correlated': data_table_correlated
    }


async def __build_table_advanced(value):
    count = 1
    data_table_advanced = ''

    for advanced_value in value:
        icon_origin = __get_icons_rules_by_origin(rule_icon=str(advanced_value[4]))
        icon_severity = __get_icons_rules_by_severity(rule_icon=str(advanced_value[3]))

        line_advanced = '<tr>'
        line_advanced += '<td>' + str(count) + '</td>'
        line_advanced += '<td> <span class="icon"> <img src="data:image/png;base64,' + icon_origin + '"></span> </td>'
        line_advanced += '<td>' + str(advanced_value[0]) + '</td>'
        line_advanced += '<td>' + str(advanced_value[1]) + '</td>'
        line_advanced += '<td> <span class="icon"> <img src="data:image/png;base64,' + icon_severity + '"></span> </td>'
        line_advanced += '<td>' + str(advanced_value[2]) + '</td>'
        line_advanced += '</tr>'

        data_table_advanced += line_advanced
        count = count + 1

    return {
        '_advanced': data_table_advanced
    }


def __get_icons_rules_by_origin(rule_icon: str):
    map_icons = {
        'Default': __get_icon_png_to_base64,
        'Tenant': __get_icon_png_to_base64,
        'Channel': __get_icon_png_to_base64,
        None: ""
    }

    resolver: Callable = map_icons.get(rule_icon)
    resolver_response = resolver(rule_icon)

    return resolver_response


def __get_icons_rules_by_severity(rule_icon: str):
    map_icons = {
        'Critical': __get_icon_png_to_base64,
        'High': __get_icon_png_to_base64,
        'Medium': __get_icon_png_to_base64,
        'Low': __get_icon_png_to_base64,
        'Info': __get_icon_png_to_base64,
        None: ""
    }

    resolver: Callable = map_icons.get(rule_icon)
    resolver_response = resolver(rule_icon)

    return resolver_response


def __get_icon_png_to_base64(name_icon):
    path_icon = "domain/templates/top_10_rules_report/imgs/" + name_icon.lower() + ".png"
    user_png = Image.open(path_icon)
    output = io.BytesIO()
    user_png.save(output, format="png")
    image_png = base64.b64encode(output.getvalue())

    return image_png.decode('utf-8')


async def __create_graphic_rules(key, value):
    res_rules_origin = defaultdict(list)

    if len(value) > 0:
        result_graphic_rules = await __build_graphic_rules_by_origin(key, value, res_rules_origin)
        graphic_rules_severity = await __build_graphic_rules_by_severity(key, value, res_rules_origin)

        return {
            'rules_origin': result_graphic_rules,
            'rules_severity': graphic_rules_severity
        }


async def __build_graphic_rules_by_origin(key, value, res_rules_origin):
    count = 0
    png_base64 = None
    percent_default = None
    percent_tenant = None
    freq_tenant = None
    freq_default = None
    freq_channel = None

    if len(value) > 0:
        for rule_value in value:
            res_rules_origin[count] = rule_value[4]
            count = count + 1

        list_rules_origin = list(res_rules_origin.values())

        freq_default = list_rules_origin.count('Default')
        freq_tenant = list_rules_origin.count('Tenant')
        freq_channel = list_rules_origin.count('Channel')

        percent_default = round(((freq_default * 100) / len(value)), None)
        percent_tenant = round(((freq_tenant * 100) / len(value)), None)
        percent_channel = round(((freq_channel * 100) / len(value)), None)

        colors_background = ['rgba(249, 234, 251, 1)', 'rgba(242, 236, 254, 1)', 'rgba(218, 236, 235, 1)']  # purple, lilac, blue
        colors_line = ['rgba(192, 38, 211, 1)', 'rgba(124, 58, 237, 1)', 'rgba(0, 197, 211, 1)']
        labels = ['Default', 'Tenant', 'Channel']
        freq_origin = [freq_default, freq_tenant, freq_channel]

        for index, value in enumerate(freq_origin):
            if value == 0:
                colors_background.pop(index)
                colors_line.pop(index)
                freq_origin.pop(index)

        fig2 = go.Figure(
            data=[go.Pie(rotation=90, direction='clockwise', sort=False, labels=labels, values=freq_origin, hole=.3)],
            layout={'showlegend': False, 'paper_bgcolor': 'rgba(0,0,0,0)', 'width': 250, 'height': 250,
                    'margin': dict(t=1, b=1, l=1, r=1)})
        fig2.update_traces(textinfo='none',
                           marker=dict(colors=colors_background, line=dict(color=colors_line, width=2)))
        fig2.show()

        png_bytes = fig2.to_image(format="png")
        png_base64 = base64.b64encode(png_bytes).decode('ascii')

        default = str(percent_default) + '%'
        tenant = str(percent_tenant) + '%'
        channel = str(percent_channel) + '%'

    return {
        'key': key,
        'png_base64': png_base64 if png_base64 else '',
        'percent_default': default if percent_default else '0%',
        'percent_tenant': tenant if percent_tenant else '0%',
        'percent_channel': channel if percent_channel else '0%',
        'count_default': freq_default if freq_default else '0',
        'count_tenant': freq_tenant if freq_tenant else '0',
        'count_channel': freq_channel if freq_channel else '0'
    }


async def __build_graphic_rules_by_severity(key, value, res_rules_severity):
    count = 0
    png_base64 = None
    percent_high = None
    percent_critical = None
    percent_medium = None
    percent_info = None
    percent_low = None
    freq_critical = None
    freq_high = None
    freq_medium = None
    freq_low = None
    freq_info = None

    if len(value) > 0:
        for rule_value in value:
            res_rules_severity[count] = rule_value[3]
            count = count + 1

        list_rules_severity = list(res_rules_severity.values())

        freq_critical = list_rules_severity.count('Critical')
        freq_high = list_rules_severity.count('High')
        freq_medium = list_rules_severity.count('Medium')
        freq_low = list_rules_severity.count('Low')
        freq_info = list_rules_severity.count('Info')

        percent_critical = round(((freq_critical * 100) / len(value)), None)
        percent_high = round(((freq_high * 100) / len(value)), None)
        percent_medium = round(((freq_medium * 100) / len(value)), None)
        percent_low = round(((freq_low * 100) / len(value)), None)
        percent_info = round(((freq_info * 100) / len(value)), None)

        colors_background = ['rgb(253, 236, 236)', 'rgb(255, 247, 237)', 'rgb(255, 251, 235)', 'rgb(231, 248, 242)',
                             'rgb(235, 243, 254)']
        colors_line = ['rgb(239, 68, 68)', 'rgb(251, 146, 60)', 'rgb(251, 191, 36)', 'rgb(5, 150, 105)',
                       'rgb(59, 130, 246)']
        labels = ['Critical', 'High', 'Medium', 'Low', 'Info']
        freq_severity = [freq_critical, freq_high, freq_medium, freq_low, freq_info]
        colors_line_ = []
        colors_background_ = []
        freq_severity_ = []

        for index, value in enumerate(freq_severity):
            if value >= 1:
                freq_severity_.append(value)
                colors_background_.append(colors_background[index])
                colors_line_.append(colors_line[index])

        fig3 = go.Figure(
            data=[
                go.Pie(rotation=180, direction='clockwise', sort=False, labels=labels, values=freq_severity_, hole=.3)],
            layout={'showlegend': False, 'paper_bgcolor': 'rgba(0,0,0,0)', 'width': 250, 'height': 250,
                    'margin': dict(t=1, b=1, l=1, r=1)})
        fig3.update_traces(textinfo='none',
                           marker=dict(colors=colors_background_, line=dict(color=colors_line_, width=2)))
        fig3.show()

        png_bytes = fig3.to_image(format="png")
        png_base64 = base64.b64encode(png_bytes).decode('ascii')

        high = str(percent_high) + '%'
        critical = str(percent_critical) + '%'
        medium = str(percent_medium) + '%'
        info = str(percent_info) + '%'
        low = str(percent_low) + '%'

    return {
        'key': key,
        'png_base64': png_base64 if png_base64 else '',
        'percent_high': high if percent_high else '0%',
        'percent_critical': critical if percent_critical else '0%',
        'percent_medium': medium if percent_medium else '0%',
        'percent_info': info if percent_info else '0%',
        'percent_low': low if percent_low else '0%',
        'count_critical': freq_critical if freq_critical else '0',
        'count_high': freq_high if freq_high else '0',
        'count_medium': freq_medium if freq_medium else '0',
        'count_low': freq_low if freq_low else '0',
        'count_info': freq_info if freq_info else '0'
    }
