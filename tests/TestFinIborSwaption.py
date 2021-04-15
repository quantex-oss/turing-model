###############################################################################
# Copyright (C) 2018, 2019, 2020 Dominic O'Kane
###############################################################################

import numpy as np

import sys
sys.path.append("..")

from turing_models.turingutils.turing_date import TuringDate
from turing_models.turingutils.turing_day_count import TuringDayCountTypes
from turing_models.turingutils.turing_frequency import TuringFrequencyTypes

from turing_models.products.rates.turing_ibor_deposit import TuringIborDeposit
from turing_models.products.rates.turing_ibor_swap import TuringIborSwap
from turing_models.products.rates.turing_ibor_swaption import TuringIborSwaption
from turing_models.products.rates.turing_ibor_swaption import TuringSwapTypes

from turing_models.models.turing_model_black import TuringModelBlack
from turing_models.models.turing_model_black_shifted import TuringModelBlackShifted
from turing_models.models.turing_model_sabr import TuringModelSABR
from turing_models.models.turing_model_sabr_shifted import TuringModelSABRShifted
from turing_models.models.turing_model_rates_hw import TuringModelRatesHW
from turing_models.models.turing_model_rates_bk import TuringModelRatesBK
from turing_models.models.turing_model_rates_bdt import TuringModelRatesBDT

from turing_models.products.rates.turing_ibor_single_curve import TuringIborSingleCurve
from turing_models.market.curves.turing_discount_curve_flat import TuringDiscountCurveFlat
from turing_models.market.curves.turing_discount_curve_zeros import TuringDiscountCurveZeros
from turing_models.market.curves.turing_interpolator import TuringInterpTypes

from TuringTestCases import TuringTestCases, globalTestCaseMode
testCases = TuringTestCases(__file__, globalTestCaseMode)

###############################################################################


def test_FinIborDepositsAndSwaps(valuationDate):

    depoBasis = TuringDayCountTypes.THIRTY_E_360_ISDA
    depos = []

    spotDays = 0
    settlementDate = valuationDate.addWeekDays(spotDays)
    depositRate = 0.05

    depo1 = TuringIborDeposit(settlementDate, "1M", depositRate, depoBasis)
    depo2 = TuringIborDeposit(settlementDate, "3M", depositRate, depoBasis)
    depo3 = TuringIborDeposit(settlementDate, "6M", depositRate, depoBasis)

    depos.append(depo1)
    depos.append(depo2)
    depos.append(depo3)

    fras = []

    swaps = []
    fixedBasis = TuringDayCountTypes.ACT_365F
    fixedFreq = TuringFrequencyTypes.SEMI_ANNUAL
    fixedLegType = TuringSwapTypes.PAY
    
    swapRate = 0.05
    swap1 = TuringIborSwap(settlementDate, "1Y", fixedLegType, swapRate, fixedFreq, fixedBasis)
    swap2 = TuringIborSwap(settlementDate, "3Y", fixedLegType, swapRate, fixedFreq, fixedBasis)
    swap3 = TuringIborSwap(settlementDate, "5Y", fixedLegType, swapRate, fixedFreq, fixedBasis)

    swaps.append(swap1)
    swaps.append(swap2)
    swaps.append(swap3)

    liborCurve = TuringIborSingleCurve(valuationDate, depos, fras, swaps)

    return liborCurve


##########################################################################

def testFinIborSwaptionModels():

    ##########################################################################
    # COMPARISON OF MODELS
    ##########################################################################

    valuationDate = TuringDate(1, 1, 2011)
    liborCurve = test_FinIborDepositsAndSwaps(valuationDate)

    exerciseDate = TuringDate(1, 1, 2012)
    swapMaturityDate = TuringDate(1, 1, 2017)

    swapFixedFrequencyType = TuringFrequencyTypes.SEMI_ANNUAL
    swapFixedDayCountType = TuringDayCountTypes.ACT_365F

    strikes = np.linspace(0.02, 0.08, 5)

    testCases.header("LAB", "STRIKE", "BLK", "BLK_SHFT", "SABR",
                     "SABR_SHFT", "HW", "BK")

    model1 = TuringModelBlack(0.00001)
    model2 = TuringModelBlackShifted(0.00001, 0.0)
    model3 = TuringModelSABR(0.013, 0.5, 0.5, 0.5)
    model4 = TuringModelSABRShifted(0.013, 0.5, 0.5, 0.5, -0.008)
    model5 = TuringModelRatesHW(0.00001, 0.00001)
    model6 = TuringModelRatesBK(0.01, 0.01)

    settlementDate = valuationDate.addWeekDays(2)

    for k in strikes:
        swaptionType = TuringSwapTypes.PAY
        swaption = TuringIborSwaption(settlementDate,
                                      exerciseDate,
                                      swapMaturityDate,
                                      swaptionType,
                                      k,
                                      swapFixedFrequencyType,
                                      swapFixedDayCountType)

        swap1 = swaption.value(valuationDate, liborCurve, model1)
        swap2 = swaption.value(valuationDate, liborCurve, model2)
        swap3 = swaption.value(valuationDate, liborCurve, model3)
        swap4 = swaption.value(valuationDate, liborCurve, model4)
        swap5 = swaption.value(valuationDate, liborCurve, model5)
        swap6 = swaption.value(valuationDate, liborCurve, model6)
        testCases.print("PAY", k, swap1, swap2, swap3, swap4, swap5, swap6)

    testCases.header("LABEL", "STRIKE", "BLK", "BLK_SHFTD", "SABR",
                     "SABR_SHFTD", "HW", "BK")

    for k in strikes:
        swaptionType = TuringSwapTypes.RECEIVE
        swaption = TuringIborSwaption(settlementDate,
                                      exerciseDate,
                                      swapMaturityDate,
                                      swaptionType,
                                      k,
                                      swapFixedFrequencyType,
                                      swapFixedDayCountType)

        swap1 = swaption.value(valuationDate, liborCurve, model1)
        swap2 = swaption.value(valuationDate, liborCurve, model2)
        swap3 = swaption.value(valuationDate, liborCurve, model3)
        swap4 = swaption.value(valuationDate, liborCurve, model4)
        swap5 = swaption.value(valuationDate, liborCurve, model5)
        swap6 = swaption.value(valuationDate, liborCurve, model6)
        testCases.print("REC", k, swap1, swap2, swap3, swap4, swap5, swap6)

###############################################################################


def test_FinIborSwaptionQLExample():

    valuationDate = TuringDate(4, 3, 2014)
    settlementDate = TuringDate(4, 3, 2014)

    depoDCCType = TuringDayCountTypes.THIRTY_E_360_ISDA
    depos = []
    depo = TuringIborDeposit(settlementDate, "1W", 0.0023, depoDCCType)
    depos.append(depo)
    depo = TuringIborDeposit(settlementDate, "1M", 0.0023, depoDCCType)
    depos.append(depo)
    depo = TuringIborDeposit(settlementDate, "3M", 0.0023, depoDCCType)
    depos.append(depo)
    depo = TuringIborDeposit(settlementDate, "6M", 0.0023, depoDCCType)
    depos.append(depo)

    # No convexity correction provided so I omit interest rate futures

    swaps = []
    accType = TuringDayCountTypes.ACT_365F
    fixedFreqType = TuringFrequencyTypes.SEMI_ANNUAL
    fixedLegType = TuringSwapTypes.PAY
    
    swap = TuringIborSwap(settlementDate, "3Y", fixedLegType, 0.00790, fixedFreqType, accType)
    swaps.append(swap)
    swap = TuringIborSwap(settlementDate, "4Y", fixedLegType, 0.01200, fixedFreqType, accType)
    swaps.append(swap)
    swap = TuringIborSwap(settlementDate, "5Y", fixedLegType, 0.01570, fixedFreqType, accType)
    swaps.append(swap)
    swap = TuringIborSwap(settlementDate, "6Y", fixedLegType, 0.01865, fixedFreqType, accType)
    swaps.append(swap)
    swap = TuringIborSwap(settlementDate, "7Y", fixedLegType, 0.02160, fixedFreqType, accType)
    swaps.append(swap)
    swap = TuringIborSwap(settlementDate, "8Y", fixedLegType, 0.02350, fixedFreqType, accType)
    swaps.append(swap)
    swap = TuringIborSwap(settlementDate, "9Y", fixedLegType, 0.02540, fixedFreqType, accType)
    swaps.append(swap)
    swap = TuringIborSwap(settlementDate, "10Y", fixedLegType, 0.0273, fixedFreqType, accType)
    swaps.append(swap)
    swap = TuringIborSwap(settlementDate, "15Y", fixedLegType, 0.0297, fixedFreqType, accType)
    swaps.append(swap)
    swap = TuringIborSwap(settlementDate, "20Y", fixedLegType, 0.0316, fixedFreqType, accType)
    swaps.append(swap)
    swap = TuringIborSwap(settlementDate, "25Y", fixedLegType, 0.0335, fixedFreqType, accType)
    swaps.append(swap)
    swap = TuringIborSwap(settlementDate, "30Y", fixedLegType, 0.0354, fixedFreqType, accType)
    swaps.append(swap)

    liborCurve = TuringIborSingleCurve(valuationDate, depos, [], swaps,
                                       TuringInterpTypes.LINEAR_ZERO_RATES)

    exerciseDate = settlementDate.addTenor("5Y")
    swapMaturityDate = exerciseDate.addTenor("5Y")
    swapFixedCoupon = 0.040852
    swapFixedFrequencyType = TuringFrequencyTypes.SEMI_ANNUAL
    swapFixedDayCountType = TuringDayCountTypes.THIRTY_E_360_ISDA
    swapFloatFrequencyType = TuringFrequencyTypes.QUARTERLY
    swapFloatDayCountType = TuringDayCountTypes.ACT_360
    swapNotional = 1000000
    swaptionType = TuringSwapTypes.PAY

    swaption = TuringIborSwaption(settlementDate,
                                  exerciseDate,
                                  swapMaturityDate,
                                  swaptionType,
                                  swapFixedCoupon,
                                  swapFixedFrequencyType,
                                  swapFixedDayCountType,
                                  swapNotional,
                                  swapFloatFrequencyType,
                                  swapFloatDayCountType)

    testCases.header("MODEL", "VALUE")

    model = TuringModelBlack(0.1533)
    v = swaption.value(settlementDate, liborCurve, model)
    testCases.print(model.__class__, v)

    model = TuringModelBlackShifted(0.1533, -0.008)
    v = swaption.value(settlementDate, liborCurve, model)
    testCases.print(model.__class__, v)

    model = TuringModelSABR(0.132, 0.5, 0.5, 0.5)
    v = swaption.value(settlementDate, liborCurve, model)
    testCases.print(model.__class__, v)

    model = TuringModelSABRShifted(0.352, 0.5, 0.15, 0.15, -0.005)
    v = swaption.value(settlementDate, liborCurve, model)
    testCases.print(model.__class__, v)

    model = TuringModelRatesHW(0.010000000, 0.00000000001)
    v = swaption.value(settlementDate, liborCurve, model)
    testCases.print(model.__class__, v)

###############################################################################


def testFinIborCashSettledSwaption():

    testCases.header("LABEL", "VALUE")

    valuationDate = TuringDate(1, 1, 2020)
    settlementDate = TuringDate(1, 1, 2020)

    depoDCCType = TuringDayCountTypes.THIRTY_E_360_ISDA
    depos = []
    depo = TuringIborDeposit(settlementDate, "1W", 0.0023, depoDCCType)
    depos.append(depo)
    depo = TuringIborDeposit(settlementDate, "1M", 0.0023, depoDCCType)
    depos.append(depo)
    depo = TuringIborDeposit(settlementDate, "3M", 0.0023, depoDCCType)
    depos.append(depo)
    depo = TuringIborDeposit(settlementDate, "6M", 0.0023, depoDCCType)
    depos.append(depo)

    # No convexity correction provided so I omit interest rate futures

    settlementDate = TuringDate(2, 1, 2020)

    swaps = []
    accType = TuringDayCountTypes.ACT_365F
    fixedFreqType = TuringFrequencyTypes.SEMI_ANNUAL
    fixedLegType = TuringSwapTypes.PAY
    
    swap = TuringIborSwap(settlementDate, "3Y", fixedLegType, 0.00790, fixedFreqType, accType)
    swaps.append(swap)
    swap = TuringIborSwap(settlementDate, "4Y", fixedLegType, 0.01200, fixedFreqType, accType)
    swaps.append(swap)
    swap = TuringIborSwap(settlementDate, "5Y", fixedLegType, 0.01570, fixedFreqType, accType)
    swaps.append(swap)
    swap = TuringIborSwap(settlementDate, "6Y", fixedLegType, 0.01865, fixedFreqType, accType)
    swaps.append(swap)
    swap = TuringIborSwap(settlementDate, "7Y", fixedLegType, 0.02160, fixedFreqType, accType)
    swaps.append(swap)
    swap = TuringIborSwap(settlementDate, "8Y", fixedLegType, 0.02350, fixedFreqType, accType)
    swaps.append(swap)
    swap = TuringIborSwap(settlementDate, "9Y", fixedLegType, 0.02540, fixedFreqType, accType)
    swaps.append(swap)
    swap = TuringIborSwap(settlementDate, "10Y", fixedLegType, 0.0273, fixedFreqType, accType)
    swaps.append(swap)
    swap = TuringIborSwap(settlementDate, "15Y", fixedLegType, 0.0297, fixedFreqType, accType)
    swaps.append(swap)
    swap = TuringIborSwap(settlementDate, "20Y", fixedLegType, 0.0316, fixedFreqType, accType)
    swaps.append(swap)
    swap = TuringIborSwap(settlementDate, "25Y", fixedLegType, 0.0335, fixedFreqType, accType)
    swaps.append(swap)
    swap = TuringIborSwap(settlementDate, "30Y", fixedLegType, 0.0354, fixedFreqType, accType)
    swaps.append(swap)

    liborCurve = TuringIborSingleCurve(valuationDate, depos, [], swaps,
                                       TuringInterpTypes.LINEAR_ZERO_RATES)

    exerciseDate = settlementDate.addTenor("5Y")
    swapMaturityDate = exerciseDate.addTenor("5Y")
    swapFixedCoupon = 0.040852
    swapFixedFrequencyType = TuringFrequencyTypes.SEMI_ANNUAL
    swapFixedDayCountType = TuringDayCountTypes.THIRTY_E_360_ISDA
    swapFloatFrequencyType = TuringFrequencyTypes.QUARTERLY
    swapFloatDayCountType = TuringDayCountTypes.ACT_360
    swapNotional = 1000000
    fixedLegType = TuringSwapTypes.PAY

    swaption = TuringIborSwaption(settlementDate,
                                  exerciseDate,
                                  swapMaturityDate,
                                  fixedLegType,
                                  swapFixedCoupon,
                                  swapFixedFrequencyType,
                                  swapFixedDayCountType,
                                  swapNotional,
                                  swapFloatFrequencyType,
                                  swapFloatDayCountType)

    model = TuringModelBlack(0.1533)
    v = swaption.value(settlementDate, liborCurve, model)
    testCases.print("Swaption No-Arb Value:", v)

    fwdSwapRate1 = liborCurve.swapRate(exerciseDate,
                                       swapMaturityDate,
                                       swapFixedFrequencyType,
                                       swapFixedDayCountType)

    testCases.print("Curve Fwd Swap Rate:", fwdSwapRate1)

    fwdSwap = TuringIborSwap(exerciseDate,
                             swapMaturityDate,
                             fixedLegType,
                             swapFixedCoupon,
                             swapFixedFrequencyType,
                             swapFixedDayCountType)

    fwdSwapRate2 = fwdSwap.swapRate(settlementDate, liborCurve)
    testCases.print("Fwd Swap Swap Rate:", fwdSwapRate2)

    model = TuringModelBlack(0.1533)

    v = swaption.cashSettledValue(valuationDate,
                                  liborCurve,
                                  fwdSwapRate2,
                                  model)

    testCases.print("Swaption Cash Settled Value:", v)

###############################################################################


def testFinIborSwaptionMatlabExamples():

    # We value a European swaption using Black's model and try to replicate a
    # ML example at https://fr.mathworks.com/help/fininst/swaptionbyblk.html

    testCases.header("=======================================")
    testCases.header("MATLAB EXAMPLE WITH FLAT TERM STRUCTURE")
    testCases.header("=======================================")

    valuationDate = TuringDate(1, 1, 2010)
    liborCurve = TuringDiscountCurveFlat(valuationDate, 0.06,
                                         TuringFrequencyTypes.CONTINUOUS,
                                         TuringDayCountTypes.THIRTY_E_360)

    settlementDate = TuringDate(1, 1, 2011)
    exerciseDate = TuringDate(1, 1, 2016)
    maturityDate = TuringDate(1, 1, 2019)

    fixedCoupon = 0.062
    fixedFrequencyType = TuringFrequencyTypes.SEMI_ANNUAL
    fixedDayCountType = TuringDayCountTypes.THIRTY_E_360_ISDA
    notional = 100.0

    # Pricing a PAY
    swaptionType = TuringSwapTypes.PAY
    swaption = TuringIborSwaption(settlementDate,
                                  exerciseDate,
                                  maturityDate,
                                  swaptionType,
                                  fixedCoupon,
                                  fixedFrequencyType,
                                  fixedDayCountType,
                                  notional)

    model = TuringModelBlack(0.20)
    v_finpy = swaption.value(valuationDate, liborCurve, model)
    v_matlab = 2.071

    testCases.header("LABEL", "VALUE")
    testCases.print("FP Price:", v_finpy)
    testCases.print("MATLAB Prix:", v_matlab)
    testCases.print("DIFF:", v_finpy - v_matlab)

###############################################################################

    testCases.header("===================================")
    testCases.header("MATLAB EXAMPLE WITH TERM STRUCTURE")
    testCases.header("===================================")

    valuationDate = TuringDate(1, 1, 2010)

    dates = [TuringDate(1, 1, 2011), TuringDate(1, 1, 2012), TuringDate(1, 1, 2013),
             TuringDate(1, 1, 2014), TuringDate(1, 1, 2015)]

    zeroRates = [0.03, 0.034, 0.037, 0.039, 0.040]

    contFreq = TuringFrequencyTypes.CONTINUOUS
    interpType = TuringInterpTypes.LINEAR_ZERO_RATES
    dayCountType = TuringDayCountTypes.THIRTY_E_360

    liborCurve = TuringDiscountCurveZeros(valuationDate, dates,
                                          zeroRates, contFreq,
                                          dayCountType, interpType)

    settlementDate = TuringDate(1, 1, 2011)
    exerciseDate = TuringDate(1, 1, 2012)
    maturityDate = TuringDate(1, 1, 2017)
    fixedCoupon = 0.03

    fixedFrequencyType = TuringFrequencyTypes.SEMI_ANNUAL
    fixedDayCountType = TuringDayCountTypes.THIRTY_E_360
    floatFrequencyType = TuringFrequencyTypes.SEMI_ANNUAL
    floatDayCountType = TuringDayCountTypes.THIRTY_E_360
    notional = 1000.0

    # Pricing a put
    swaptionType = TuringSwapTypes.RECEIVE
    swaption = TuringIborSwaption(settlementDate,
                                  exerciseDate,
                                  maturityDate,
                                  swaptionType,
                                  fixedCoupon,
                                  fixedFrequencyType,
                                  fixedDayCountType,
                                  notional,
                                  floatFrequencyType,
                                  floatDayCountType)

    model = TuringModelBlack(0.21)
    v_finpy = swaption.value(valuationDate, liborCurve, model)
    v_matlab = 0.5771

    testCases.header("LABEL", "VALUE")
    testCases.print("FP Price:", v_finpy)
    testCases.print("MATLAB Prix:", v_matlab)
    testCases.print("DIFF:", v_finpy - v_matlab)

###############################################################################

    testCases.header("===================================")
    testCases.header("MATLAB EXAMPLE WITH SHIFTED BLACK")
    testCases.header("===================================")

    valuationDate = TuringDate(1, 1, 2016)

    dates = [TuringDate(1, 1, 2017), TuringDate(1, 1, 2018), TuringDate(1, 1, 2019),
             TuringDate(1, 1, 2020), TuringDate(1, 1, 2021)]

    zeroRates = np.array([-0.02, 0.024, 0.047, 0.090, 0.12])/100.0

    contFreq = TuringFrequencyTypes.ANNUAL
    interpType = TuringInterpTypes.LINEAR_ZERO_RATES
    dayCountType = TuringDayCountTypes.THIRTY_E_360

    liborCurve = TuringDiscountCurveZeros(valuationDate, dates, zeroRates,
                                          contFreq, dayCountType, interpType)

    settlementDate = TuringDate(1, 1, 2016)
    exerciseDate = TuringDate(1, 1, 2017)
    maturityDate = TuringDate(1, 1, 2020)
    fixedCoupon = -0.003

    fixedFrequencyType = TuringFrequencyTypes.SEMI_ANNUAL
    fixedDayCountType = TuringDayCountTypes.THIRTY_E_360_ISDA
    floatFrequencyType = TuringFrequencyTypes.SEMI_ANNUAL
    floatDayCountType = TuringDayCountTypes.THIRTY_E_360_ISDA
    notional = 1000.0

    # Pricing a PAY
    swaptionType = TuringSwapTypes.PAY
    swaption = TuringIborSwaption(settlementDate,
                                  exerciseDate,
                                  maturityDate,
                                  swaptionType,
                                  fixedCoupon,
                                  fixedFrequencyType,
                                  fixedDayCountType,
                                  notional,
                                  floatFrequencyType,
                                  floatDayCountType)

    model = TuringModelBlackShifted(0.31, 0.008)
    v_finpy = swaption.value(valuationDate, liborCurve, model)
    v_matlab = 12.8301

    testCases.header("LABEL", "VALUE")
    testCases.print("FP Price:", v_finpy)
    testCases.print("MATLAB Prix:", v_matlab)
    testCases.print("DIFF:", v_finpy - v_matlab)

###############################################################################

    testCases.header("===================================")
    testCases.header("MATLAB EXAMPLE WITH HULL WHITE")
    testCases.header("===================================")

    # https://fr.mathworks.com/help/fininst/swaptionbyhw.html

    valuationDate = TuringDate(1, 1, 2007)

    dates = [TuringDate(1, 1, 2007), TuringDate(1, 7, 2007), TuringDate(1, 1, 2008),
             TuringDate(1, 7, 2008), TuringDate(1, 1, 2009), TuringDate(1, 7, 2009),
             TuringDate(1, 1, 2010), TuringDate(1, 7, 2010),
             TuringDate(1, 1, 2011), TuringDate(1, 7, 2011), TuringDate(1, 1, 2012)]

    zeroRates = np.array([0.075] * 11)
    interpType = TuringInterpTypes.FLAT_FWD_RATES
    dayCountType = TuringDayCountTypes.THIRTY_E_360_ISDA
    contFreq = TuringFrequencyTypes.SEMI_ANNUAL

    liborCurve = TuringDiscountCurveZeros(valuationDate, dates, zeroRates,
                                          contFreq,
                                          dayCountType, interpType)

    settlementDate = valuationDate
    exerciseDate = TuringDate(1, 1, 2010)
    maturityDate = TuringDate(1, 1, 2012)
    fixedCoupon = 0.04

    fixedFrequencyType = TuringFrequencyTypes.SEMI_ANNUAL
    fixedDayCountType = TuringDayCountTypes.THIRTY_E_360_ISDA
    notional = 100.0

    swaptionType = TuringSwapTypes.RECEIVE
    swaption = TuringIborSwaption(settlementDate,
                                  exerciseDate,
                                  maturityDate,
                                  swaptionType,
                                  fixedCoupon,
                                  fixedFrequencyType,
                                  fixedDayCountType,
                                  notional)

    model = TuringModelRatesHW(0.05, 0.01)
    v_finpy = swaption.value(valuationDate, liborCurve, model)
    v_matlab = 2.9201

    testCases.header("LABEL", "VALUE")
    testCases.print("FP Price:", v_finpy)
    testCases.print("MATLAB Prix:", v_matlab)
    testCases.print("DIFF:", v_finpy - v_matlab)

###############################################################################

    testCases.header("====================================")
    testCases.header("MATLAB EXAMPLE WITH BLACK KARASINSKI")
    testCases.header("====================================")

    # https://fr.mathworks.com/help/fininst/swaptionbybk.html
    valuationDate = TuringDate(1, 1, 2007)

    dates = [TuringDate(1, 1, 2007), TuringDate(1, 7, 2007), TuringDate(1, 1, 2008),
             TuringDate(1, 7, 2008), TuringDate(1, 1, 2009), TuringDate(1, 7, 2009),
             TuringDate(1, 1, 2010), TuringDate(1, 7, 2010),
             TuringDate(1, 1, 2011), TuringDate(1, 7, 2011), TuringDate(1, 1, 2012)]

    zeroRates = np.array([0.07] * 11)

    interpType = TuringInterpTypes.FLAT_FWD_RATES
    dayCountType = TuringDayCountTypes.THIRTY_E_360_ISDA
    contFreq = TuringFrequencyTypes.SEMI_ANNUAL

    liborCurve = TuringDiscountCurveZeros(valuationDate, dates, zeroRates,
                                          contFreq, dayCountType, interpType)

    settlementDate = valuationDate
    exerciseDate = TuringDate(1, 1, 2011)
    maturityDate = TuringDate(1, 1, 2012)

    fixedFrequencyType = TuringFrequencyTypes.SEMI_ANNUAL
    fixedDayCountType = TuringDayCountTypes.THIRTY_E_360_ISDA
    notional = 100.0

    model = TuringModelRatesBK(0.1, 0.05, 200)

    fixedCoupon = 0.07
    swaptionType = TuringSwapTypes.PAY
    swaption = TuringIborSwaption(settlementDate,
                                  exerciseDate,
                                  maturityDate,
                                  swaptionType,
                                  fixedCoupon,
                                  fixedFrequencyType,
                                  fixedDayCountType,
                                  notional)

    v_finpy = swaption.value(valuationDate, liborCurve, model)
    v_matlab = 0.3634

    testCases.header("LABEL", "VALUE")
    testCases.print("FP Price:", v_finpy)
    testCases.print("MATLAB Prix:", v_matlab)
    testCases.print("DIFF:", v_finpy - v_matlab)

    fixedCoupon = 0.0725
    swaptionType = TuringSwapTypes.RECEIVE
    swaption = TuringIborSwaption(settlementDate,
                                  exerciseDate,
                                  maturityDate,
                                  swaptionType,
                                  fixedCoupon,
                                  fixedFrequencyType,
                                  fixedDayCountType,
                                  notional)

    v_finpy = swaption.value(valuationDate, liborCurve, model)
    v_matlab = 0.4798

    testCases.header("LABEL", "VALUE")
    testCases.print("FP Price:", v_finpy)
    testCases.print("MATLAB Prix:", v_matlab)
    testCases.print("DIFF:", v_finpy - v_matlab)

###############################################################################

    testCases.header("====================================")
    testCases.header("MATLAB EXAMPLE WITH BLACK-DERMAN-TOY")
    testCases.header("====================================")

    # https://fr.mathworks.com/help/fininst/swaptionbybdt.html

    valuationDate = TuringDate(1, 1, 2007)

    dates = [TuringDate(1, 1, 2007), TuringDate(1, 7, 2007), TuringDate(1, 1, 2008),
             TuringDate(1, 7, 2008), TuringDate(1, 1, 2009), TuringDate(1, 7, 2009),
             TuringDate(1, 1, 2010), TuringDate(1, 7, 2010),
             TuringDate(1, 1, 2011), TuringDate(1, 7, 2011), TuringDate(1, 1, 2012)]

    zeroRates = np.array([0.06] * 11)

    interpType = TuringInterpTypes.FLAT_FWD_RATES
    dayCountType = TuringDayCountTypes.THIRTY_E_360_ISDA
    contFreq = TuringFrequencyTypes.ANNUAL

    liborCurve = TuringDiscountCurveZeros(valuationDate, dates, zeroRates,
                                          contFreq, dayCountType, interpType)

    settlementDate = valuationDate
    exerciseDate = TuringDate(1, 1, 2012)
    maturityDate = TuringDate(1, 1, 2015)

    fixedFrequencyType = TuringFrequencyTypes.ANNUAL
    fixedDayCountType = TuringDayCountTypes.THIRTY_E_360_ISDA
    notional = 100.0

    fixedCoupon = 0.062
    swaptionType = TuringSwapTypes.PAY
    swaption = TuringIborSwaption(settlementDate,
                                  exerciseDate,
                                  maturityDate,
                                  swaptionType,
                                  fixedCoupon,
                                  fixedFrequencyType,
                                  fixedDayCountType,
                                  notional)

    model = TuringModelRatesBDT(0.20, 200)
    v_finpy = swaption.value(valuationDate, liborCurve, model)
    v_matlab = 2.0592

    testCases.header("LABEL", "VALUE")
    testCases.print("FP Price:", v_finpy)
    testCases.print("MATLAB Prix:", v_matlab)
    testCases.print("DIFF:", v_finpy - v_matlab)


###############################################################################


testFinIborSwaptionModels()
testFinIborCashSettledSwaption()
testFinIborSwaptionMatlabExamples()
test_FinIborSwaptionQLExample()

testCases.compareTestCases()
