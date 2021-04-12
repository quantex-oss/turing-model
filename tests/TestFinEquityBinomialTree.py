###############################################################################
# Copyright (C) 2018, 2019, 2020 Dominic O'Kane
###############################################################################

import numpy as np
import time

import sys
sys.path.append("..")

from financepy.products.equity.turing_equity_binomial_tree import FinEquityBinomialTree
from financepy.products.equity.turing_equity_binomial_tree import FinEquityTreeExerciseTypes
from financepy.products.equity.turing_equity_binomial_tree import FinEquityTreePayoffTypes
from financepy.products.equity.turing_equity_vanilla_option import FinEquityVanillaOption
from financepy.finutils.turing_global_types import FinOptionTypes
from financepy.finutils.turing_date import FinDate
from financepy.models.turing_model_black_scholes import FinModelBlackScholes
from financepy.market.curves.turing_discount_curve_flat import FinDiscountCurveFlat

from FinTestCases import FinTestCases, globalTestCaseMode
testCases = FinTestCases(__file__, globalTestCaseMode)

###############################################################################

def test_FinBinomialTree():

    stockPrice = 50.0
    riskFreeRate = 0.06
    dividendYield = 0.04
    volatility = 0.40

    valueDate = FinDate(1, 1, 2016)
    expiryDate = FinDate(1, 1, 2017)

    model = FinModelBlackScholes(volatility)
    discountCurve = FinDiscountCurveFlat(valueDate, riskFreeRate)
    dividendCurve = FinDiscountCurveFlat(valueDate, dividendYield)

    numStepsList = [100, 500, 1000, 2000, 5000]

    strikePrice = 50.0

    testCases.banner("================== EUROPEAN PUT =======================")

    putOption = FinEquityVanillaOption(
        expiryDate,
        strikePrice,
        FinOptionTypes.EUROPEAN_PUT)
    value = putOption.value(valueDate, stockPrice, discountCurve, dividendCurve, model)
    delta = putOption.delta(valueDate, stockPrice, discountCurve, dividendCurve, model)
    gamma = putOption.gamma(valueDate, stockPrice, discountCurve, dividendCurve, model)
    theta = putOption.theta(valueDate, stockPrice, discountCurve, dividendCurve, model)
    testCases.header("BS Value", "BS Delta", "BS Gamma", "BS Theta")
    testCases.print(value, delta, gamma, theta)

    payoff = FinEquityTreePayoffTypes.VANILLA_OPTION
    exercise = FinEquityTreeExerciseTypes.EUROPEAN
    params = np.array([-1, strikePrice])

    testCases.header("NumSteps", "Results", "TIME")

    for numSteps in numStepsList:
        start = time.time()
        tree = FinEquityBinomialTree()
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

    payoff = FinEquityTreePayoffTypes.VANILLA_OPTION
    exercise = FinEquityTreeExerciseTypes.AMERICAN
    params = np.array([-1, strikePrice])

    testCases.header("NumSteps", "Results", "TIME")

    for numSteps in numStepsList:
        start = time.time()
        tree = FinEquityBinomialTree()
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

    callOption = FinEquityVanillaOption(
        expiryDate,
        strikePrice,
        FinOptionTypes.EUROPEAN_CALL)
    value = callOption.value(valueDate, stockPrice, discountCurve, dividendCurve, model)
    delta = callOption.delta(valueDate, stockPrice, discountCurve, dividendCurve, model)
    gamma = callOption.gamma(valueDate, stockPrice, discountCurve, dividendCurve, model)
    theta = callOption.theta(valueDate, stockPrice, discountCurve, dividendCurve, model)
    testCases.header("BS Value", "BS Delta", "BS Gamma", "BS Theta")
    testCases.print(value, delta, gamma, theta)

    payoff = FinEquityTreePayoffTypes.VANILLA_OPTION
    exercise = FinEquityTreeExerciseTypes.EUROPEAN
    params = np.array([1.0, strikePrice])

    testCases.header("NumSteps", "Results", "TIME")
    for numSteps in numStepsList:
        start = time.time()
        tree = FinEquityBinomialTree()

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

    payoff = FinEquityTreePayoffTypes.VANILLA_OPTION
    exercise = FinEquityTreeExerciseTypes.AMERICAN
    params = np.array([1.0, strikePrice])

    testCases.header("NumSteps", "Results", "TIME")
    for numSteps in numStepsList:
        start = time.time()
        tree = FinEquityBinomialTree()

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
