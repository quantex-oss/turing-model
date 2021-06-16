# TODO
import time
import numpy as np

import sys
sys.path.append("..")

from turing_models.products.bonds.bond_convertible import TuringBondConvertible
from turing_models.utilities.turing_date import TuringDate
from turing_models.utilities.frequency import TuringFrequencyTypes
from turing_models.utilities.day_count import TuringDayCountTypes
from fundamental.market.curves.discount_curve_flat import TuringDiscountCurveFlat

from TuringTestCases import TuringTestCases, globalTestCaseMode
testCases = TuringTestCases(__file__, globalTestCaseMode)

###############################################################################


def test_FinBondConvertible():

    settlementDate = TuringDate(2003, 12, 31)
    startConvertDate = TuringDate(2003, 12, 31)
    maturityDate = TuringDate(2022, 3, 15)
    conversionRatio = 38.4615  # adjust for face
    coupon = 0.0575
    freqType = TuringFrequencyTypes.SEMI_ANNUAL
    accrualBasis = TuringDayCountTypes.ACT_365F
    face = 1000.0

    callPrice = 1100
    callDates = [TuringDate(2007, 3, 20),
                 TuringDate(2012, 3, 15),
                 TuringDate(2017, 3, 15)]
    callPrices = np.array([callPrice, callPrice, callPrice])

    putPrice = 90
    putDates = [TuringDate(2007, 3, 20),
                TuringDate(2012, 3, 15),
                TuringDate(2017, 3, 15)]
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

    dividendDates = [TuringDate(2007, 3, 20),
                     TuringDate(2008, 3, 15),
                     TuringDate(2009, 3, 15),
                     TuringDate(2010, 3, 15),
                     TuringDate(2011, 3, 15),
                     TuringDate(2012, 3, 15),
                     TuringDate(2013, 3, 15),
                     TuringDate(2014, 3, 15),
                     TuringDate(2015, 3, 15),
                     TuringDate(2016, 3, 15),
                     TuringDate(2017, 3, 15),
                     TuringDate(2018, 3, 15),
                     TuringDate(2019, 3, 15),
                     TuringDate(2020, 3, 15),
                     TuringDate(2021, 3, 15),
                     TuringDate(2022, 3, 15)]

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
