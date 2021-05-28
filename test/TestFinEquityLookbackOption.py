import time

import sys
sys.path.append("..")

from turing_models.products.equity.equity_float_lookback_option import TuringEquityFloatLookbackOption
from turing_models.products.equity.equity_fixed_lookback_option import TuringEquityFixedLookbackOption
from turing_models.utilities.global_types import TuringOptionTypes
from fundamental.market.curves.discount_curve_flat import TuringDiscountCurveFlat
from turing_models.utilities.turing_date import TuringDate

from TuringTestCases import TuringTestCases, globalTestCaseMode
testCases = TuringTestCases(__file__, globalTestCaseMode)

###############################################################################

def test_FinEquityLookBackOption():
    valueDate = TuringDate(1, 1, 2015)
    expiryDate = TuringDate(1, 1, 2016)
    stockPrice = 100.0
    volatility = 0.3
    interestRate = 0.05
    dividendYield = 0.01
    numPathsRange = [10000]
    stockPriceRange = range(90, 110, 10)
    numStepsPerYear = 252

    discountCurve = TuringDiscountCurveFlat(valueDate, interestRate)
    dividendCurve = TuringDiscountCurveFlat(valueDate, dividendYield)

###############################################################################

    testCases.header(
        "NUMPATHS",
        "OPTION_TYPE",
        "S",
        "SMIN",
        "VALUE",
        "VALUE_MC",
        "DIFF",
        "TIME")

    optionType = TuringOptionTypes.EUROPEAN_CALL
    for stockPrice in stockPriceRange:
        for numPaths in numPathsRange:
            option = TuringEquityFloatLookbackOption(expiryDate, optionType)
            stockMin = stockPrice
            value = option.value(
                valueDate,
                stockPrice,
                discountCurve,
                dividendCurve,
                volatility,
                stockMin)
            start = time.time()
            valueMC = option.valueMC(
                valueDate,
                stockPrice,
                discountCurve,
                dividendCurve,
                volatility,
                stockMin,
                numPaths,
                numStepsPerYear)
            end = time.time()
            timeElapsed = round(end - start, 3)
            diff = valueMC - value
            testCases.print(
                numPaths,
                optionType,
                stockPrice,
                stockMin,
                value,
                valueMC,
                diff,
                timeElapsed)

    testCases.header(
        "NUMPATHS",
        "OPTION_TYPE",
        "S",
        "SMIN",
        "VALUE",
        "VALUE_MC",
        "DIFF",
        "TIME")

    optionType = TuringOptionTypes.EUROPEAN_CALL
    for stockPrice in stockPriceRange:
        for numPaths in numPathsRange:
            option = TuringEquityFloatLookbackOption(expiryDate, optionType)
            stockMin = stockPrice - 10
            value = option.value(
                valueDate,
                stockPrice,
                discountCurve,
                dividendCurve,
                volatility,
                stockMin)
            start = time.time()
            valueMC = option.valueMC(
                valueDate,
                stockPrice,
                discountCurve,
                dividendCurve,
                volatility,
                stockMin,
                numPaths,
                numStepsPerYear)
            end = time.time()
            timeElapsed = round(end - start, 3)
            diff = valueMC - value
            testCases.print(
                numPaths,
                optionType,
                stockPrice,
                stockMin,
                value,
                valueMC,
                diff,
                timeElapsed)

    testCases.header(
        "NUMPATHS",
        "OPTION_TYPE",
        "S",
        "SMAX",
        "VALUE",
        "VALUE_MC",
        "DIFF",
        "TIME")

    optionType = TuringOptionTypes.EUROPEAN_PUT
    for stockPrice in stockPriceRange:
        for numPaths in numPathsRange:
            option = TuringEquityFloatLookbackOption(expiryDate, optionType)
            stockMax = stockPrice
            value = option.value(
                valueDate,
                stockPrice,
                discountCurve,
                dividendCurve,
                volatility,
                stockMax)
            start = time.time()
            valueMC = option.valueMC(
                valueDate,
                stockPrice,
                discountCurve,
                dividendCurve,
                volatility,
                stockMax,
                numPaths,
                numStepsPerYear)
            end = time.time()
            timeElapsed = round(end - start, 3)
            diff = valueMC - value
            testCases.print(
                numPaths,
                optionType,
                stockPrice,
                stockMax,
                value,
                valueMC,
                diff,
                timeElapsed)

    testCases.header(
        "NUMPATHS",
        "OPTION_TYPE",
        "S",
        "SMAX",
        "VALUE",
        "VALUE_MC",
        "DIFF",
        "TIME")

    optionType = TuringOptionTypes.EUROPEAN_PUT
    for stockPrice in stockPriceRange:
        for numPaths in numPathsRange:
            option = TuringEquityFloatLookbackOption(expiryDate, optionType)
            stockMax = stockPrice + 10
            value = option.value(
                valueDate,
                stockPrice,
                discountCurve,
                dividendCurve,
                volatility,
                stockMax)
            start = time.time()
            valueMC = option.valueMC(
                valueDate,
                stockPrice,
                discountCurve,
                dividendCurve,
                volatility,
                stockMax,
                numPaths,
                numStepsPerYear)
            end = time.time()
            timeElapsed = round(end - start, 3)
            diff = valueMC - value
            testCases.print(
                numPaths,
                optionType,
                stockPrice,
                stockMax,
                value,
                valueMC,
                diff,
                timeElapsed)

###############################################################################
###############################################################################

    stockPriceRange = range(90, 110, 10)
    numStepsPerYear = 252

    testCases.header(
        "NUMPATHS",
        "OPTION_TYPE",
        "S",
        "K",
        "SMAX",
        "VALUE",
        "VALUE_MC",
        "DIFF",
        "TIME")

    optionType = TuringOptionTypes.EUROPEAN_CALL
    k = 95.0
    for stockPrice in stockPriceRange:
        for numPaths in numPathsRange:
            option = TuringEquityFixedLookbackOption(expiryDate, optionType, k)
            stockMax = stockPrice
            value = option.value(
                valueDate,
                stockPrice,
                discountCurve,
                dividendCurve,
                volatility,
                stockMax)
            start = time.time()
            valueMC = option.valueMC(
                valueDate,
                stockPrice,
                discountCurve,
                dividendCurve,
                volatility,
                stockMax,
                numPaths,
                numStepsPerYear)
            end = time.time()
            timeElapsed = round(end - start, 3)
            diff = valueMC - value
            testCases.print(
                numPaths,
                optionType,
                stockPrice,
                k,
                stockMax,
                value,
                valueMC,
                diff,
                timeElapsed)

    testCases.header(
        "NUMPATHS",
        "OPTION_TYPE",
        "S",
        "K",
        "SMAX",
        "VALUE",
        "VALUE_MC",
        "DIFF",
        "TIME")

    optionType = TuringOptionTypes.EUROPEAN_CALL
    k = 100.0
    for stockPrice in stockPriceRange:
        for numPaths in numPathsRange:
            option = TuringEquityFixedLookbackOption(expiryDate, optionType, k)
            stockMax = stockPrice
            value = option.value(
                valueDate,
                stockPrice,
                discountCurve,
                dividendCurve,
                volatility,
                stockMax)
            start = time.time()
            valueMC = option.valueMC(
                valueDate,
                stockPrice,
                discountCurve,
                dividendCurve,
                volatility,
                stockMax,
                numPaths,
                numStepsPerYear)
            end = time.time()
            timeElapsed = round(end - start, 3)
            diff = valueMC - value
            testCases.print(
                numPaths,
                optionType,
                stockPrice,
                k,
                stockMax,
                value,
                valueMC,
                diff,
                timeElapsed)

    testCases.header(
        "NUMPATHS",
        "OPTION_TYPE",
        "S",
        "K",
        "SMAX",
        "VALUE",
        "VALUE_MC",
        "DIFF",
        "TIME")

    optionType = TuringOptionTypes.EUROPEAN_CALL
    k = 105.0
    for stockPrice in stockPriceRange:
        for numPaths in numPathsRange:
            option = TuringEquityFixedLookbackOption(expiryDate, optionType, k)
            stockMax = stockPrice + 10.0
            value = option.value(
                valueDate,
                stockPrice,
                discountCurve,
                dividendCurve,
                volatility,
                stockMax)
            start = time.time()
            valueMC = option.valueMC(
                valueDate,
                stockPrice,
                discountCurve,
                dividendCurve,
                volatility,
                stockMax,
                numPaths,
                numStepsPerYear)
            end = time.time()
            timeElapsed = round(end - start, 3)
            diff = valueMC - value
            testCases.print(
                numPaths,
                optionType,
                stockPrice,
                k,
                stockMax,
                value,
                valueMC,
                diff,
                timeElapsed)

    testCases.header(
        "NUMPATHS",
        "OPTION_TYPE",
        "S",
        "K",
        "SMIN",
        "VALUE",
        "VALUE_MC",
        "DIFF",
        "TIME")

    optionType = TuringOptionTypes.EUROPEAN_PUT
    k = 95.0
    for stockPrice in stockPriceRange:
        for numPaths in numPathsRange:
            option = TuringEquityFixedLookbackOption(expiryDate, optionType, k)
            stockMin = stockPrice
            value = option.value(
                valueDate,
                stockPrice,
                discountCurve,
                dividendCurve,
                volatility,
                stockMin)
            start = time.time()
            valueMC = option.valueMC(
                valueDate,
                stockPrice,
                discountCurve,
                dividendCurve,
                volatility,
                stockMin,
                numPaths,
                numStepsPerYear)
            end = time.time()
            timeElapsed = round(end - start, 3)
            diff = valueMC - value
            testCases.print(
                numPaths,
                optionType,
                stockPrice,
                k,
                stockMin,
                value,
                valueMC,
                diff,
                timeElapsed)

    testCases.header(
        "NUMPATHS",
        "OPTION_TYPE",
        "S",
        "K",
        "SMIN",
        "VALUE",
        "VALUE_MC",
        "DIFF",
        "TIME")

    optionType = TuringOptionTypes.EUROPEAN_PUT
    k = 100.0
    for stockPrice in stockPriceRange:
        for numPaths in numPathsRange:
            option = TuringEquityFixedLookbackOption(expiryDate, optionType, k)
            stockMin = stockPrice
            value = option.value(
                valueDate,
                stockPrice,
                discountCurve,
                dividendCurve,
                volatility,
                stockMin)
            start = time.time()
            valueMC = option.valueMC(
                valueDate,
                stockPrice,
                discountCurve,
                dividendCurve,
                volatility,
                stockMin,
                numPaths,
                numStepsPerYear)
            end = time.time()
            timeElapsed = round(end - start, 3)
            diff = valueMC - value
            testCases.print(
                numPaths,
                optionType,
                stockPrice,
                k,
                stockMin,
                value,
                valueMC,
                diff,
                timeElapsed)

    testCases.header(
        "NUMPATHS",
        "OPTION_TYPE",
        "S",
        "K",
        "SMIN",
        "VALUE",
        "VALUE_MC",
        "DIFF",
        "TIME")

    optionType = TuringOptionTypes.EUROPEAN_PUT
    k = 105.0
    for stockPrice in stockPriceRange:
        for numPaths in numPathsRange:
            option = TuringEquityFixedLookbackOption(expiryDate, optionType, k)
            stockMin = stockPrice - 10.0
            value = option.value(
                valueDate,
                stockPrice,
                discountCurve,
                dividendCurve,
                volatility,
                stockMin)
            start = time.time()
            valueMC = option.valueMC(
                valueDate,
                stockPrice,
                discountCurve,
                dividendCurve,
                volatility,
                stockMin,
                numPaths,
                numStepsPerYear)
            end = time.time()
            timeElapsed = round(end - start, 3)
            diff = valueMC - value
            testCases.print(
                numPaths,
                optionType,
                stockPrice,
                k,
                stockMin,
                value,
                valueMC,
                diff,
                timeElapsed)

###############################################################################

def test_example():

    expiryDate = TuringDate(1, 1, 2021)
    strikePrice = 105.0
    optionTypeCall = TuringOptionTypes.EUROPEAN_CALL
    optionTypePut = TuringOptionTypes.EUROPEAN_PUT
    lookbackCall = TuringEquityFixedLookbackOption(expiryDate, optionTypeCall, strikePrice)
    lookbackPut = TuringEquityFixedLookbackOption(expiryDate, optionTypePut, strikePrice)

    valueDate = TuringDate(1, 1, 2020)
    interestRate = 0.10
    stockPrice = 100.0
    dividendYield = 0.0
    stockMinMax = 100.0

    discountCurve = TuringDiscountCurveFlat(valueDate, interestRate)
    dividendCurve = TuringDiscountCurveFlat(valueDate, dividendYield)

    volatilities = [0.30]

    testCases.header("VALUE")
    for vol in volatilities:
        v = lookbackCall.value(valueDate, stockPrice, discountCurve, dividendCurve, vol, stockMinMax)
        testCases.print(v)

###############################################################################

test_example()
#test_FinEquityLookBackOption()
testCases.compareTestCases()
