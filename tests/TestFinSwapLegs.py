###############################################################################
# Copyright (C) 2018, 2019, 2020 Dominic O'Kane
###############################################################################

import sys
sys.path.append("..")

from turingmodel.turingutils.turing_math import ONE_MILLION
from turingmodel.turingutils.turing_global_types import TuringSwapTypes
from turingmodel.turingutils.turing_calendar import TuringBusDayAdjustTypes
from turingmodel.turingutils.turing_calendar import TuringDateGenRuleTypes
from turingmodel.turingutils.turing_day_count import TuringDayCountTypes
from turingmodel.turingutils.turing_amount import TuringAmount
from turingmodel.turingutils.turing_frequency import TuringFrequencyTypes
from turingmodel.turingutils.turing_calendar import TuringCalendarTypes
from turingmodel.turingutils.turing_date import TuringDate
from turingmodel.products.rates.turing_fixed_leg import FinFixedLeg
from turingmodel.products.rates.turing_float_leg import FinFloatLeg
from turingmodel.market.curves.turing_discount_curve_flat import TuringDiscountCurveFlat

from TuringTestCases import TuringTestCases, globalTestCaseMode
testCases = TuringTestCases(__file__, globalTestCaseMode)

###############################################################################


def test_FinFixedIborSwapLeg():

    effectiveDate = TuringDate(28, 10, 2020)
    maturityDate = TuringDate(28, 10, 2025)
    
    coupon = -0.44970/100.0
    freqType = TuringFrequencyTypes.ANNUAL
    dayCountType = TuringDayCountTypes.THIRTY_360_BOND
    notional = 10.0 * ONE_MILLION
    legPayRecType = TuringSwapTypes.PAY
    calendarType = TuringCalendarTypes.TARGET
    busDayAdjustType = TuringBusDayAdjustTypes.FOLLOWING
    dateGenRuleType = TuringDateGenRuleTypes.BACKWARD
    paymentLag = 0
    principal = 0.0

    swapFixedLeg = FinFixedLeg(effectiveDate,
                               maturityDate,
                               legPayRecType,
                               coupon,
                               freqType,
                               dayCountType,
                               notional,
                               principal,
                               paymentLag,
                               calendarType,
                               busDayAdjustType,
                               dateGenRuleType)

###############################################################################

def test_FinFixedOISSwapLeg():

    effectiveDate = TuringDate(28, 10, 2020)
    maturityDate = TuringDate(28, 10, 2025)
    
    coupon = -0.515039/100.0
    freqType = TuringFrequencyTypes.ANNUAL
    dayCountType = TuringDayCountTypes.ACT_360
    notional = 10.0 * ONE_MILLION
    legPayRecType = TuringSwapTypes.PAY
    calendarType = TuringCalendarTypes.TARGET
    busDayAdjustType = TuringBusDayAdjustTypes.FOLLOWING
    dateGenRuleType = TuringDateGenRuleTypes.BACKWARD
    paymentLag = 1
    principal = 0.0

    swapFixedLeg = FinFixedLeg(effectiveDate,
                                  maturityDate,
                                  legPayRecType,
                                  coupon,
                                  freqType,
                                  dayCountType,
                                  notional,
                                  principal,
                                  paymentLag,
                                  calendarType,
                                  busDayAdjustType,
                                  dateGenRuleType)

###############################################################################

def test_FinFloatIborLeg():

    effectiveDate = TuringDate(28, 10, 2020)
    maturityDate = TuringDate(28, 10, 2025)
    
    spread = 0.0
    freqType = TuringFrequencyTypes.ANNUAL
    dayCountType = TuringDayCountTypes.THIRTY_360_BOND
    notional = 10.0 * ONE_MILLION
    legPayRecType = TuringSwapTypes.PAY
    calendarType = TuringCalendarTypes.TARGET
    busDayAdjustType = TuringBusDayAdjustTypes.FOLLOWING
    dateGenRuleType = TuringDateGenRuleTypes.BACKWARD
    paymentLag = 0
    principal = 0.0

    swapFloatLeg = FinFloatLeg(effectiveDate,
                               maturityDate,
                               legPayRecType,
                               spread,
                               freqType,
                               dayCountType,
                               notional,
                               principal,
                               paymentLag,
                               calendarType,
                               busDayAdjustType,
                               dateGenRuleType)

    liborCurve = TuringDiscountCurveFlat(effectiveDate, 0.05)

    firstFixing = 0.03

    v = swapFloatLeg.value(effectiveDate, liborCurve, liborCurve, 
                           firstFixing)


###############################################################################

def test_FinFloatOISLeg():

    effectiveDate = TuringDate(28, 10, 2020)
    maturityDate = TuringDate(28, 10, 2025)
    
    spread = 0.0
    freqType = TuringFrequencyTypes.ANNUAL
    dayCountType = TuringDayCountTypes.ACT_360
    notional = 10.0 * ONE_MILLION
    legPayRecType = TuringSwapTypes.PAY
    calendarType = TuringCalendarTypes.TARGET
    busDayAdjustType = TuringBusDayAdjustTypes.FOLLOWING
    dateGenRuleType = TuringDateGenRuleTypes.BACKWARD
    paymentLag = 1
    principal = 0.0

    swapFloatLeg = FinFloatLeg(effectiveDate,
                                  maturityDate,
                                  legPayRecType,
                                  spread,
                                  freqType,
                                  dayCountType,
                                  notional,
                                  principal,
                                  paymentLag,
                                  calendarType,
                                  busDayAdjustType,
                                  dateGenRuleType)

    liborCurve = TuringDiscountCurveFlat(effectiveDate, 0.05)

    firstFixing = 0.03

    v = swapFloatLeg.value(effectiveDate, liborCurve, liborCurve, 
                           firstFixing)

###############################################################################

# Ibor Swap
test_FinFixedIborSwapLeg()
test_FinFloatIborLeg()

# OIS Swap
test_FinFixedOISSwapLeg()
test_FinFloatOISLeg()

testCases.compareTestCases()
