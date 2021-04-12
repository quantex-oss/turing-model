###############################################################################
# Copyright (C) 2018, 2019, 2020 Dominic O'Kane
###############################################################################

import sys
sys.path.append("..")

from financepy.products.equity.turing_equity_cliquet_option import FinEquityCliquetOption
from financepy.models.turing_model_black_scholes import FinModelBlackScholes
from financepy.market.curves.turing_discount_curve_flat import FinDiscountCurveFlat
from financepy.finutils.turing_frequency import FinFrequencyTypes
from financepy.finutils.turing_date import FinDate
from financepy.finutils.turing_global_types import FinOptionTypes

from FinTestCases import FinTestCases, globalTestCaseMode
testCases = FinTestCases(__file__, globalTestCaseMode)

###############################################################################


def test_FinEquityCliquetOption():

    startDate = FinDate(1, 1, 2014)
    finalExpiryDate = FinDate(1, 1, 2017)
    freqType = FinFrequencyTypes.QUARTERLY
    optionType = FinOptionTypes.EUROPEAN_CALL

    cliquetOption = FinEquityCliquetOption(startDate,
                                           finalExpiryDate,
                                           optionType,
                                           freqType)

    valueDate = FinDate(1, 1, 2015)
    stockPrice = 100.0
    volatility = 0.20
    interestRate = 0.05
    dividendYield = 0.02
    model = FinModelBlackScholes(volatility)
    discountCurve = FinDiscountCurveFlat(valueDate, interestRate)
    dividendCurve = FinDiscountCurveFlat(valueDate, dividendYield)

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
