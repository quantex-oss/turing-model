import matplotlib.pyplot as plt
import numpy as np
import time as time

import sys
sys.path.append("..")

from turing_models.utilities.date import TuringDate
from turing_models.utilities.day_count import TuringDayCountTypes
from turing_models.utilities.frequency import TuringFrequencyTypes
from turing_models.utilities.calendar import TuringCalendarTypes
from turing_models.products.rates.ibor_fra import TuringIborFRA
from turing_models.products.rates.ibor_future import TuringIborFuture
from turing_models.products.rates.ibor_deposit import TuringIborDeposit
from turing_models.products.rates.ibor_swap import TuringIborSwap
from turing_models.utilities.calendar import TuringBusDayAdjustTypes
from turing_models.market.curves.interpolator import TuringInterpTypes
from turing_models.utilities.mathematics import ONE_MILLION
from turing_models.utilities.global_types import TuringSwapTypes
from turing_models.market.curves.interpolator import TuringInterpTypes
from turing_models.products.rates.ibor_single_curve import TuringIborSingleCurve
from turing_models.products.rates.ibor_dual_curve import TuringIborDualCurve
from turing_models.products.rates.ois_curve import TuringOISCurve
from turing_models.products.rates.ois import TuringOIS

from TuringTestCases import TuringTestCases, globalTestCaseMode
testCases = TuringTestCases(__file__, globalTestCaseMode)

PLOT_GRAPHS = False

###############################################################################

def buildOIS(valuationDate):
    ''' Build the OIS funding curve from futures (FRAs) and OIS '''

    dccType = TuringDayCountTypes.THIRTY_E_360_ISDA
    depos = []

    spotDays = 0
    spotDays = 0
    settlementDate = valuationDate.addWeekDays(spotDays)
    fixedLegType = TuringSwapTypes.PAY

    fras = []
    # 1 x 4 FRA
    
    swaps = []
    fixedFreqType = TuringFrequencyTypes.SEMI_ANNUAL
    fixedDCCType = TuringDayCountTypes.ACT_365F

    swapRate = 0.000022
    maturityDate = settlementDate.addMonths(24)
    swap = TuringOIS(settlementDate, maturityDate, fixedLegType, swapRate,
                     fixedFreqType, fixedDCCType)
    swaps.append(swap)

    swapRate += 0.000
    fixedLegType = TuringSwapTypes.PAY
    maturityDate = settlementDate.addMonths(36)
    swap = TuringOIS(settlementDate, maturityDate, fixedLegType, swapRate,
                     fixedFreqType, fixedDCCType)
    swaps.append(swap)

    swapRate += 0.000
    maturityDate = settlementDate.addMonths(48)
    swap = TuringOIS(settlementDate, maturityDate, fixedLegType, swapRate,
                     fixedFreqType,
                     fixedDCCType)
    swaps.append(swap)

    swapRate = 0.02
    maturityDate = settlementDate.addMonths(60)
    swap = TuringOIS(settlementDate, maturityDate, fixedLegType, swapRate,
                     fixedFreqType,
                     fixedDCCType)
    swaps.append(swap)

    maturityDate = settlementDate.addMonths(72)
    swap = TuringOIS(settlementDate, maturityDate, fixedLegType, swapRate,
                     fixedFreqType,
                     fixedDCCType)
    swaps.append(swap)

    maturityDate = settlementDate.addMonths(84)
    swap = TuringOIS(settlementDate, maturityDate, fixedLegType, swapRate,
                     fixedFreqType,
                     fixedDCCType)
    swaps.append(swap)

    maturityDate = settlementDate.addMonths(96)
    swap = TuringOIS(settlementDate, maturityDate, fixedLegType, swapRate,
                     fixedFreqType,
                     fixedDCCType)
    swaps.append(swap)

    maturityDate = settlementDate.addMonths(108)
    swap = TuringOIS(settlementDate, maturityDate, fixedLegType, swapRate,
                     fixedFreqType,
                     fixedDCCType)
    swaps.append(swap)

    maturityDate = settlementDate.addMonths(120)
    swap = TuringOIS(settlementDate, maturityDate, fixedLegType, swapRate,
                     fixedFreqType,
                     fixedDCCType)
    swaps.append(swap)

    maturityDate = settlementDate.addMonths(132)
    swap = TuringOIS(settlementDate, maturityDate, fixedLegType, swapRate,
                     fixedFreqType,
                     fixedDCCType)
    swaps.append(swap)

    maturityDate = settlementDate.addMonths(144)
    swap = TuringOIS(settlementDate, maturityDate, fixedLegType, swapRate,
                     fixedFreqType,
                     fixedDCCType)
    swaps.append(swap)

    maturityDate = settlementDate.addMonths(180)
    swap = TuringOIS(settlementDate, maturityDate, fixedLegType, swapRate,
                     fixedFreqType,
                     fixedDCCType)
    swaps.append(swap)

    maturityDate = settlementDate.addMonths(240)
    swap = TuringOIS(settlementDate, maturityDate, fixedLegType, swapRate,
                     fixedFreqType,
                     fixedDCCType)
    swaps.append(swap)

    maturityDate = settlementDate.addMonths(300)
    swap = TuringOIS(settlementDate, maturityDate, fixedLegType, swapRate,
                     fixedFreqType,
                     fixedDCCType)
    swaps.append(swap)

    maturityDate = settlementDate.addMonths(360)
    swap = TuringOIS(settlementDate, maturityDate, fixedLegType, swapRate,
                     fixedFreqType,
                     fixedDCCType)
    swaps.append(swap)

    oisCurve = TuringOISCurve(valuationDate,
                              [],
                              fras,
                              swaps)

    return oisCurve

###############################################################################


def test_bloombergPricingExample():

    ''' This is an example of a replication of a BBG example from
    https://github.com/vilen22/curve-building/blob/master/Bloomberg%20Curve%20Building%20Replication.xlsx

    '''
    valuationDate = TuringDate(6, 6, 2018)

    # We do the O/N rate which settles on trade date
    spotDays = 0
    settlementDate = valuationDate.addWeekDays(spotDays)
    depoDCCType = TuringDayCountTypes.ACT_360
    depos = []
    depositRate = 0.0231381
    maturityDate = settlementDate.addMonths(3)
    depo = TuringIborDeposit(settlementDate, maturityDate, depositRate,
                             depoDCCType)
    depos.append(depo)

    futs = []
    fut = TuringIborFuture(valuationDate, 1); futs.append(fut)
    fut = TuringIborFuture(valuationDate, 2); futs.append(fut)
    fut = TuringIborFuture(valuationDate, 3); futs.append(fut)
    fut = TuringIborFuture(valuationDate, 4); futs.append(fut)
    fut = TuringIborFuture(valuationDate, 5); futs.append(fut)
    fut = TuringIborFuture(valuationDate, 6); futs.append(fut)

    fras = [None]*6
    fras[0] = futs[0].toFRA(97.6675, -0.00005)
    fras[1] = futs[1].toFRA(97.5200, -0.00060)
    fras[2] = futs[2].toFRA(97.3550, -0.00146)
    fras[3] = futs[3].toFRA(97.2450, -0.00263)
    fras[4] = futs[4].toFRA(97.1450, -0.00411)
    fras[5] = futs[5].toFRA(97.0750, -0.00589)

    accrual = TuringDayCountTypes.THIRTY_E_360
    freq = TuringFrequencyTypes.SEMI_ANNUAL

    spotDays = 2
    settlementDate = valuationDate.addWeekDays(spotDays)
    notional = ONE_MILLION
    fixedLegType = TuringSwapTypes.PAY
    interpType = TuringInterpTypes.FLAT_FWD_RATES

    swaps = []
    swap = TuringIborSwap(settlementDate, "2Y", fixedLegType, (2.77417 + 2.77844) / 200, freq, accrual); swaps.append(swap)
    swap = TuringIborSwap(settlementDate, "3Y", fixedLegType, (2.86098 + 2.86582) / 200, freq, accrual); swaps.append(swap)
    swap = TuringIborSwap(settlementDate, "4Y", fixedLegType, (2.90240 + 2.90620) / 200, freq, accrual); swaps.append(swap)
    swap = TuringIborSwap(settlementDate, "5Y", fixedLegType, (2.92944 + 2.92906) / 200, freq, accrual); swaps.append(swap)
    swap = TuringIborSwap(settlementDate, "6Y", fixedLegType, (2.94001 + 2.94499) / 200, freq, accrual); swaps.append(swap)
    swap = TuringIborSwap(settlementDate, "7Y", fixedLegType, (2.95352 + 2.95998) / 200, freq, accrual); swaps.append(swap)
    swap = TuringIborSwap(settlementDate, "8Y", fixedLegType, (2.96830 + 2.97400) / 200, freq, accrual); swaps.append(swap)
    swap = TuringIborSwap(settlementDate, "9Y", fixedLegType, (2.98403 + 2.98817) / 200, freq, accrual); swaps.append(swap)
    swap = TuringIborSwap(settlementDate, "10Y", fixedLegType, (2.99716 + 3.00394) / 200, freq, accrual); swaps.append(swap)
    swap = TuringIborSwap(settlementDate, "11Y", fixedLegType, (3.01344 + 3.01596) / 200, freq, accrual); swaps.append(swap)
    swap = TuringIborSwap(settlementDate, "12Y", fixedLegType, (3.02276 + 3.02684) / 200, freq, accrual); swaps.append(swap)
    swap = TuringIborSwap(settlementDate, "15Y", fixedLegType, (3.04092 + 3.04508) / 200, freq, accrual); swaps.append(swap)
    swap = TuringIborSwap(settlementDate, "20Y", fixedLegType, (3.04417 + 3.05183) / 200, freq, accrual); swaps.append(swap)
    swap = TuringIborSwap(settlementDate, "25Y", fixedLegType, (3.03219 + 3.03621) / 200, freq, accrual); swaps.append(swap)
    swap = TuringIborSwap(settlementDate, "30Y", fixedLegType, (3.01030 + 3.01370) / 200, freq, accrual); swaps.append(swap)
    swap = TuringIborSwap(settlementDate, "40Y", fixedLegType, (2.96946 + 2.97354) / 200, freq, accrual); swaps.append(swap)
    swap = TuringIborSwap(settlementDate, "50Y", fixedLegType, (2.91552 + 2.93748) / 200, freq, accrual); swaps.append(swap)

    liborCurve = TuringIborSingleCurve(valuationDate, depos, fras, swaps, interpType, True)

    principal = 0.0
    testCases.banner("======================================================")
    testCases.banner("SINGLE CURVE VALUATION")
    testCases.header("LABEL", "VALUE")
    testCases.print("VALUE:", swaps[0].value(valuationDate, liborCurve, liborCurve, None))
    testCases.print("FIXED:", swaps[0]._fixedLeg.value(valuationDate, liborCurve))
    testCases.print("FLOAT:", swaps[0]._floatLeg.value(valuationDate, liborCurve, liborCurve, None))

    testCases.banner("======================================================")
    testCases.banner("SINGLE CURVE VALUATION TO SWAP SETTLEMENT DATE")
    testCases.header("LABEL", "VALUE")
    testCases.print("VALUE:", swaps[0].value(settlementDate, liborCurve, liborCurve, None))
    testCases.print("FIXED:", swaps[0]._fixedLeg.value(settlementDate, liborCurve))
    testCases.print("FLOAT:", swaps[0]._floatLeg.value(settlementDate, liborCurve, liborCurve, None))
    testCases.banner("======================================================")

#    swaps[0].printFixedLegPV()
#    swaps[0].printFloatLegPV()

    oisCurve = buildOIS(valuationDate)
#    print(oisCurve)

    liborDualCurve = TuringIborDualCurve(valuationDate, oisCurve, depos, fras, swaps,
                                         TuringInterpTypes.FLAT_FWD_RATES, True)
#    print(liborDualCurve) 
    
    # The valuation of 53714.55 is very close to the spreadsheet value 53713.96

    testCases.header("VALUATION TO TODAY DATE"," PV")
    testCases.print("VALUE:", swaps[0].value(valuationDate, oisCurve, liborDualCurve, None))
    testCases.print("FIXED:", swaps[0]._fixedLeg.value(valuationDate, oisCurve))
    testCases.print("FLOAT:", swaps[0]._floatLeg.value(valuationDate, oisCurve, liborCurve, None))

    testCases.header("VALUATION TO SWAP SETTLEMENT DATE"," PV")
    testCases.print("VALUE:", swaps[0].value(settlementDate, oisCurve, liborDualCurve, None))
    testCases.print("FIXED:", swaps[0]._fixedLeg.value(settlementDate, oisCurve))
    testCases.print("FLOAT:", swaps[0]._floatLeg.value(settlementDate, oisCurve, liborDualCurve, None, ))

#    swaps[0].printFixedLegPV()
#    swaps[0].printFloatLegPV()

    PLOT = False
    if PLOT is True:

        years = np.linspace(0, 5, 21)
        dates = settlementDate.addYears(years)
    
        singleCurveFwds = liborCurve.fwd(dates)    
        plt.plot(years, singleCurveFwds, label="Single Libor Curve")
 
        oisCurveFwds = oisCurve.fwd(dates)    
        plt.plot(years, oisCurveFwds, label="OIS Curve")

        indexCurveFwds = liborDualCurve.fwd(dates)    
        plt.plot(years, indexCurveFwds, label="Libor Index Curve")
        
        plt.legend()
    
    # swaps[0].printFixedLegPV()
    # swaps[0].printFloatLegPV()

###############################################################################

def test_swapValuationExample():
    
    # Example from
    # https://blog.deriscope.com/index.php/en/excel-interest-rate-swap-price-dual-bootstrapping-curve
    
    vBloomberg = 388147

    valuationDate = TuringDate(30, 11, 2018)

    startDate = TuringDate(27, 12, 2017)
    maturityDate = TuringDate(27, 12, 2067)
    notional = 10 * ONE_MILLION
    fixedLegType = TuringSwapTypes.RECEIVE
    
    fixedRate = 0.0150
    fixedDCCType = TuringDayCountTypes.THIRTY_360_BOND
    fixedFreqType = TuringFrequencyTypes.ANNUAL
    
    floatSpread = 0.0
    floatDCCType = TuringDayCountTypes.ACT_360
    floatFreqType = TuringFrequencyTypes.SEMI_ANNUAL

    offMarketSwap = TuringIborSwap(startDate, maturityDate, fixedLegType,
                                   fixedRate, fixedFreqType, fixedDCCType,
                                   notional,
                                   floatSpread, floatFreqType, floatDCCType)
    
    interpType = TuringInterpTypes.LINEAR_ZERO_RATES
    
    depoDCCType = TuringDayCountTypes.ACT_360
    depos = []
    
    ###########################################################################
    # MARKET
    ###########################################################################
    
    spotDays = 0
    settlementDate = valuationDate.addWeekDays(spotDays)
    depo = TuringIborDeposit(settlementDate, "6M", -0.2510 / 100.0, depoDCCType); depos.append(depo)
    
    fras = []
    fraDCCType = TuringDayCountTypes.ACT_360
    
    fra = TuringIborFRA(settlementDate.addTenor("1M"), "6M", -0.2450 / 100.0, fraDCCType); fras.append(fra)
    fra = TuringIborFRA(settlementDate.addTenor("2M"), "6M", -0.2435 / 100.0, fraDCCType); fras.append(fra)
    fra = TuringIborFRA(settlementDate.addTenor("3M"), "6M", -0.2400 / 100.0, fraDCCType); fras.append(fra)
    fra = TuringIborFRA(settlementDate.addTenor("4M"), "6M", -0.2360 / 100.0, fraDCCType); fras.append(fra)
    fra = TuringIborFRA(settlementDate.addTenor("5M"), "6M", -0.2285 / 100.0, fraDCCType); fras.append(fra)
    fra = TuringIborFRA(settlementDate.addTenor("6M"), "6M", -0.2230 / 100.0, fraDCCType); fras.append(fra)
    fra = TuringIborFRA(settlementDate.addTenor("7M"), "6M", -0.2110 / 100.0, fraDCCType); fras.append(fra)
    fra = TuringIborFRA(settlementDate.addTenor("8M"), "6M", -0.1990 / 100.0, fraDCCType); fras.append(fra)
    fra = TuringIborFRA(settlementDate.addTenor("9M"), "6M", -0.1850 / 100.0, fraDCCType); fras.append(fra)
    fra = TuringIborFRA(settlementDate.addTenor("10M"), "6M", -0.1680 / 100.0, fraDCCType); fras.append(fra)
    fra = TuringIborFRA(settlementDate.addTenor("11M"), "6M", -0.1510 / 100.0, fraDCCType); fras.append(fra)
    fra = TuringIborFRA(settlementDate.addTenor("12M"), "6M", -0.1360 / 100.0, fraDCCType); fras.append(fra)
    
    swaps = []
    fixedLegType = TuringSwapTypes.PAY
    fixedDCCType = TuringDayCountTypes.THIRTY_360_BOND
    fixedFreqType = TuringFrequencyTypes.ANNUAL
    
    swap = TuringIborSwap(settlementDate, "2Y", fixedLegType, -0.1525 / 100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = TuringIborSwap(settlementDate, "3Y", fixedLegType, -0.0185 / 100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = TuringIborSwap(settlementDate, "4Y", fixedLegType, 0.1315 / 100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = TuringIborSwap(settlementDate, "5Y", fixedLegType, 0.2745 / 100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = TuringIborSwap(settlementDate, "6Y", fixedLegType, 0.4135 / 100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = TuringIborSwap(settlementDate, "7Y", fixedLegType, 0.5439 / 100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = TuringIborSwap(settlementDate, "8Y", fixedLegType, 0.6652 / 100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = TuringIborSwap(settlementDate, "9Y", fixedLegType, 0.7784 / 100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = TuringIborSwap(settlementDate, "10Y", fixedLegType, 0.8799 / 100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = TuringIborSwap(settlementDate, "11Y", fixedLegType, 0.9715 / 100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = TuringIborSwap(settlementDate, "12Y", fixedLegType, 1.0517 / 100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = TuringIborSwap(settlementDate, "15Y", fixedLegType, 1.2369 / 100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = TuringIborSwap(settlementDate, "20Y", fixedLegType, 1.3965 / 100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = TuringIborSwap(settlementDate, "25Y", fixedLegType, 1.4472 / 100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = TuringIborSwap(settlementDate, "30Y", fixedLegType, 1.4585 / 100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = TuringIborSwap(settlementDate, "35Y", fixedLegType, 1.4595 / 100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = TuringIborSwap(settlementDate, "40Y", fixedLegType, 1.4535 / 100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = TuringIborSwap(settlementDate, "45Y", fixedLegType, 1.4410 / 100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = TuringIborSwap(settlementDate, "50Y", fixedLegType, 1.4335 / 100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    
    iborDepos = depos.copy()
    iborFras = fras.copy()
    iborSwaps = swaps.copy()
    
    iborCurve = TuringIborSingleCurve(valuationDate, iborDepos, iborFras, iborSwaps, interpType)
    v1 = offMarketSwap.value(valuationDate, iborCurve, iborCurve, -0.268/100.0)    

    testCases.banner("DERISCOPE EXAMPLE REPLICATION")    
    testCases.header("LABEL", "VALUE")
    testCases.print("BBG VALUE", vBloomberg)
    testCases.print("FP ONE CURVE VALUE", v1)
    
    ###############################################################################
    
    depoDCCType = TuringDayCountTypes.ACT_360
    depos = []
    
    spotDays = 0
    settlementDate = valuationDate.addWeekDays(spotDays)
    depo = TuringIborDeposit(settlementDate, "1D", -0.3490 / 100.0, depoDCCType); depos.append(depo)
    
    fras = []
    
    swaps = []
    fixedLegType = TuringSwapTypes.PAY
    fixedDCCType = TuringDayCountTypes.ACT_365F
    fixedFreqType = TuringFrequencyTypes.ANNUAL
    
    # Standard OIS with standard annual terms
    swap = TuringOIS(settlementDate, "2W", fixedLegType, -0.3600 / 100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = TuringOIS(settlementDate, "1M", fixedLegType, -0.3560 / 100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = TuringOIS(settlementDate, "2M", fixedLegType, -0.3570 / 100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = TuringOIS(settlementDate, "3M", fixedLegType, -0.3580 / 100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = TuringOIS(settlementDate, "4M", fixedLegType, -0.3575 / 100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = TuringOIS(settlementDate, "5M", fixedLegType, -0.3578 / 100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = TuringOIS(settlementDate, "6M", fixedLegType, -0.3580 / 100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = TuringOIS(settlementDate, "7M", fixedLegType, -0.3600 / 100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = TuringOIS(settlementDate, "8M", fixedLegType, -0.3575 / 100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = TuringOIS(settlementDate, "9M", fixedLegType, -0.3569 / 100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = TuringOIS(settlementDate, "10M", fixedLegType, -0.3553 / 100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = TuringOIS(settlementDate, "11M", fixedLegType, -0.3534 / 100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = TuringOIS(settlementDate, "12M", fixedLegType, -0.3496 / 100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = TuringOIS(settlementDate, "18M", fixedLegType, -0.3173 / 100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    
    swap = TuringOIS(settlementDate, "2Y", fixedLegType, -0.2671 / 100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = TuringOIS(settlementDate, "30M", fixedLegType, -0.2070 / 100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = TuringOIS(settlementDate, "3Y", fixedLegType, -0.1410 / 100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = TuringOIS(settlementDate, "4Y", fixedLegType, -0.0060 / 100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = TuringOIS(settlementDate, "5Y", fixedLegType, 0.1285 / 100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = TuringOIS(settlementDate, "6Y", fixedLegType, 0.2590 / 100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = TuringOIS(settlementDate, "7Y", fixedLegType, 0.3830 / 100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = TuringOIS(settlementDate, "8Y", fixedLegType, 0.5020 / 100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = TuringOIS(settlementDate, "9Y", fixedLegType, 0.6140 / 100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = TuringOIS(settlementDate, "10Y", fixedLegType, 0.7160 / 100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = TuringOIS(settlementDate, "11Y", fixedLegType, 0.8070 / 100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = TuringOIS(settlementDate, "12Y", fixedLegType, 0.8890 / 100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = TuringOIS(settlementDate, "15Y", fixedLegType, 1.0790 / 100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = TuringOIS(settlementDate, "20Y", fixedLegType, 1.2460 / 100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = TuringOIS(settlementDate, "25Y", fixedLegType, 1.3055 / 100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = TuringOIS(settlementDate, "30Y", fixedLegType, 1.3270 / 100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = TuringOIS(settlementDate, "35Y", fixedLegType, 1.3315 / 100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = TuringOIS(settlementDate, "40Y", fixedLegType, 1.3300 / 100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    swap = TuringOIS(settlementDate, "50Y", fixedLegType, 1.3270 / 100.0, fixedFreqType, fixedDCCType); swaps.append(swap)
    
    oisDepos = depos.copy()
    oisFras = fras.copy()
    oisSwaps = swaps.copy()
    
#    oisCurveFF = TuringOISCurve(valuationDate, oisDepos, oisFras, oisSwaps, interpType)
    
    iborDualCurve = TuringIborDualCurve(valuationDate, oisCurveFF, iborDepos, iborFras, iborSwaps, interpType)
    
#    v2 = offMarketSwap.value(valuationDate, oisCurveFF, iborDualCurve, -0.268/100.0)
    
#    testCases.print("FP DUAL CURVE VALUE", v2)

#    swapRate = offMarketSwap.swapRate(valuationDate, oisCurveFF, iborCurve, -0.268/100.0)

#    testCases.print("FP DUAL CURVE SWAP RATE", swapRate)

#    offMarketSwap.printFixedLegFlows()
#    offMarketSwap.printFloatLegFlows()
#    offMarketSwap.printFixedLegPV()
#    offMarketSwap.printFloatLegPV()
    

###############################################################################

#test_swapValuationExample()

test_bloombergPricingExample()

testCases.compareTestCases()
