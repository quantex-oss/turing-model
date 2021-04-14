###############################################################################
# Copyright (C) 2018, 2019, 2020 Dominic O'Kane
###############################################################################

import sys
sys.path.append("..")

from turingmodel.products.equity.turing_equity_one_touch_option import TuringEquityOneTouchOption
from turingmodel.products.equity.turing_equity_one_touch_option import TuringTouchOptionPayoffTypes
from turingmodel.market.curves.turing_discount_curve_flat import TuringDiscountCurveFlat
from turingmodel.models.turing_model_black_scholes import TuringModelBlackScholes
from turingmodel.turingutils.turing_date import TuringDate

from TuringTestCases import TuringTestCases, globalTestCaseMode
testCases = TuringTestCases(__file__, globalTestCaseMode)

###############################################################################


def test_FinFXOneTouchOption():
    # Examples Haug Page 180 Table 4-22
    # Agreement not exact at t is not exactly 0.50

    valueDate = TuringDate(1, 1, 2016)
    expiryDate = TuringDate(2, 7, 2016)
    volatility = 0.20
    barrierLevel = 1.0  # H
    model = TuringModelBlackScholes(volatility)

    domesticRate = 0.10
    foreignRate = 0.03

    numPaths = 20000
    numStepsPerYear = 252

    domCurve = TuringDiscountCurveFlat(valueDate, domesticRate)
    forCurve = TuringDiscountCurveFlat(valueDate, foreignRate)

    spotFXRate = 1.050
    paymentSize = 1.5

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
                         spotFXRate,
                         domCurve,
                         forCurve,
                         model)

        v_mc = option.valueMC(valueDate,
                              spotFXRate,
                              domCurve,
                              forCurve,
                              model,
                              numStepsPerYear,
                              numPaths)

        testCases.print("%60s " % downType,
                        "%9.5f" % v,
                        "%9.5f" % v_mc)

    spotFXRate = 0.950
    paymentSize = 1.5

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
                         spotFXRate,
                         domCurve,
                         forCurve,
                         model)

        v_mc = option.valueMC(valueDate,
                              spotFXRate,
                              domCurve,
                              forCurve,
                              model,
                              numStepsPerYear,
                              numPaths)

        testCases.print("%60s " % upType,
                        "%9.5f" % v,
                        "%9.5f" % v_mc)

    ###########################################################################

    spotFXRate = 1.050

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
                         spotFXRate,
                         domCurve,
                         forCurve,
                         model)

        v_mc = option.valueMC(valueDate,
                              spotFXRate,
                              domCurve,
                              forCurve,
                              model,
                              numStepsPerYear,
                              numPaths)

        testCases.print("%60s " % downType,
                        "%9.5f" % v,
                        "%9.5f" % v_mc)

    spotFXRate = 0.950

    upTypes = [TuringTouchOptionPayoffTypes.UP_AND_IN_ASSET_AT_HIT,
               TuringTouchOptionPayoffTypes.UP_AND_IN_ASSET_AT_EXPIRY,
               TuringTouchOptionPayoffTypes.UP_AND_OUT_ASSET_OR_NOTHING]

    for upType in upTypes:

        option = TuringEquityOneTouchOption(expiryDate,
                                            upType,
                                            barrierLevel)

        v = option.value(valueDate,
                         spotFXRate,
                         domCurve,
                         forCurve,
                         model)

        v_mc = option.valueMC(valueDate,
                              spotFXRate,
                              domCurve,
                              forCurve,
                              model,
                              numStepsPerYear,
                              numPaths)

        testCases.print("%60s " % upType,
                        "%9.5f" % v,
                        "%9.5f" % v_mc)

###############################################################################


test_FinFXOneTouchOption()
testCases.compareTestCases()
