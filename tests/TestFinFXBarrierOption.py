###############################################################################
# Copyright (C) 2018, 2019, 2020 Dominic O'Kane
###############################################################################

import sys
sys.path.append("..")

from turingmodel.models.turing_process_simulator import FinProcessTypes
from turingmodel.models.turing_process_simulator import FinGBMNumericalScheme
from turingmodel.models.turing_model_black_scholes import FinModelBlackScholes
from turingmodel.products.fx.turing_fx_barrier_option import TuringFXBarrierTypes
from turingmodel.products.fx.turing_fx_barrier_option import TuringFXBarrierOption
from turingmodel.market.curves.turing_discount_curve_flat import TuringDiscountCurveFlat
from turingmodel.turingutils.turing_date import TuringDate

from TuringTestCases import TuringTestCases, globalTestCaseMode
testCases = TuringTestCases(__file__, globalTestCaseMode)

###############################################################################

def test_FinFXBarrierOption():

    valueDate = TuringDate(1, 1, 2015)
    expiryDate = TuringDate(1, 1, 2016)
    spotFXRate = 100.0
    currencyPair = "USDJPY"
    volatility = 0.20
    domInterestRate = 0.05
    forInterestRate = 0.02
    optionType = TuringFXBarrierTypes.DOWN_AND_OUT_CALL
    notional = 100.0
    notionalCurrency = "USD"

    drift = domInterestRate - forInterestRate
    scheme = FinGBMNumericalScheme.ANTITHETIC
    processType = FinProcessTypes.GBM
    domDiscountCurve = TuringDiscountCurveFlat(valueDate, domInterestRate)
    forDiscountCurve = TuringDiscountCurveFlat(valueDate, forInterestRate)
    model = FinModelBlackScholes(volatility)

    ###########################################################################

    import time
    start = time.time()
    numObservationsPerYear = 100

    for optionType in TuringFXBarrierTypes:

        testCases.header("Type", "K", "B", "S", "Value",
                         "ValueMC", "TIME", "Diff")

        for spotFXRate in range(60, 140, 10):
            B = 110.0
            K = 100.0

            option = TuringFXBarrierOption(expiryDate, K, currencyPair,
                                           optionType, B,
                                           numObservationsPerYear,
                                           notional, notionalCurrency)

            value = option.value(valueDate, spotFXRate,
                                 domDiscountCurve, forDiscountCurve, model)

            start = time.time()
            modelParams = (spotFXRate, drift, volatility, scheme)
            valueMC = option.valueMC(valueDate, spotFXRate,
                                     domInterestRate, processType,
                                     modelParams)

            end = time.time()
            timeElapsed = round(end - start, 3)
            diff = valueMC - value

            testCases.print(optionType, K, B, spotFXRate, value, valueMC,
                            timeElapsed, diff)

        for spotFXRate in range(60, 140, 10):
            B = 100.0
            K = 110.0

            option = TuringFXBarrierOption(expiryDate, K, currencyPair,
                                           optionType, B,
                                           numObservationsPerYear,
                                           notional, notionalCurrency)

            value = option.value(valueDate, spotFXRate,
                                 domDiscountCurve, forDiscountCurve, model)

            start = time.time()
            modelParams = (spotFXRate, drift, volatility, scheme)
            valueMC = option.valueMC(valueDate,
                                     spotFXRate,
                                     domInterestRate,
                                     processType,
                                     modelParams)

            end = time.time()
            timeElapsed = round(end - start, 3)
            diff = valueMC - value

            testCases.print(optionType, K, B, spotFXRate, value, valueMC,
                            timeElapsed, diff)

    end = time.time()

##########################################################################

    spotFXRates = range(50, 150, 50)
    B = 105.0

    testCases.header("Type", "K", "B", "S:", "Value", "Delta", "Vega", "Theta")

    for optionType in TuringFXBarrierTypes:
        for spotFXRate in spotFXRates:
            barrierOption = TuringFXBarrierOption(expiryDate,
                                                  100.0,
                                                  currencyPair,
                                                  optionType,
                                                  B,
                                                  numObservationsPerYear,
                                                  notional,
                                                  notionalCurrency)

            value = barrierOption.value(valueDate,
                                        spotFXRate,
                                        domDiscountCurve,
                                        forDiscountCurve,
                                        model)

            delta = barrierOption.delta(valueDate,
                                        spotFXRate,
                                        domDiscountCurve,
                                        forDiscountCurve,
                                        model)

            vega = barrierOption.vega(valueDate,
                                      spotFXRate,
                                      domDiscountCurve,
                                      forDiscountCurve,
                                      model)

            theta = barrierOption.theta(valueDate,
                                        spotFXRate,
                                        domDiscountCurve,
                                        forDiscountCurve,
                                        model)

            testCases.print(optionType,
                            K,
                            B,
                            spotFXRate,
                            value,
                            delta,
                            vega,
                            theta)

###############################################################################

test_FinFXBarrierOption()
testCases.compareTestCases()
