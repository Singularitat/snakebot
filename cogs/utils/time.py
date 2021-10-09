from datetime import datetime, timezone


def parse_date(date):
    """Parses a date string.

    >>> parse_date("13-10-2020")
    datetime.datetime(2020, 10, 13, 0, 0)

    >>> parse_date("2020-10-13")
    datetime.datetime(2020, 10, 13, 0, 0)

    >>> parse_date("13.10.2020")
    datetime.datetime(2020, 10, 13, 0, 0)

    >>> parse_date("2020/10/13")
    datetime.datetime(2020, 10, 13, 0, 0)
    """
    for seperator in ("-", ".", "/"):
        if seperator in date:
            day, month, year = map(int, date.split(seperator))
            if day > year:
                day, year = year, day
            return datetime(year, month, day, tzinfo=timezone.utc)
