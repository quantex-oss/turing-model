###############################################################################
# Copyright (C) 2018, 2019, 2020 Dominic O'Kane
###############################################################################

# TODO
import time
import numpy as np

import sys
sys.path.append("..")

from financepy.products.bonds.turing_bond_convertible import TuringBondConvertible
from financepy.turingutils.turing_date import TuringDate
from financepy.turingutils.turing_frequency import TuringFrequencyTypes
from financepy.turingutils.turing_day_count import TuringDayCountTypes
from financepy.market.curves.turing_discount_curve_flat import TuringDiscountCurveFlat

from TuringTestCases import TuringTestCases, globalTestCaseMode
testCases = TuringTestCases(__file__, globalTestCaseMode)

###############################################################################


def test_FinBondConvertible():

    settlementDate = TuringDate(31, 12, 2003)
    startConvertDate = TuringDate(31, 12, 2003)
    maturityDate = TuringDate(15, 3, 2022)
    conversionRatio = 38.4615  # adjust for face
    coupon = 0.0575
    freqType = TuringFrequencyTypes.SEMI_ANNUAL
    accrualBasis = TuringDayCountTypes.ACT_365F
    face = 1000.0

    callPrice = 1100
    callDates = [TuringDate(20, 3, 2007),
                 TuringDate(15, 3, 2012),
                 TuringDate(15, 3, 2017)]
    callPrices = np.array([callPrice, callPrice, callPrice])

    putPrice = 90
    putDates = [TuringDate(20, 3, 2007),
                TuringDate(15, 3, 2012),
                TuringDate(15, 3, 2017)]
    putPrices = np.array([putPrice, putPrice, putPrice])

    bond = TuringBondConvertible(maturityDate,
                                 coupon,
                                 freqType,
                                 startConvertDate,
                                 conversionRatio,
                                 callDates,
                                 callPrices,
                                 putDates,
                                 putPrices,
                                 accrualBasis,
                                 face)
#    print(bond)

    dividendDates = [TuringDate(20, 3, 2007),
                     TuringDate(15, 3, 2008),
                     TuringDate(15, 3, 2009),
                     TuringDate(15, 3, 2010),
                     TuringDate(15, 3, 2011),
                     TuringDate(15, 3, 2012),
                     TuringDate(15, 3, 2013),
                     TuringDate(15, 3, 2014),
                     TuringDate(15, 3, 2015),
                     TuringDate(15, 3, 2016),
                     TuringDate(15, 3, 2017),
                     TuringDate(15, 3, 2018),
                     TuringDate(15, 3, 2019),
                     TuringDate(15, 3, 2020),
                     TuringDate(15, 3, 2021),
                     TuringDate(15, 3, 2022)]

    dividendYields = [0.00] * 16
    stockPrice = 28.5
    stockVolatility = 0.370
    rate = 0.04
    discountCurve = TuringDiscountCurveFlat(settlementDate,
                                            rate,
                                            TuringFrequencyTypes.CONTINUOUS)
    creditSpread = 0.00
    recoveryRate = 0.40
    numStepsPerYear = 20

    testCases.header("LABEL")
    testCases.print("NO CALLS OR PUTS")

    testCases.header("TIME", "NUMSTEPS", "PRICE")

    for numStepsPerYear in [5, 10, 20, 80]:
        start = time.time()
        res = bond.value(settlementDate,
                         stockPrice,
                         stockVolatility,
                         dividendDates,
                         dividendYields,
                         discountCurve,
                         creditSpread,
                         recoveryRate,
                         numStepsPerYear)

        end = time.time()
        period = end - start
        testCases.print(period, numStepsPerYear, res)

    dividendYields = [0.02] * 16
    testCases.header("LABEL")
    testCases.print("DIVIDENDS")

    testCases.header("TIME", "NUMSTEPS", "PRICE")
    for numStepsPerYear in [5, 20, 80]:
        start = time.time()
        res = bond.value(settlementDate,
                         stockPrice,
                         stockVolatility,
                         dividendDates,
                         dividendYields,
                         discountCurve,
                         creditSpread,
                         recoveryRate,
                         numStepsPerYear)
        end = time.time()
        period = end - start
        testCases.print(period, numStepsPerYear, res)

###############################################################################

test_FinBondConvertible()
testCases.compareTestCases()
