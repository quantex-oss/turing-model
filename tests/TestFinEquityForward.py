###############################################################################
# Copyright (C) 2018, 2019, 2020 Dominic O'Kane
###############################################################################

import sys
sys.path.append("..")

from turingmodel.products.equity.turing_equity_forward import TuringEquityForward
from turingmodel.turingutils.turing_date import TuringDate
from turingmodel.turingutils.turing_global_types import TuringLongShort
from turingmodel.market.curves.turing_discount_curve_flat import TuringDiscountCurveFlat

from TuringTestCases import TuringTestCases, globalTestCaseMode
testCases = TuringTestCases(__file__, globalTestCaseMode)

##########################################################################


def test_FinEquityForward():

    valueDate = TuringDate(13, 2, 2018)
    expiryDate = valueDate.addMonths(12)

    stockPrice = 130.0
    forwardPrice = 125.0 # Locked
    discountRate = 0.05
    dividendRate = 0.02

    ###########################################################################

    expiryDate = valueDate.addMonths(12)
    notional = 100.0

    discountCurve = TuringDiscountCurveFlat(valueDate, discountRate)
    dividendCurve = TuringDiscountCurveFlat(valueDate, dividendRate)

    equityForward = TuringEquityForward(expiryDate,
                                        forwardPrice,
                                        notional,
                                        TuringLongShort.LONG)

    testCases.header("SPOT FX", "FX FWD", "VALUE_BS")

    fwdPrice = equityForward.forward(valueDate,
                                     stockPrice,
                                     discountCurve, 
                                     dividendCurve)

    fwdValue = equityForward.value(valueDate,
                                   stockPrice,
                                   discountCurve, 
                                   dividendCurve)

#    print(stockPrice, fwdPrice, fwdValue)
    testCases.print(stockPrice, fwdPrice, fwdValue)

###############################################################################


test_FinEquityForward()
testCases.compareTestCases()
