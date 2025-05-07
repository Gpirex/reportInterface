from pytz import timezone


def formate_date(data, timezone_set, format_return):
    return_date = data
    return_date = return_date.astimezone(timezone(timezone_set))
    return_date = return_date.strftime(format_return)

    return return_date
