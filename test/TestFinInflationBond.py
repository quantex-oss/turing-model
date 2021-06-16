import numpy as np

import sys
sys.path.append("..")

from turing_models.utilities.frequency import TuringFrequencyTypes
from turing_models.utilities.day_count import TuringDayCountTypes
from turing_models.utilities.turing_date import TuringDate
from turing_models.products.inflation.inflation_bond import TuringInflationBond
from turing_models.products.bonds import TuringYTMCalcType
from turing_models.products.inflation.inflation_index_curve import TuringInflationIndexCurve
from fundamental.market.curves.discount_curve_zeros import TuringDiscountCurveZeros
from fundamental.market.curves.discount_curve_flat import TuringDiscountCurveFlat

from TuringTestCases import TuringTestCases, globalTestCaseMode
testCases = TuringTestCases(__file__, globalTestCaseMode)

##########################################################################


def test_FinInflationBondBBG():

    ##########################################################################
    # https://data.bloomberglp.com/bat/sites/3/2017/07/SF-2017_Paul-Fjeldsted.pdf
    # Look for CPI Bond example
    ##########################################################################

    testCases.banner("BLOOMBERG US TIPS EXAMPLE")
    settlementDate = TuringDate(2017, 7, 21)
    issueDate = TuringDate(2010, 7, 15)
    maturityDate = TuringDate(2020, 7, 15)
    coupon = 0.0125
    freqType = TuringFrequencyTypes.SEMI_ANNUAL
    accrualType = TuringDayCountTypes.ACT_ACT_ICMA
    face = 100.0
    baseCPIValue = 218.08532

    bond = TuringInflationBond(issueDate,
                               maturityDate,
                               coupon,
                               freqType,
                               accrualType,
                               face,
                               baseCPIValue,
                               convention=TuringYTMCalcType.UK_DMO)

    testCases.header("FIELD", "VALUE")
    cleanPrice = 104.03502

    yld = bond.currentYield(cleanPrice)
    testCases.print("Current Yield = ", yld)

    ###########################################################################
    # Inherited functions that just calculate real yield without CPI adjustments
    ###########################################################################

    ytm = bond.yieldToMaturity(settlementDate,
                               cleanPrice)

    testCases.print("UK DMO REAL Yield To Maturity = ", ytm)

    bond = TuringInflationBond(issueDate,
                               maturityDate,
                               coupon,
                               freqType,
                               accrualType,
                               face,
                               baseCPIValue,
                               convention=TuringYTMCalcType.US_STREET)

    ytm = bond.yieldToMaturity(settlementDate,
                               cleanPrice)

    testCases.print("US STREET REAL Yield To Maturity = ", ytm)

    bond = TuringInflationBond(issueDate,
                               maturityDate,
                               coupon,
                               freqType,
                               accrualType,
                               face,
                               baseCPIValue,
                               convention=TuringYTMCalcType.US_TREASURY)

    ytm = bond.yieldToMaturity(settlementDate,
                               cleanPrice)

    testCases.print("US TREASURY REAL Yield To Maturity = ", ytm)

    fullPrice = bond.fullPriceFromYTM(settlementDate, ytm)
    testCases.print("Full Price from REAL YTM = ", fullPrice)

    cleanPrice = bond.cleanPriceFromYTM(settlementDate, ytm)
    testCases.print("Clean Price from Real YTM = ", cleanPrice)

    accddays = bond._accruedDays
    testCases.print("Accrued Days = ", accddays)

    accd = bond._accruedInterest
    testCases.print("REAL Accrued Interest = ", accd)

    ###########################################################################
    # Inflation functions that calculate nominal yield with CPI adjustment
    ###########################################################################

    refCPIValue = 244.65884

    ###########################################################################

    cleanPrice = bond.cleanPriceFromYTM(settlementDate, ytm)
    testCases.print("Clean Price from Real YTM = ", cleanPrice)

    inflationAccd = bond.calcInflationAccruedInterest(settlementDate,
                                                      refCPIValue)

    testCases.print("Inflation Accrued = ", inflationAccd)

    lastCpnCPIValue = 244.61839

    cleanPrice = bond.flatPriceFromYieldToMaturity(settlementDate, ytm,
                                                   lastCpnCPIValue)

    testCases.print("Flat Price from Real YTM = ", cleanPrice)

    principal = bond.inflationPrincipal(settlementDate,
                                        ytm,
                                        refCPIValue)

    testCases.print("Inflation Principal = ", principal)

    ###########################################################################

    duration = bond.dollarDuration(settlementDate, ytm)
    testCases.print("Dollar Duration = ", duration)

    modifiedDuration = bond.modifiedDuration(settlementDate, ytm)
    testCases.print("Modified Duration = ", modifiedDuration)

    macauleyDuration = bond.macauleyDuration(settlementDate, ytm)
    testCases.print("Macauley Duration = ", macauleyDuration)

    conv = bond.convexityFromYTM(settlementDate, ytm)
    testCases.print("Convexity = ", conv)


###############################################################################
###############################################################################

def test_FinInflationBondStack():

    ##########################################################################
    # https://stackoverflow.com/questions/57676724/failing-to-obtain-correct-accrued-interest-with-quantlib-inflation-bond-pricer-i
    ##########################################################################

    testCases.banner("=============================")
    testCases.banner("QUANT FINANCE US TIPS EXAMPLE")
    testCases.banner("=============================")
    settlementDate = TuringDate(2019, 8, 23)
    issueDate = TuringDate(2013, 9, 25)
    maturityDate = TuringDate(2068, 3, 22)
    coupon = 0.00125
    freqType = TuringFrequencyTypes.SEMI_ANNUAL
    accrualType = TuringDayCountTypes.ACT_ACT_ICMA
    face = 100.0
    baseCPIValue = 249.70

    ###########################################################################
    # Discount curve
    discountCurve = TuringDiscountCurveFlat(settlementDate,
                                            0.01033692,
                                            TuringFrequencyTypes.ANNUAL,
                                            TuringDayCountTypes.ACT_ACT_ISDA)

    lag = 3
    fixingCPI = 244.65884
    fixingDate = settlementDate.addMonths(-lag)

    ###########################################################################
    # Create Index Curve
    months = range(0, 12, 1)
    fixingDates = TuringDate(2018, 8, 31).addMonths(months)
    fixingRates = [284.2, 284.1, 284.5, 284.6, 285.6, 283.0, 285.0,
                   285.1, 288.2, 289.2, 289.6, 289.5]
    inflationIndex = TuringInflationIndexCurve(fixingDates, fixingRates, lag)
#    print(inflationIndex)
    ###########################################################################

    zciisData = [(TuringDate(2020, 7, 31), 3.1500000000137085),
                 (TuringDate(2021, 7, 31), 3.547500000013759),
                 (TuringDate(2022, 7, 31), 3.675000000013573),
                 (TuringDate(2023, 7, 31), 3.7250000000134342),
                 (TuringDate(2024, 7, 31), 3.750000000013265),
                 (TuringDate(2025, 7, 31), 3.7430000000129526),
                 (TuringDate(2026, 7, 31), 3.741200000012679),
                 (TuringDate(2027, 7, 31), 3.7337000000123632),
                 (TuringDate(2028, 7, 31), 3.725000000011902),
                 (TuringDate(2029, 7, 31), 3.720000000011603),
                 (TuringDate(2030, 7, 31), 3.712517289063011),
                 (TuringDate(2031, 7, 31), 3.7013000000108764),
                 (TuringDate(2032, 7, 31), 3.686986039205209),
                 (TuringDate(2033, 7, 31), 3.671102614032895),
                 (TuringDate(2034, 7, 31), 3.655000000009778),
                 (TuringDate(2035, 7, 31), 3.6394715951305834),
                 (TuringDate(2036, 7, 31), 3.624362044800966),
                 (TuringDate(2037, 7, 31), 3.6093619727979087),
                 (TuringDate(2038, 7, 31), 3.59421438364369),
                 (TuringDate(2039, 7, 31), 3.5787000000081948),
                 (TuringDate(2040, 7, 31), 3.5626192748395624),
                 (TuringDate(2041, 7, 31), 3.545765016376823),
                 (TuringDate(2042, 7, 31), 3.527943521613608),
                 (TuringDate(2043, 7, 31), 3.508977137925462),
                 (TuringDate(2044, 7, 31), 3.48870000000685),
                 (TuringDate(2045, 7, 31), 3.467083068721011),
                 (TuringDate(2046, 7, 31), 3.4445738220594935),
                 (TuringDate(2047, 7, 31), 3.4216470902302065),
                 (TuringDate(2048, 7, 31), 3.3986861494999188),
                 (TuringDate(2049, 7, 31), 3.376000000005752),
                 (TuringDate(2050, 7, 31), 3.3538412080641233),
                 (TuringDate(2051, 7, 31), 3.3324275806807746),
                 (TuringDate(2052, 7, 31), 3.311938788306623),
                 (TuringDate(2053, 7, 31), 3.2925208131865835),
                 (TuringDate(2054, 7, 31), 3.274293040759302),
                 (TuringDate(2055, 7, 31), 3.2573541974782794),
                 (TuringDate(2056, 7, 31), 3.241787355503245),
                 (TuringDate(2057, 7, 31), 3.227664186159851),
                 (TuringDate(2058, 7, 31), 3.2150486140060774),
                 (TuringDate(2059, 7, 31), 3.204000000004159),
                 (TuringDate(2060, 7, 31), 3.1945334946674064),
                 (TuringDate(2061, 7, 31), 3.1865047145143377),
                 (TuringDate(2062, 7, 31), 3.179753073456304),
                 (TuringDate(2063, 7, 31), 3.1741427790361154),
                 (TuringDate(2064, 7, 31), 3.1695593261025223),
                 (TuringDate(2065, 7, 31), 3.1659065919088736),
                 (TuringDate(2066, 7, 31), 3.163104428386987),
                 (TuringDate(2067, 7, 31), 3.1610866681252903),
                 (TuringDate(2068, 7, 31), 3.1597994770515836),
                 (TuringDate(2069, 7, 31), 3.159200000003204),
                 (TuringDate(2070, 7, 31), 3.159242349440139),
                 (TuringDate(2071, 7, 31), 3.1598400898057433),
                 (TuringDate(2072, 7, 31), 3.16090721831932),
                 (TuringDate(2073, 7, 31), 3.162369676612098),
                 (TuringDate(2074, 7, 31), 3.1641636543027207)]

    zcDates = []
    zcRates = []
    for i in range(0, len(zciisData)):
        zcDates.append(zciisData[i][0])
        zcRates.append(zciisData[i][1]/100.0)

    inflationZeroCurve = TuringDiscountCurveZeros(settlementDate,
                                                  zcDates,
                                                  zcRates,
                                                  TuringFrequencyTypes.ANNUAL,
                                                  TuringDayCountTypes.ACT_ACT_ISDA)

#    print(inflationZeroCurve)

    ###########################################################################

    bond = TuringInflationBond(issueDate,
                               maturityDate,
                               coupon,
                               freqType,
                               accrualType,
                               face,
                               baseCPIValue)

    testCases.header("FIELD", "VALUE")
    cleanPrice = 104.03502

    yld = bond.currentYield(cleanPrice)
    testCases.print("Current Yield = ", yld)

    return

    ###########################################################################
    # Inherited functions that just calculate real yield without CPI adjustments
    ###########################################################################

    bond = TuringInflationBond(issueDate,
                               maturityDate,
                               coupon,
                               freqType,
                               accrualType,
                               face,
                               baseCPIValue,
                               convention=TuringYTMCalcType.UK_DMO)

    ytm = bond.yieldToMaturity(settlementDate,
                               cleanPrice)

    testCases.print("UK DMO REAL Yield To Maturity = ", ytm)

    bond = TuringInflationBond(issueDate,
                               maturityDate,
                               coupon,
                               freqType,
                               accrualType,
                               face,
                               baseCPIValue,
                               convention=TuringYTMCalcType.US_STREET)

    ytm = bond.yieldToMaturity(settlementDate,
                               cleanPrice)

    testCases.print("US STREET REAL Yield To Maturity = ", ytm)

    bond = TuringInflationBond(issueDate,
                               maturityDate,
                               coupon,
                               freqType,
                               accrualType,
                               face,
                               baseCPIValue,
                               convention=TuringYTMCalcType.US_TREASURY)

    ytm = bond.yieldToMaturity(settlementDate,
                               cleanPrice)

    testCases.print("US TREASURY REAL Yield To Maturity = ", ytm)

    fullPrice = bond.fullPriceFromYTM(settlementDate, ytm)
    testCases.print("Full Price from REAL YTM = ", fullPrice)

    cleanPrice = bond.cleanPriceFromYTM(settlementDate, ytm)
    testCases.print("Clean Price from Real YTM = ", cleanPrice)

    accddays = bond._accruedDays
    testCases.print("Accrued Days = ", accddays)

    accd = bond._accruedInterest
    testCases.print("REAL Accrued Interest = ", accd)

    ###########################################################################
    # Inflation functions that calculate nominal yield with CPI adjustment
    ###########################################################################




    ###########################################################################

    cleanPrice = bond.cleanPriceFromYTM(settlementDate, ytm)
    testCases.print("Clean Price from Real YTM = ", cleanPrice)

    inflationAccd = bond.calcInflationAccruedInterest(settlementDate,
                                                      refCPIValue)

    testCases.print("Inflation Accrued = ", inflationAccd)

    lastCpnCPIValue = 244.61839

    cleanPrice = bond.flatPriceFromYieldToMaturity(settlementDate, ytm,
                                                   lastCpnCPIValue)

    testCases.print("Flat Price from Real YTM = ", cleanPrice)

    principal = bond.inflationPrincipal(settlementDate,
                                        ytm,
                                        refCPIValue)

    testCases.print("Inflation Principal = ", principal)

    ###########################################################################

    duration = bond.dollarDuration(settlementDate, ytm)
    testCases.print("Dollar Duration = ", duration)

    modifiedDuration = bond.modifiedDuration(settlementDate, ytm)
    testCases.print("Modified Duration = ", modifiedDuration)

    macauleyDuration = bond.macauleyDuration(settlementDate, ytm)
    testCases.print("Macauley Duration = ", macauleyDuration)

    conv = bond.convexityFromYTM(settlementDate, ytm)
    testCases.print("Convexity = ", conv)

###############################################################################


test_FinInflationBondBBG()
test_FinInflationBondStack()
testCases.compareTestCases()
