import sys
import numpy as np
sys.path.append("..")

from turing_models.utilities.math import ONE_MILLION
from turing_models.products.rates.ibor_single_curve import TuringIborSingleCurve
from turing_models.products.rates.ibor_swap import TuringIborSwap
from turing_models.products.rates.ibor_fra import TuringIborFRA
from turing_models.products.rates.ibor_deposit import TuringIborDeposit
from turing_models.utilities.calendar import TuringBusDayAdjustTypes
from turing_models.utilities.calendar import TuringDateGenRuleTypes
from turing_models.utilities.calendar import TuringCalendarTypes
from turing_models.utilities.frequency import TuringFrequencyTypes
from turing_models.utilities.day_count import TuringDayCountTypes
from turing_models.utilities.date import TuringDate
from turing_models.utilities.global_types import TuringSwapTypes
from turing_models.market.curves.discount_curve import TuringDiscountCurve
from turing_models.market.curves.interpolator import TuringInterpTypes

from TuringTestCases import TuringTestCases, globalTestCaseMode
testCases = TuringTestCases(__file__, globalTestCaseMode)

###############################################################################


def buildIborSingleCurve(valuationDate):

    settlementDate = valuationDate.addDays(2)
    dcType = TuringDayCountTypes.ACT_360

    depos = []
    fras = []
    swaps = []

    maturityDate = settlementDate.addMonths(1)
    depo1 = TuringIborDeposit(valuationDate, maturityDate, -0.00251, dcType)
    depos.append(depo1)

    # Series of 1M futures
    startDate = settlementDate.nextIMMDate()
    endDate = startDate.addMonths(1)
    fra = TuringIborFRA(startDate, endDate, -0.0023, dcType)
    fras.append(fra)

    startDate = startDate.addMonths(1)
    endDate = startDate.addMonths(1)
    fra = TuringIborFRA(startDate, endDate, -0.00234, dcType)
    fras.append(fra)

    startDate = startDate.addMonths(1)
    endDate = startDate.addMonths(1)
    fra = TuringIborFRA(startDate, endDate, -0.00225, dcType)
    fras.append(fra)

    startDate = startDate.addMonths(1)
    endDate = startDate.addMonths(1)
    fra = TuringIborFRA(startDate, endDate, -0.00226, dcType)
    fras.append(fra)

    startDate = startDate.addMonths(1)
    endDate = startDate.addMonths(1)
    fra = TuringIborFRA(startDate, endDate, -0.00219, dcType)
    fras.append(fra)

    startDate = startDate.addMonths(1)
    endDate = startDate.addMonths(1)
    fra = TuringIborFRA(startDate, endDate, -0.00213, dcType)
    fras.append(fra)

    startDate = startDate.addMonths(1)
    endDate = startDate.addMonths(1)
    fra = TuringIborFRA(startDate, endDate, -0.00186, dcType)
    fras.append(fra)

    startDate = startDate.addMonths(1)
    endDate = startDate.addMonths(1)
    fra = TuringIborFRA(startDate, endDate, -0.00189, dcType)
    fras.append(fra)

    startDate = startDate.addMonths(1)
    endDate = startDate.addMonths(1)
    fra = TuringIborFRA(startDate, endDate, -0.00175, dcType)
    fras.append(fra)

    startDate = startDate.addMonths(1)
    endDate = startDate.addMonths(1)
    fra = TuringIborFRA(startDate, endDate, -0.00143, dcType)
    fras.append(fra)

    startDate = startDate.addMonths(1)
    endDate = startDate.addMonths(1)
    fra = TuringIborFRA(startDate, endDate, -0.00126, dcType)
    fras.append(fra)

    startDate = startDate.addMonths(1)
    endDate = startDate.addMonths(1)
    fra = TuringIborFRA(startDate, endDate, -0.00126, dcType)
    fras.append(fra)

    ###########################################################################
    ###########################################################################
    ###########################################################################
    ###########################################################################
    
    fixedFreq = TuringFrequencyTypes.ANNUAL
    dcType = TuringDayCountTypes.THIRTY_E_360
    fixedLegType = TuringSwapTypes.PAY

    #######################################
    maturityDate = settlementDate.addMonths(24) 
    swapRate = -0.001506    
    swap1 = TuringIborSwap(settlementDate, maturityDate, fixedLegType,
                           swapRate, fixedFreq, dcType)
    swaps.append(swap1)

    #######################################
    maturityDate = settlementDate.addMonths(36)
    swapRate = -0.000185 
    swap2 = TuringIborSwap(settlementDate, maturityDate, fixedLegType,
                           swapRate, fixedFreq, dcType)
    swaps.append(swap2)

    #######################################
    maturityDate = settlementDate.addMonths(48)   
    swapRate = 0.001358
    swap3 = TuringIborSwap(settlementDate, maturityDate, fixedLegType,
                           swapRate, fixedFreq, dcType)
    swaps.append(swap3)

    #######################################
    maturityDate = settlementDate.addMonths(60)   
    swapRate = 0.0027652
    swap4 = TuringIborSwap(settlementDate, maturityDate, fixedLegType,
                           swapRate, fixedFreq, dcType)
    swaps.append(swap4)

    #######################################
    maturityDate = settlementDate.addMonths(72)
    swapRate = 0.0041539
    swap5 = TuringIborSwap(settlementDate, maturityDate, fixedLegType,
                           swapRate, fixedFreq, dcType)
    swaps.append(swap5)

    #######################################
    maturityDate = settlementDate.addMonths(84)
    swapRate = 0.0054604
    swap6 = TuringIborSwap(settlementDate, maturityDate, fixedLegType,
                           swapRate, fixedFreq, dcType)
    swaps.append(swap6)

    #######################################
    maturityDate = settlementDate.addMonths(96)
    swapRate = 0.006674
    swap7 = TuringIborSwap(settlementDate, maturityDate, fixedLegType,
                           swapRate, fixedFreq, dcType)
    swaps.append(swap7)

    #######################################
    maturityDate = settlementDate.addMonths(108)
    swapRate = 0.007826
    swap8 = TuringIborSwap(settlementDate, maturityDate, fixedLegType,
                           swapRate, fixedFreq, dcType)
    swaps.append(swap8)

    #######################################
    maturityDate = settlementDate.addMonths(120)
    swapRate = 0.008821
    swap9 = TuringIborSwap(settlementDate, maturityDate, fixedLegType,
                           swapRate, fixedFreq, dcType)
    swaps.append(swap9)

    #######################################
    maturityDate = settlementDate.addMonths(132)
    swapRate = 0.0097379
    swap10 = TuringIborSwap(settlementDate, maturityDate, fixedLegType,
                            swapRate, fixedFreq, dcType)
    swaps.append(swap10)

    #######################################
    maturityDate = settlementDate.addMonths(144)
    swapRate = 0.0105406
    swap11 = TuringIborSwap(settlementDate, maturityDate, fixedLegType,
                            swapRate, fixedFreq, dcType)
    swaps.append(swap11)

    #######################################
    maturityDate = settlementDate.addMonths(180)
    swapRate = 0.0123927
    swap12 = TuringIborSwap(settlementDate, maturityDate, fixedLegType,
                            swapRate, fixedFreq, dcType)
    swaps.append(swap12)

    #######################################
    maturityDate = settlementDate.addMonths(240)
    swapRate = 0.0139882
    swap13 = TuringIborSwap(settlementDate, maturityDate, fixedLegType,
                            swapRate, fixedFreq, dcType)
    swaps.append(swap13)

    #######################################
    maturityDate = settlementDate.addMonths(300)
    swapRate = 0.0144972
    swap14 = TuringIborSwap(settlementDate, maturityDate, fixedLegType,
                            swapRate, fixedFreq, dcType)
    swaps.append(swap14)

    #######################################
    maturityDate = settlementDate.addMonths(360)
    swapRate = 0.0146081
    swap15 = TuringIborSwap(settlementDate, maturityDate, fixedLegType,
                            swapRate, fixedFreq, dcType)
    swaps.append(swap15)

    #######################################
    maturityDate = settlementDate.addMonths(420)
    swapRate = 0.01461897
    swap16 = TuringIborSwap(settlementDate, maturityDate, fixedLegType,
                            swapRate, fixedFreq, dcType)
    swaps.append(swap16)

    #######################################
    maturityDate = settlementDate.addMonths(480)
    swapRate = 0.014567455
    swap17 = TuringIborSwap(settlementDate, maturityDate, fixedLegType,
                            swapRate, fixedFreq, dcType)
    swaps.append(swap17)

    #######################################
    maturityDate = settlementDate.addMonths(540)
    swapRate = 0.0140826
    swap18 = TuringIborSwap(settlementDate, maturityDate, fixedLegType,
                            swapRate, fixedFreq, dcType)
    swaps.append(swap18)

    #######################################
    maturityDate = settlementDate.addMonths(600)
    swapRate = 0.01436822
    swap19 = TuringIborSwap(settlementDate, maturityDate, fixedLegType,
                            swapRate, fixedFreq, dcType)
    swaps.append(swap19)
    
    ########################################
    
    liborCurve = TuringIborSingleCurve(valuationDate, depos, fras, swaps)

    testCases.header("LABEL", "DATE", "VALUE")

    ''' Check calibration '''
    for depo in depos:
        v = depo.value(settlementDate, liborCurve)
        testCases.print("DEPO VALUE:", depo._maturityDate, v)

    for fra in fras:
        v = fra.value(settlementDate, liborCurve)
        testCases.print("FRA VALUE:", fra._maturityDate, v)
    
    for swap in swaps:
        v = swap.value(settlementDate, liborCurve)
        testCases.print("SWAP VALUE:", swap._maturityDate, v)

    return liborCurve

###############################################################################


def test_LiborSwap():

    # I have tried to reproduce the example from the blog by Ioannis Rigopoulos
    # https://blog.deriscope.com/index.php/en/excel-interest-rate-swap-price-dual-bootstrapping-curve
    startDate = TuringDate(27, 12, 2017)
    endDate = TuringDate(27, 12, 2067)

    fixedCoupon = 0.015
    fixedFreqType = TuringFrequencyTypes.ANNUAL
    fixedDayCountType = TuringDayCountTypes.THIRTY_E_360

    floatSpread = 0.0
    floatFreqType = TuringFrequencyTypes.SEMI_ANNUAL
    floatDayCountType = TuringDayCountTypes.ACT_360
    firstFixing = -0.00268

    swapCalendarType = TuringCalendarTypes.WEEKEND
    busDayAdjustType = TuringBusDayAdjustTypes.FOLLOWING
    dateGenRuleType = TuringDateGenRuleTypes.BACKWARD
    fixedLegType = TuringSwapTypes.RECEIVE
    
    notional = 10.0 * ONE_MILLION

    swap = TuringIborSwap(startDate,
                          endDate,
                          fixedLegType,
                          fixedCoupon,
                          fixedFreqType,
                          fixedDayCountType,
                          notional,
                          floatSpread,
                          floatFreqType,
                          floatDayCountType,
                          swapCalendarType,
                          busDayAdjustType,
                          dateGenRuleType)

    ''' Now perform a valuation after the swap has seasoned but with the
    same curve being used for discounting and working out the implied
    future Libor rates. '''

    valuationDate = TuringDate(30, 11, 2018)
    settlementDate = valuationDate.addDays(2)
    liborCurve = buildIborSingleCurve(valuationDate)
    v = swap.value(settlementDate, liborCurve, liborCurve, firstFixing)

    v_bbg = 388147.0
    testCases.header("LABEL", "VALUE")
    testCases.print("SWAP_VALUE USING ONE_CURVE", v)
    testCases.print("BLOOMBERG VALUE", v_bbg)
    testCases.print("DIFFERENCE VALUE", v_bbg - v)

###############################################################################


def test_dp_example():

    #  http://www.derivativepricing.com/blogpage.asp?id=8

    startDate = TuringDate(14, 11, 2011)
    endDate = TuringDate(14, 11, 2016)
    fixedFreqType = TuringFrequencyTypes.SEMI_ANNUAL
    swapCalendarType = TuringCalendarTypes.TARGET
    busDayAdjustType = TuringBusDayAdjustTypes.MODIFIED_FOLLOWING
    dateGenRuleType = TuringDateGenRuleTypes.BACKWARD
    fixedDayCountType = TuringDayCountTypes.THIRTY_E_360_ISDA
    fixedLegType = TuringSwapTypes.PAY
    fixedCoupon = 0.0124
    notional = ONE_MILLION

    swap = TuringIborSwap(startDate,
                          endDate,
                          fixedLegType,
                          fixedCoupon=fixedCoupon,
                          fixedFreqType=fixedFreqType,
                          fixedDayCountType=fixedDayCountType,
                          floatFreqType=TuringFrequencyTypes.SEMI_ANNUAL,
                          floatDayCountType=TuringDayCountTypes.ACT_360,
                          notional=notional,
                          calendarType=swapCalendarType,
                          busDayAdjustType=busDayAdjustType,
                          dateGenRuleType=dateGenRuleType)

#    swap.printFixedLegFlows()

    dts = [TuringDate(14, 11, 2011), TuringDate(14, 5, 2012), TuringDate(14, 11, 2012),
           TuringDate(14, 5, 2013), TuringDate(14, 11, 2013), TuringDate(14, 5, 2014),
           TuringDate(14, 11, 2014), TuringDate(14, 5, 2015), TuringDate(16, 11, 2015),
           TuringDate(16, 5, 2016), TuringDate(14, 11, 2016)]

    dfs = [0.9999843, 0.9966889, 0.9942107, 0.9911884, 0.9880738, 0.9836490,
           0.9786276, 0.9710461, 0.9621778, 0.9514315, 0.9394919]

    valuationDate = startDate

    curve = TuringDiscountCurve(valuationDate, dts, np.array(dfs),
                                TuringInterpTypes.FLAT_FWD_RATES)

    v = swap.value(valuationDate, curve, curve)

#    swap.printFixedLegPV()
#    swap.printFloatLegPV()

    # This is essentially zero
    testCases.header("LABEL", "VALUE")
    testCases.print("Swap Value on a Notional of $1M:", v)

###############################################################################

test_LiborSwap()
test_dp_example()
testCases.compareTestCases()
