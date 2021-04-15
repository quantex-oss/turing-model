###############################################################################
# Copyright (C) 2018, 2019, 2020 Dominic O'Kane
###############################################################################

import os
import time
import numpy as np

import sys
sys.path.append("..")

from turing_models.products.credit.turing_cds_index_portfolio import TuringCDSIndexPortfolio
from turing_models.products.credit.turing_cds_index_option import TuringCDSIndexOption
from turing_models.products.credit.turing_cds import TuringCDS
from turing_models.products.rates.turing_ibor_swap import TuringIborSwap
from turing_models.products.rates.turing_ibor_single_curve import TuringIborSingleCurve
from turing_models.products.credit.turing_cds_curve import TuringCDSCurve
from turing_models.turingutils.turing_frequency import TuringFrequencyTypes
from turing_models.turingutils.turing_day_count import TuringDayCountTypes
from turing_models.turingutils.turing_date import TuringDate
from turing_models.turingutils.turing_global_types import TuringSwapTypes

from TuringTestCases import TuringTestCases, globalTestCaseMode
testCases = TuringTestCases(__file__, globalTestCaseMode)

##########################################################################
# TO DO
##########################################################################


##########################################################################


def buildIborCurve(tradeDate):

    valuationDate = tradeDate.addDays(1)
    dcType = TuringDayCountTypes.ACT_360
    depos = []

    depos = []
    fras = []
    swaps = []

    dcType = TuringDayCountTypes.THIRTY_E_360_ISDA
    fixedFreq = TuringFrequencyTypes.SEMI_ANNUAL
    settlementDate = valuationDate

    maturityDate = settlementDate.addMonths(12)
    swap1 = TuringIborSwap(
        settlementDate,
        maturityDate,
        TuringSwapTypes.PAY,
        0.0502,
        fixedFreq,
        dcType)
    swaps.append(swap1)

    maturityDate = settlementDate.addMonths(24)
    swap2 = TuringIborSwap(
        settlementDate,
        maturityDate,
        TuringSwapTypes.PAY,
        0.0502,
        fixedFreq,
        dcType)
    swaps.append(swap2)

    maturityDate = settlementDate.addMonths(36)
    swap3 = TuringIborSwap(
        settlementDate,
        maturityDate,
        TuringSwapTypes.PAY,
        0.0501,
        fixedFreq,
        dcType)
    swaps.append(swap3)

    maturityDate = settlementDate.addMonths(48)
    swap4 = TuringIborSwap(
        settlementDate,
        maturityDate,
        TuringSwapTypes.PAY,
        0.0502,
        fixedFreq,
        dcType)
    swaps.append(swap4)

    maturityDate = settlementDate.addMonths(60)
    swap5 = TuringIborSwap(
        settlementDate,
        maturityDate,
        TuringSwapTypes.PAY,
        0.0501,
        fixedFreq,
        dcType)
    swaps.append(swap5)

    liborCurve = TuringIborSingleCurve(valuationDate, depos, fras, swaps)

    return liborCurve

##########################################################################


def buildFlatIssuerCurve(tradeDate, liborCurve, spread, recoveryRate):

    valuationDate = tradeDate.addDays(1)

    cdsMarketContracts = []

    maturityDate = TuringDate(29, 6, 2010)
    cds = TuringCDS(valuationDate, maturityDate, spread)
    cdsMarketContracts.append(cds)

    issuerCurve = TuringCDSCurve(valuationDate,
                                 cdsMarketContracts,
                                 liborCurve,
                                 recoveryRate)

    return issuerCurve

##########################################################################


def test_fullPriceCDSIndexOption():

    tradeDate = TuringDate(1, 8, 2007)
    stepInDate = tradeDate.addDays(1)
    valuationDate = stepInDate

    liborCurve = buildIborCurve(tradeDate)

    maturity3Y = tradeDate.nextCDSDate(36)
    maturity5Y = tradeDate.nextCDSDate(60)
    maturity7Y = tradeDate.nextCDSDate(84)
    maturity10Y = tradeDate.nextCDSDate(120)

    path = os.path.join(os.path.dirname(__file__), './/data//CDX_NA_IG_S7_SPREADS.csv')
    f = open(path, 'r')
    data = f.readlines()
    f.close()
    issuerCurves = []

    for row in data[1:]:

        splitRow = row.split(",")
        creditName = splitRow[0]
        spd3Y = float(splitRow[1]) / 10000.0
        spd5Y = float(splitRow[2]) / 10000.0
        spd7Y = float(splitRow[3]) / 10000.0
        spd10Y = float(splitRow[4]) / 10000.0
        recoveryRate = float(splitRow[5])

        cds3Y = TuringCDS(stepInDate, maturity3Y, spd3Y)
        cds5Y = TuringCDS(stepInDate, maturity5Y, spd5Y)
        cds7Y = TuringCDS(stepInDate, maturity7Y, spd7Y)
        cds10Y = TuringCDS(stepInDate, maturity10Y, spd10Y)
        cdsContracts = [cds3Y, cds5Y, cds7Y, cds10Y]

        issuerCurve = TuringCDSCurve(valuationDate,
                                     cdsContracts,
                                     liborCurve,
                                     recoveryRate)

        issuerCurves.append(issuerCurve)

    ##########################################################################
    ##########################################################################

    indexUpfronts = [0.0, 0.0, 0.0, 0.0]
    indexMaturityDates = [TuringDate(20, 12, 2009),
                          TuringDate(20, 12, 2011),
                          TuringDate(20, 12, 2013),
                          TuringDate(20, 12, 2016)]
    indexRecovery = 0.40

    testCases.banner(
        "======================= CDS INDEX OPTION ==========================")

    indexCoupon = 0.004
    volatility = 0.50
    expiryDate = TuringDate(1, 2, 2008)
    maturityDate = TuringDate(20, 12, 2011)
    notional = 10000.0
    tolerance = 1e-6

    testCases.header(
        "TIME",
        "STRIKE",
        "INDEX",
        "PAY",
        "RECEIVER",
        "G(K)",
        "X",
        "EXPH",
        "ABPAY",
        "ABREC")

    for index in np.linspace(20, 60, 10):

        #######################################################################

        cdsContracts = []
        for dt in indexMaturityDates:
            cds = TuringCDS(valuationDate, dt, index / 10000.0)
            cdsContracts.append(cds)

        indexCurve = TuringCDSCurve(valuationDate, cdsContracts,
                                    liborCurve, indexRecovery)

        if 1 == 1:

            indexSpreads = [index / 10000.0] * 4

            indexPortfolio = TuringCDSIndexPortfolio()
            adjustedIssuerCurves = indexPortfolio.hazardRateAdjustIntrinsic(
                valuationDate,
                issuerCurves,
                indexSpreads,
                indexUpfronts,
                indexMaturityDates,
                indexRecovery,
                tolerance)
        else:

            indexSpread = index / 10000.0
            issuerCurve = buildFlatIssuerCurve(tradeDate,
                                               liborCurve,
                                               indexSpread,
                                               indexRecovery)

            adjustedIssuerCurves = []
            for iCredit in range(0, 125):
                adjustedIssuerCurves.append(issuerCurve)

        #######################################################################

        for strike in np.linspace(20, 60, 20):

            start = time.time()

            option = TuringCDSIndexOption(expiryDate,
                                          maturityDate,
                                          indexCoupon,
                                          strike / 10000.0,
                                          notional)

            v_pay_1, v_rec_1, strikeValue, mu, expH = option.valueAnderson(
                valuationDate, adjustedIssuerCurves, indexRecovery, volatility)
            end = time.time()
            elapsed = end - start

            end = time.time()

            v_pay_2, v_rec_2 = option.valueAdjustedBlack(valuationDate,
                                                         indexCurve,
                                                         indexRecovery,
                                                         liborCurve,
                                                         volatility)

            elapsed = end - start

            testCases.print(
                elapsed,
                strike,
                index,
                v_pay_1,
                v_rec_1,
                strikeValue,
                mu,
                expH,
                v_pay_2,
                v_rec_2)

##########################################################################


test_fullPriceCDSIndexOption()
testCases.compareTestCases()
