###############################################################################
# Copyright (C) 2018, 2019, 2020 Dominic O'Kane
###############################################################################

import numpy as np
import time
import matplotlib.pyplot as plt

import sys
sys.path.append("..")

from turingmodel.turingutils.turing_date import TuringDate
from turingmodel.market.curves.turing_discount_curve import TuringDiscountCurve
from turingmodel.market.curves.turing_discount_curve_flat import TuringDiscountCurveFlat

from turingmodel.products.bonds.turing_bond import TuringBond
from turingmodel.turingutils.turing_frequency import TuringFrequencyTypes
from turingmodel.turingutils.turing_day_count import TuringDayCountTypes
from turingmodel.turingutils.turing_global_variables import gDaysInYear
from turingmodel.products.bonds.turing_bond_option import TuringBondOption
from turingmodel.turingutils.turing_global_types import TuringOptionTypes
from turingmodel.models.turing_model_rates_bk import TuringModelRatesBK

from TuringTestCases import TuringTestCases, globalTestCaseMode
testCases = TuringTestCases(__file__, globalTestCaseMode)

plotGraphs = False

###############################################################################


def test_FinBondOption():

    settlementDate = TuringDate(1, 12, 2019)
    issueDate = TuringDate(1, 12, 2018)
    maturityDate = settlementDate.addTenor("10Y")
    coupon = 0.05
    freqType = TuringFrequencyTypes.SEMI_ANNUAL
    accrualType = TuringDayCountTypes.ACT_ACT_ICMA
    bond = TuringBond(issueDate, maturityDate, coupon, freqType, accrualType)

    tmat = (maturityDate - settlementDate) / gDaysInYear
    times = np.linspace(0, tmat, 20)
    dates = settlementDate.addYears(times)
    dfs = np.exp(-0.05*times)
    discountCurve = TuringDiscountCurve(settlementDate, dates, dfs)

    expiryDate = settlementDate.addTenor("18m")
    strikePrice = 105.0
    face = 100.0

    ###########################################################################

    strikes = [80, 85, 90, 95, 100, 105, 110, 115, 120]

    optionType = TuringOptionTypes.EUROPEAN_CALL

    testCases.header("LABEL", "VALUE")

    price = bond.fullPriceFromDiscountCurve(settlementDate, discountCurve)
    testCases.print("Fixed Income Price:", price)

    numTimeSteps = 20

    testCases.header("OPTION TYPE AND MODEL", "STRIKE", "VALUE")

    for strikePrice in strikes:

        sigma = 0.20
        a = 0.1

        bondOption = TuringBondOption(bond, expiryDate, strikePrice, face, optionType)
        model = TuringModelRatesBK(sigma, a, numTimeSteps)
        v = bondOption.value(settlementDate, discountCurve, model)
        testCases.print("EUROPEAN CALL - BK", strikePrice, v)

    for strikePrice in strikes:

        sigma = 0.20
        a = 0.05

        bondOption = TuringBondOption(bond, expiryDate, strikePrice, face, optionType)
        model = TuringModelRatesBK(sigma, a, numTimeSteps)
        v = bondOption.value(settlementDate, discountCurve, model)
        testCases.print("EUROPEAN CALL - BK", strikePrice, v)

    ###########################################################################

    optionType = TuringOptionTypes.AMERICAN_CALL

    price = bond.fullPriceFromDiscountCurve(settlementDate, discountCurve)
    testCases.header("LABEL", "VALUE")
    testCases.print("Fixed Income Price:", price)

    testCases.header("OPTION TYPE AND MODEL", "STRIKE", "VALUE")

    for strikePrice in strikes:

        sigma = 0.01
        a = 0.1

        bondOption = TuringBondOption(bond, expiryDate, strikePrice, face, optionType)
        model = TuringModelRatesBK(sigma, a)
        v = bondOption.value(settlementDate, discountCurve, model)
        testCases.print("AMERICAN CALL - BK", strikePrice, v)

    for strikePrice in strikes:

        sigma = 0.20
        a = 0.05

        bondOption = TuringBondOption(bond, expiryDate, strikePrice, face, optionType)
        model = TuringModelRatesBK(sigma, a)
        v = bondOption.value(settlementDate, discountCurve, model)
        testCases.print("AMERICAN CALL - BK", strikePrice, v)

    ###########################################################################

    optionType = TuringOptionTypes.EUROPEAN_PUT

    price = bond.fullPriceFromDiscountCurve(settlementDate, discountCurve)

    for strikePrice in strikes:

        sigma = 0.01
        a = 0.1

        bondOption = TuringBondOption(bond, expiryDate, strikePrice, face, optionType)
        model = TuringModelRatesBK(sigma, a)
        v = bondOption.value(settlementDate, discountCurve, model)
        testCases.print("EUROPEAN PUT - BK", strikePrice, v)

    for strikePrice in strikes:

        sigma = 0.20
        a = 0.05

        bondOption = TuringBondOption(bond, expiryDate, strikePrice, face, optionType)
        model = TuringModelRatesBK(sigma, a)
        v = bondOption.value(settlementDate, discountCurve, model)
        testCases.print("EUROPEAN PUT - BK", strikePrice, v)

    ###########################################################################

    optionType = TuringOptionTypes.AMERICAN_PUT

    price = bond.fullPriceFromDiscountCurve(settlementDate, discountCurve)

    for strikePrice in strikes:

        sigma = 0.02
        a = 0.1

        bondOption = TuringBondOption(bond, expiryDate, strikePrice, face, optionType)
        model = TuringModelRatesBK(sigma, a)
        v = bondOption.value(settlementDate, discountCurve, model)
        testCases.print("AMERICAN PUT - BK", strikePrice, v)

    for strikePrice in strikes:

        sigma = 0.20
        a = 0.05

        bondOption = TuringBondOption(bond, expiryDate, strikePrice, face, optionType)
        model = TuringModelRatesBK(sigma, a)
        v = bondOption.value(settlementDate, discountCurve, model)
        testCases.print("AMERICAN PUT - BK", strikePrice, v)

###############################################################################


def test_FinBondOptionAmericanConvergenceONE():

    # Build discount curve
    settlementDate = TuringDate(1, 12, 2019)
    discountCurve = TuringDiscountCurveFlat(settlementDate, 0.05)

    # Bond details
    maturityDate = TuringDate(1, 9, 2025)
    issueDate = TuringDate(1, 9, 2016)
    coupon = 0.05
    freqType = TuringFrequencyTypes.SEMI_ANNUAL
    accrualType = TuringDayCountTypes.ACT_ACT_ICMA
    bond = TuringBond(issueDate, maturityDate, coupon, freqType, accrualType)

    # Option Details
    expiryDate = TuringDate(1, 12, 2020)
    strikePrice = 100.0
    face = 100.0

    testCases.header("TIME", "N", "PUT_AMER", "PUT_EUR",
                     "CALL_AME", "CALL_EUR")

    timeSteps = range(30, 100, 10)

    for numTimeSteps in timeSteps:

        sigma = 0.20
        a = 0.1

        start = time.time()

        optionType = TuringOptionTypes.AMERICAN_PUT
        bondOption1 = TuringBondOption(bond, expiryDate, strikePrice, face, optionType)
        model1 = TuringModelRatesBK(sigma, a, numTimeSteps)
        v1put = bondOption1.value(settlementDate, discountCurve, model1)

        optionType = TuringOptionTypes.EUROPEAN_PUT
        bondOption2 = TuringBondOption(bond, expiryDate, strikePrice, face, optionType)
        model2 = TuringModelRatesBK(sigma, a, numTimeSteps)
        v2put = bondOption2.value(settlementDate, discountCurve, model2)

        optionType = TuringOptionTypes.AMERICAN_CALL
        bondOption1 = TuringBondOption(bond, expiryDate, strikePrice, face, optionType)
        model1 = TuringModelRatesBK(sigma, a, numTimeSteps)
        v1call = bondOption1.value(settlementDate, discountCurve, model1)

        optionType = TuringOptionTypes.EUROPEAN_CALL
        bondOption2 = TuringBondOption(bond, expiryDate, strikePrice, face, optionType)
        model2 = TuringModelRatesBK(sigma, a, numTimeSteps)
        v2call = bondOption2.value(settlementDate, discountCurve, model2)

        end = time.time()

        period = end - start

        testCases.print(period, numTimeSteps, v1put, v2put, v1call, v2call)

###############################################################################


def test_FinBondOptionAmericanConvergenceTWO():

    # Build discount curve
    settlementDate = TuringDate(1, 12, 2019)
    discountCurve = TuringDiscountCurveFlat(settlementDate,
                                            0.05,
                                            TuringFrequencyTypes.CONTINUOUS)

    # Bond details
    issueDate = TuringDate(1, 9, 2014)
    maturityDate = TuringDate(1, 9, 2025)
    coupon = 0.05
    freqType = TuringFrequencyTypes.ANNUAL
    accrualType = TuringDayCountTypes.ACT_ACT_ICMA
    bond = TuringBond(issueDate, maturityDate, coupon, freqType, accrualType)
    expiryDate = settlementDate.addTenor("18m")
    face = 100.0

    spotValue = bond.fullPriceFromDiscountCurve(settlementDate, discountCurve)
    testCases.header("LABEL", "VALUE")
    testCases.print("BOND PRICE", spotValue)

    testCases.header("TIME", "N", "EUR_CALL", "AMER_CALL",
                     "EUR_PUT", "AMER_PUT")

    sigma = 0.2
    a = 0.1
    bkModel = TuringModelRatesBK(sigma, a)
    K = 101.0

    vec_ec = []
    vec_ac = []
    vec_ep = []
    vec_ap = []

    if 1 == 1:
        K = 100.0
        bkModel = TuringModelRatesBK(sigma, a, 100)
        europeanCallBondOption = TuringBondOption(bond, expiryDate, K, face,
                                                  TuringOptionTypes.EUROPEAN_CALL)

        v_ec = europeanCallBondOption.value(settlementDate, discountCurve,
                                            bkModel)
        testCases.header("LABEL", "VALUE")
        testCases.print("OPTION", v_ec)

    numStepsVector = range(100, 100, 1)  # should be 100-400

    for numSteps in numStepsVector:

        bkModel = TuringModelRatesBK(sigma, a, numSteps)

        start = time.time()

        europeanCallBondOption = TuringBondOption(bond, expiryDate, K, face,
                                                  TuringOptionTypes.EUROPEAN_CALL)
        v_ec = europeanCallBondOption.value(settlementDate, discountCurve,
                                            bkModel)

        americanCallBondOption = TuringBondOption(bond, expiryDate, K, face,
                                                  TuringOptionTypes.AMERICAN_CALL)
        v_ac = americanCallBondOption.value(settlementDate, discountCurve,
                                            bkModel)

        europeanPutBondOption = TuringBondOption(bond, expiryDate, K, face,
                                                 TuringOptionTypes.EUROPEAN_PUT)
        v_ep = europeanPutBondOption.value(settlementDate, discountCurve,
                                           bkModel)

        americanPutBondOption = TuringBondOption(bond, expiryDate, K, face,
                                                 TuringOptionTypes.AMERICAN_PUT)
        v_ap = americanPutBondOption.value(settlementDate, discountCurve,
                                           bkModel)

        end = time.time()
        period = end - start

        testCases.print(period, numSteps, v_ec, v_ac, v_ep, v_ap)

        vec_ec.append(v_ec)
        vec_ac.append(v_ac)
        vec_ep.append(v_ep)
        vec_ap.append(v_ap)

    if plotGraphs:

        plt.figure()
        plt.plot(numStepsVector, vec_ec, label="European Call")
        plt.legend()

        plt.figure()
        plt.plot(numStepsVector, vec_ac, label="American Call")
        plt.legend()

        plt.figure()
        plt.plot(numStepsVector, vec_ep, label="European Put")
        plt.legend()

        plt.figure()
        plt.plot(numStepsVector, vec_ap, label="American Put")
        plt.legend()

###############################################################################

def test_FinBondOptionZEROVOLConvergence():

    # Build discount curve
    settlementDate = TuringDate(1, 9, 2019)
    rate = 0.05
    discountCurve = TuringDiscountCurveFlat(settlementDate, rate, TuringFrequencyTypes.ANNUAL)

    # Bond details
    issueDate = TuringDate(1, 9, 2014)
    maturityDate = TuringDate(1, 9, 2025)
    coupon = 0.06
    freqType = TuringFrequencyTypes.ANNUAL
    accrualType = TuringDayCountTypes.ACT_ACT_ICMA
    bond = TuringBond(issueDate, maturityDate, coupon, freqType, accrualType)

    # Option Details
    expiryDate = TuringDate(1, 12, 2021)
    face = 100.0

    dfExpiry = discountCurve.df(expiryDate)
    fwdCleanValue = bond.cleanPriceFromDiscountCurve(expiryDate, discountCurve)
    fwdFullValue = bond.fullPriceFromDiscountCurve(expiryDate, discountCurve)
#    print("BOND FwdCleanBondPx", fwdCleanValue)
#    print("BOND FwdFullBondPx", fwdFullValue)
#    print("BOND Accrued:", bond._accruedInterest)

    spotCleanValue = bond.cleanPriceFromDiscountCurve(settlementDate, discountCurve)

    testCases.header("STRIKE", "STEPS",
                     "CALL_INT", "CALL_INT_PV", "CALL_EUR", "CALL_AMER",
                     "PUT_INT", "PUT_INT_PV", "PUT_EUR", "PUT_AMER") 

    numTimeSteps = range(100, 1000, 100)
    strikePrices = [90, 100, 110, 120]

    for strikePrice in strikePrices:
        
        callIntrinsic = max(spotCleanValue - strikePrice, 0)
        putIntrinsic = max(strikePrice - spotCleanValue, 0)
        callIntrinsicPV = max(fwdCleanValue - strikePrice, 0) * dfExpiry
        putIntrinsicPV = max(strikePrice - fwdCleanValue, 0) * dfExpiry

        for numSteps in numTimeSteps:

            sigma = 0.0000001
            a = 0.1
            model = TuringModelRatesBK(sigma, a, numSteps)
        
            optionType = TuringOptionTypes.EUROPEAN_CALL
            bondOption1 = TuringBondOption(bond, expiryDate, strikePrice, face, optionType)
            v1 = bondOption1.value(settlementDate, discountCurve, model)
    
            optionType = TuringOptionTypes.AMERICAN_CALL
            bondOption2 = TuringBondOption(bond, expiryDate, strikePrice, face, optionType)
            v2 = bondOption2.value(settlementDate, discountCurve, model)

            optionType = TuringOptionTypes.EUROPEAN_PUT
            bondOption3 = TuringBondOption(bond, expiryDate, strikePrice, face, optionType)
            v3 = bondOption3.value(settlementDate, discountCurve, model)
        
            optionType = TuringOptionTypes.AMERICAN_PUT
            bondOption4 = TuringBondOption(bond, expiryDate, strikePrice, face, optionType)
            v4 = bondOption4.value(settlementDate, discountCurve, model)
        
            testCases.print(strikePrice, numSteps,
                            callIntrinsic, callIntrinsicPV, v1, v2,
                            putIntrinsic, putIntrinsicPV, v3, v4)

###############################################################################


test_FinBondOptionZEROVOLConvergence()
test_FinBondOption()
test_FinBondOptionAmericanConvergenceONE()
test_FinBondOptionAmericanConvergenceTWO()
testCases.compareTestCases()
