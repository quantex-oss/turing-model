###############################################################################
# Copyright (C) 2018, 2019, 2020 Dominic O'Kane
###############################################################################

import numpy as np

import sys
sys.path.append("..")

from turing_models.turingutils.turing_date import TuringDate
from turing_models.market.volatility.turing_equity_vol_curve import TuringEquityVolCurve
from turing_models.products.equity.turing_equity_variance_swap import TuringEquityVarianceSwap
from turing_models.market.curves.turing_discount_curve_flat import TuringDiscountCurveFlat

from TuringTestCases import TuringTestCases, globalTestCaseMode
testCases = TuringTestCases(__file__, globalTestCaseMode)

###############################################################################


def volSkew(K, atmVol, atmK, skew):
    v = atmVol + skew * (K-atmK)
    return v

###############################################################################


def test_FinEquityVarianceSwap():

    startDate = TuringDate(20, 3, 2018)
    tenor = "3M"
    strike = 0.3*0.3

    volSwap = TuringEquityVarianceSwap(startDate, tenor, strike)

    valuationDate = TuringDate(20, 3, 2018)
    stockPrice = 100.0
    dividendYield = 0.0
    dividendCurve = TuringDiscountCurveFlat(valuationDate, dividendYield)

    maturityDate = startDate.addMonths(3)

    atmVol = 0.20
    atmK = 100.0
    skew = -0.02/5.0  # defined as dsigma/dK
    strikes = np.linspace(50.0, 135.0, 18)
    vols = volSkew(strikes, atmVol, atmK, skew)
    volCurve = TuringEquityVolCurve(valuationDate, maturityDate, strikes, vols)

    strikeSpacing = 5.0
    numCallOptions = 10
    numPutOptions = 10
    r = 0.05

    discountCurve = TuringDiscountCurveFlat(valuationDate, r)

    useForward = False

    testCases.header("LABEL", "VALUE")

    k1 = volSwap.fairStrike(valuationDate, stockPrice, dividendCurve,
                            volCurve, numCallOptions, numPutOptions,
                            strikeSpacing, discountCurve, useForward)

    testCases.print("REPLICATION VARIANCE:", k1)

    k2 = volSwap.fairStrikeApprox(valuationDate, stockPrice, strikes, vols)
    testCases.print("DERMAN SKEW APPROX for K:", k2)

##########################################################################


test_FinEquityVarianceSwap()
testCases.compareTestCases()
