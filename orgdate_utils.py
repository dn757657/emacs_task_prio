import datetime

import orgparse.date


def orgdate_2_dt(dates):
    """ get datetime object from orgdate

     :return list of dates in datetime format
     """

    dates_dt = []

    if not isinstance(dates, list):
        dates = [dates]

    # pull date times objects out of orgdate objects from ancestral
    for date in dates:
        # start is preferred because it is soner (worst case) for scoring
        if date.start:
            dates_dt.append(ensure_datetime(date.start))
        elif date.end:
            dates_dt.append(ensure_datetime(date.end))

    return dates_dt


def ensure_datetime(date):
    if isinstance(date, datetime.date):
        date = datetime.datetime.combine(date, datetime.datetime.min.time())

    return date


def repeater_2_timedelta(repeater):
    """ convert orgdate repeater to timedelta

     only covering basic behavior for now, + (no ++, no .+) although perhaps in future may be required
     """
    tdelta = None

    sign = repeater[0]
    quan = repeater[1]
    if sign == '-':
        quan = -quan

    size = repeater[2]

    windows = {'h': 'hours',
               'd': 'days',
               'w': 'weeks',
               'm': 'months',
               'y': 'years'}

    delta_args = {}
    for key in windows.keys():
        if size == key:
            delta_args[windows[key]] = quan

    tdelta = datetime.timedelta(**delta_args)

    return tdelta


def push_repeated_2_present(orgdate, push_past=datetime.datetime.today()):
    """ adjust a repeated orgdate to the present (latest after today())
        - may need to adjust start and end?
     """

    tdelta = repeater_2_timedelta(orgdate._repeater)

    if orgdate.start:
        new_start = orgdate.start
        while new_start < push_past:
            new_start += tdelta
    else:
        new_start = orgdate.start

    if orgdate.end:
        new_end = orgdate.end
        while new_end < push_past:
            new_end += tdelta
    else:
        new_end = orgdate.end

    pushed = orgparse.date.OrgDate(start=new_start,
                                   end=new_end,
                                   active=orgdate._active,
                                   repeater=orgdate._repeater,
                                   warning=orgdate._warning)

    return pushed


def expand_repeated_2_window(orgdate, wmin, wmax):
    """ return list of orgdates in window if orgdate has repeater """

    if not orgdate._repeater:
        return False

    expanded = []
    tdelta = repeater_2_timedelta(orgdate._repeater)

    # first push orgdate into the present
    pushed_orgdate = push_repeated_2_present(orgdate, wmin)
    expanded.append(pushed_orgdate)

    if pushed_orgdate.end:
        loc = orgdate.end
    else:
        loc = pushed_orgdate.start

    while loc < wmax:  # use end to ensure dates stay in window
        if pushed_orgdate.start:
            pushed_start = pushed_orgdate.start + tdelta
        else:
            pushed_start = None
        if pushed_orgdate.end:
            pushed_end = pushed_orgdate.end + tdelta
        else:
            pushed_end = None
        pushed_orgdate = orgparse.date.OrgDate(start=pushed_start,
                                               end=pushed_end,
                                               active=orgdate._active,
                                               repeater=orgdate._repeater,
                                               warning=orgdate._warning)

        expanded.append(pushed_orgdate)

        if pushed_orgdate.end:
            loc = orgdate.end
        else:
            loc = pushed_orgdate.start

    # do not return final because while loop overshoots
    return expanded[:-1]
