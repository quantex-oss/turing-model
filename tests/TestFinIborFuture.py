###############################################################################
# Copyright (C) 2018, 2019, 2020 Dominic O'Kane
###############################################################################

import sys
sys.path.append("..")

from turingmodel.products.rates.turing_ibor_future import FinIborFuture
from turingmodel.turingutils.turing_date import *

from TuringTestCases import TuringTestCases, globalTestCaseMode
testCases = TuringTestCases(__file__, globalTestCaseMode)

setDateFormatType(TuringDateFormatTypes.UK_LONG)

###############################################################################


def test_FinIborFuture():

    todayDate = TuringDate(5, 5, 2020)

    testCases.header("VALUES")

    for i in range(1, 12):
        fut = FinIborFuture(todayDate, i, "3M")
        testCases.print(fut)

        fra = fut.toFRA(0.020, 0.0)
        testCases.print(fra)

###############################################################################


test_FinIborFuture()
testCases.compareTestCases()
