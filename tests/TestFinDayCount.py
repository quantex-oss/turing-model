###############################################################################
# Copyright (C) 2018, 2019, 2020 Dominic O'Kane
###############################################################################

import sys
sys.path.append("..")

from financepy.finutils.turing_date import TuringDate
from financepy.finutils.turing_day_count import TuringDayCount, TuringDayCountTypes
from financepy.finutils.turing_frequency import TuringFrequencyTypes

from TuringTestCases import TuringTestCases, globalTestCaseMode
testCases = TuringTestCases(__file__, globalTestCaseMode)

##############################################################################

def test_FinDayCount():

    testCases.header("DAY_COUNT_METHOD", "START", "END", "ALPHA")

    finFreq = TuringFrequencyTypes.ANNUAL

    for dayCountMethod in TuringDayCountTypes:

        startDate = TuringDate(1, 1, 2019)
        nextDate = startDate
        numDays = 20
        dayCount = TuringDayCount(dayCountMethod)

        for _ in range(0, numDays):
            nextDate = nextDate.addDays(7)
            dcf = dayCount.yearFrac(startDate, nextDate, nextDate, finFreq)

            testCases.print(
                str(dayCountMethod),
                str(startDate),
                str(nextDate),
                dcf[0])


test_FinDayCount()
testCases.compareTestCases()
