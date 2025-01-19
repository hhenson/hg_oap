"""
The following items are important to deal with when implementing LME Futures:
* LME Trading Calendar
* LME Rolling Rules


"""
from datetime import date, timedelta

import holidays

from hg_oap.dates import HolidayCalendar, DGen, Calendar
from hg_oap.utils import is_op, lazy


class LmeTradingHolidayCalendar(HolidayCalendar):
    def __init__(self):
        super().__init__(holidays=frozenset(
            holidays.country_holidays(country="GB", years=[1990 + i for i in range(date.today().year - 1990 + 10)]),
        ))
        # Get 10 years of UK holidays plus time from 1990
        # For now we just setup the calendar using the UK holidays in the holidays package.


class LmeRollDGen(DGen):

    def __init__(self, gen, calendar=None):
        self.gen = gen
        self.calendar = LmeTradingHolidayCalendar() if calendar is None else calendar

    def cadence(self):
        return self.gen.cadence()

    def is_single_date_gen(self):
        return self.gen.is_single_date_gen()

    def __invoke__(
        self,
        start: date = date.min,
        end: date = date.max,
        after: date = date.min,
        before: date = date.max,
        calendar: Calendar = None,
        **kwargs,
    ):
        c = self.calendar or calendar
        assert c, "Business days calculation requires a calendar"
        yield from (
            self._roll(d)
            for d in self.gen.__invoke__log__(start, end, after, before, calendar, **kwargs)
        )

    def _roll(self, d: date):
        """
        From LME Trading Rules:
        If the current date is not a business day, the prompt date is the next business day, unless:
        * The current date is a Saturday and the preceding Friday is a business day.
        * The current date is Good Friday.
        * The current date is Christmas Day and Christmas Day is on a Tuesday, Wednesday, Thursday or Friday.
        * The current date is a day declared by the Exchange as not a business day.
        In these cases, the prompt date is the preceding business day. (Except in the last case where it is
        non-deterministic).
        However, these rules can be simplified into the following approach:
        * If the current date is not a business day, role forward one day, if that is not a business day, role back one day.
        * repeat until a business day is found.
        The last rule relates to the 3M contract; this says that if the roll results in the contract falling into the forth
        calendar month after the contract was made, then the roll should be to the last business day of the third month.
        """
        # TODO: Test this actually does what the rules stipulate
        count = 0
        while True:
            dt = d + timedelta(days=count)
            if self.calendar.is_business_day(dt) and dt.month == d.month:
                return dt
            else:
                dt = d - timedelta(days=count)
                if self.calendar.is_business_day(dt):
                    return dt
            count += 1

    def __repr__(self):
        return (
            f"roll_lme({self.gen})"
            if self.calendar is None
            else f"roll_lme({self.gen}, {self.calendar})"
        )

def roll_lme(x, calendar=None):
    if is_op(x) or is_op(calendar):
        return lazy(roll_lme)(x, calendar)
    else:
        return LmeRollDGen(x, calendar)
