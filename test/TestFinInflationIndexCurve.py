import sys
sys.path.append("..")

from turing_models.utilities.turing_date import TuringDate
from turing_models.products.inflation.inflation_index_curve import TuringInflationIndexCurve

from TuringTestCases import TuringTestCases, globalTestCaseMode
testCases = TuringTestCases(__file__, globalTestCaseMode)

##############################################################################

def test_FinInflationIndexCurve():

    # Create a curve from times and discount factors
    indexDates = [TuringDate(2008, 1, 15), TuringDate(2008, 4, 1), TuringDate(2008, 5, 1)]
    indexValues = [209.49645, 214.823, 216.632]
    lag = 3 # months

    curve = TuringInflationIndexCurve(indexDates, indexValues, lag)

    refDate = TuringDate(2008, 7, 22)

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
