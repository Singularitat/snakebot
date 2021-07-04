# Taken from https://github.com/dateutil/dateutil/blob/master/dateutil/relativedelta.py
# https://github.com/dateutil/dateutil/blob/master/LICENSE

import datetime
import calendar

import operator
from math import copysign


class weekday:
    __slots__ = ["weekday", "n"]

    def __init__(self, weekday, n=None):
        self.weekday = weekday
        self.n = n

    def __call__(self, n):
        if n == self.n:
            return self
        return self.__class__(self.weekday, n)

    def __eq__(self, other):
        try:
            if self.weekday != other.weekday or self.n != other.n:
                return False
        except AttributeError:
            return False
        return True

    def __hash__(self):
        return hash(
            (
                self.weekday,
                self.n,
            )
        )

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        s = ("MO", "TU", "WE", "TH", "FR", "SA", "SU")[self.weekday]
        if not self.n:
            return s
        return "%s(%+d)" % (s, self.n)


MO, TU, WE, TH, FR, SA, SU = weekdays = tuple(weekday(x) for x in range(7))

__all__ = ["relativedelta", "MO", "TU", "WE", "TH", "FR", "SA", "SU"]


class relativedelta:
    def __init__(
        self,
        dt1=None,
        dt2=None,
    ):
        self.years = 0
        self.months = 0
        self.days = 0
        self.leapdays = 0
        self.hours = 0
        self.minutes = 0
        self.seconds = 0
        self.microseconds = 0
        self.year = None
        self.month = None
        self.day = None
        self.weekday = None
        self.hour = None
        self.minute = None
        self.second = None
        self.microsecond = None
        self._has_time = 0

        months = (dt1.year - dt2.year) * 12 + (dt1.month - dt2.month)
        self._set_months(months)

        dtm = self.__radd__(dt2)

        if dt1 < dt2:
            compare = operator.gt
            increment = 1
        else:
            compare = operator.lt
            increment = -1

        while compare(dt1, dtm):
            months += increment
            self._set_months(months)
            dtm = self.__radd__(dt2)

        delta = dt1 - dtm
        self.seconds = delta.seconds + delta.days * 86400
        self.microseconds = delta.microseconds

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

        if (
            self.hours
            or self.minutes
            or self.seconds
            or self.microseconds
            or self.hour is not None
            or self.minute is not None
            or self.second is not None
            or self.microsecond is not None
        ):
            self._has_time = 1
        else:
            self._has_time = 0

    @property
    def weeks(self):
        return int(self.days / 7.0)

    @weeks.setter
    def weeks(self, value):
        self.days = self.days - (self.weeks * 7) + value * 7

    def _set_months(self, months):
        self.months = months
        if abs(self.months) > 11:
            s = _sign(self.months)
            div, mod = divmod(self.months * s, 12)
            self.months = mod * s
            self.years = div * s
        else:
            self.years = 0

    def __add__(self, other):
        year = (self.year or other.year) + self.years
        month = self.month or other.month

        if self.months:
            if not 1 <= abs(self.months) <= 12:
                raise ValueError
            month += self.months
            if month > 12:
                year += 1
                month -= 12
            elif month < 1:
                year -= 1
                month += 12

        day = min(calendar.monthrange(year, month)[1], self.day or other.day)
        repl = {"year": year, "month": month, "day": day}

        for attr in ["hour", "minute", "second", "microsecond"]:
            value = getattr(self, attr)
            if value is not None:
                repl[attr] = value

        days = self.days

        if self.leapdays and month > 2 and calendar.isleap(year):
            days += self.leapdays

        ret = other.replace(**repl) + datetime.timedelta(
            days=days,
            hours=self.hours,
            minutes=self.minutes,
            seconds=self.seconds,
            microseconds=self.microseconds,
        )

        if self.weekday:
            weekday, nth = self.weekday.weekday, self.weekday.n or 1
            jumpdays = (abs(nth) - 1) * 7
            if nth > 0:
                jumpdays += (7 - ret.weekday() + weekday) % 7
            else:
                jumpdays += (ret.weekday() - weekday) % 7
                jumpdays *= -1
            ret += datetime.timedelta(days=jumpdays)
        return ret

    def __radd__(self, other):
        return self.__add__(other)

    def __bool__(self):
        return not (
            not self.years
            and not self.months
            and not self.days
            and not self.hours
            and not self.minutes
            and not self.seconds
            and not self.microseconds
            and not self.leapdays
            and self.year is None
            and self.month is None
            and self.day is None
            and self.weekday is None
            and self.hour is None
            and self.minute is None
            and self.second is None
            and self.microsecond is None
        )

    def __mul__(self, other):
        try:
            f = float(other)
        except TypeError:
            return NotImplemented

        return self.__class__(
            years=int(self.years * f),
            months=int(self.months * f),
            days=int(self.days * f),
            hours=int(self.hours * f),
            minutes=int(self.minutes * f),
            seconds=int(self.seconds * f),
            microseconds=int(self.microseconds * f),
            leapdays=self.leapdays,
            year=self.year,
            month=self.month,
            day=self.day,
            weekday=self.weekday,
            hour=self.hour,
            minute=self.minute,
            second=self.second,
            microsecond=self.microsecond,
        )

    __rmul__ = __mul__

    def __div__(self, other):
        try:
            reciprocal = 1 / float(other)
        except TypeError:
            return NotImplemented

        return self.__mul__(reciprocal)

    __truediv__ = __div__


def _sign(x):
    return int(copysign(1, x))


def time_since(past_time):
    """Get a datetime object or a int() Epoch timestamp and return a pretty time string."""
    now = datetime.datetime.utcnow()

    if isinstance(past_time, int):
        diff = relativedelta(now, datetime.fromtimestamp(past_time))
    else:
        diff = relativedelta(now, past_time)

    years = diff.years
    months = diff.months
    days = diff.days
    hours = diff.hours
    minutes = diff.minutes
    seconds = diff.seconds

    def fmt_time(amount: int, unit: str):
        return f"{amount} {unit}{'s' if amount else ''}"

    if not days and not months and not years:
        h, m, s = "", "", ""
        if hours:
            h = f"{fmt_time(hours, 'hour')} {'and' if not seconds else ''}"

        if minutes:
            m = f"{fmt_time(minutes, 'minute')} {'and' if hours else ''} "

        if seconds:
            s = f"{seconds} second{'s' if seconds > 1 else ''}"
        return f"{h}{m}{s}"

    y, m, d = "", "", ""

    if years:
        y = f"{fmt_time(years, 'year')} {'and' if not days else ''} "

    if months:
        m = f"{fmt_time(months, 'month')} {'and' if days else ''} "

    if days:
        d = f"{days} day{'s' if days > 1 else ''}"

    return f"{y}{m}{d}"
