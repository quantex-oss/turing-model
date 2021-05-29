import numpy as np

import sys
sys.path.append("..")

from turing_models.products.equity.equity_basket_option import TuringEquityBasketOption
from turing_models.utilities.global_types import TuringOptionTypes
from fundamental.market.curves.discount_curve_flat import TuringDiscountCurveFlat
from turing_models.utilities.helper_functions import betaVectorToCorrMatrix
from turing_models.utilities.turing_date import TuringDate

from TuringTestCases import TuringTestCases, globalTestCaseMode
testCases = TuringTestCases(__file__, globalTestCaseMode)

###############################################################################


def test_FinEquityBasketOption():

    import time

    valueDate = TuringDate(1, 1, 2015)
    expiryDate = TuringDate(1, 1, 2016)
    volatility = 0.30
    interestRate = 0.05
    discountCurve = TuringDiscountCurveFlat(valueDate, interestRate)

    ##########################################################################
    # Homogeneous Basket
    ##########################################################################

    numAssets = 5
    volatilities = np.ones(numAssets) * volatility
    dividendYields = np.ones(numAssets) * 0.01
    stockPrices = np.ones(numAssets) * 100

    dividendCurves = []
    for q in dividendYields:
        dividendCurve = TuringDiscountCurveFlat(valueDate, q)
        dividendCurves.append(dividendCurve)

    betaList = np.linspace(0.0, 0.999999, 11)

    testCases.header("NumPaths", "Beta", "Value", "ValueMC", "TIME")

    for beta in betaList:
        for numPaths in [10000]:
            callOption = TuringEquityBasketOption(
                expiryDate, 100.0, TuringOptionTypes.EUROPEAN_CALL, numAssets)
            betas = np.ones(numAssets) * beta
            corrMatrix = betaVectorToCorrMatrix(betas)

            start = time.time()
            v = callOption.value(
                valueDate,
                stockPrices,
                discountCurve,
                dividendCurves,
                volatilities,
                corrMatrix)

            vMC = callOption.valueMC(
                valueDate,
                stockPrices,
                discountCurve,
                dividendCurves,
                volatilities,
                corrMatrix,
                numPaths)
            end = time.time()
            duration = end - start
            testCases.print(numPaths, beta, v, vMC, duration)

    ##########################################################################
    # INHomogeneous Basket
    ##########################################################################

    numAssets = 5
    volatilities = np.array([0.3, 0.2, 0.25, 0.22, 0.4])
    dividendYields = np.array([0.01, 0.02, 0.04, 0.01, 0.02])
    stockPrices = np.array([100, 105, 120, 100, 90])

    dividendCurves = []
    for q in dividendYields:
        dividendCurve = TuringDiscountCurveFlat(valueDate, q)
        dividendCurves.append(dividendCurve)

    betaList = np.linspace(0.0, 0.999999, 11)

    testCases.header("NumPaths", "Beta", "Value", "ValueMC", "TIME")

    for beta in betaList:

        for numPaths in [10000]:

            callOption = TuringEquityBasketOption(
                expiryDate, 100.0, TuringOptionTypes.EUROPEAN_CALL, numAssets)
            betas = np.ones(numAssets) * beta
            corrMatrix = betaVectorToCorrMatrix(betas)

            start = time.time()

            v = callOption.value(
                    valueDate,
                    stockPrices,
                    discountCurve,
                    dividendCurves,
                    volatilities,
                    corrMatrix)

            vMC = callOption.valueMC(
                    valueDate,
                    stockPrices,
                    discountCurve,
                    dividendCurves,
                    volatilities,
                    corrMatrix,
                    numPaths)

            end = time.time()
            duration = end - start
            testCases.print(numPaths, beta, v, vMC, duration)

    ##########################################################################
    # Homogeneous Basket
    ##########################################################################

    numAssets = 5
    volatilities = np.ones(numAssets) * volatility
    dividendYields = np.ones(numAssets) * 0.01
    stockPrices = np.ones(numAssets) * 100
    betaList = np.linspace(0.0, 0.999999, 11)

    dividendCurves = []
    for q in dividendYields:
        dividendCurve = TuringDiscountCurveFlat(valueDate, q)
        dividendCurves.append(dividendCurve)

    testCases.header("NumPaths", "Beta", "Value", "ValueMC", "TIME")

    for beta in betaList:
        for numPaths in [10000]:
            callOption = TuringEquityBasketOption(
                expiryDate, 100.0, TuringOptionTypes.EUROPEAN_PUT, numAssets)
            betas = np.ones(numAssets) * beta
            corrMatrix = betaVectorToCorrMatrix(betas)

            start = time.time()
            v = callOption.value(
                valueDate,
                stockPrices,
                discountCurve,
                dividendCurves,
                volatilities,
                corrMatrix)
            vMC = callOption.valueMC(
                valueDate,
                stockPrices,
                discountCurve,
                dividendCurves,
                volatilities,
                corrMatrix,
                numPaths)
            end = time.time()
            duration = end - start
            testCases.print(numPaths, beta, v, vMC, duration)

    ##########################################################################
    # INHomogeneous Basket
    ##########################################################################

    numAssets = 5
    volatilities = np.array([0.3, 0.2, 0.25, 0.22, 0.4])
    dividendYields = np.array([0.01, 0.02, 0.04, 0.01, 0.02])
    stockPrices = np.array([100, 105, 120, 100, 90])
    betaList = np.linspace(0.0, 0.999999, 11)

    dividendCurves = []
    for q in dividendYields:
        dividendCurve = TuringDiscountCurveFlat(valueDate, q)
        dividendCurves.append(dividendCurve)

    testCases.header("NumPaths", "Beta", "Value", "ValueMC", "TIME")

    for beta in betaList:

        for numPaths in [10000]:

            callOption = TuringEquityBasketOption(
                expiryDate, 100.0, TuringOptionTypes.EUROPEAN_PUT, numAssets)
            betas = np.ones(numAssets) * beta
            corrMatrix = betaVectorToCorrMatrix(betas)

            start = time.time()
            v = callOption.value(
                valueDate,
                stockPrices,
                discountCurve,
                dividendCurves,
                volatilities,
                corrMatrix)
            vMC = callOption.valueMC(
                valueDate,
                stockPrices,
                discountCurve,
                dividendCurves,
                volatilities,
                corrMatrix,
                numPaths)
            end = time.time()
            duration = end - start
            testCases.print(numPaths, beta, v, vMC, duration)


###############################################################################


test_FinEquityBasketOption()
testCases.compareTestCases()
