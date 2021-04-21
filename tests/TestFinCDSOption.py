import numpy as np
import sys
sys.path.append("..")

from turing_models.products.credit.cds_option import TuringCDSOption
from turing_models.products.credit.cds import TuringCDS
from turing_models.products.rates.ibor_swap import TuringIborSwap
from turing_models.products.rates.ibor_deposit import TuringIborDeposit
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


def buildFullIssuerCurve(valuationDate):

    dcType = TuringDayCountTypes.ACT_360
    depos = []
    irBump = 0.0

    m = 1.0  # 0.00000000000

    spotDays = 0
    settlementDate = valuationDate.addDays(spotDays)

    maturityDate = settlementDate.addMonths(1)
    depo1 = TuringIborDeposit(settlementDate, maturityDate, m * 0.0016, dcType)

    maturityDate = settlementDate.addMonths(2)
    depo2 = TuringIborDeposit(settlementDate, maturityDate, m * 0.0020, dcType)

    maturityDate = settlementDate.addMonths(3)
    depo3 = TuringIborDeposit(settlementDate, maturityDate, m * 0.0024, dcType)

    maturityDate = settlementDate.addMonths(6)
    depo4 = TuringIborDeposit(settlementDate, maturityDate, m * 0.0033, dcType)

    maturityDate = settlementDate.addMonths(12)
    depo5 = TuringIborDeposit(settlementDate, maturityDate, m * 0.0056, dcType)

    depos.append(depo1)
    depos.append(depo2)
    depos.append(depo3)
    depos.append(depo4)
    depos.append(depo5)

    fras = []

    spotDays = 2
    settlementDate = valuationDate.addDays(spotDays)

    swaps = []
    dcType = TuringDayCountTypes.THIRTY_E_360_ISDA
    fixedFreq = TuringFrequencyTypes.SEMI_ANNUAL

    maturityDate = settlementDate.addMonths(24)
    swap1 = TuringIborSwap(
        settlementDate,
        maturityDate,
        TuringSwapTypes.PAY,
        m * 0.0044 + irBump,
        fixedFreq,
        dcType)
    swaps.append(swap1)

    maturityDate = settlementDate.addMonths(36)
    swap2 = TuringIborSwap(
        settlementDate,
        maturityDate,
        TuringSwapTypes.PAY,
        m * 0.0078 + irBump,
        fixedFreq,
        dcType)
    swaps.append(swap2)

    maturityDate = settlementDate.addMonths(48)
    swap3 = TuringIborSwap(
        settlementDate,
        maturityDate,
        TuringSwapTypes.PAY,
        m * 0.0119 + irBump,
        fixedFreq,
        dcType)
    swaps.append(swap3)

    maturityDate = settlementDate.addMonths(60)
    swap4 = TuringIborSwap(
        settlementDate,
        maturityDate,
        TuringSwapTypes.PAY,
        m * 0.0158 + irBump,
        fixedFreq,
        dcType)
    swaps.append(swap4)

    maturityDate = settlementDate.addMonths(72)
    swap5 = TuringIborSwap(
        settlementDate,
        maturityDate,
        TuringSwapTypes.PAY,
        m * 0.0192 + irBump,
        fixedFreq,
        dcType)
    swaps.append(swap5)

    maturityDate = settlementDate.addMonths(84)
    swap6 = TuringIborSwap(
        settlementDate,
        maturityDate,
        TuringSwapTypes.PAY,
        m * 0.0219 + irBump,
        fixedFreq,
        dcType)
    swaps.append(swap6)

    maturityDate = settlementDate.addMonths(96)
    swap7 = TuringIborSwap(
        settlementDate,
        maturityDate,
        TuringSwapTypes.PAY,
        m * 0.0242 + irBump,
        fixedFreq,
        dcType)
    swaps.append(swap7)

    maturityDate = settlementDate.addMonths(108)
    swap8 = TuringIborSwap(
        settlementDate,
        maturityDate,
        TuringSwapTypes.PAY,
        m * 0.0261 + irBump,
        fixedFreq,
        dcType)
    swaps.append(swap8)

    maturityDate = settlementDate.addMonths(120)
    swap9 = TuringIborSwap(
        settlementDate,
        maturityDate,
        TuringSwapTypes.PAY,
        m * 0.0276 + irBump,
        fixedFreq,
        dcType)
    swaps.append(swap9)

    liborCurve = TuringIborSingleCurve(valuationDate, depos, fras, swaps)

    cdsMarketContracts = []
    cdsCoupon = 0.005743
    maturityDate = valuationDate.nextCDSDate(6)
    cds = TuringCDS(valuationDate, maturityDate, cdsCoupon)
    cdsMarketContracts.append(cds)

    cdsCoupon = 0.007497
    maturityDate = valuationDate.nextCDSDate(12)
    cds = TuringCDS(valuationDate, maturityDate, cdsCoupon)
    cdsMarketContracts.append(cds)

    cdsCoupon = 0.011132
    maturityDate = valuationDate.nextCDSDate(24)
    cds = TuringCDS(valuationDate, maturityDate, cdsCoupon)
    cdsMarketContracts.append(cds)

    cdsCoupon = 0.013932
    maturityDate = valuationDate.nextCDSDate(36)
    cds = TuringCDS(valuationDate, maturityDate, cdsCoupon)
    cdsMarketContracts.append(cds)

    cdsCoupon = 0.015764
    maturityDate = valuationDate.nextCDSDate(48)
    cds = TuringCDS(valuationDate, maturityDate, cdsCoupon)
    cdsMarketContracts.append(cds)

    cdsCoupon = 0.017366
    maturityDate = valuationDate.nextCDSDate(60)
    cds = TuringCDS(valuationDate, maturityDate, cdsCoupon)
    cdsMarketContracts.append(cds)

    cdsCoupon = 0.020928
    maturityDate = valuationDate.nextCDSDate(84)
    cds = TuringCDS(valuationDate, maturityDate, cdsCoupon)
    cdsMarketContracts.append(cds)

    cdsCoupon = 0.022835
    maturityDate = valuationDate.nextCDSDate(120)
    cds = TuringCDS(valuationDate, maturityDate, cdsCoupon)
    cdsMarketContracts.append(cds)

    recoveryRate = 0.40

    issuerCurve = TuringCDSCurve(valuationDate,
                                 cdsMarketContracts,
                                 liborCurve,
                                 recoveryRate)

    return liborCurve, issuerCurve

##########################################################################


def test_fullPriceCDSwaption():

    # This reproduces example on page 38 of Open Gamma note on CDS Option
    tradeDate = TuringDate(5, 2, 2014)
    _, issuerCurve = buildFullIssuerCurve(tradeDate)
    stepInDate = tradeDate.addDays(1)
    valuationDate = stepInDate
    expiryDate = TuringDate(20, 3, 2014)
    maturityDate = TuringDate(20, 6, 2019)

    cdsRecovery = 0.40
    notional = 100.0
    longProtection = False
    cdsCoupon = 0.0  # NOT KNOWN

    cdsContract = TuringCDS(stepInDate,
                            maturityDate,
                            cdsCoupon,
                            notional,
                            longProtection)

    testCases.banner(
        "=============================== CDS ===============================")
#    cdsContract.print(valuationDate)

    testCases.header("LABEL", "VALUE")
    spd = cdsContract.parSpread(
        valuationDate,
        issuerCurve,
        cdsRecovery) * 10000.0
    testCases.print("PAR SPREAD:", spd)

    v = cdsContract.value(valuationDate, issuerCurve, cdsRecovery)
    testCases.print("FULL VALUE", v['full_pv'])
    testCases.print("CLEAN VALUE", v['clean_pv'])

    p = cdsContract.cleanPrice(valuationDate, issuerCurve, cdsRecovery)
    testCases.print("CLEAN PRICE", p)

    accruedDays = cdsContract.accruedDays()
    testCases.print("ACCRUED DAYS", accruedDays)

    accruedInterest = cdsContract.accruedInterest()
    testCases.print("ACCRUED COUPON", accruedInterest)

    protPV = cdsContract.protectionLegPV(
        valuationDate, issuerCurve, cdsRecovery)
    testCases.print("PROTECTION LEG PV", protPV)

    premPV = cdsContract.premiumLegPV(valuationDate, issuerCurve, cdsRecovery)
    testCases.print("PREMIUM LEG PV", premPV)

    fullRPV01, cleanRPV01 = cdsContract.riskyPV01(valuationDate, issuerCurve)
    testCases.print("FULL  RPV01", fullRPV01)
    testCases.print("CLEAN RPV01", cleanRPV01)

#    cdsContract.printFlows(issuerCurve)

    testCases.banner(
        "=========================== FORWARD CDS ===========================")

    cdsContract = TuringCDS(expiryDate,
                            maturityDate,
                            cdsCoupon,
                            notional,
                            longProtection)

#    cdsContract.print(valuationDate)

    spd = cdsContract.parSpread(
        valuationDate,
        issuerCurve,
        cdsRecovery) * 10000.0
    testCases.print("PAR SPREAD", spd)

    v = cdsContract.value(valuationDate, issuerCurve, cdsRecovery)
    testCases.print("FULL VALUE", v['full_pv'])
    testCases.print("CLEAN VALUE", v['clean_pv'])

    protPV = cdsContract.protectionLegPV(
        valuationDate, issuerCurve, cdsRecovery)
    testCases.print("PROTECTION LEG PV", protPV)

    premPV = cdsContract.premiumLegPV(valuationDate, issuerCurve, cdsRecovery)
    testCases.print("PREMIUM LEG PV", premPV)

    fullRPV01, cleanRPV01 = cdsContract.riskyPV01(valuationDate, issuerCurve)
    testCases.print("FULL  RPV01", fullRPV01)
    testCases.print("CLEAN RPV01", cleanRPV01)

#    cdsContract.printFlows(issuerCurve)

    testCases.banner(
        "========================== CDS OPTIONS ============================")

    cdsCoupon = 0.01
    volatility = 0.3
    testCases.print("Expiry Date:", str(expiryDate))
    testCases.print("Maturity Date:", str(maturityDate))
    testCases.print("CDS Coupon:", cdsCoupon)

    testCases.header("STRIKE", "FULL VALUE", "IMPLIED VOL")

    for strike in np.linspace(100, 300, 41):

        cdsOption = TuringCDSOption(expiryDate,
                                    maturityDate,
                                    strike / 10000.0,
                                    notional)

        v = cdsOption.value(valuationDate,
                            issuerCurve,
                            volatility)

        vol = cdsOption.impliedVolatility(valuationDate,
                                          issuerCurve,
                                          v)

        testCases.print(strike, v, vol)

##########################################################################


test_fullPriceCDSwaption()
testCases.compareTestCases()
