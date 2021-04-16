import sys
sys.path.append("..")

import numpy as np
import matplotlib.pyplot as plt

from turing_models.market.curves.discount_curve_flat import TuringDiscountCurveFlat
from turing_models.utilities.date import TuringDate

from turing_models.models.model_volatility_fns import TuringVolFunctionTypes
from turing_models.models.model_volatility_fns import volFunctionClark

from turing_models.models.model_black_scholes import TuringModelBlackScholes
from turing_models.models.model_option_implied_dbn import optionImpliedDbn

from turing_models.market.volatility.fx_vol_surface import TuringFXVolSurface
from turing_models.market.volatility.fx_vol_surface import TuringFXATMMethod
from turing_models.market.volatility.fx_vol_surface import TuringFXDeltaMethod


from TuringTestCases import TuringTestCases, globalTestCaseMode
testCases = TuringTestCases(__file__, globalTestCaseMode)

###############################################################################


def test_FinOptionImpliedDbn():

    if 1 == 1:

        # Example from Book extract by Iain Clark using Tables 3.3 and 3.4
        # print("EURUSD EXAMPLE CLARK")

        valueDate = TuringDate(10, 4, 2020)

        forName = "EUR"
        domName = "USD"
        forCCRate = 0.03460  # EUR
        domCCRate = 0.02940  # USD

        domDiscountCurve = TuringDiscountCurveFlat(valueDate, domCCRate)
        forDiscountCurve = TuringDiscountCurveFlat(valueDate, forCCRate)

        currencyPair = forName + domName
        spotFXRate = 1.3465

        tenors = ['1M', '2M', '3M', '6M', '1Y', '2Y']
        atmVols = [21.00, 21.00, 20.750, 19.400, 18.250, 17.677]
        marketStrangle25DeltaVols = [0.65, 0.75, 0.85, 0.90, 0.95, 0.85]
        riskReversal25DeltaVols = [-0.20, -0.25, -0.30, -0.50, -0.60, -0.562]

        notionalCurrency = forName

        atmMethod = TuringFXATMMethod.FWD_DELTA_NEUTRAL
        deltaMethod = TuringFXDeltaMethod.SPOT_DELTA

        fxMarket = TuringFXVolSurface(valueDate,
                                      spotFXRate,
                                      currencyPair,
                                      notionalCurrency,
                                      domDiscountCurve,
                                      forDiscountCurve,
                                      tenors,
                                      atmVols,
                                      marketStrangle25DeltaVols,
                                      riskReversal25DeltaVols,
                                      atmMethod,
                                      deltaMethod)

#        fxMarket.checkCalibration(True)

        PLOT_GRAPHS = False
        if PLOT_GRAPHS:
            fxMarket.plotVolCurves()
 
        for iTenor in range(0, len(fxMarket._tenors)):
            
            F = fxMarket._F0T[iTenor]
            texp = fxMarket._texp[iTenor]

            startFX = F * 0.05
            endFX = F * 5.0

            numSteps = 10000
            dFX = (endFX - startFX)/ numSteps

            domDF = domDiscountCurve._df(texp)
            forDF = forDiscountCurve._df(texp)

            rd = -np.log(domDF) / texp
            rf = -np.log(forDF) / texp

            params = fxMarket._parameters[iTenor]

            strikes = []
            vols = []

            for iK in range(0, numSteps):
                strike = startFX + iK*dFX                
                vol = volFunctionClark(params, F, strike, texp)
                strikes.append(strike) 
                vols.append(vol)
            
            strikes = np.array(strikes)
            vols = np.array(vols)

            dbn = optionImpliedDbn(spotFXRate, texp, rd, rf, strikes, vols)
            
#            print("SUM:", dbn.sum())
#            plt.figure()
#            plt.plot(dbn._x, dbn._densitydx)

###############################################################################


test_FinOptionImpliedDbn()
testCases.compareTestCases()
