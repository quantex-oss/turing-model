###############################################################################
# Copyright (C) 2018, 2019, 2020 Dominic O'Kane
###############################################################################

import sys
sys.path.append("..")

from financepy.models.turing_process_simulator import FinProcessTypes
from financepy.models.turing_process_simulator import FinGBMNumericalScheme
from financepy.products.equity.turing_equity_barrier_option import FinEquityBarrierTypes
from financepy.products.equity.turing_equity_barrier_option import TuringEquityBarrierOption
from financepy.models.turing_model_black_scholes import FinModelBlackScholes
from financepy.market.curves.turing_discount_curve_flat import TuringDiscountCurveFlat
from financepy.finutils.turing_date import TuringDate

from TuringTestCases import TuringTestCases, globalTestCaseMode
testCases = TuringTestCases(__file__, globalTestCaseMode)

###############################################################################

def test_FinEquityBarrierOption():

    valueDate = TuringDate(1, 1, 2015)
    expiryDate = TuringDate(1, 1, 2016)
    stockPrice = 100.0
    volatility = 0.20
    interestRate = 0.05
    dividendYield = 0.02
    optionType = FinEquityBarrierTypes.DOWN_AND_OUT_CALL

    drift = interestRate - dividendYield
    scheme = FinGBMNumericalScheme.NORMAL
    processType = FinProcessTypes.GBM

    discountCurve = TuringDiscountCurveFlat(valueDate, interestRate)
    dividendCurve = TuringDiscountCurveFlat(valueDate, dividendYield)

    model = FinModelBlackScholes(volatility)

    #######################################################################

    import time
    start = time.time()
    numObservationsPerYear = 100

    testCases.header(
        "Type",
        "K",
        "B",
        "S:",
        "Value:",
        "ValueMC",
        "Diff",
        "TIME")

    for optionType in FinEquityBarrierTypes:
        for stockPrice in range(80, 120, 10):

            B = 110.0
            K = 100.0

            option = TuringEquityBarrierOption(
                expiryDate, K, optionType, B, numObservationsPerYear)
            value = option.value(
                valueDate,
                stockPrice,
                discountCurve,
                dividendCurve,
                model)
            start = time.time()
            modelParams = (stockPrice, drift, volatility, scheme)
            valueMC = option.valueMC(valueDate,
                                     stockPrice,
                                     discountCurve,
                                     dividendCurve,
                                     processType,
                                     modelParams)

            end = time.time()
            timeElapsed = round(end - start, 3)
            diff = valueMC - value

            testCases.print(
                optionType,
                K,
                B,
                stockPrice,
                value,
                valueMC,
                diff,
                timeElapsed)

        for stockPrice in range(80, 120, 10):

            B = 100.0
            K = 110.0

            option = TuringEquityBarrierOption(
                expiryDate, K, optionType, B, numObservationsPerYear)
            value = option.value(
                valueDate,
                stockPrice,
                discountCurve,
                dividendCurve,
                model)
            start = time.time()
            modelParams = (stockPrice, drift, volatility, scheme)
            valueMC = option.valueMC(
                valueDate,
                stockPrice,
                discountCurve,
                dividendCurve,
                processType,
                modelParams)
            end = time.time()
            timeElapsed = round(end - start, 3)
            diff = valueMC - value

            testCases.print(
                optionType,
                K,
                B,
                stockPrice,
                value,
                valueMC,
                diff,
                timeElapsed)

        end = time.time()

##########################################################################

    stockPrices = range(50, 150, 50)
    B = 105.0

    testCases.header("Type", "K", "B", "S:", "Value", "Delta", "Vega", "Theta")

    for optionType in FinEquityBarrierTypes:

        for stockPrice in stockPrices:

            barrierOption = TuringEquityBarrierOption(
                expiryDate, 100.0, optionType, B, numObservationsPerYear)

            value = barrierOption.value(
                valueDate,
                stockPrice,
                discountCurve,
                dividendCurve,
                model)
            delta = barrierOption.delta(
                valueDate,
                stockPrice,
                discountCurve,
                dividendCurve,
                model)
            vega = barrierOption.vega(
                valueDate,
                stockPrice,
                discountCurve,
                dividendCurve,
                model)
            theta = barrierOption.theta(
                valueDate,
                stockPrice,
                discountCurve,
                dividendCurve,
                model)

            testCases.print(
                optionType,
                K,
                B,
                stockPrice,
                value,
                delta,
                vega,
                theta)

###############################################################################

test_FinEquityBarrierOption()
testCases.compareTestCases()
