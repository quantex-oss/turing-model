###############################################################################
# Copyright (C) 2018, 2019, 2020 Dominic O'Kane
###############################################################################

import sys
sys.path.append("..")

from financepy.products.equity.turing_equity_one_touch_option import TuringEquityOneTouchOption
from financepy.products.equity.turing_equity_one_touch_option import TuringTouchOptionPayoffTypes
from financepy.market.curves.turing_discount_curve_flat import TuringDiscountCurveFlat
from financepy.models.turing_model_black_scholes import FinModelBlackScholes
from financepy.finutils.turing_date import TuringDate

from TuringTestCases import TuringTestCases, globalTestCaseMode
testCases = TuringTestCases(__file__, globalTestCaseMode)

###############################################################################


def test_FinEquityOneTouchOption():
    # Examples Haug Page 180 Table 4-22
    # Agreement not exact at t is not exactly 0.50

    valueDate = TuringDate(1, 1, 2016)
    expiryDate = TuringDate(2, 7, 2016)
    interestRate = 0.10
    volatility = 0.20
    barrierLevel = 100.0  # H
    model = FinModelBlackScholes(volatility)
    dividendYield = 0.03
    numPaths = 10000
    numStepsPerYear = 252

    discountCurve = TuringDiscountCurveFlat(valueDate, interestRate)
    dividendCurve = TuringDiscountCurveFlat(valueDate, dividendYield)

    stockPrice = 105.0
    paymentSize = 15.0

    testCases.header("================================= CASH ONLY")

    downTypes = [TuringTouchOptionPayoffTypes.DOWN_AND_IN_CASH_AT_HIT,
                 TuringTouchOptionPayoffTypes.DOWN_AND_IN_CASH_AT_EXPIRY,
                 TuringTouchOptionPayoffTypes.DOWN_AND_OUT_CASH_OR_NOTHING]

    testCases.header("TYPE", "VALUE", "VALUE_MC")

    for downType in downTypes:

        option = TuringEquityOneTouchOption(expiryDate,
                                            downType,
                                            barrierLevel,
                                            paymentSize)

        v = option.value(valueDate,
                         stockPrice,
                         discountCurve,
                         dividendCurve,
                         model)

        v_mc = option.valueMC(valueDate,
                              stockPrice,
                              discountCurve,
                              dividendCurve,
                              model,
                              numStepsPerYear,
                              numPaths)

        testCases.print("%60s " % downType,
                        "%9.5f" % v,
                        "%9.5f" % v_mc)

    stockPrice = 95.0
    paymentSize = 15.0

    upTypes = [TuringTouchOptionPayoffTypes.UP_AND_IN_CASH_AT_HIT,
               TuringTouchOptionPayoffTypes.UP_AND_IN_CASH_AT_EXPIRY,
               TuringTouchOptionPayoffTypes.UP_AND_OUT_CASH_OR_NOTHING]

    testCases.header("TYPE", "VALUE", "VALUE_MC")

    for upType in upTypes:

        option = TuringEquityOneTouchOption(expiryDate,
                                            upType,
                                            barrierLevel,
                                            paymentSize)

        v = option.value(valueDate,
                         stockPrice,
                         discountCurve,
                         dividendCurve,
                         model)

        v_mc = option.valueMC(valueDate,
                              stockPrice,
                              discountCurve,
                              dividendCurve,
                              model,
                              numStepsPerYear,
                              numPaths)

        testCases.print("%60s " % upType,
                        "%9.5f" % v,
                        "%9.5f" % v_mc)

    ###########################################################################

    stockPrice = 105.0

    testCases.banner("================= ASSET ONLY")

    downTypes = [TuringTouchOptionPayoffTypes.DOWN_AND_IN_ASSET_AT_HIT,
                 TuringTouchOptionPayoffTypes.DOWN_AND_IN_ASSET_AT_EXPIRY,
                 TuringTouchOptionPayoffTypes.DOWN_AND_OUT_ASSET_OR_NOTHING]

    testCases.header("TYPE", "VALUE", "VALUE_MC")
    for downType in downTypes:

        option = TuringEquityOneTouchOption(expiryDate,
                                            downType,
                                            barrierLevel)

        v = option.value(valueDate,
                         stockPrice,
                         discountCurve,
                         dividendCurve,
                         model)

        v_mc = option.valueMC(valueDate,
                              stockPrice,
                              discountCurve,
                              dividendCurve,
                              model,
                              numStepsPerYear,
                              numPaths)

        testCases.print("%60s " % downType,
                        "%9.5f" % v,
                        "%9.5f" % v_mc)

    stockPrice = 95.0

    upTypes = [TuringTouchOptionPayoffTypes.UP_AND_IN_ASSET_AT_HIT,
               TuringTouchOptionPayoffTypes.UP_AND_IN_ASSET_AT_EXPIRY,
               TuringTouchOptionPayoffTypes.UP_AND_OUT_ASSET_OR_NOTHING]

    for upType in upTypes:

        option = TuringEquityOneTouchOption(expiryDate,
                                            upType,
                                            barrierLevel)

        v = option.value(valueDate,
                         stockPrice,
                         discountCurve,
                         dividendCurve,
                         model)

        v_mc = option.valueMC(valueDate,
                              stockPrice,
                              discountCurve,
                              dividendCurve,
                              model,
                              numStepsPerYear,
                              numPaths)

        testCases.print("%60s " % upType,
                        "%9.5f" % v,
                        "%9.5f" % v_mc)

###############################################################################


test_FinEquityOneTouchOption()
testCases.compareTestCases()
