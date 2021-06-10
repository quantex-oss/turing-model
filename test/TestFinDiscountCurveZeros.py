import time
import numpy as np

import sys
sys.path.append("..")

from turing_models.utilities.day_count import TuringDayCountTypes
from turing_models.utilities.frequency import TuringFrequencyTypes
from turing_models.utilities.turing_date import TuringDate
from fundamental.market.curves.interpolator import TuringInterpTypes
from fundamental.market.curves.discount_curve_zeros import TuringDiscountCurveZeros

from TuringTestCases import TuringTestCases, globalTestCaseMode
testCases = TuringTestCases(__file__, globalTestCaseMode)

###############################################################################

def test_FinDiscountCurveZeros():

    startDate = TuringDate(2018, 1, 1)
    times = np.linspace(1.0, 10.0, 10)
    dates = startDate.addYears(times)
    zeroRates = np.linspace(5.0, 6.0, 10)/100
    freqType = TuringFrequencyTypes.ANNUAL
    dayCountType = TuringDayCountTypes.ACT_ACT_ISDA

    curve = TuringDiscountCurveZeros(startDate,
                                     dates,
                                     zeroRates,
                                     freqType,
                                     dayCountType,
                                     TuringInterpTypes.FLAT_FWD_RATES)

    testCases.header("T", "DF")

    years = np.linspace(0, 10, 21)
    dates = startDate.addYears(years)
    for dt in dates:
        df = curve.df(dt)
        testCases.print(dt, df)

#    print(curve)

###############################################################################

    numRepeats = 100

    start = time.time()

    for i in range(0, numRepeats):
        freqType = TuringFrequencyTypes.ANNUAL
        dayCountType = TuringDayCountTypes.ACT_ACT_ISDA

        dates = [TuringDate(2016, 6, 14), TuringDate(2016, 9, 14),
                 TuringDate(2016, 12, 14), TuringDate(2017, 6, 14),
                 TuringDate(2019, 6, 14), TuringDate(2021, 6, 14),
                 TuringDate(2026, 6, 15), TuringDate(2031, 6, 16),
                 TuringDate(2036, 6, 16), TuringDate(2046, 6, 14)]

        zeroRates = [0.000000, 0.006616, 0.007049, 0.007795,
                     0.009599, 0.011203, 0.015068, 0.017583,
                     0.018998, 0.020080]

        startDate = dates[0]

        curve = TuringDiscountCurveZeros(startDate,
                                         dates,
                                         zeroRates,
                                         freqType,
                                         dayCountType,
                                         TuringInterpTypes.FLAT_FWD_RATES)

    end = time.time()
    period = end - start
#    print("Time taken:", period)

#    print(curve)

###############################################################################


test_FinDiscountCurveZeros()
testCases.compareTestCases()
