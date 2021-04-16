import sys
sys.path.append("..")

from turing_models.utilities.math import ONE_MILLION
from turing_models.utilities.global_types import TuringSwapTypes
from turing_models.utilities.calendar import TuringBusDayAdjustTypes
from turing_models.utilities.calendar import TuringDateGenRuleTypes
from turing_models.utilities.day_count import TuringDayCountTypes
from turing_models.utilities.amount import TuringAmount
from turing_models.utilities.frequency import TuringFrequencyTypes
from turing_models.utilities.calendar import TuringCalendarTypes
from turing_models.utilities.date import TuringDate
from turing_models.products.rates.fixed_leg import TuringFixedLeg
from turing_models.products.rates.float_leg import TuringFloatLeg
from turing_models.market.curves.discount_curve_flat import TuringDiscountCurveFlat

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

    swapFixedLeg = TuringFixedLeg(effectiveDate,
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

    swapFixedLeg = TuringFixedLeg(effectiveDate,
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

    swapFloatLeg = TuringFloatLeg(effectiveDate,
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

    swapFloatLeg = TuringFloatLeg(effectiveDate,
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
