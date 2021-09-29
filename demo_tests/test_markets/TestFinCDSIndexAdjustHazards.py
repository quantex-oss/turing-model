from os.path import dirname, join

import sys
sys.path.append("..")

from turing_models.instruments.archive.credit import TuringCDSIndexPortfolio
from turing_models.instruments.archive.credit.cds import TuringCDS
from turing_models.instruments.archive.rates import TuringIborSwap
from turing_models.instruments.archive.rates import TuringIborSingleCurve
from turing_models.instruments.archive.credit.cds_curve import TuringCDSCurve
from turing_models.utilities.frequency import TuringFrequencyTypes
from turing_models.utilities.day_count import TuringDayCountTypes
from turing_models.utilities.turing_date import TuringDate
from turing_models.utilities.global_types import TuringSwapTypes

from TuringTestCases import TuringTestCases, globalTestCaseMode
testCases = TuringTestCases(__file__, globalTestCaseMode)

##########################################################################
# TO DO
##########################################################################


def buildIborCurve(tradeDate):

    valuationDate = tradeDate.addDays(1)
    dcType = TuringDayCountTypes.ACT_360

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


def buildIssuerCurve(tradeDate, liborCurve):

    valuationDate = tradeDate.addDays(1)

    cdsMarketContracts = []

    cdsCoupon = 0.0048375
    maturityDate = TuringDate(29, 6, 2010)
    cds = TuringCDS(valuationDate, maturityDate, cdsCoupon)
    cdsMarketContracts.append(cds)

    recoveryRate = 0.40

    issuerCurve = TuringCDSCurve(valuationDate,
                                 cdsMarketContracts,
                                 liborCurve,
                                 recoveryRate)

    return issuerCurve

##########################################################################


def test_performCDSIndexHazardRateAdjustment():

    tradeDate = TuringDate(1, 8, 2007)
    stepInDate = tradeDate.addDays(1)
    valuationDate = stepInDate

    liborCurve = buildIborCurve(tradeDate)

    maturity3Y = tradeDate.nextCDSDate(36)
    maturity5Y = tradeDate.nextCDSDate(60)
    maturity7Y = tradeDate.nextCDSDate(84)
    maturity10Y = tradeDate.nextCDSDate(120)

    path = dirname(__file__)
    filename = "CDX_NA_IG_S7_SPREADS.csv"
    full_filename_path = join(path, "data", filename)
    f = open(full_filename_path, 'r')

    data = f.readlines()
    issuerCurves = []

    for row in data[1:]:

        splitRow = row.split(",")
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
    # Now determine the average spread of the index
    ##########################################################################

    cdsIndex = TuringCDSIndexPortfolio()

    averageSpd3Y = cdsIndex.averageSpread(valuationDate,
                                          stepInDate,
                                          maturity3Y,
                                          issuerCurves) * 10000.0

    averageSpd5Y = cdsIndex.averageSpread(valuationDate,
                                          stepInDate,
                                          maturity5Y,
                                          issuerCurves) * 10000.0

    averageSpd7Y = cdsIndex.averageSpread(valuationDate,
                                          stepInDate,
                                          maturity7Y,
                                          issuerCurves) * 10000.0

    averageSpd10Y = cdsIndex.averageSpread(valuationDate,
                                           stepInDate,
                                           maturity10Y,
                                           issuerCurves) * 10000.0

    testCases.header("LABEL", "VALUE")
    testCases.print("AVERAGE SPD 3Y", averageSpd3Y)
    testCases.print("AVERAGE SPD 5Y", averageSpd5Y)
    testCases.print("AVERAGE SPD 7Y", averageSpd7Y)
    testCases.print("AVERAGE SPD 10Y", averageSpd10Y)
    testCases.banner(
        "===================================================================")

    ##########################################################################
    # Now determine the intrinsic spread of the index to the same maturity dates
    # As the single name CDS contracts
    ##########################################################################

    cdsIndex = TuringCDSIndexPortfolio()

    intrinsicSpd3Y = cdsIndex.intrinsicSpread(valuationDate,
                                              stepInDate,
                                              maturity3Y,
                                              issuerCurves) * 10000.0

    intrinsicSpd5Y = cdsIndex.intrinsicSpread(valuationDate,
                                              stepInDate,
                                              maturity5Y,
                                              issuerCurves) * 10000.0

    intrinsicSpd7Y = cdsIndex.intrinsicSpread(valuationDate,
                                              stepInDate,
                                              maturity7Y,
                                              issuerCurves) * 10000.0

    intrinsicSpd10Y = cdsIndex.intrinsicSpread(valuationDate,
                                               stepInDate,
                                               maturity10Y,
                                               issuerCurves) * 10000.0

    ##########################################################################
    ##########################################################################

    testCases.header("LABEL", "VALUE")
    testCases.print("INTRINSIC SPD 3Y", intrinsicSpd3Y)
    testCases.print("INTRINSIC SPD 5Y", intrinsicSpd5Y)
    testCases.print("INTRINSIC SPD 7Y", intrinsicSpd7Y)
    testCases.print("INTRINSIC SPD 10Y", intrinsicSpd10Y)
    testCases.banner(
        "===================================================================")

    ##########################################################################
    ##########################################################################

    indexCoupons = [0.002, 0.0037, 0.0050, 0.0063]
    indexUpfronts = [0.0, 0.0, 0.0, 0.0]

    indexMaturityDates = [TuringDate(20, 12, 2009),
                          TuringDate(20, 12, 2011),
                          TuringDate(20, 12, 2013),
                          TuringDate(20, 12, 2016)]

    indexRecoveryRate = 0.40

    tolerance = 1e-6

    import time
    start = time.time()

    indexPortfolio = TuringCDSIndexPortfolio()
    adjustedIssuerCurves = indexPortfolio.hazardRateAdjustIntrinsic(
        valuationDate,
        issuerCurves,
        indexCoupons,
        indexUpfronts,
        indexMaturityDates,
        indexRecoveryRate,
        tolerance)

    end = time.time()
    testCases.header("TIME")
    testCases.print(end - start)

#    numCredits = len(issuerCurves)
#    testCases.print("#","MATURITY","CDS_UNADJ","CDS_ADJ")
#    for m in range(0,numCredits):
#        for cds in cdsContracts:
#            unadjustedSpread = cds.parSpread(valuationDate,issuerCurves[m])
#            adjustedSpread = cds.parSpread(valuationDate,adjustedIssuerCurves[m])
#            testCases.print(m,str(cds._maturityDate),"%10.3f"%(unadjustedSpread*10000),"%10.3f" %(adjustedSpread*10000))

    cdsIndex = TuringCDSIndexPortfolio()

    intrinsicSpd3Y = cdsIndex.intrinsicSpread(valuationDate,
                                              stepInDate,
                                              indexMaturityDates[0],
                                              adjustedIssuerCurves) * 10000.0

    intrinsicSpd5Y = cdsIndex.intrinsicSpread(valuationDate,
                                              stepInDate,
                                              indexMaturityDates[1],
                                              adjustedIssuerCurves) * 10000.0

    intrinsicSpd7Y = cdsIndex.intrinsicSpread(valuationDate,
                                              stepInDate,
                                              indexMaturityDates[2],
                                              adjustedIssuerCurves) * 10000.0

    intrinsicSpd10Y = cdsIndex.intrinsicSpread(valuationDate,
                                               stepInDate,
                                               indexMaturityDates[3],
                                               adjustedIssuerCurves) * 10000.0

    # If the adjustment works then this should equal the index spreads
    testCases.header("LABEL", "VALUE")
    testCases.print("ADJUSTED INTRINSIC SPD 3Y", intrinsicSpd3Y)
    testCases.print("ADJUSTED INTRINSIC SPD 5Y", intrinsicSpd5Y)
    testCases.print("ADJUSTED INTRINSIC SPD 7Y", intrinsicSpd7Y)
    testCases.print("ADJUSTED INTRINSIC SPD 10Y", intrinsicSpd10Y)

###############################################################################


test_performCDSIndexHazardRateAdjustment()
testCases.compareTestCases()
