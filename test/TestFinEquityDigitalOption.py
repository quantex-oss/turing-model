import sys
sys.path.append("..")

from turing_models.utilities.global_types import TuringOptionTypes
from turing_models.products.equity.equity_digital_option import TuringEquityDigitalOption, TuringDigitalOptionTypes
from turing_models.models.model_black_scholes import TuringModelBlackScholes
from fundamental.market.curves.discount_curve_flat import TuringDiscountCurveFlat
from turing_models.utilities.turing_date import TuringDate

from TuringTestCases import TuringTestCases, globalTestCaseMode
testCases = TuringTestCases(__file__, globalTestCaseMode)

##########################################################################


def test_FinEquityDigitalOption():

    underlyingType = TuringDigitalOptionTypes.CASH_OR_NOTHING

    valueDate = TuringDate(1, 1, 2015)
    expiryDate = TuringDate(1, 1, 2016)
    stockPrice = 100.0
    volatility = 0.30
    interestRate = 0.05
    dividendYield = 0.01
    discountCurve = TuringDiscountCurveFlat(valueDate, interestRate)
    dividendCurve = TuringDiscountCurveFlat(valueDate, dividendYield)
    
    model = TuringModelBlackScholes(volatility)
    import time

    callOptionValues = []
    callOptionValuesMC = []
    numPathsList = [
        10000,
        20000,
        40000,
        80000,
        160000,
        320000,
        640000,
        1280000,
        2560000]

    testCases.header("NumLoops", "ValueBS", "ValueMC", "TIME")

    for numPaths in numPathsList:

        callOption = TuringEquityDigitalOption(
            expiryDate, 100.0, TuringOptionTypes.EUROPEAN_CALL, underlyingType)
        value = callOption.value(
            valueDate,
            stockPrice,
            discountCurve,
            dividendCurve,
            model)
        start = time.time()
        valueMC = callOption.valueMC(
            valueDate,
            stockPrice,
            discountCurve,
            dividendCurve,
            model,
            numPaths)
        end = time.time()
        duration = end - start
        testCases.print(numPaths, value, valueMC, duration)

        callOptionValues.append(value)
        callOptionValuesMC.append(valueMC)

#    plt.figure(figsize=(10,8))
#    plt.plot(numPathsList, callOptionValues, color = 'b', label="Call Option")
#    plt.plot(numPathsList, callOptionValuesMC, color = 'r', label = "Call Option MC")
#    plt.xlabel("Num Loops")
#    plt.legend(loc='best')

##########################################################################

    stockPrices = range(50, 150, 50)
    callOptionValues = []
    callOptionDeltas = []
    callOptionVegas = []
    callOptionThetas = []

    for stockPrice in stockPrices:
        callOption = TuringEquityDigitalOption(
            expiryDate, 100.0, TuringOptionTypes.EUROPEAN_CALL, underlyingType)
        value = callOption.value(
            valueDate,
            stockPrice,
            discountCurve,
            dividendCurve,
            model)
        delta = callOption.delta(
            valueDate,
            stockPrice,
            discountCurve,
            dividendCurve,
            model)
        vega = callOption.vega(
            valueDate,
            stockPrice,
            discountCurve,
            dividendCurve,
            model)
        theta = callOption.theta(
            valueDate,
            stockPrice,
            discountCurve,
            dividendCurve,
            model)
        callOptionValues.append(value)
        callOptionDeltas.append(delta)
        callOptionVegas.append(vega)
        callOptionThetas.append(theta)

    putOptionValues = []
    putOptionDeltas = []
    putOptionVegas = []
    putOptionThetas = []

    for stockPrice in stockPrices:
        putOption = TuringEquityDigitalOption(
            expiryDate, 100.0, TuringOptionTypes.EUROPEAN_PUT, underlyingType)
        value = putOption.value(
            valueDate,
            stockPrice,
            discountCurve,
            dividendCurve,
            model)
        delta = putOption.delta(
            valueDate,
            stockPrice,
            discountCurve,
            dividendCurve,
            model)
        vega = putOption.vega(
            valueDate,
            stockPrice,
            discountCurve,
            dividendCurve,
            model)
        theta = putOption.theta(
            valueDate,
            stockPrice,
            discountCurve,
            dividendCurve,
            model)
        putOptionValues.append(value)
        putOptionDeltas.append(delta)
        putOptionVegas.append(vega)
        putOptionThetas.append(theta)

##########################################################################

test_FinEquityDigitalOption()
testCases.compareTestCases()
