import numpy as np

import sys
sys.path.append("..")

from turing_models.utilities.turing_date import TuringDate
from turing_models.utilities.global_types import TuringOptionTypes
from turing_models.products.fx.fx_vanilla_option import TuringFXVanillaOption
from turing_models.models.model_black_scholes import TuringModelBlackScholes
from fundamental.market.curves.discount_curve_flat import TuringDiscountCurveFlat

from TuringTestCases import TuringTestCases, globalTestCaseMode
testCases = TuringTestCases(__file__, globalTestCaseMode)

##########################################################################

def test_FinFXAmericanOption():

    # There is no FXAmericanOption class. It is embedded in the FXVanillaOption
    # class. This test just compares it to the European

    valueDate = TuringDate(2018, 2, 13)
    expiryDate = TuringDate(2019, 2, 13)

    # In BS the FX rate is the price in domestic of one unit of foreign
    # In case of EURUSD = 1.3 the domestic currency is USD and foreign is EUR
    # DOM = USD , FOR = EUR
    ccy1 = "EUR"
    ccy2 = "USD"
    ccy1CCRate = 0.030  # EUR
    ccy2CCRate = 0.025  # USD

    currencyPair = ccy1 + ccy2  # Always ccy1ccy2
    spotFXRate = 1.20
    strikeFXRate = 1.250
    volatility = 0.10

    domDiscountCurve = TuringDiscountCurveFlat(valueDate, ccy2CCRate)
    forDiscountCurve = TuringDiscountCurveFlat(valueDate, ccy1CCRate)

    model = TuringModelBlackScholes(volatility)

    # Two examples to show that changing the notional currency and notional
    # keeps the value unchanged

    testCases.header("SPOT FX RATE", "VALUE_BS", "VOL_IN", "IMPLD_VOL")

    spotFXRates = np.arange(50, 200, 10)/100.0

    for spotFXRate in spotFXRates:

        callOption = TuringFXVanillaOption(expiryDate,
                                           strikeFXRate,
                                           currencyPair,
                                           TuringOptionTypes.EUROPEAN_CALL,
                                           1000000,
                                        "USD")

        valueEuropean = callOption.value(valueDate,
                                         spotFXRate,
                                         domDiscountCurve,
                                         forDiscountCurve,
                                         model)['v']

        callOption = TuringFXVanillaOption(expiryDate,
                                           strikeFXRate,
                                        "EURUSD",
                                           TuringOptionTypes.AMERICAN_CALL,
                                           1000000,
                                        "USD")

        valueAmerican = callOption.value(valueDate,
                                         spotFXRate,
                                         domDiscountCurve,
                                         forDiscountCurve,
                                         model)['v']

        diff = (valueAmerican - valueEuropean)
        testCases.print(spotFXRate, valueEuropean, valueAmerican, diff)

    for spotFXRate in spotFXRates:

        callOption = TuringFXVanillaOption(expiryDate,
                                           strikeFXRate,
                                        "EURUSD",
                                           TuringOptionTypes.EUROPEAN_PUT,
                                           1000000,
                                        "USD")

        valueEuropean = callOption.value(valueDate,
                                         spotFXRate,
                                         domDiscountCurve,
                                         forDiscountCurve,
                                         model)['v']

        callOption = TuringFXVanillaOption(expiryDate,
                                           strikeFXRate,
                                        "EURUSD",
                                           TuringOptionTypes.AMERICAN_PUT,
                                           1000000,
                                        "USD")

        valueAmerican = callOption.value(valueDate,
                                         spotFXRate,
                                         domDiscountCurve,
                                         forDiscountCurve,
                                         model)['v']

        diff = (valueAmerican - valueEuropean)
        testCases.print(spotFXRate, valueEuropean, valueAmerican, diff)

###############################################################################

test_FinFXAmericanOption()
testCases.compareTestCases()
