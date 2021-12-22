import calendar
import datetime
import re
from math import copysign

TIME_REGEX = re.compile(
    "(?:(?P<years>[0-9])(?:years?|y))?"
    "(?:(?P<months>[0-9]{1,2})(?:months?|mo))?"
    "(?:(?P<weeks>[0-9]{1,4})(?:weeks?|w))?"
    "(?:(?P<days>[0-9]{1,5})(?:days?|d))?"
    "(?:(?P<hours>[0-9]{1,5})(?:hours?|h))?"
    "(?:(?P<minutes>[0-9]{1,5})(?:minutes?|m))?"
    "(?:(?P<seconds>[0-9]{1,5})(?:seconds?|s))?",
    re.VERBOSE,
)


def parse_date(date: str) -> datetime.datetime:
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
            return datetime.datetime(year, month, day, tzinfo=datetime.timezone.utc)


def parse_time(time_string: str) -> datetime.datetime:
    match = TIME_REGEX.fullmatch(time_string.replace(" ", ""))

    if not match:
        return None

    data = {k: int(v) for k, v in match.groupdict(default=0).items()}
    return relativedelta(**data) + datetime.datetime.now(datetime.timezone.utc)


class relativedelta:
    def __init__(
        self,
        years=0,
        months=0,
        days=0,
        leapdays=0,
        weeks=0,
        hours=0,
        minutes=0,
        seconds=0,
        microseconds=0,
    ):
        self.years = years
        self.months = months
        self.days = days + weeks * 7
        self.leapdays = leapdays
        self.hours = hours
        self.minutes = minutes
        self.seconds = seconds
        self.microseconds = microseconds

        self._fix()

    def _fix(self):
        if abs(self.microseconds) > 999999:
            s = _sign(self.microseconds)
            div, mod = divmod(self.microseconds * s, 1000000)
            self.microseconds = mod * s
            self.seconds += div * s
        if abs(self.seconds) > 59:
            s = _sign(self.seconds)
            div, mod = divmod(self.seconds * s, 60)
            self.seconds = mod * s
            self.minutes += div * s
        if abs(self.minutes) > 59:
            s = _sign(self.minutes)
            div, mod = divmod(self.minutes * s, 60)
            self.minutes = mod * s
            self.hours += div * s
        if abs(self.hours) > 23:
            s = _sign(self.hours)
            div, mod = divmod(self.hours * s, 24)
            self.hours = mod * s
            self.days += div * s
        if abs(self.months) > 11:
            s = _sign(self.months)
            div, mod = divmod(self.months * s, 12)
            self.months = mod * s
            self.years += div * s

    def __add__(self, other):
        year = other.year + self.years
        month = other.month
        if self.months:
            assert 1 <= abs(self.months) <= 12
            month += self.months
            if month > 12:
                year += 1
                month -= 12
            elif month < 1:
                year -= 1
                month += 12
        day = min(calendar.monthrange(year, month)[1], other.day)
        days = self.days
        if self.leapdays and month > 2 and calendar.isleap(year):
            days += self.leapdays
        return other.replace(year=year, month=month, day=day) + datetime.timedelta(
            days=days,
            hours=self.hours,
            minutes=self.minutes,
            seconds=self.seconds,
            microseconds=self.microseconds,
        )


def _sign(x):
    return int(copysign(1, x))
