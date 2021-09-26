from turing_models.utilities.calendar import TuringCalendar, TuringCalendarTypes
from turing_models.utilities.turing_date import TuringDate


ib_calendar = TuringCalendar(TuringCalendarTypes.CHINA_IB)
print(ib_calendar.isBusinessDay(TuringDate(2021, 9, 27)))
