import sys
sys.path.append("..")

from turing_models.products.equity.equity_cliquet_option import TuringEquityCliquetOption
from turing_models.models.model_black_scholes import TuringModelBlackScholes
from turing_models.market.curves.discount_curve_flat import TuringDiscountCurveFlat
from turing_models.utilities.frequency import TuringFrequencyTypes
from turing_models.utilities.turing_date import TuringDate
from turing_models.utilities.global_types import TuringOptionTypes

from TuringTestCases import TuringTestCases, globalTestCaseMode
testCases = TuringTestCases(__file__, globalTestCaseMode)

###############################################################################


def test_FinEquityCliquetOption():

    startDate = TuringDate(1, 1, 2014)
    finalExpiryDate = TuringDate(1, 1, 2017)
    freqType = TuringFrequencyTypes.QUARTERLY
    optionType = TuringOptionTypes.EUROPEAN_CALL

    cliquetOption = TuringEquityCliquetOption(startDate,
                                              finalExpiryDate,
                                              optionType,
                                              freqType)

    valueDate = TuringDate(1, 1, 2015)
    stockPrice = 100.0
    volatility = 0.20
    interestRate = 0.05
    dividendYield = 0.02
    model = TuringModelBlackScholes(volatility)
    discountCurve = TuringDiscountCurveFlat(valueDate, interestRate)
    dividendCurve = TuringDiscountCurveFlat(valueDate, dividendYield)

    v = cliquetOption.value(valueDate,
                            stockPrice,
                            discountCurve,
                            dividendCurve,
                            model)

    testCases.header("LABEL", "VALUE")
    testCases.print("Turing_models", v)

###############################################################################


test_FinEquityCliquetOption()
testCases.compareTestCases()
