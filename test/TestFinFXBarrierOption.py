import sys
sys.path.append("..")

from turing_models.models.process_simulator import TuringProcessTypes
from turing_models.models.process_simulator import TuringGBMNumericalScheme
from turing_models.models.model_black_scholes import TuringModelBlackScholes
from turing_models.products.fx.fx_barrier_option import TuringFXBarrierTypes
from turing_models.products.fx.fx_barrier_option import TuringFXBarrierOption
from fundamental.market.curves.discount_curve_flat import TuringDiscountCurveFlat
from turing_models.utilities.turing_date import TuringDate

from TuringTestCases import TuringTestCases, globalTestCaseMode
testCases = TuringTestCases(__file__, globalTestCaseMode)

###############################################################################

def test_FinFXBarrierOption():

    valueDate = TuringDate(2015, 1, 1)
    expiryDate = TuringDate(2016, 1, 1)
    spotFXRate = 100.0
    currencyPair = "USDJPY"
    volatility = 0.20
    domInterestRate = 0.05
    forInterestRate = 0.02
    optionType = TuringFXBarrierTypes.DOWN_AND_OUT_CALL
    notional = 100.0
    notionalCurrency = "USD"

    drift = domInterestRate - forInterestRate
    scheme = TuringGBMNumericalScheme.ANTITHETIC
    processType = TuringProcessTypes.GBM
    domDiscountCurve = TuringDiscountCurveFlat(valueDate, domInterestRate)
    forDiscountCurve = TuringDiscountCurveFlat(valueDate, forInterestRate)
    model = TuringModelBlackScholes(volatility)

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
