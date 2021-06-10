import numpy as np
import time

import sys
sys.path.append("..")

from turing_models.products.equity.equity_binomial_tree import TuringEquityBinomialTree
from turing_models.products.equity.equity_binomial_tree import TuringEquityTreeExerciseTypes
from turing_models.products.equity.equity_binomial_tree import TuringEquityTreePayoffTypes
from turing_models.products.equity.equity_vanilla_option import TuringEquityVanillaOption
from turing_models.utilities.global_types import TuringOptionTypes
from turing_models.utilities.turing_date import TuringDate
from turing_models.models.model_black_scholes import TuringModelBlackScholes
from fundamental.market.curves.discount_curve_flat import TuringDiscountCurveFlat

from TuringTestCases import TuringTestCases, globalTestCaseMode
testCases = TuringTestCases(__file__, globalTestCaseMode)

###############################################################################

def test_FinBinomialTree():

    stockPrice = 50.0
    riskFreeRate = 0.06
    dividendYield = 0.04
    volatility = 0.40

    valueDate = TuringDate(2016, 1, 1)
    expiryDate = TuringDate(2017, 1, 1)

    model = TuringModelBlackScholes(volatility)
    discountCurve = TuringDiscountCurveFlat(valueDate, riskFreeRate)
    dividendCurve = TuringDiscountCurveFlat(valueDate, dividendYield)

    numStepsList = [100, 500, 1000, 2000, 5000]

    strikePrice = 50.0

    testCases.banner("================== EUROPEAN PUT =======================")

    putOption = TuringEquityVanillaOption(
        expiryDate,
        strikePrice,
        TuringOptionTypes.EUROPEAN_PUT)
    value = putOption.value(valueDate, stockPrice, discountCurve, dividendCurve, model)
    delta = putOption.delta(valueDate, stockPrice, discountCurve, dividendCurve, model)
    gamma = putOption.gamma(valueDate, stockPrice, discountCurve, dividendCurve, model)
    theta = putOption.theta(valueDate, stockPrice, discountCurve, dividendCurve, model)
    testCases.header("BS Value", "BS Delta", "BS Gamma", "BS Theta")
    testCases.print(value, delta, gamma, theta)

    payoff = TuringEquityTreePayoffTypes.VANILLA_OPTION
    exercise = TuringEquityTreeExerciseTypes.EUROPEAN
    params = np.array([-1, strikePrice])

    testCases.header("NumSteps", "Results", "TIME")

    for numSteps in numStepsList:
        start = time.time()
        tree = TuringEquityBinomialTree()
        results = tree.value(
            stockPrice,
            discountCurve,
            dividendCurve,
            volatility,
            numSteps,
            valueDate,
            payoff,
            expiryDate,
            payoff,
            exercise,
            params)
        end = time.time()
        duration = end - start
        testCases.print(numSteps, results, duration)

    testCases.banner("================== AMERICAN PUT =======================")

    payoff = TuringEquityTreePayoffTypes.VANILLA_OPTION
    exercise = TuringEquityTreeExerciseTypes.AMERICAN
    params = np.array([-1, strikePrice])

    testCases.header("NumSteps", "Results", "TIME")

    for numSteps in numStepsList:
        start = time.time()
        tree = TuringEquityBinomialTree()
        results = tree.value(
            stockPrice,
            discountCurve,
            dividendCurve,
            volatility,
            numSteps,
            valueDate,
            payoff,
            expiryDate,
            payoff,
            exercise,
            params)
        end = time.time()
        duration = end - start
        testCases.print(numSteps, results, duration)

    testCases.banner(
        "================== EUROPEAN CALL =======================")

    callOption = TuringEquityVanillaOption(
        expiryDate,
        strikePrice,
        TuringOptionTypes.EUROPEAN_CALL)
    value = callOption.value(valueDate, stockPrice, discountCurve, dividendCurve, model)
    delta = callOption.delta(valueDate, stockPrice, discountCurve, dividendCurve, model)
    gamma = callOption.gamma(valueDate, stockPrice, discountCurve, dividendCurve, model)
    theta = callOption.theta(valueDate, stockPrice, discountCurve, dividendCurve, model)
    testCases.header("BS Value", "BS Delta", "BS Gamma", "BS Theta")
    testCases.print(value, delta, gamma, theta)

    payoff = TuringEquityTreePayoffTypes.VANILLA_OPTION
    exercise = TuringEquityTreeExerciseTypes.EUROPEAN
    params = np.array([1.0, strikePrice])

    testCases.header("NumSteps", "Results", "TIME")
    for numSteps in numStepsList:
        start = time.time()
        tree = TuringEquityBinomialTree()

        results = tree.value(
            stockPrice,
            discountCurve,
            dividendCurve,
            volatility,
            numSteps,
            valueDate,
            payoff,
            expiryDate,
            payoff,
            exercise,
            params)

        end = time.time()
        duration = end - start
        testCases.print(numSteps, results, duration)

    testCases.banner(
        "================== AMERICAN CALL =======================")

    payoff = TuringEquityTreePayoffTypes.VANILLA_OPTION
    exercise = TuringEquityTreeExerciseTypes.AMERICAN
    params = np.array([1.0, strikePrice])

    testCases.header("NumSteps", "Results", "TIME")
    for numSteps in numStepsList:
        start = time.time()
        tree = TuringEquityBinomialTree()

        results = tree.value(
            stockPrice,
            discountCurve,
            dividendCurve,
            volatility,
            numSteps,
            valueDate,
            payoff,
            expiryDate,
            payoff,
            exercise,
            params)

        end = time.time()
        duration = end - start
        testCases.print(numSteps, results, duration)

###############################################################################

test_FinBinomialTree()
testCases.compareTestCases()
