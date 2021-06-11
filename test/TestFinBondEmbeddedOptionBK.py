import matplotlib.pyplot as plt
import time

import sys
sys.path.append("..")

from turing_models.utilities.turing_date import TuringDate
from turing_models.utilities.frequency import TuringFrequencyTypes
from turing_models.utilities.day_count import TuringDayCountTypes

from turing_models.products.rates.ibor_swap import TuringIborSwap
from turing_models.products.rates.ibor_deposit import TuringIborDeposit

from turing_models.products.rates.ibor_single_curve import TuringIborSingleCurve
from fundamental.market.curves.discount_curve_flat import TuringDiscountCurveFlat
from turing_models.products.bonds.bond import TuringBond
from turing_models.products.bonds.bond_embedded_option import TuringBondEmbeddedOption
from turing_models.utilities.global_types import TuringSwapTypes

from turing_models.models.model_rates_bk import TuringModelRatesBK

from TuringTestCases import TuringTestCases, globalTestCaseMode
testCases = TuringTestCases(__file__, globalTestCaseMode)

plotGraphs = False

###############################################################################


def test_FinBondEmbeddedOptionMATLAB():
    # https://fr.mathworks.com/help/fininst/optembndbybk.html
    # I FIND THAT THE PRICE CONVERGES TO 102.365 WHICH IS CLOSE TO 102.382
    # FOUND BY MATLAB ALTHOUGH THEY DO NOT EXAMINE THE ASYMPTOTIC PRICE
    # WHICH MIGHT BE A BETTER MATCH - ALSO THEY DO NOT USE A REALISTIC VOL

    valuationDate = TuringDate(2007, 1, 1)
    settlementDate = valuationDate

    ###########################################################################

    fixedLegType = TuringSwapTypes.PAY
    dcType = TuringDayCountTypes.THIRTY_E_360
    fixedFreq = TuringFrequencyTypes.ANNUAL
    swap1 = TuringIborSwap(settlementDate, "1Y", fixedLegType, 0.0350, fixedFreq, dcType)
    swap2 = TuringIborSwap(settlementDate, "2Y", fixedLegType, 0.0400, fixedFreq, dcType)
    swap3 = TuringIborSwap(settlementDate, "3Y", fixedLegType, 0.0450, fixedFreq, dcType)
    swaps = [swap1, swap2, swap3]
    discountCurve = TuringIborSingleCurve(valuationDate, [], [], swaps)

    ###########################################################################

    issueDate = TuringDate(2005, 1, 1)
    maturityDate = TuringDate(2010, 1, 1)
    coupon = 0.0525
    freqType = TuringFrequencyTypes.ANNUAL
    accrualType = TuringDayCountTypes.ACT_ACT_ICMA
    bond = TuringBond(issueDate, maturityDate, coupon, freqType, accrualType)

    callDates = []
    callPrices = []
    putDates = []
    putPrices = []

    putDate = TuringDate(2008, 1, 1)
    for _ in range(0, 24):
        putDates.append(putDate)
        putPrices.append(100)
        putDate = putDate.addMonths(1)

    testCases.header("BOND PRICE", "PRICE")
    v = bond.cleanPriceFromDiscountCurve(settlementDate, discountCurve)
    testCases.print("Bond Pure Price:", v)

    sigma = 0.01  # This volatility is very small for a BK process
    a = 0.1

    puttableBond = TuringBondEmbeddedOption(issueDate, maturityDate, coupon,
                                            freqType, accrualType,
                                            callDates, callPrices,
                                            putDates, putPrices)

    testCases.header("TIME", "NumTimeSteps", "BondWithOption", "BondPure")

    timeSteps = range(100, 200, 10)  # 1000, 10)
    values = []
    for numTimeSteps in timeSteps:
        model = TuringModelRatesBK(sigma, a, numTimeSteps)
        start = time.time()
        v = puttableBond.value(settlementDate, discountCurve, model)
        end = time.time()
        period = end - start
        testCases.print(period, numTimeSteps, v['bondwithoption'],
                        v['bondpure'])

        values.append(v['bondwithoption'])

    if plotGraphs:
        plt.figure()
        plt.plot(timeSteps, values)

###############################################################################


def test_FinBondEmbeddedOptionQUANTLIB():

    # Based on example at the nice blog on Quantlib at
    # http://gouthamanbalaraman.com/blog/callable-bond-quantlib-python.html
    # I get a price of 68.97 for 1000 time steps which is higher than the
    # 68.38 found in blog article. But this is for 40 grid points.
    # Note also that a basis point vol of 0.120 is 12% which is VERY HIGH!

    valuationDate = TuringDate(2016, 8, 16)
    settlementDate = valuationDate.addWeekDays(3)

    ###########################################################################

    discountCurve = TuringDiscountCurveFlat(valuationDate, 0.035,
                                            TuringFrequencyTypes.SEMI_ANNUAL)

    ###########################################################################

    issueDate = TuringDate(2010, 9, 15)
    maturityDate = TuringDate(2022, 9, 15)
    coupon = 0.025
    freqType = TuringFrequencyTypes.QUARTERLY
    accrualType = TuringDayCountTypes.ACT_ACT_ICMA
    bond = TuringBond(issueDate, maturityDate, coupon, freqType, accrualType)

    ###########################################################################
    # Set up the call and put times and prices
    ###########################################################################

    nextCallDate = TuringDate(2016, 9, 15)
    callDates = [nextCallDate]
    callPrices = [100.0]

    for _ in range(1, 24):
        nextCallDate = nextCallDate.addMonths(3)
        callDates.append(nextCallDate)
        callPrices.append(100.0)

    putDates = []
    putPrices = []

    # the value used in blog of 12% bp vol is unrealistic
    sigma = 0.12/0.035  # basis point volatility
    a = 0.03

    puttableBond = TuringBondEmbeddedOption(issueDate, maturityDate, coupon,
                                            freqType, accrualType,
                                            callDates, callPrices,
                                            putDates, putPrices)

    testCases.header("BOND PRICE", "PRICE")
    v = bond.cleanPriceFromDiscountCurve(settlementDate, discountCurve)
    testCases.print("Bond Pure Price:", v)

    testCases.header("TIME", "NumTimeSteps", "BondWithOption", "BondPure")
    timeSteps = range(100, 200, 20)  # 1000, 10)
    values = []
    for numTimeSteps in timeSteps:
        model = TuringModelRatesBK(sigma, a, numTimeSteps)
        start = time.time()
        v = puttableBond.value(settlementDate, discountCurve, model)
        end = time.time()
        period = end - start
        testCases.print(period, numTimeSteps, v['bondwithoption'],
                        v['bondpure'])
        values.append(v['bondwithoption'])

    if plotGraphs:
        plt.figure()
        plt.title("Puttable Bond Price Convergence")
        plt.plot(timeSteps, values)

###############################################################################


test_FinBondEmbeddedOptionMATLAB()
test_FinBondEmbeddedOptionQUANTLIB()
testCases.compareTestCases()
