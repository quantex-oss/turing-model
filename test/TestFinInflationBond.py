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
    settlementDate = TuringDate(21, 7, 2017)
    issueDate = TuringDate(15, 7, 2010)
    maturityDate = TuringDate(15, 7, 2020)
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
                               baseCPIValue)

    testCases.header("FIELD", "VALUE")
    cleanPrice = 104.03502

    yld = bond.currentYield(cleanPrice)
    testCases.print("Current Yield = ", yld)

    ###########################################################################
    # Inherited functions that just calculate real yield without CPI adjustments
    ###########################################################################

    ytm = bond.yieldToMaturity(settlementDate,
                               cleanPrice,
                               TuringYTMCalcType.UK_DMO)

    testCases.print("UK DMO REAL Yield To Maturity = ", ytm)

    ytm = bond.yieldToMaturity(settlementDate,
                               cleanPrice,
                               TuringYTMCalcType.US_STREET)

    testCases.print("US STREET REAL Yield To Maturity = ", ytm)

    ytm = bond.yieldToMaturity(settlementDate,
                               cleanPrice,
                               TuringYTMCalcType.US_TREASURY)

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
                                                   lastCpnCPIValue,
                                                   TuringYTMCalcType.US_TREASURY)

    testCases.print("Flat Price from Real YTM = ", cleanPrice)

    principal = bond.inflationPrincipal(settlementDate,
                                        ytm,
                                        refCPIValue,
                                        TuringYTMCalcType.US_TREASURY)

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
    settlementDate = TuringDate(23, 8, 2019)
    issueDate = TuringDate(25, 9, 2013)
    maturityDate = TuringDate(22, 3, 2068)
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
    fixingDates = TuringDate(31, 8, 2018).addMonths(months)
    fixingRates = [284.2, 284.1, 284.5, 284.6, 285.6, 283.0, 285.0,
                   285.1, 288.2, 289.2, 289.6, 289.5]    
    inflationIndex = TuringInflationIndexCurve(fixingDates, fixingRates, lag)
#    print(inflationIndex)
    ###########################################################################
        
    zciisData = [(TuringDate(31, 7, 2020), 3.1500000000137085),
                 (TuringDate(31, 7, 2021), 3.547500000013759),
                 (TuringDate(31, 7, 2022), 3.675000000013573),
                 (TuringDate(31, 7, 2023), 3.7250000000134342),
                 (TuringDate(31, 7, 2024), 3.750000000013265),
                 (TuringDate(31, 7, 2025), 3.7430000000129526),
                 (TuringDate(31, 7, 2026), 3.741200000012679),
                 (TuringDate(31, 7, 2027), 3.7337000000123632),
                 (TuringDate(31, 7, 2028), 3.725000000011902),
                 (TuringDate(31, 7, 2029), 3.720000000011603),
                 (TuringDate(31, 7, 2030), 3.712517289063011),
                 (TuringDate(31, 7, 2031), 3.7013000000108764),
                 (TuringDate(31, 7, 2032), 3.686986039205209),
                 (TuringDate(31, 7, 2033), 3.671102614032895),
                 (TuringDate(31, 7, 2034), 3.655000000009778),
                 (TuringDate(31, 7, 2035), 3.6394715951305834),
                 (TuringDate(31, 7, 2036), 3.624362044800966),
                 (TuringDate(31, 7, 2037), 3.6093619727979087),
                 (TuringDate(31, 7, 2038), 3.59421438364369),
                 (TuringDate(31, 7, 2039), 3.5787000000081948),
                 (TuringDate(31, 7, 2040), 3.5626192748395624),
                 (TuringDate(31, 7, 2041), 3.545765016376823),
                 (TuringDate(31, 7, 2042), 3.527943521613608),
                 (TuringDate(31, 7, 2043), 3.508977137925462),
                 (TuringDate(31, 7, 2044), 3.48870000000685),
                 (TuringDate(31, 7, 2045), 3.467083068721011),
                 (TuringDate(31, 7, 2046), 3.4445738220594935),
                 (TuringDate(31, 7, 2047), 3.4216470902302065),
                 (TuringDate(31, 7, 2048), 3.3986861494999188),
                 (TuringDate(31, 7, 2049), 3.376000000005752),
                 (TuringDate(31, 7, 2050), 3.3538412080641233),
                 (TuringDate(31, 7, 2051), 3.3324275806807746),
                 (TuringDate(31, 7, 2052), 3.311938788306623),
                 (TuringDate(31, 7, 2053), 3.2925208131865835),
                 (TuringDate(31, 7, 2054), 3.274293040759302),
                 (TuringDate(31, 7, 2055), 3.2573541974782794),
                 (TuringDate(31, 7, 2056), 3.241787355503245),
                 (TuringDate(31, 7, 2057), 3.227664186159851),
                 (TuringDate(31, 7, 2058), 3.2150486140060774),
                 (TuringDate(31, 7, 2059), 3.204000000004159),
                 (TuringDate(31, 7, 2060), 3.1945334946674064),
                 (TuringDate(31, 7, 2061), 3.1865047145143377),
                 (TuringDate(31, 7, 2062), 3.179753073456304),
                 (TuringDate(31, 7, 2063), 3.1741427790361154),
                 (TuringDate(31, 7, 2064), 3.1695593261025223),
                 (TuringDate(31, 7, 2065), 3.1659065919088736),
                 (TuringDate(31, 7, 2066), 3.163104428386987),
                 (TuringDate(31, 7, 2067), 3.1610866681252903),
                 (TuringDate(31, 7, 2068), 3.1597994770515836),
                 (TuringDate(31, 7, 2069), 3.159200000003204),
                 (TuringDate(31, 7, 2070), 3.159242349440139),
                 (TuringDate(31, 7, 2071), 3.1598400898057433),
                 (TuringDate(31, 7, 2072), 3.16090721831932),
                 (TuringDate(31, 7, 2073), 3.162369676612098),
                 (TuringDate(31, 7, 2074), 3.1641636543027207)]

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

    ytm = bond.yieldToMaturity(settlementDate,
                               cleanPrice,
                               TuringYTMCalcType.UK_DMO)

    testCases.print("UK DMO REAL Yield To Maturity = ", ytm)

    ytm = bond.yieldToMaturity(settlementDate,
                               cleanPrice,
                               TuringYTMCalcType.US_STREET)

    testCases.print("US STREET REAL Yield To Maturity = ", ytm)

    ytm = bond.yieldToMaturity(settlementDate,
                               cleanPrice,
                               TuringYTMCalcType.US_TREASURY)

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
                                                   lastCpnCPIValue,
                                                   TuringYTMCalcType.US_TREASURY)

    testCases.print("Flat Price from Real YTM = ", cleanPrice)

    principal = bond.inflationPrincipal(settlementDate,
                                        ytm,
                                        refCPIValue,
                                        TuringYTMCalcType.US_TREASURY)

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
