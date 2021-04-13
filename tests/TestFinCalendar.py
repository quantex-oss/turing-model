###############################################################################
# Copyright (C) 2018, 2019, 2020 Dominic O'Kane
###############################################################################

import sys
sys.path.append("..")

from financepy.turingutils.turing_date import TuringDate
from financepy.turingutils.turing_date import setDateFormatType, TuringDateFormatTypes
from financepy.turingutils.turing_calendar import TuringCalendar, TuringCalendarTypes

from TuringTestCases import TuringTestCases, globalTestCaseMode
testCases = TuringTestCases(__file__, globalTestCaseMode)

###############################################################################


def test_FinCalendar():

    setDateFormatType(TuringDateFormatTypes.US_LONGEST)
    endDate = TuringDate(31, 12, 2030)

    for calendarType in TuringCalendarTypes:

        testCases.banner("================================")
        testCases.banner("================================")

        testCases.header("CALENDAR", "HOLIDAY")
        testCases.print("STARTING", calendarType)

        cal = TuringCalendar(calendarType)
        nextDate = TuringDate(31, 12, 2020)

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
