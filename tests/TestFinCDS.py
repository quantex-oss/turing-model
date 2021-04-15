###############################################################################
# Copyright (C) 2018, 2019, 2020 Dominic O'Kane
###############################################################################

import time
import numpy as np

import sys
sys.path.append("..")

from turing_models.products.credit.turing_cds import TuringCDS
from turing_models.turingutils.turing_math import ONE_MILLION
from turing_models.market.curves.turing_interpolator import TuringInterpTypes
from turing_models.products.rates.turing_ibor_swap import TuringIborSwap
from turing_models.products.rates.turing_ibor_deposit import TuringIborDeposit
from turing_models.market.curves.turing_discount_curve import TuringDiscountCurve
from turing_models.products.rates.turing_ibor_single_curve import TuringIborSingleCurve
from turing_models.products.credit.turing_cds_curve import TuringCDSCurve
from turing_models.turingutils.turing_global_variables import gDaysInYear
from turing_models.turingutils.turing_calendar import TuringBusDayAdjustTypes
from turing_models.turingutils.turing_calendar import TuringDateGenRuleTypes
from turing_models.turingutils.turing_calendar import TuringCalendarTypes
from turing_models.turingutils.turing_frequency import TuringFrequencyTypes
from turing_models.turingutils.turing_day_count import TuringDayCountTypes
from turing_models.turingutils.turing_date import TuringDate
from turing_models.turingutils.turing_global_types import TuringSwapTypes

from TuringTestCases import TuringTestCases, globalTestCaseMode
testCases = TuringTestCases(__file__, globalTestCaseMode)

##########################################################################
# TO DO
##########################################################################


def test_CDSFastApproximation():

    valueDate = TuringDate(20, 6, 2018)
    # I build a discount curve that requires no bootstrap
    times = np.linspace(0, 10.0, 11)
    r = 0.05

    discountFactors = np.power((1.0 + r), -times)
    dates = valueDate.addYears(times)

    liborCurve = TuringDiscountCurve(valueDate,
                                     dates,
                                     discountFactors,
                                     TuringInterpTypes.FLAT_FWD_RATES)

    ##########################################################################

    maturityDate = valueDate.nextCDSDate(120)
    t = (maturityDate - valueDate) / 365.242
    z = liborCurve.df(maturityDate)
    r = -np.log(z) / t

    recoveryRate = 0.40

    contractCoupon = 0.010

    testCases.header("MKT_SPD", "EXACT_VALUE", "APPROX_VALUE", "DIFF(%NOT)")

    for mktCoupon in np.linspace(0.000, 0.05, 21):

        cdsContracts = []

        cdsMkt = TuringCDS(valueDate, maturityDate, mktCoupon, ONE_MILLION)

        cdsContracts.append(cdsMkt)

        issuerCurve = TuringCDSCurve(valueDate,
                                     cdsContracts,
                                     liborCurve,
                                     recoveryRate)

        cdsContract = TuringCDS(valueDate, maturityDate, contractCoupon)
        v_exact = cdsContract.value(
            valueDate, issuerCurve, recoveryRate)['full_pv']
        v_approx = cdsContract.valueFastApprox(
            valueDate, r, mktCoupon, recoveryRate)[0]
        pctdiff = (v_exact - v_approx) / ONE_MILLION * 100.0
        testCases.print(mktCoupon * 10000, v_exact, v_approx, pctdiff)

##########################################################################


def test_CDSCurveRepricing():

    valuationDate = TuringDate(20, 6, 2018)
    recoveryRate = 0.40

    cdsContracts, issuerCurve = test_IssuerCurveBuild()
    testCases.header("CDS_MATURITY_DATE", "PAR_SPREAD")
    for cds in cdsContracts:
        spd = cds.parSpread(valuationDate, issuerCurve, recoveryRate)
        testCases.print(str(cds._maturityDate), spd * 10000.0)

##########################################################################


def test_CDSCurveBuildTiming():

    numCurves = 1000

    start = time.time()
    for _ in range(0, numCurves):
        test_IssuerCurveBuild()

    end = time.time()

    testCases.header("LABEL", "TIME")
    duration = (end - start) / numCurves
    testCases.print(str(numCurves) + " Libor curves", duration)

##########################################################################


def test_IssuerCurveBuild():
    ''' Test issuer curve build with simple libor curve to isolate cds
    curve building time cost. '''

    valuationDate = TuringDate(20, 6, 2018)

    times = np.linspace(0.0, 10.0, 11)
    r = 0.05
    discountFactors = np.power((1.0 + r), -times)
    dates = valuationDate.addYears(times)
    liborCurve = TuringDiscountCurve(valuationDate,
                                     dates,
                                     discountFactors,
                                     TuringInterpTypes.FLAT_FWD_RATES)
    recoveryRate = 0.40

    cdsContracts = []

    cdsCoupon = 0.005  # 50 bps
    maturityDate = valuationDate.addMonths(12)
    cds = TuringCDS(valuationDate, maturityDate, cdsCoupon)
    cdsContracts.append(cds)

    cdsCoupon = 0.0055
    maturityDate = valuationDate.addMonths(24)
    cds = TuringCDS(valuationDate, maturityDate, cdsCoupon)
    cdsContracts.append(cds)

    cdsCoupon = 0.0060
    maturityDate = valuationDate.addMonths(36)
    cds = TuringCDS(valuationDate, maturityDate, cdsCoupon)
    cdsContracts.append(cds)

    cdsCoupon = 0.0065
    maturityDate = valuationDate.addMonths(60)
    cds = TuringCDS(valuationDate, maturityDate, cdsCoupon)
    cdsContracts.append(cds)

    cdsCoupon = 0.0070
    maturityDate = valuationDate.addMonths(84)
    cds = TuringCDS(valuationDate, maturityDate, cdsCoupon)
    cdsContracts.append(cds)

    cdsCoupon = 0.0073
    maturityDate = valuationDate.addMonths(120)
    cds = TuringCDS(valuationDate, maturityDate, cdsCoupon)
    cdsContracts.append(cds)

    issuerCurve = TuringCDSCurve(valuationDate,
                                 cdsContracts,
                                 liborCurve,
                                 recoveryRate)

    return cdsContracts, issuerCurve

##########################################################################


def buildFullIssuerCurve1(mktSpreadBump, irBump):

    # https://www.markit.com/markit.jsp?jsppage=pv.jsp
    # YIELD CURVE 8-AUG-2019 SNAP AT 1600

    tradeDate = TuringDate(9, 8, 2019)
    valuationDate = tradeDate.addDays(1)

    m = 1.0  # 0.00000000000

    dcType = TuringDayCountTypes.ACT_360
    depos = []
    depo1 = TuringIborDeposit(valuationDate, "1D", m * 0.0220, dcType)
    depos.append(depo1)

    spotDays = 2
    settlementDate = valuationDate.addDays(spotDays)

    maturityDate = settlementDate.addMonths(1)
    depo1 = TuringIborDeposit(settlementDate, maturityDate, m * 0.022009, dcType)

    maturityDate = settlementDate.addMonths(2)
    depo2 = TuringIborDeposit(settlementDate, maturityDate, m * 0.022138, dcType)

    maturityDate = settlementDate.addMonths(3)
    depo3 = TuringIborDeposit(settlementDate, maturityDate, m * 0.021810, dcType)

    maturityDate = settlementDate.addMonths(6)
    depo4 = TuringIborDeposit(settlementDate, maturityDate, m * 0.020503, dcType)

    maturityDate = settlementDate.addMonths(12)
    depo5 = TuringIborDeposit(settlementDate, maturityDate, m * 0.019930, dcType)

    depos.append(depo1)
    depos.append(depo2)
    depos.append(depo3)
    depos.append(depo4)
    depos.append(depo5)

    fras = []

    swaps = []
    dcType = TuringDayCountTypes.THIRTY_E_360_ISDA
    fixedFreq = TuringFrequencyTypes.SEMI_ANNUAL

    maturityDate = settlementDate.addMonths(24)
    swap1 = TuringIborSwap(
        settlementDate,
        maturityDate,
        TuringSwapTypes.PAY,
        m * 0.015910 + irBump,
        fixedFreq,
        dcType)
    swaps.append(swap1)

    maturityDate = settlementDate.addMonths(36)
    swap2 = TuringIborSwap(
        settlementDate,
        maturityDate,
        TuringSwapTypes.PAY,
        m * 0.014990 + irBump,
        fixedFreq,
        dcType)
    swaps.append(swap2)

    maturityDate = settlementDate.addMonths(48)
    swap3 = TuringIborSwap(
        settlementDate,
        maturityDate,
        TuringSwapTypes.PAY,
        m * 0.014725 + irBump,
        fixedFreq,
        dcType)
    swaps.append(swap3)

    maturityDate = settlementDate.addMonths(60)
    swap4 = TuringIborSwap(
        settlementDate,
        maturityDate,
        TuringSwapTypes.PAY,
        m * 0.014640 + irBump,
        fixedFreq,
        dcType)
    swaps.append(swap4)

    maturityDate = settlementDate.addMonths(72)
    swap5 = TuringIborSwap(
        settlementDate,
        maturityDate,
        TuringSwapTypes.PAY,
        m * 0.014800 + irBump,
        fixedFreq,
        dcType)
    swaps.append(swap5)

    maturityDate = settlementDate.addMonths(84)
    swap6 = TuringIborSwap(
        settlementDate,
        maturityDate,
        TuringSwapTypes.PAY,
        m * 0.014995 + irBump,
        fixedFreq,
        dcType)
    swaps.append(swap6)

    maturityDate = settlementDate.addMonths(96)
    swap7 = TuringIborSwap(
        settlementDate,
        maturityDate,
        TuringSwapTypes.PAY,
        m * 0.015180 + irBump,
        fixedFreq,
        dcType)
    swaps.append(swap7)

    maturityDate = settlementDate.addMonths(108)
    swap8 = TuringIborSwap(
        settlementDate,
        maturityDate,
        TuringSwapTypes.PAY,
        m * 0.015610 + irBump,
        fixedFreq,
        dcType)
    swaps.append(swap8)

    maturityDate = settlementDate.addMonths(120)
    swap9 = TuringIborSwap(
        settlementDate,
        maturityDate,
        TuringSwapTypes.PAY,
        m * 0.015880 + irBump,
        fixedFreq,
        dcType)
    swaps.append(swap9)

    maturityDate = settlementDate.addMonths(144)
    swap10 = TuringIborSwap(
        settlementDate,
        maturityDate,
        TuringSwapTypes.PAY,
        m * 0.016430 + irBump,
        fixedFreq,
        dcType)
    swaps.append(swap10)

    liborCurve = TuringIborSingleCurve(valuationDate, depos, fras, swaps)

    cdsMarketContracts = []

    cdsCoupon = 0.04 + mktSpreadBump

    maturityDate = valuationDate.nextCDSDate(6)
    cds = TuringCDS(valuationDate, maturityDate, cdsCoupon)
    cdsMarketContracts.append(cds)

    maturityDate = valuationDate.nextCDSDate(12)
    cds = TuringCDS(valuationDate, maturityDate, cdsCoupon)
    cdsMarketContracts.append(cds)

    maturityDate = valuationDate.nextCDSDate(24)
    cds = TuringCDS(valuationDate, maturityDate, cdsCoupon)
    cdsMarketContracts.append(cds)

    maturityDate = valuationDate.nextCDSDate(36)
    cds = TuringCDS(valuationDate, maturityDate, cdsCoupon)
    cdsMarketContracts.append(cds)

    maturityDate = valuationDate.nextCDSDate(48)
    cds = TuringCDS(valuationDate, maturityDate, cdsCoupon)
    cdsMarketContracts.append(cds)

    maturityDate = valuationDate.nextCDSDate(60)
    cds = TuringCDS(valuationDate, maturityDate, cdsCoupon)
    cdsMarketContracts.append(cds)

    maturityDate = valuationDate.nextCDSDate(84)
    cds = TuringCDS(valuationDate, maturityDate, cdsCoupon)
    cdsMarketContracts.append(cds)

    maturityDate = valuationDate.nextCDSDate(120)
    cds = TuringCDS(valuationDate, maturityDate, cdsCoupon)
    cdsMarketContracts.append(cds)

    maturityDate = valuationDate.nextCDSDate(180)
    cds = TuringCDS(valuationDate, maturityDate, cdsCoupon)
    cdsMarketContracts.append(cds)

    recoveryRate = 0.40

    issuerCurve = TuringCDSCurve(valuationDate,
                                 cdsMarketContracts,
                                 liborCurve,
                                 recoveryRate)

    return liborCurve, issuerCurve

##########################################################################


def test_fullPriceCDS1():

    mktSpread = 0.040

    testCases.header("Example", "Markit 9 Aug 2019")

    liborCurve, issuerCurve = buildFullIssuerCurve1(0.0, 0.0)

    # This is the 10 year contract at an off market coupon
    maturityDate = TuringDate(20, 6, 2029)
    cdsCoupon = 0.0150
    notional = ONE_MILLION
    longProtection = True
    tradeDate = TuringDate(9, 8, 2019)
    valuationDate = tradeDate.addDays(1)
    effectiveDate = valuationDate

    cdsContract = TuringCDS(effectiveDate,
                            maturityDate,
                            cdsCoupon,
                            notional,
                            longProtection)

    cdsRecovery = 0.40

    testCases.header("LABEL", "VALUE")
    spd = cdsContract.parSpread(
        valuationDate,
        issuerCurve,
        cdsRecovery) * 10000.0
    testCases.print("PAR_SPREAD", spd)

    v = cdsContract.value(valuationDate, issuerCurve, cdsRecovery)
    testCases.print("FULL_VALUE", v['full_pv'])
    testCases.print("CLEAN_VALUE", v['clean_pv'])

    p = cdsContract.cleanPrice(valuationDate, issuerCurve, cdsRecovery)
    testCases.print("CLEAN_PRICE", p)

    # MARKIT PRICE IS 168517
    
    accruedDays = cdsContract.accruedDays()
    testCases.print("ACCRUED_DAYS", accruedDays)

    accruedInterest = cdsContract.accruedInterest()
    testCases.print("ACCRUED_COUPON", accruedInterest)

    protPV = cdsContract.protectionLegPV(
        valuationDate, issuerCurve, cdsRecovery)
    testCases.print("PROTECTION_PV", protPV)

    premPV = cdsContract.premiumLegPV(valuationDate, issuerCurve, cdsRecovery)
    testCases.print("PREMIUM_PV", premPV)

    fullRPV01, cleanRPV01 = cdsContract.riskyPV01(valuationDate, issuerCurve)
    testCases.print("FULL_RPV01", fullRPV01)
    testCases.print("CLEAN_RPV01", cleanRPV01)

    # cdsContract.printFlows(issuerCurve)

    bump = 1.0 / 10000.0  # 1 bp

    liborCurve, issuerCurve = buildFullIssuerCurve1(bump, 0)
    v_bump = cdsContract.value(valuationDate, issuerCurve, cdsRecovery)
    dv = v_bump['full_pv'] - v['full_pv']
    testCases.print("CREDIT_DV01", dv)

    # Interest Rate Bump
    liborCurve, issuerCurve = buildFullIssuerCurve1(0, bump)
    v_bump = cdsContract.value(valuationDate, issuerCurve, cdsRecovery)
    dv = v_bump['full_pv'] - v['full_pv']
    testCases.print("INTEREST_DV01", dv)

    t = (maturityDate - valuationDate) / gDaysInYear
    z = liborCurve.df(maturityDate)
    r = -np.log(z) / t

    v_approx = cdsContract.valueFastApprox(valuationDate,
                                           r,
                                           mktSpread,
                                           cdsRecovery)

    testCases.print("FULL APPROX VALUE", v_approx[0])
    testCases.print("CLEAN APPROX VALUE", v_approx[1])
    testCases.print("APPROX CREDIT DV01", v_approx[2])
    testCases.print("APPROX INTEREST DV01", v_approx[3])

##########################################################################


def buildFullIssuerCurve2(mktSpreadBump, irBump):

    # https://www.markit.com/markit.jsp?jsppage=pv.jsp
    # YIELD CURVE 20 August 2020 SNAP AT 1600

    m = 1.0

    valuationDate = TuringDate(24, 8, 2020)
    settlementDate = TuringDate(24, 8, 2020)
    dcType = TuringDayCountTypes.ACT_360
    depos = []

    maturityDate = settlementDate.addMonths(1)
    depo1 = TuringIborDeposit(settlementDate, maturityDate, m * 0.001709, dcType)

    maturityDate = settlementDate.addMonths(2)
    depo2 = TuringIborDeposit(settlementDate, maturityDate, m * 0.002123, dcType)

    maturityDate = settlementDate.addMonths(3)
    depo3 = TuringIborDeposit(settlementDate, maturityDate, m * 0.002469, dcType)

    maturityDate = settlementDate.addMonths(6)
    depo4 = TuringIborDeposit(settlementDate, maturityDate, m * 0.003045, dcType)

    maturityDate = settlementDate.addMonths(12)
    depo5 = TuringIborDeposit(settlementDate, maturityDate, m * 0.004449, dcType)

    depos.append(depo1)
    depos.append(depo2)
    depos.append(depo3)
    depos.append(depo4)
    depos.append(depo5)

    swaps = []
    dcType = TuringDayCountTypes.THIRTY_E_360_ISDA
    fixedFreq = TuringFrequencyTypes.SEMI_ANNUAL

    maturityDate = settlementDate.addMonths(24)
    swap1 = TuringIborSwap(
        settlementDate,
        maturityDate,
        TuringSwapTypes.PAY,
        m * 0.002155 + irBump,
        fixedFreq,
        dcType)
    swaps.append(swap1)

    maturityDate = settlementDate.addMonths(36)
    swap2 = TuringIborSwap(
        settlementDate,
        maturityDate,
        TuringSwapTypes.PAY,
        m * 0.002305 + irBump,
        fixedFreq,
        dcType)
    swaps.append(swap2)

    maturityDate = settlementDate.addMonths(48)
    swap3 = TuringIborSwap(
        settlementDate,
        maturityDate,
        TuringSwapTypes.PAY,
        m * 0.002665 + irBump,
        fixedFreq,
        dcType)
    swaps.append(swap3)

    maturityDate = settlementDate.addMonths(60)
    swap4 = TuringIborSwap(
        settlementDate,
        maturityDate,
        TuringSwapTypes.PAY,
        m * 0.003290 + irBump,
        fixedFreq,
        dcType)
    swaps.append(swap4)

    liborCurve = TuringIborSingleCurve(valuationDate, depos, [], swaps)

    cdsCoupon = 0.01 + mktSpreadBump

    cdsMarketContracts = []
    effectiveDate = TuringDate(21, 8, 2020)
    cds = TuringCDS(effectiveDate, "6M", cdsCoupon)
    cdsMarketContracts.append(cds)

    cds = TuringCDS(effectiveDate, "1Y", cdsCoupon)
    cdsMarketContracts.append(cds)

    cds = TuringCDS(effectiveDate, "2Y", cdsCoupon)
    cdsMarketContracts.append(cds)

    cds = TuringCDS(effectiveDate, "3Y", cdsCoupon)
    cdsMarketContracts.append(cds)

    cds = TuringCDS(effectiveDate, "4Y", cdsCoupon)
    cdsMarketContracts.append(cds)

    cds = TuringCDS(effectiveDate, "5Y", cdsCoupon)
    cdsMarketContracts.append(cds)

    cds = TuringCDS(effectiveDate, "7Y", cdsCoupon)
    cdsMarketContracts.append(cds)

    cds = TuringCDS(effectiveDate, "10Y", cdsCoupon)
    cdsMarketContracts.append(cds)

    recoveryRate = 0.40

    issuerCurve = TuringCDSCurve(settlementDate,
                                 cdsMarketContracts,
                                 liborCurve,
                                 recoveryRate)

    testCases.header("DATE", "DISCOUNT_FACTOR", "SURV_PROB")
    years = np.linspace(0.0, 10.0, 20)
    dates = settlementDate.addYears(years)
    for dt in dates:
        df = liborCurve.df(dt)
        q = issuerCurve.survProb(dt)
        testCases.print("%16s" % dt, "%12.8f" % df, "%12.8f" % q)

    return liborCurve, issuerCurve

##########################################################################


def test_fullPriceCDSModelCheck():

    testCases.print("Example", "MARKIT CHECK 19 Aug 2020")

    liborCurve, issuerCurve = buildFullIssuerCurve2(0.0, 0.0)

    # This is the 10 year contract at an off market coupon
    maturityDate = TuringDate(20, 6, 2025)
    cdsCoupon = 0.050
    notional = ONE_MILLION
    longProtection = True
    tradeDate = TuringDate(20, 8, 2020)
    effectiveDate = TuringDate(21, 8, 2020)
    valuationDate = tradeDate

    cdsContract = TuringCDS(effectiveDate,
                            maturityDate,
                            cdsCoupon,
                            notional,
                            longProtection)

    cdsRecovery = 0.40

    testCases.header("LABEL", "VALUE")
    spd = cdsContract.parSpread(
        valuationDate,
        issuerCurve,
        cdsRecovery) * 10000.0
    testCases.print("PAR_SPREAD", spd)

    v = cdsContract.value(valuationDate, issuerCurve, cdsRecovery)
    testCases.print("FULL_VALUE", v['full_pv'])
    testCases.print("CLEAN_VALUE", v['clean_pv'])

    p = cdsContract.cleanPrice(valuationDate, issuerCurve, cdsRecovery)
    testCases.print("CLEAN_PRICE", p)

    accruedDays = cdsContract.accruedDays()
    testCases.print("ACCRUED_DAYS", accruedDays)

    accruedInterest = cdsContract.accruedInterest()
    testCases.print("ACCRUED_COUPON", accruedInterest)

    protPV = cdsContract.protectionLegPV(valuationDate, issuerCurve, cdsRecovery)
    testCases.print("PROTECTION_PV", protPV)

    premPV = cdsContract.premiumLegPV(valuationDate, issuerCurve, cdsRecovery)
    testCases.print("PREMIUM_PV", premPV)

    rpv01 = cdsContract.riskyPV01(valuationDate, issuerCurve)
    testCases.print("FULL_RPV01", rpv01['full_rpv01'])
    testCases.print("CLEAN_RPV01", rpv01['clean_rpv01'])

    creditDV01 = cdsContract.creditDV01(valuationDate, issuerCurve, cdsRecovery)
    testCases.print("CREDIT DV01", creditDV01)

    interestDV01 = cdsContract.interestDV01(valuationDate, issuerCurve, cdsRecovery)
    testCases.print("INTEREST DV01", interestDV01)

    # Consider fast approximation
    t = (maturityDate - valuationDate) / gDaysInYear
    z = liborCurve.df(maturityDate)
    r = -np.log(z) / t

    mktSpread = 0.01
    v_approx = cdsContract.valueFastApprox(valuationDate,
                                           r,
                                           mktSpread,
                                           cdsRecovery)

    testCases.header("FAST VALUATIONS", "VALUE")

    testCases.print("FULL APPROX VALUE", v_approx[0])
    testCases.print("CLEAN APPROX VALUE", v_approx[1])
    testCases.print("APPROX CREDIT DV01", v_approx[2])
    testCases.print("APPROX INTEREST DV01", v_approx[3])

##########################################################################


def test_fullPriceCDSConvergence():

    _, issuerCurve = buildFullIssuerCurve1(0.0, 0.0)

    # This is the 10 year contract at an off market coupon
    maturityDate = TuringDate(20, 6, 2029)
    cdsCoupon = 0.0150
    notional = ONE_MILLION
    longProtection = False
    tradeDate = TuringDate(9, 8, 2019)
    valuationDate = tradeDate.addDays(1)

    cdsContract = TuringCDS(valuationDate,
                            maturityDate,
                            cdsCoupon,
                            notional,
                            longProtection)

    cdsRecovery = 0.40

    testCases.header("NumSteps", "Value")
    for n in [10, 50, 100, 500, 1000]:
        v_full = cdsContract.value(
            valuationDate, issuerCurve, cdsRecovery, 0, 1, n)['full_pv']
        testCases.print(n, v_full)

##########################################################################


def test_CDSDateGeneration():

    # This is the 10 year contract at an off market coupon
    maturityDate = TuringDate(20, 6, 2029)
    cdsCoupon = 0.0100

    tradeDate = TuringDate(9, 8, 2019)
    valuationDate = tradeDate.addDays(1)

    cdsContract = TuringCDS(valuationDate,
                            maturityDate,
                            cdsCoupon,
                            ONE_MILLION,
                            True,
                            TuringFrequencyTypes.QUARTERLY,
                            TuringDayCountTypes.ACT_360,
                            TuringCalendarTypes.WEEKEND,
                            TuringBusDayAdjustTypes.FOLLOWING,
                            TuringDateGenRuleTypes.BACKWARD)

    testCases.header("Flow Date", "AccrualFactor", "Flow")
    numFlows = len(cdsContract._adjustedDates)
    for n in range(0, numFlows):
        testCases.print(str(
            cdsContract._adjustedDates[n]), cdsContract._accrualFactors[n],
            cdsContract._flows[n])

##########################################################################



test_CDSCurveBuildTiming()
test_fullPriceCDSModelCheck()
test_CDSDateGeneration()
test_fullPriceCDS1()
test_fullPriceCDSConvergence()
test_CDSCurveRepricing()
test_CDSFastApproximation()

testCases.compareTestCases()
