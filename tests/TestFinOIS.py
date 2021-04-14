###############################################################################
# Copyright (C) 2018, 2019, 2020 Dominic O'Kane
###############################################################################

import sys
sys.path.append("..")

from turingmodel.turingutils.turing_math import ONE_MILLION
from turingmodel.products.rates.turing_ois import TuringOIS
from turingmodel.market.curves.turing_discount_curve_flat import TuringDiscountCurveFlat
from turingmodel.turingutils.turing_frequency import TuringFrequencyTypes
from turingmodel.turingutils.turing_day_count import TuringDayCountTypes
from turingmodel.turingutils.turing_date import TuringDate
from turingmodel.turingutils.turing_global_types import TuringSwapTypes

from TuringTestCases import TuringTestCases, globalTestCaseMode
testCases = TuringTestCases(__file__, globalTestCaseMode)

###############################################################################

def test_FinFixedOIS():

    # Here I follow the example in
    # https://blog.deriscope.com/index.php/en/excel-quantlib-overnight-index-swap

    effectiveDate = TuringDate(30, 11, 2018)
    endDate = TuringDate(30, 11, 2023)

    endDate = effectiveDate.addMonths(60)
    oisRate = 0.04
    fixedLegType = TuringSwapTypes.PAY
    fixedFreqType = TuringFrequencyTypes.ANNUAL
    fixedDayCount = TuringDayCountTypes.ACT_360
    floatFreqType = TuringFrequencyTypes.ANNUAL
    floatDayCount = TuringDayCountTypes.ACT_360
    floatSpread = 0.0
    notional = ONE_MILLION
    paymentLag = 1
    
    ois = TuringOIS(effectiveDate,
                    endDate,
                    fixedLegType,
                    oisRate,
                    fixedFreqType,
                    fixedDayCount,
                    notional,
                    paymentLag,
                    floatSpread,
                    floatFreqType,
                    floatDayCount)

#    print(ois)

    valueDate = effectiveDate
    marketRate = 0.05
    oisCurve = TuringDiscountCurveFlat(valueDate, marketRate,
                                       TuringFrequencyTypes.ANNUAL)

    v = ois.value(effectiveDate, oisCurve)
    
#    print(v)
    
#    ois._fixedLeg.printValuation()
#    ois._floatLeg.printValuation()
    
    testCases.header("LABEL", "VALUE")
    testCases.print("SWAP_VALUE", v)
    
###############################################################################

test_FinFixedOIS()
testCases.compareTestCases()
