###############################################################################
# Copyright (C) 2018, 2019, 2020 Dominic O'Kane
###############################################################################

import sys
sys.path.append("..")

from turingmodel.turingutils.turing_date import TuringDate
from turingmodel.products.inflation.turing_inflation_index_curve import TuringInflationIndexCurve

from TuringTestCases import TuringTestCases, globalTestCaseMode
testCases = TuringTestCases(__file__, globalTestCaseMode)

##############################################################################

def test_FinInflationIndexCurve():

    # Create a curve from times and discount factors
    indexDates = [TuringDate(15, 1, 2008), TuringDate(1, 4, 2008), TuringDate(1, 5, 2008)]
    indexValues = [209.49645, 214.823, 216.632]
    lag = 3 # months

    curve = TuringInflationIndexCurve(indexDates, indexValues, lag)

    refDate = TuringDate(22, 7, 2008)
    
    testCases.header("LABEL", "VALUE")

    value = curve.indexValue(refDate)
    value = curve.indexValue(refDate)
    value = curve.indexValue(refDate)
    value = curve.indexValue(refDate)

    testCases.print(refDate, value)

    indexRatio = curve.indexRatio(refDate)
    testCases.print(refDate, indexRatio)

#    print(curve)

###############################################################################


test_FinInflationIndexCurve()
testCases.compareTestCases()
