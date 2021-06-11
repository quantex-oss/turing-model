import sys
sys.path.append("..")

from turing_models.utilities.turing_date import TuringDate
from turing_models.utilities.turing_date import setDateFormatType, TuringDateFormatTypes
from turing_models.utilities.calendar import TuringCalendar, TuringCalendarTypes

from TuringTestCases import TuringTestCases, globalTestCaseMode
testCases = TuringTestCases(__file__, globalTestCaseMode)

###############################################################################


def test_FinCalendar():

    setDateFormatType(TuringDateFormatTypes.US_LONGEST)
    endDate = TuringDate(2030, 12, 31)

    for calendarType in TuringCalendarTypes:

        testCases.banner("================================")
        testCases.banner("================================")

        testCases.header("CALENDAR", "HOLIDAY")
        testCases.print("STARTING", calendarType)

        cal = TuringCalendar(calendarType)
        nextDate = TuringDate(2020, 12, 31)

        while nextDate < endDate:
            nextDate = nextDate.addDays(1)

            if nextDate._d == 1 and nextDate._m == 1:
                testCases.banner("================================")
#                print("=========================")

            isHolidayDay = cal.isHoliday(nextDate)
            if isHolidayDay is True:
                testCases.print(cal, nextDate)
#                print(cal, nextDate)

    setDateFormatType(TuringDateFormatTypes.US_LONG)

###############################################################################


test_FinCalendar()
testCases.compareTestCases()
