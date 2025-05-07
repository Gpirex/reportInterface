"""OpenSearch chart series."""
from db.opensearch import get_open_search_data
from domain.triggered_rules import get_fixed_intervals
from datetime import datetime


async def get_open_search_chart_series(start_date, end_date, url, session):
    """Opensearch chart series get info."""
    intervals = get_fixed_intervals(start_date, end_date)

    payload = {
        "size": 0,
        "query": {
            "bool": {
                "must": [
                    {
                        "range": {
                            "@timestamp": {
                                "gte": start_date.strftime(
                                    "%Y-%m-%dT%H:%M:%SZ"),
                                "lte": end_date.strftime("%Y-%m-%dT%H:%M:%SZ")
                            }
                        }
                    },
                    {
                        "query_string": {
                            "query": "*:*"
                        }
                    }
                ]
            }
        },
        "aggs": {
            "@timestamp": {
                "date_histogram": {
                    "field": "@timestamp",
                    "calendar_interval": f"{intervals[0]}"
                }
            }
        }
    }
    
    try:
        raw_doc_response = await get_open_search_data(payload, url, session)
        print('raw_doc_response', raw_doc_response)
    except Exception as e:
        return e

    try:
        buckets = raw_doc_response['aggregations']['@timestamp']['buckets']

        labels = list(map(lambda x: datetime.strptime(
                    x['key_as_string'],
                    "%Y-%m-%dT%H:%M:%S.000Z").strftime(
                    intervals[1]), buckets))

        data = list(map(lambda x: int(x['doc_count']), buckets))

        dataset = [{
            "label": f"Approximately {sum(data)} processed events",
            "fill": False,
            "backgroundColor": "#126098",
            "borderColor": "#126098",
            "pointStrokeColor": "#fff",
            "borderCapStyle": 'butt',
            "data": data,
        }]

        return labels, dataset

    except Exception:
        return None
