import datetime


def ensure_datetime(date):
    if isinstance(date, datetime.date):
        date = datetime.datetime.combine(date, datetime.datetime.min.time())

    return date
