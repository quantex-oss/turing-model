###############################################################################
# Copyright (C) 2018, 2019, 2020 Dominic O'Kane
###############################################################################

import sys
sys.path.append("..")

from financepy.finutils.turing_date import TuringDate
from financepy.finutils.turing_schedule import TuringSchedule
from financepy.finutils.turing_frequency import TuringFrequencyTypes
from financepy.finutils.turing_calendar import TuringCalendarTypes
from financepy.finutils.turing_calendar import TuringBusDayAdjustTypes
from financepy.finutils.turing_calendar import TuringDateGenRuleTypes

from TuringTestCases import TuringTestCases, globalTestCaseMode
testCases = TuringTestCases(__file__, globalTestCaseMode)

###############################################################################


def test_FinDateAdjust():

    startDate = TuringDate(28, 2, 2008)
    endDate = TuringDate(28, 2, 2011)

    freqType = TuringFrequencyTypes.SEMI_ANNUAL
    calendarType = TuringCalendarTypes.NONE
    busDayAdjustType = TuringBusDayAdjustTypes.FOLLOWING
    dateGenRuleType = TuringDateGenRuleTypes.BACKWARD

    testCases.header("NO ADJUSTMENTS", "DATE")
    schedule = TuringSchedule(startDate,
                              endDate,
                              freqType,
                              calendarType,
                              busDayAdjustType,
                              dateGenRuleType)

    for dt in schedule._adjustedDates:
        testCases.print("Date:", dt)

    testCases.banner("")
    testCases.header("NO WEEKENDS AND FOLLOWING", "DATE")
    freqType = TuringFrequencyTypes.SEMI_ANNUAL
    calendarType = TuringCalendarTypes.WEEKEND
    busDayAdjustType = TuringBusDayAdjustTypes.FOLLOWING
    dateGenRuleType = TuringDateGenRuleTypes.BACKWARD

    schedule = TuringSchedule(startDate,
                              endDate,
                              freqType,
                              calendarType,
                              busDayAdjustType,
                              dateGenRuleType)

    for dt in schedule._adjustedDates:
        testCases.print("Date:", dt)

    testCases.banner("")
    testCases.header("NO WEEKENDS AND MODIFIED FOLLOWING", "DATE")
    freqType = TuringFrequencyTypes.SEMI_ANNUAL
    calendarType = TuringCalendarTypes.WEEKEND
    busDayAdjustType = TuringBusDayAdjustTypes.MODIFIED_FOLLOWING
    dateGenRuleType = TuringDateGenRuleTypes.BACKWARD

    schedule = TuringSchedule(startDate,
                              endDate,
                              freqType,
                              calendarType,
                              busDayAdjustType,
                              dateGenRuleType)

    for dt in schedule._adjustedDates:
        testCases.print("Date:", dt)

    testCases.banner("")
    testCases.header("NO WEEKENDS AND US HOLIDAYS AND MODIFIED FOLLOWING",
                     "DATE")
    freqType = TuringFrequencyTypes.SEMI_ANNUAL
    calendarType = TuringCalendarTypes.UNITED_STATES
    busDayAdjustType = TuringBusDayAdjustTypes.MODIFIED_FOLLOWING
    dateGenRuleType = TuringDateGenRuleTypes.BACKWARD

    startDate = TuringDate(4, 7, 2008)
    endDate = TuringDate(4, 7, 2011)

    schedule = TuringSchedule(startDate,
                              endDate,
                              freqType,
                              calendarType,
                              busDayAdjustType,
                              dateGenRuleType)

    for dt in schedule._adjustedDates:
        testCases.print("Date:", dt)

###############################################################################


test_FinDateAdjust()
testCases.compareTestCases()
