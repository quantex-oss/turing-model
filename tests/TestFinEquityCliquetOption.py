###############################################################################
# Copyright (C) 2018, 2019, 2020 Dominic O'Kane
###############################################################################

import sys
sys.path.append("..")

from turing_models.products.equity.turing_equity_cliquet_option import TuringEquityCliquetOption
from turing_models.models.turing_model_black_scholes import TuringModelBlackScholes
from turing_models.market.curves.turing_discount_curve_flat import TuringDiscountCurveFlat
from turing_models.turingutils.turing_frequency import TuringFrequencyTypes
from turing_models.turingutils.turing_date import TuringDate
from turing_models.turingutils.turing_global_types import TuringOptionTypes

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
    testCases.print("FINANCEPY", v)

###############################################################################


test_FinEquityCliquetOption()
testCases.compareTestCases()
