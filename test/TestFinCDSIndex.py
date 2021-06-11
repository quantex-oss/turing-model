import sys
sys.path.append("..")

from turing_models.products.credit.cds import TuringCDS
from turing_models.utilities.mathematics import ONE_MILLION
from turing_models.products.rates.ibor_swap import TuringIborSwap
from turing_models.products.rates.ibor_single_curve import TuringIborSingleCurve
from turing_models.products.credit.cds_curve import TuringCDSCurve
from turing_models.utilities.frequency import TuringFrequencyTypes
from turing_models.utilities.day_count import TuringDayCountTypes
from turing_models.utilities.turing_date import TuringDate
from turing_models.utilities.global_types import TuringSwapTypes

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


def buildIssuerCurve(tradeDate, liborCurve):

    valuationDate = tradeDate.addDays(1)

    cdsMarketContracts = []

    cdsCoupon = 0.0048375
    maturityDate = TuringDate(2010, 6, 20)
    cds = TuringCDS(valuationDate, maturityDate, cdsCoupon)
    cdsMarketContracts.append(cds)

    recoveryRate = 0.40

    issuerCurve = TuringCDSCurve(valuationDate,
                                 cdsMarketContracts,
                                 liborCurve,
                                 recoveryRate)
    return issuerCurve

##########################################################################


def test_valueCDSIndex():

    # We treat an index as a CDS contract with a flat CDS curve
    tradeDate = TuringDate(2006, 2, 7)
    liborCurve = buildIborCurve(tradeDate)
    issuerCurve = buildIssuerCurve(tradeDate, liborCurve)
    stepInDate = tradeDate.addDays(1)
    valuationDate = stepInDate
    maturityDate = TuringDate(2010, 6, 20)

    cdsRecovery = 0.40
    notional = 10.0 * ONE_MILLION
    longProtection = True
    indexCoupon = 0.004

    cdsIndexContract = TuringCDS(stepInDate,
                                 maturityDate,
                                 indexCoupon,
                                 notional,
                                 longProtection)

#    cdsIndexContract.print(valuationDate)

    testCases.header("LABEL", "VALUE")

    spd = cdsIndexContract.parSpread(
        valuationDate, issuerCurve, cdsRecovery) * 10000.0
    testCases.print("PAR SPREAD", spd)

    v = cdsIndexContract.value(valuationDate, issuerCurve, cdsRecovery)
    testCases.print("FULL VALUE", v['full_pv'])
    testCases.print("CLEAN VALUE", v['clean_pv'])

    p = cdsIndexContract.cleanPrice(valuationDate, issuerCurve, cdsRecovery)
    testCases.print("CLEAN PRICE", p)

    accruedDays = cdsIndexContract.accruedDays()
    testCases.print("ACCRUED DAYS", accruedDays)

    accruedInterest = cdsIndexContract.accruedInterest()
    testCases.print("ACCRUED COUPON", accruedInterest)

    protPV = cdsIndexContract.protectionLegPV(
        valuationDate, issuerCurve, cdsRecovery)
    testCases.print("PROTECTION LEG PV", protPV)

    premPV = cdsIndexContract.premiumLegPV(
        valuationDate, issuerCurve, cdsRecovery)
    testCases.print("PREMIUM LEG PV", premPV)

    fullRPV01, cleanRPV01 = cdsIndexContract.riskyPV01(
        valuationDate, issuerCurve)
    testCases.print("FULL  RPV01", fullRPV01)
    testCases.print("CLEAN RPV01", cleanRPV01)

#    cdsIndexContract.printFlows(issuerCurve)


test_valueCDSIndex()
testCases.compareTestCases()
