import re
import datetime
from dateutil.relativedelta import relativedelta


def get_matching_emote(guild, emote):
    """Finds an emoji based off its name."""
    emote_name = emote.split(":")[1]
    for emoji in guild.emojis:
        if emoji.name == emote_name:
            return emoji
    return emote_name


def _stringify_time_unit(value: int, unit: str) -> str:
    """Returns a string to represent a value and time unit, ensuring that it uses the right plural form of the unit.
    >>> _stringify_time_unit(1, "seconds")
    "1 second"
    >>> _stringify_time_unit(24, "hours")
    "24 hours"
    >>> _stringify_time_unit(0, "minutes")
    "less than a minute"
    """
    if unit == "seconds" and value == 0:
        return "0 seconds"
    if value == 1:
        return f"{value} {unit[:-1]}"
    if value == 0:
        return f"less than a {unit[:-1]}"
    return f"{value} {unit}"


def humanize_delta(
    delta: relativedelta, precision: str = "seconds", max_units: int = 6
) -> str:
    """Returns a human-readable version of the relativedelta.
    precision specifies the smallest unit of time to include (e.g. "seconds", "minutes").
    max_units specifies the maximum number of units of time to include (e.g. 1 may include days but not hours).
    """
    if max_units <= 0:
        raise ValueError("max_units must be positive")

    units = (
        ("years", delta.years),
        ("months", delta.months),
        ("days", delta.days),
        ("hours", delta.hours),
        ("minutes", delta.minutes),
        ("seconds", delta.seconds),
    )
    # Add the time units that are >0, but stop at accuracy or max_units.
    time_strings = []
    unit_count = 0
    for unit, value in units:
        if value:
            time_strings.append(_stringify_time_unit(value, unit))
            unit_count += 1

        if unit == precision or unit_count >= max_units:
            break

    # Add the 'and' between the last two units, if necessary
    if len(time_strings) > 1:
        time_strings[-1] = f"{time_strings[-2]} and {time_strings[-1]}"
        del time_strings[-2]

    # If nothing has been found, just make the value 0 precision, e.g. `0 days`.
    if not time_strings:
        humanized = _stringify_time_unit(0, precision)
    else:
        humanized = ", ".join(time_strings)

    return humanized


def time_since(
    past_datetime: datetime.datetime, precision: str = "seconds", max_units: int = 6
) -> str:
    """Takes a datetime and returns a human-readable string that describes how long ago that datetime was.
    precision specifies the smallest unit of time to include (e.g. "seconds", "minutes").
    max_units specifies the maximum number of units of time to include (e.g. 1 may include days but not hours).
    """
    now = datetime.datetime.utcnow()
    delta = abs(relativedelta(now, past_datetime))

    humanized = humanize_delta(delta, precision, max_units)

    return f"{humanized} ago"


def find_nth_occurrence(string: str, substring: str, n: int):
    """Return index of `n`th occurrence of `substring` in `string`, or None if not found."""
    index = 0
    for _ in range(n):
        index = string.find(substring, index + 1)
        if index == -1:
            return None
    return index


def remove_html_tags(text):
    """Removes html tags from a string."""
    clean = re.compile("<.*?>")
    return re.sub(clean, "", text)


def clean_non_letters(text):
    """Removes non-alphabet characters from a string."""
    clean = re.compile("[^a-zA-Z]")
    return re.sub(clean, "", text)


def clean_non_numbers(text):
    """Removes non-numeric characters from a string."""
    clean = re.compile(r"[^\d.]+")
    return re.sub(clean, "", text)
