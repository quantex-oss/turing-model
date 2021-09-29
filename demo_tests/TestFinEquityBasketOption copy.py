from turing_models.models.model_black_scholes import TuringModelBlackScholes
import numpy as np

import sys
sys.path.append("..")

from turing_models.instruments.archive.equity import TuringSnowballBasketOption
from turing_models.instruments.archive.equity import TuringEquitySnowballOption
from turing_models.utilities.global_types import TuringOptionTypes
from turing_models.market.curves.discount_curve_flat import TuringDiscountCurveFlat
from turing_models.utilities.helper_functions import betaVectorToCorrMatrix
from turing_models.utilities.turing_date import TuringDate

# from TuringTestCases import TuringTestCases, globalTestCaseMode
# testCases = TuringTestCases(__file__, globalTestCaseMode)

###############################################################################


def test_FinEquityBasketOption():

    import time
    valueDate = TuringDate(2015, 1, 1)
    expiryDate = TuringDate(2016, 1, 1)
    # volatility = 0.30
    interestRate = 0.05
    discountCurve = TuringDiscountCurveFlat(valueDate, interestRate)

    ##########################################################################
    # INHomogeneous Basket
    ##########################################################################

    numAssets = 5
    # volatilities = np.array([0.3, 0.2, 0.25, 0.22, 0.4])
    # dividendYields = np.array([0.01, 0.02, 0.04, 0.01, 0.02])
    # stockPrices = np.array([100., 105., 120., 100., 90.])
    # weights = np.array([0.2, 0.2, 0.2, 0.2, 0.2])
    betaList = np.linspace(0.0, 0.999999, 2)
    volatilities = np.array([0.3, 0.3, 0.3, 0.3, 0.3])
    dividendYields = np.array([0.01, 0.01, 0.01, 0.01, 0.01])
    stockPrices = np.array([100., 100., 100., 100., 100.])
    weights = np.array([0.2, 0.2, 0.2, 0.2, 0.2])

    dividendCurves = []
    for q in dividendYields:
        dividendCurve = TuringDiscountCurveFlat(valueDate, q)
        dividendCurves.append(dividendCurve)

    # testCases.header("NumPaths", "Beta", "Value", "ValueMC", "TIME")

    for beta in betaList:

        for numPaths in [100000]:

            callOption = TuringSnowballBasketOption(
                expiryDate, TuringOptionTypes.SNOWBALL_CALL, 110, 88, 1000000, 0.2, numAssets)
            betas = np.ones(numAssets) * beta
            corrMatrix = betaVectorToCorrMatrix(betas)
            # print(corrMatrix)
            start = time.time()
            vMC = callOption.valueMC(
                valueDate,
                stockPrices,
                discountCurve,
                dividendCurves,
                volatilities,
                corrMatrix,
                weights,
                numPaths
                )
            end = time.time()
            duration = end - start
            print(numPaths, vMC, duration)


###############################################################################
def test_FinEquitySnowballOption():

    import time
    valueDate = TuringDate(2015, 1, 1)
    expiryDate = TuringDate(2016, 1, 1)
    # volatility = 0.30
    interestRate = 0.05
    discountCurve = TuringDiscountCurveFlat(valueDate, interestRate)

    ##########################################################################
    # INHomogeneous Basket
    ##########################################################################

    # betaList = np.linspace(0.0, 0.999999, 2)
    volatilities = 0.3
    dividendYields = 0.01
    stockPrices = 100
    model = TuringModelBlackScholes(volatilities)
    # weights = np.array([0.2, 0.2, 0.2, 0.2, 0.2])

    dividendCurves = TuringDiscountCurveFlat(valueDate, dividendYields)

    # testCases.header("NumPaths", "Beta", "Value", "ValueMC", "TIME")

    # for beta in betaList:

    for numPaths in [100000]:

        callOption = TuringEquitySnowballOption(
            expiryDate,  110, 88, 1000000, 0.2, TuringOptionTypes.SNOWBALL_CALL)
        # betas = np.ones(numAssets) * beta
        # corrMatrix = betaVectorToCorrMatrix(betas)
        # print(corrMatrix)
        start = time.time()
        vMC = callOption.value(
            valueDate,
            stockPrices,
            discountCurve,
            dividendCurves,
            model
            )
        end = time.time()
        duration = end - start
        print(numPaths, vMC, duration)


# p = cProfile.Profile()
# p.enable()
test_FinEquityBasketOption()
# test_FinEquitySnowballOption()
# p.disable()
# p.print_stats(sort='tottime')
# testCases.compareTestCases()
