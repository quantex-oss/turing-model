import time

import sys
sys.path.append("..")

from turing_models.utilities.global_types import TuringOptionTypes
from turing_models.products.equity.equity_asian_option import TuringEquityAsianOption
from turing_models.products.equity.equity_asian_option import TuringAsianOptionValuationMethods
from fundamental.market.curves.discount_curve_flat import TuringDiscountCurveFlat
from turing_models.models.model_black_scholes import TuringModelBlackScholes
from turing_models.utilities.turing_date import TuringDate

from TuringTestCases import TuringTestCases, globalTestCaseMode
testCases = TuringTestCases(__file__, globalTestCaseMode)

###############################################################################

testConvergence = False
testTimeEvolution = False
testMCTimings = True

###############################################################################


def testConvergence():

    valueDate = TuringDate(2014, 1, 1)
    startAveragingDate = TuringDate(2014, 6, 1)
    expiryDate = TuringDate(2015, 1, 1)
    stockPrice = 100.0
    volatility = 0.20
    interestRate = 0.30
    dividendYield = 0.10
    numObservations = 120  # daily as we have a half year
    accruedAverage = None
    K = 100
    seed = 1976

    model = TuringModelBlackScholes(volatility)
    discountCurve = TuringDiscountCurveFlat(valueDate, interestRate)
    dividendCurve = TuringDiscountCurveFlat(valueDate, dividendYield)

    asianOption = TuringEquityAsianOption(startAveragingDate,
                                          expiryDate,
                                          K,
                                          TuringOptionTypes.EUROPEAN_CALL,
                                          numObservations)

    testCases.header(
        "K",
        "Geometric",
        "Turnbull_Wakeman",
        "Curran",
        "FastMC",
        "FastMC_CV")

    valuesTurnbull = []
    valuesCurran = []
    valuesGeometric = []
    valuesMC_fast = []
    valuesMC_CV = []

    numPathsList = [5000]

    for numPaths in numPathsList:

        accruedAverage = stockPrice * 1.1

        valueMC_fast = asianOption._valueMC_fast(valueDate,
                                                 stockPrice,
                                                 discountCurve,
                                                 dividendCurve,
                                                 model,
                                                 numPaths,
                                                 seed,
                                                 accruedAverage)

        valueMC_CV = asianOption.valueMC(valueDate,
                                         stockPrice,
                                         discountCurve,
                                         dividendCurve,
                                         model,
                                         numPaths,
                                         seed,
                                         accruedAverage)

        valueGeometric = asianOption.value(valueDate,
                                           stockPrice,
                                           discountCurve,
                                           dividendCurve,
                                           model,
                                           TuringAsianOptionValuationMethods.GEOMETRIC,
                                           accruedAverage)

        valueTurnbullWakeman = asianOption.value(valueDate,
                                                 stockPrice,
                                                 discountCurve,
                                                 dividendCurve,
                                                 model,
                                                 TuringAsianOptionValuationMethods.TURNBULL_WAKEMAN,
                                                 accruedAverage)

        valueCurran = asianOption.value(valueDate,
                                        stockPrice,
                                        discountCurve,
                                        dividendCurve,
                                        model,
                                        TuringAsianOptionValuationMethods.CURRAN,
                                        accruedAverage)

        valuesGeometric.append(valueGeometric)
        valuesTurnbull.append(valueTurnbullWakeman)
        valuesCurran.append(valueCurran)
        valuesMC_fast.append(valueMC_fast)
        valuesMC_CV.append(valueMC_CV)

        testCases.print(
            numPaths,
            valueGeometric,
            valueTurnbullWakeman,
            valueCurran,
            valueMC_fast,
            valueMC_CV)

#    import matplotlib.pyplot as plt
#    x = numPathsList
#    plt.figure(figsize=(8,6))
#    plt.plot(x,valuesGeometric,label="Geometric")
#    plt.plot(x,valuesTurnbull,label="Turbull_Wakeman")
#    plt.plot(x,valuesCurran,label="Curran")
#    plt.plot(x,valuesMC_fast,label="MC_Fast")
#    plt.plot(x,valuesMC_CV,label="MC_CV")
#    plt.legend()
#    plt.xlabel("Number of Paths")
#    plt.show()

###############################################################################


def testTimeEvolution():

    startAveragingDate = TuringDate(2015, 1, 1)
    expiryDate = TuringDate(2016, 1, 1)
    stockPrice = 100.0
    volatility = 0.20
    interestRate = 0.30
    dividendYield = 0.10
    numObservations = 100  # weekly as we have a year
    accruedAverage = None
    K = 100
    seed = 1976

    model = TuringModelBlackScholes(volatility)

    asianOption = TuringEquityAsianOption(startAveragingDate,
                                          expiryDate,
                                          K,
                                          TuringOptionTypes.EUROPEAN_CALL,
                                          numObservations)

    testCases.header(
        "Date",
        "Geometric",
        "Turnbull_Wakeman",
        "Curran",
        "FastMC",
        "FastMC_CV")

    valuesTurnbull = []
    valuesCurran = []
    valuesGeometric = []
    valuesMC_fast = []
    valuesMC_CV = []

    valueDates = []
    valueDates.append(TuringDate(2014, 4, 1))
    valueDates.append(TuringDate(2014, 6, 1))
    valueDates.append(TuringDate(2014, 8, 1))
    valueDates.append(TuringDate(2015, 2, 1))
    valueDates.append(TuringDate(2015, 4, 1))
    valueDates.append(TuringDate(2015, 6, 1))
    valueDates.append(TuringDate(2015, 8, 1))

    numPaths = 10000

    for valueDate in valueDates:

        accruedAverage = stockPrice * 0.9

        discountCurve = TuringDiscountCurveFlat(valueDate, interestRate)
        dividendCurve = TuringDiscountCurveFlat(valueDate, dividendYield)

        valueMC_fast = asianOption._valueMC_fast(valueDate,
                                                 stockPrice,
                                                 discountCurve,
                                                 dividendCurve,
                                                 model,
                                                 numPaths,
                                                 seed,
                                                 accruedAverage)

        valueMC_CV = asianOption.valueMC(valueDate,
                                         stockPrice,
                                         discountCurve,
                                         dividendCurve,
                                         model,
                                         numPaths,
                                         seed,
                                         accruedAverage)

        valueGeometric = asianOption.value(valueDate,
                                           stockPrice,
                                           discountCurve,
                                           dividendCurve,
                                           model,
                                           TuringAsianOptionValuationMethods.GEOMETRIC,
                                           accruedAverage)

        valueTurnbullWakeman = asianOption.value(valueDate,
                                                 stockPrice,
                                                 discountCurve,
                                                 dividendCurve,
                                                 model,
                                                 TuringAsianOptionValuationMethods.TURNBULL_WAKEMAN,
                                                 accruedAverage)

        valueCurran = asianOption.value(valueDate,
                                        stockPrice,
                                        discountCurve,
                                        dividendCurve,
                                        model,
                                        TuringAsianOptionValuationMethods.CURRAN,
                                        accruedAverage)

        valuesGeometric.append(valueGeometric)
        valuesTurnbull.append(valueTurnbullWakeman)
        valuesCurran.append(valueCurran)
        valuesMC_fast.append(valueMC_fast)
        valuesMC_CV.append(valueMC_CV)

        testCases.print(
            str(valueDate),
            valueGeometric,
            valueTurnbullWakeman,
            valueCurran,
            valueMC_fast,
            valueMC_CV)

#    import matplotlib.pyplot as plt
#    x = [ dt.date() for dt in valueDates]
#
#    plt.figure(figsize=(8,6))
#    plt.plot(x,valuesGeometric,label="Geometric")
#    plt.plot(x,valuesTurnbull,label="Turbull_Wakeman")
#    plt.plot(x,valuesCurran,label="Curran")
#    plt.plot(x,valuesMC_fast,label="MC_Fast")
#    plt.plot(x,valuesMC_CV,label="MC_CV")
#    plt.legend()
#    plt.xlabel("Valuation Date")
#    plt.show()

##########################################################################


def testMCTimings():

    valueDate = TuringDate(2014, 1, 1)
    startAveragingDate = TuringDate(2014, 6, 1)
    expiryDate = TuringDate(2015, 1, 1)
    stockPrice = 100.0
    volatility = 0.20
    interestRate = 0.30
    dividendYield = 0.10
    numObservations = 120  # daily as we have a half year
    accruedAverage = None
    K = 100
    seed = 1976

    model = TuringModelBlackScholes(volatility)
    discountCurve = TuringDiscountCurveFlat(valueDate, interestRate)
    dividendCurve = TuringDiscountCurveFlat(valueDate, dividendYield)

    asianOption = TuringEquityAsianOption(startAveragingDate,
                                          expiryDate,
                                          K,
                                          TuringOptionTypes.EUROPEAN_CALL,
                                          numObservations)

    testCases.header(
        "NUMPATHS",
        "VALUE",
        "TIME",
        "VALUE_MC",
        "TIME",
        "VALUE_MC_CV",
        "TIME")

    valuesMC = []
    valuesMC_fast = []
    valuesMC_fast_CV = []

    tvaluesMC = []
    tvaluesMC_fast = []
    tvaluesMC_fast_CV = []

    numPathsList = [5000]

    for numPaths in numPathsList:

        accruedAverage = stockPrice * 1.1

        start = time.time()
        valueMC = asianOption.valueMC(valueDate,
                                      stockPrice,
                                      discountCurve,
                                      dividendCurve,
                                      model,
                                      numPaths,
                                      seed,
                                      accruedAverage)

        end = time.time()
        t_MC = end - start

        start = time.time()
        valueMC_fast = asianOption._valueMC_fast(valueDate,
                                                 stockPrice,
                                                 discountCurve,
                                                 dividendCurve,
                                                 model,
                                                 numPaths,
                                                 seed,
                                                 accruedAverage)

        end = time.time()
        t_MC_fast = end - start

        start = time.time()
        valueMC_fast_CV = asianOption.valueMC(valueDate,
                                              stockPrice,
                                              discountCurve,
                                              dividendCurve,
                                              model,
                                              numPaths,
                                              seed,
                                              accruedAverage)

        end = time.time()
        t_MC_fast_CV = end - start

        valuesMC.append(valueMC)
        valuesMC_fast.append(valueMC_fast)
        valuesMC_fast_CV.append(valueMC_fast_CV)

        tvaluesMC.append(t_MC)
        tvaluesMC_fast.append(t_MC_fast)
        tvaluesMC_fast_CV.append(t_MC_fast_CV)

        testCases.print(
            numPaths,
            valueMC,
            t_MC,
            valueMC_fast,
            t_MC_fast,
            valueMC_fast_CV,
            t_MC_fast_CV)

#    import matplotlib.pyplot as plt
#    x = numPathsList
#    plt.figure(figsize=(8,6))
#    plt.plot(x,valuesMC,label="Basic MC")
#    plt.plot(x,valuesMC_fast,label="MC_Fast")
#    plt.plot(x,valuesMC_fast_CV,label="MC_Fast CV")
#    plt.legend()
#    plt.xlabel("Number of Paths")
#    plt.show()


testConvergence()
testMCTimings()
testTimeEvolution()
testCases.compareTestCases()
