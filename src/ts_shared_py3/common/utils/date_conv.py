from datetime import datetime, timedelta, date

#
# from constants import ISO_8601_DATE_FORMAT

EPOCH = datetime(1970, 1, 1, 0, 0, 0)


# def message_to_date(msg):
#     raise UnicodeError
#     # return date(year=msg.year, month=msg.month, day=msg.day)


# def date_to_message(_date=None):
#     if _date is None:
#         _date = date.today()
#     # return DateMessage(day=_date.day, month=_date.month, year=_date.year)
#     return _date.strftime(ISO_8601_DATE_FORMAT)
#     # return DateMsgConverter.to_message(None, None, None, _date)


def dateTime_to_epoch(dt: date = None) -> int:
    """return all date time values as secs since 1970"""
    if dt is None:
        dt = datetime.now()
    elif isinstance(dt, date):
        dt = datetime.combine(dt, datetime.min.time())
    # print("dt: %s" % dt)
    # print("epoch: %s" % EPOCH)
    return (dt - EPOCH).total_seconds()


def date_from_epoch(flt: int) -> date:
    # print("flt == %s" % flt)
    return date.fromtimestamp(flt)


def date_to_epoch(dt: date = None) -> int:
    """return all date time values as secs since 1970"""
    if dt is None:
        dt = date.today()
    return (dt - EPOCH.date()).total_seconds()


def dateTime_from_epoch(flt: str) -> date:
    return datetime.fromtimestamp(flt)


def dateToShortString(dateObj: date) -> str:
    assert isinstance(dateObj, datetime) or isinstance(
        dateObj, date
    ), "Arg to xx was not Date/Time obj"
    return dateObj.strftime("%m/%d/%Y")


def overlappingDates(
    dateOneStart: date, dateOneEnd: date, dateTwoStart: date, dateTwoEnd: date
) -> tuple[date, date]:
    """calc dates of overlap between two sets of dates"""
    if dateOneEnd < dateTwoStart or dateTwoEnd < dateOneStart:
        return None, None
    latest_start = max(dateOneStart, dateTwoStart)
    earliest_end = min(dateOneEnd, dateTwoEnd)
    # print('latest_start={0} & earliest_end={1}'.format(latest_start, earliest_end) )

    # start should always be SMALLER than end
    # our phases dont discriminate to time so we cant discern
    # order of breakup and dating new person;  so same day is NOT currently treated as an incident
    if latest_start >= earliest_end:
        return None, None
    return latest_start, earliest_end


def calcOverlappingDays(
    dateOneStart: date, dateOneEnd: date, dateTwoStart: date, dateTwoEnd: date
) -> int:
    """calc # of days overlap between two sets of dates"""
    latest_start, earliest_end = overlappingDates(
        dateOneStart, dateOneEnd, dateTwoStart, dateTwoEnd
    )
    if latest_start is None:
        return 0
    overlap = (earliest_end - latest_start).days
    return abs(overlap)  # if overlap > 0 else 0


def dateByAddingDays(refDate: date, days: int = 1) -> date:
    return refDate + timedelta(days=days)


def roundTime(dt: date = None, roundTo: int = 60) -> date:
    """Round a datetime object to any time lapse in seconds
    dt : datetime.datetime object, default now.
    roundTo : Closest number of seconds to round to, default 1 minute.
    Author: Thierry Husson 2012 - Use it as you want but don't blame me.
    """
    if dt == None:
        dt = datetime.now()
    seconds: int = (dt.replace(tzinfo=None) - dt.min).seconds
    rounding: int = (seconds + roundTo / 2) / roundTo * roundTo
    return dt + timedelta(0, rounding - seconds, -dt.microsecond)


def lastDayOfMonth(any_day: date) -> date:
    next_month: date = any_day.replace(day=28) + timedelta(days=4)
    return next_month - timedelta(days=next_month.day)


def firstDayOfNextMonth(any_day: date) -> date:
    ldm: date = lastDayOfMonth(any_day)
    return ldm + timedelta(days=1)


if __name__ == "__main__":
    #
    dt = date.today()
    lastInMonth = lastDayOfMonth(dt)
    print("lastInMonth: {0}".format(lastInMonth))
