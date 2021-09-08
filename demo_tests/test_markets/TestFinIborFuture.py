import sys
sys.path.append("..")

from turing_models.products.rates.ibor_future import TuringIborFuture
from turing_models.utilities.turing_date import *

from TuringTestCases import TuringTestCases, globalTestCaseMode
testCases = TuringTestCases(__file__, globalTestCaseMode)

setDateFormatType(TuringDateFormatTypes.UK_LONG)

###############################################################################


def test_FinIborFuture():

    todayDate = TuringDate(5, 5, 2020)

    testCases.header("VALUES")

    for i in range(1, 12):
        fut = TuringIborFuture(todayDate, i, "3M")
        testCases.print(fut)

        fra = fut.toFRA(0.020, 0.0)
        testCases.print(fra)

###############################################################################


test_FinIborFuture()
testCases.compareTestCases()
