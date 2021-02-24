__author__ = 'ramses'
from dateutil import parser
from dateutil.relativedelta import relativedelta
import calendar

MONTHS = {
    1: 31, 2: 29, 3: 31, 4: 30, 5: 31, 6: 30,
    7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31
}


def get_days(init, end):
    thirdty_days_months_val = 0
    while init <= end:
        val = MONTHS[init]
        if val > 30:
            thirdty_days_months_val -= 1
        if val in [28, 29]:
            thirdty_days_months_val += 1
        init += 1
    return thirdty_days_months_val


def thirdty_days_months(start_month, end_month):
    d30 = 0
    if start_month > end_month:
        d30 = get_days(start_month, 12)
        d30 += get_days(1, end_month)
    else:
        d30 = get_days(start_month, end_month)
    return d30


def thirty_days_months2(date_start, date_end):
    date_start = parser.parse(date_start)
    date_end = parser.parse(date_end)
    days = 0
    while date_start < date_end:
        if date_start.month == date_end.month and date_start.year == date_end.year:
            break
        tuple_month = calendar.monthrange(date_start.year, date_start.month)
        if tuple_month[1] > 30:
            days += 1
        elif tuple_month[1] == 29:
            days -= 1
        elif tuple_month[1] == 28:
            days -= 2
        date_start += relativedelta(months=1)
    if date_end.day == calendar.monthrange(date_end.year, date_end.month)[1] and date_end.day > 30:
        days += 1
    return days

# def thirty_days_months2(date_start, date_end):
#     date_start = parser.parse(date_start)
#     date_end = parser.parse(date_end)
#     days = 0
#     if date_start.day < date_end.day:
#         days = -1
#     while date_start <= date_end:
#         dm = MONTHS[date_start.month]
#         if dm > 30:
#             days += 1
#         if dm < 30:
#             tuple_feb = calendar.monthrange(date_start.year, date_start.month)
#             if tuple_feb[1] == 28:
#                 days -= 2
#             else:
#                 days -= 1
#         date_start += relativedelta(months=1)
#     return days