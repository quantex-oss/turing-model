###############################################################################
# Copyright (C) 2018, 2019, 2020 Dominic O'Kane
###############################################################################

import sys
sys.path.append("..")

from turingmodel.turingutils.turing_date import TuringDate
from turingmodel.turingutils.turing_day_count import TuringDayCountTypes
from turingmodel.turingutils.turing_frequency import TuringFrequencyTypes
from turingmodel.turingutils.turing_global_types import TuringSwapTypes
from turingmodel.turingutils.turing_global_types import TuringExerciseTypes
from turingmodel.products.rates.turing_ibor_swaption import FinIborSwaption
from turingmodel.products.rates.turing_ibor_swap import FinIborSwap

from turingmodel.products.rates.turing_ibor_bermudan_swaption import FinIborBermudanSwaption
from turingmodel.models.turing_model_black import FinModelBlack
from turingmodel.models.turing_model_rates_bk import TuringModelRatesBK
from turingmodel.models.turing_model_rates_hw import FinModelRatesHW
from turingmodel.models.turing_model_rates_bdt import TuringModelRatesBDT
from turingmodel.market.curves.turing_discount_curve_flat import TuringDiscountCurveFlat

from TuringTestCases import TuringTestCases, globalTestCaseMode
testCases = TuringTestCases(__file__, globalTestCaseMode)

##########################################################################


def test_FinIborBermudanSwaptionBKModel():
    ''' Replicate examples in paper by Leif Andersen which can be found at
    file:///C:/Users/Dominic/Downloads/SSRN-id155208.pdf '''

    valuationDate = TuringDate(1, 1, 2011)
    settlementDate = valuationDate
    exerciseDate = settlementDate.addYears(1)
    swapMaturityDate = settlementDate.addYears(4)

    swapFixedCoupon = 0.060
    swapFixedFrequencyType = TuringFrequencyTypes.SEMI_ANNUAL
    swapFixedDayCountType = TuringDayCountTypes.ACT_365F

    liborCurve = TuringDiscountCurveFlat(valuationDate,
                                         0.0625,
                                         TuringFrequencyTypes.SEMI_ANNUAL,
                                         TuringDayCountTypes.ACT_365F)

    fwdPAYSwap = FinIborSwap(exerciseDate,
                             swapMaturityDate,
                             TuringSwapTypes.PAY,
                             swapFixedCoupon,
                             swapFixedFrequencyType,
                             swapFixedDayCountType)

    fwdSwapValue = fwdPAYSwap.value(settlementDate, liborCurve, liborCurve)

    testCases.header("LABEL", "VALUE")
    testCases.print("FWD SWAP VALUE", fwdSwapValue)

    # fwdPAYSwap.printFixedLegPV()

    # Now we create the European swaptions
    fixedLegType = TuringSwapTypes.PAY
    europeanSwaptionPay = FinIborSwaption(settlementDate,
                                           exerciseDate,
                                           swapMaturityDate,
                                           fixedLegType,
                                           swapFixedCoupon,
                                           swapFixedFrequencyType,
                                           swapFixedDayCountType)

    fixedLegType = TuringSwapTypes.RECEIVE
    europeanSwaptionRec = FinIborSwaption(settlementDate,
                                           exerciseDate,
                                           swapMaturityDate,
                                           fixedLegType,
                                           swapFixedCoupon,
                                           swapFixedFrequencyType,
                                           swapFixedDayCountType)
    
    ###########################################################################
    ###########################################################################
    ###########################################################################
    # BLACK'S MODEL
    ###########################################################################
    ###########################################################################
    ###########################################################################

    testCases.banner("======= ZERO VOLATILITY ========")
    model = FinModelBlack(0.0000001)
    testCases.print("Black Model", model._volatility)

    valuePay = europeanSwaptionPay.value(settlementDate, liborCurve, model)
    testCases.print("EUROPEAN BLACK PAY VALUE ZERO VOL:", valuePay)

    valueRec = europeanSwaptionRec.value(settlementDate, liborCurve, model)
    testCases.print("EUROPEAN BLACK REC VALUE ZERO VOL:", valueRec)

    payRec = valuePay - valueRec
    testCases.print("PAY MINUS RECEIVER :", payRec)

    testCases.banner("======= 20%% BLACK VOLATILITY ========")

    model = FinModelBlack(0.20)
    testCases.print("Black Model", model._volatility)

    valuePay = europeanSwaptionPay.value(settlementDate, liborCurve, model)
    testCases.print("EUROPEAN BLACK PAY VALUE:", valuePay)

    valueRec = europeanSwaptionRec.value(settlementDate, liborCurve, model)
    testCases.print("EUROPEAN BLACK REC VALUE:", valueRec)

    payRec = valuePay - valueRec
    testCases.print("PAY MINUS RECEIVER :", payRec)

    ###########################################################################
    ###########################################################################
    ###########################################################################
    # BK MODEL
    ###########################################################################
    ###########################################################################
    ###########################################################################

    testCases.banner("=======================================================")
    testCases.banner("=======================================================")
    testCases.banner("==================== BK MODEL =========================")
    testCases.banner("=======================================================")
    testCases.banner("=======================================================")

    testCases.banner("======= 0% VOLATILITY EUROPEAN SWAPTION BK MODEL ======")

    # Used BK with constant short-rate volatility
    sigma = 0.000000001
    a = 0.01
    numTimeSteps = 100
    model = TuringModelRatesBK(sigma, a, numTimeSteps)

    valuePay = europeanSwaptionPay.value(valuationDate, liborCurve, model)
    testCases.print("EUROPEAN BK PAY VALUE:", valuePay)
    
    valueRec = europeanSwaptionRec.value(valuationDate, liborCurve, model)
    testCases.print("EUROPEAN BK REC VALUE:", valueRec)
    
    payRec = valuePay - valueRec
    testCases.print("PAY MINUS RECEIVER :", payRec)


    testCases.banner("======= 20% VOLATILITY EUROPEAN SWAPTION BK MODEL ========")

    # Used BK with constant short-rate volatility
    sigma = 0.20
    a = 0.01
    model = TuringModelRatesBK(sigma, a, numTimeSteps)

    testCases.banner("BK MODEL SWAPTION CLASS EUROPEAN EXERCISE")

    valuePay = europeanSwaptionPay.value(valuationDate, liborCurve, model)
    testCases.print("EUROPEAN BK PAY VALUE:", valuePay)

    valueRec = europeanSwaptionRec.value(valuationDate, liborCurve, model)
    testCases.print("EUROPEAN BK REC VALUE:", valueRec)

    payRec = valuePay - valueRec
    testCases.print("PAY MINUS RECEIVER :", payRec)
    
    ###########################################################################

    # Now we create the Bermudan swaptions but only allow European exercise
    fixedLegType = TuringSwapTypes.PAY
    exerciseType = TuringExerciseTypes.EUROPEAN

    bermudanSwaptionPay = FinIborBermudanSwaption(settlementDate,
                                                   exerciseDate,
                                                   swapMaturityDate,
                                                   fixedLegType,
                                                   exerciseType,
                                                   swapFixedCoupon,
                                                   swapFixedFrequencyType,
                                                   swapFixedDayCountType)

    fixedLegType = TuringSwapTypes.RECEIVE
    exerciseType = TuringExerciseTypes.EUROPEAN

    bermudanSwaptionRec = FinIborBermudanSwaption(settlementDate,
                                                   exerciseDate,
                                                   swapMaturityDate,
                                                   fixedLegType,
                                                   exerciseType,
                                                   swapFixedCoupon,
                                                   swapFixedFrequencyType,
                                                   swapFixedDayCountType)
   
    testCases.banner("======= 0% VOLATILITY BERMUDAN SWAPTION EUROPEAN EXERCISE BK MODEL ========")

    # Used BK with constant short-rate volatility
    sigma = 0.000001
    a = 0.01
    model = TuringModelRatesBK(sigma, a, numTimeSteps)

    testCases.banner("BK MODEL BERMUDAN SWAPTION CLASS EUROPEAN EXERCISE")
    valuePay = bermudanSwaptionPay.value(valuationDate, liborCurve, model)
    testCases.print("BERMUDAN BK PAY VALUE:", valuePay)

    valueRec = bermudanSwaptionRec.value(valuationDate, liborCurve, model)
    testCases.print("BERMUDAN BK REC VALUE:", valueRec)

    payRec = valuePay - valueRec
    testCases.print("PAY MINUS RECEIVER :", payRec)

    testCases.banner("======= 20% VOLATILITY BERMUDAN SWAPTION EUROPEAN EXERCISE BK MODEL ========")

    # Used BK with constant short-rate volatility
    sigma = 0.2
    a = 0.01
    model = TuringModelRatesBK(sigma, a, numTimeSteps)

    testCases.banner("BK MODEL BERMUDAN SWAPTION CLASS EUROPEAN EXERCISE")
    valuePay = bermudanSwaptionPay.value(valuationDate, liborCurve, model)
    testCases.print("BERMUDAN BK PAY VALUE:", valuePay)

    valueRec = bermudanSwaptionRec.value(valuationDate, liborCurve, model)
    testCases.print("BERMUDAN BK REC VALUE:", valueRec)

    payRec = valuePay - valueRec
    testCases.print("PAY MINUS RECEIVER :", payRec)
    
    ###########################################################################
    # Now we create the Bermudan swaptions but allow Bermudan exercise
    ###########################################################################

    fixedLegType = TuringSwapTypes.PAY
    exerciseType = TuringExerciseTypes.BERMUDAN

    bermudanSwaptionPay = FinIborBermudanSwaption(settlementDate,
                                                   exerciseDate,
                                                   swapMaturityDate,
                                                   fixedLegType,
                                                   exerciseType,
                                                   swapFixedCoupon,
                                                   swapFixedFrequencyType,
                                                   swapFixedDayCountType)

    fixedLegType = TuringSwapTypes.RECEIVE
    exerciseType = TuringExerciseTypes.BERMUDAN

    bermudanSwaptionRec = FinIborBermudanSwaption(settlementDate,
                                                   exerciseDate,
                                                   swapMaturityDate,
                                                   fixedLegType,
                                                   exerciseType,
                                                   swapFixedCoupon,
                                                   swapFixedFrequencyType,
                                                   swapFixedDayCountType)

    testCases.banner("======= ZERO VOLATILITY BERMUDAN SWAPTION BERMUDAN EXERCISE BK MODEL ========")

    # Used BK with constant short-rate volatility
    sigma = 0.000001
    a = 0.01
    model = TuringModelRatesBK(sigma, a, numTimeSteps)

    testCases.banner("BK MODEL BERMUDAN SWAPTION CLASS BERMUDAN EXERCISE")
    valuePay = bermudanSwaptionPay.value(valuationDate, liborCurve, model)
    testCases.print("BERMUDAN BK PAY VALUE:", valuePay)

    valueRec = bermudanSwaptionRec.value(valuationDate, liborCurve, model)
    testCases.print("BERMUDAN BK REC VALUE:", valueRec)

    payRec = valuePay - valueRec
    testCases.print("PAY MINUS RECEIVER :", payRec)

    testCases.banner("======= 20% VOLATILITY BERMUDAN SWAPTION BERMUDAN EXERCISE BK MODEL ========")

    # Used BK with constant short-rate volatility
    sigma = 0.20
    a = 0.01
    model = TuringModelRatesBK(sigma, a, numTimeSteps)

    testCases.banner("BK MODEL BERMUDAN SWAPTION CLASS BERMUDAN EXERCISE")
    valuePay = bermudanSwaptionPay.value(valuationDate, liborCurve, model)
    testCases.print("BERMUDAN BK PAY VALUE:", valuePay)

    valueRec = bermudanSwaptionRec.value(valuationDate, liborCurve, model)
    testCases.print("BERMUDAN BK REC VALUE:", valueRec)

    payRec = valuePay - valueRec
    testCases.print("PAY MINUS RECEIVER :", payRec)
    
    ###########################################################################
    ###########################################################################
    ###########################################################################
    # BDT MODEL
    ###########################################################################
    ###########################################################################
    ###########################################################################

    testCases.banner("=======================================================")
    testCases.banner("=======================================================")
    testCases.banner("======================= BDT MODEL =====================")
    testCases.banner("=======================================================")
    testCases.banner("=======================================================")

    testCases.banner("====== 0% VOLATILITY EUROPEAN SWAPTION BDT MODEL ======")

    # Used BK with constant short-rate volatility
    sigma = 0.00001
    numTimeSteps = 200
    model = TuringModelRatesBDT(sigma, numTimeSteps)

    valuePay = europeanSwaptionPay.value(valuationDate, liborCurve, model)
    testCases.print("EUROPEAN BDT PAY VALUE:", valuePay)

    valueRec = europeanSwaptionRec.value(valuationDate, liborCurve, model)
    testCases.print("EUROPEAN BDT REC VALUE:", valueRec)

    payRec = valuePay - valueRec
    testCases.print("PAY MINUS RECEIVER :", payRec)

    testCases.banner("===== 20% VOLATILITY EUROPEAN SWAPTION BDT MODEL ======")

    # Used BK with constant short-rate volatility
    sigma = 0.20
    a = 0.01
    model = TuringModelRatesBDT(sigma, numTimeSteps)

    testCases.banner("BDT MODEL SWAPTION CLASS EUROPEAN EXERCISE")

    valuePay = europeanSwaptionPay.value(valuationDate, liborCurve, model)
    testCases.print("EUROPEAN BDT PAY VALUE:", valuePay)

    valueRec = europeanSwaptionRec.value(valuationDate, liborCurve, model)
    testCases.print("EUROPEAN BDT REC VALUE:", valueRec)

    payRec = valuePay - valueRec
    testCases.print("PAY MINUS RECEIVER :", payRec)

    ###########################################################################

    # Now we create the Bermudan swaptions but only allow European exercise
    fixedLegType = TuringSwapTypes.PAY
    exerciseType = TuringExerciseTypes.EUROPEAN

    bermudanSwaptionPay = FinIborBermudanSwaption(settlementDate,
                                                   exerciseDate,
                                                   swapMaturityDate,
                                                   fixedLegType,
                                                   exerciseType,
                                                   swapFixedCoupon,
                                                   swapFixedFrequencyType,
                                                   swapFixedDayCountType)

    fixedLegType = TuringSwapTypes.RECEIVE
    bermudanSwaptionRec = FinIborBermudanSwaption(settlementDate,
                                                   exerciseDate,
                                                   swapMaturityDate,
                                                   fixedLegType,
                                                   exerciseType,
                                                   swapFixedCoupon,
                                                   swapFixedFrequencyType,
                                                   swapFixedDayCountType)
   
    testCases.banner("======= 0% VOLATILITY BERMUDAN SWAPTION EUROPEAN EXERCISE BDT MODEL ========")

    # Used BK with constant short-rate volatility
    sigma = 0.000001
    model = TuringModelRatesBDT(sigma, numTimeSteps)

    testCases.banner("BK MODEL BERMUDAN SWAPTION CLASS EUROPEAN EXERCISE")
    valuePay = bermudanSwaptionPay.value(valuationDate, liborCurve, model)
    testCases.print("BERMUDAN BDT PAY VALUE:", valuePay)

    valueRec = bermudanSwaptionRec.value(valuationDate, liborCurve, model)
    testCases.print("BERMUDAN BDT REC VALUE:", valueRec)

    payRec = valuePay - valueRec
    testCases.print("PAY MINUS RECEIVER :", payRec)

    testCases.banner("======= 20% VOLATILITY BERMUDAN SWAPTION EUROPEAN EXERCISE BDT MODEL ========")

    # Used BK with constant short-rate volatility
    sigma = 0.2
    model = TuringModelRatesBDT(sigma, numTimeSteps)

    testCases.banner("BDT MODEL BERMUDAN SWAPTION CLASS EUROPEAN EXERCISE")
    valuePay = bermudanSwaptionPay.value(valuationDate, liborCurve, model)
    testCases.print("BERMUDAN BDT PAY VALUE:", valuePay)

    valueRec = bermudanSwaptionRec.value(valuationDate, liborCurve, model)
    testCases.print("BERMUDAN BDT REC VALUE:", valueRec)

    payRec = valuePay - valueRec
    testCases.print("PAY MINUS RECEIVER :", payRec)
    
    ###########################################################################
    # Now we create the Bermudan swaptions but allow Bermudan exercise
    ###########################################################################

    fixedLegType = TuringSwapTypes.PAY
    exerciseType = TuringExerciseTypes.BERMUDAN

    bermudanSwaptionPay = FinIborBermudanSwaption(settlementDate,
                                                   exerciseDate,
                                                   swapMaturityDate,
                                                   fixedLegType,
                                                   exerciseType,
                                                   swapFixedCoupon,
                                                   swapFixedFrequencyType,
                                                   swapFixedDayCountType)

    fixedLegType = TuringSwapTypes.RECEIVE
    bermudanSwaptionRec = FinIborBermudanSwaption(settlementDate,
                                                   exerciseDate,
                                                   swapMaturityDate,
                                                   fixedLegType,
                                                   exerciseType,
                                                   swapFixedCoupon,
                                                   swapFixedFrequencyType,
                                                   swapFixedDayCountType)

    testCases.banner("======= ZERO VOLATILITY BERMUDAN SWAPTION BERMUDAN EXERCISE BDT MODEL ========")

    # Used BK with constant short-rate volatility
    sigma = 0.000001
    a = 0.01
    model = TuringModelRatesBDT(sigma, numTimeSteps)

    testCases.banner("BK MODEL BERMUDAN SWAPTION CLASS BERMUDAN EXERCISE")
    valuePay = bermudanSwaptionPay.value(valuationDate, liborCurve, model)
    testCases.print("BERMUDAN BDT PAY VALUE:", valuePay)

    valueRec = bermudanSwaptionRec.value(valuationDate, liborCurve, model)
    testCases.print("BERMUDAN BDT REC VALUE:", valueRec)

    payRec = valuePay - valueRec
    testCases.print("PAY MINUS RECEIVER :", payRec)

    testCases.banner("======= 20% VOLATILITY BERMUDAN SWAPTION BERMUDAN EXERCISE BDT MODEL ========")

    # Used BK with constant short-rate volatility
    sigma = 0.20
    a = 0.01
    model = TuringModelRatesBDT(sigma, numTimeSteps)

#    print("BDT MODEL BERMUDAN SWAPTION CLASS BERMUDAN EXERCISE")
    valuePay = bermudanSwaptionPay.value(valuationDate, liborCurve, model)
    testCases.print("BERMUDAN BDT PAY VALUE:", valuePay)

    valueRec = bermudanSwaptionRec.value(valuationDate, liborCurve, model)
    testCases.print("BERMUDAN BDT REC VALUE:", valueRec)

    payRec = valuePay - valueRec
    testCases.print("PAY MINUS RECEIVER :", payRec)
    
    ###########################################################################
    ###########################################################################
    ###########################################################################
    # BDT MODEL
    ###########################################################################
    ###########################################################################
    ###########################################################################

    testCases.banner("=======================================================")
    testCases.banner("=======================================================")
    testCases.banner("======================= HW MODEL ======================")
    testCases.banner("=======================================================")
    testCases.banner("=======================================================")

    testCases.banner("====== 0% VOLATILITY EUROPEAN SWAPTION HW MODEL ======")

    sigma = 0.0000001
    a = 0.1
    numTimeSteps = 200
    model = FinModelRatesHW(sigma, a, numTimeSteps)

    valuePay = europeanSwaptionPay.value(valuationDate, liborCurve, model)
    testCases.print("EUROPEAN HW PAY VALUE:", valuePay)

    valueRec = europeanSwaptionRec.value(valuationDate, liborCurve, model)
    testCases.print("EUROPEAN HW REC VALUE:", valueRec)

    payRec = valuePay - valueRec
    testCases.print("PAY MINUS RECEIVER :", payRec)

    testCases.banner("===== 20% VOLATILITY EUROPEAN SWAPTION BDT MODEL ======")

    # Used BK with constant short-rate volatility
    sigma = 0.01
    a = 0.01
    model = FinModelRatesHW(sigma, a, numTimeSteps)

    testCases.banner("HW MODEL SWAPTION CLASS EUROPEAN EXERCISE")

    valuePay = europeanSwaptionPay.value(valuationDate, liborCurve, model)
    testCases.print("EUROPEAN HW PAY VALUE:", valuePay)

    valueRec = europeanSwaptionRec.value(valuationDate, liborCurve, model)
    testCases.print("EUROPEAN HW REC VALUE:", valueRec)

    payRec = valuePay - valueRec
    testCases.print("PAY MINUS RECEIVER :", payRec)

    ###########################################################################

    # Now we create the Bermudan swaptions but only allow European exercise
    fixedLegType = TuringSwapTypes.PAY
    exerciseType = TuringExerciseTypes.EUROPEAN

    bermudanSwaptionPay = FinIborBermudanSwaption(settlementDate,
                                                   exerciseDate,
                                                   swapMaturityDate,
                                                   fixedLegType,
                                                   exerciseType,
                                                   swapFixedCoupon,
                                                   swapFixedFrequencyType,
                                                   swapFixedDayCountType)

    fixedLegType = TuringSwapTypes.RECEIVE
    bermudanSwaptionRec = FinIborBermudanSwaption(settlementDate,
                                                   exerciseDate,
                                                   swapMaturityDate,
                                                   fixedLegType,
                                                   exerciseType,
                                                   swapFixedCoupon,
                                                   swapFixedFrequencyType,
                                                   swapFixedDayCountType)
   
    testCases.banner("======= 0% VOLATILITY BERMUDAN SWAPTION EUROPEAN EXERCISE HW MODEL ========")

    sigma = 0.000001
    model = FinModelRatesHW(sigma, a, numTimeSteps)

    testCases.banner("BK MODEL BERMUDAN SWAPTION CLASS EUROPEAN EXERCISE")
    valuePay = bermudanSwaptionPay.value(valuationDate, liborCurve, model)
    testCases.print("BERMUDAN BDT PAY VALUE:", valuePay)

    valueRec = bermudanSwaptionRec.value(valuationDate, liborCurve, model)
    testCases.print("BERMUDAN BDT REC VALUE:", valueRec)

    payRec = valuePay - valueRec
    testCases.print("PAY MINUS RECEIVER :", payRec)

    testCases.banner("======= 100bp VOLATILITY BERMUDAN SWAPTION EUROPEAN EXERCISE HW MODEL ========")

    # Used BK with constant short-rate volatility
    sigma = 0.01
    model = FinModelRatesHW(sigma, a, numTimeSteps)

    testCases.banner("BDT MODEL BERMUDAN SWAPTION CLASS EUROPEAN EXERCISE")
    valuePay = bermudanSwaptionPay.value(valuationDate, liborCurve, model)
    testCases.print("BERMUDAN BDT PAY VALUE:", valuePay)

    valueRec = bermudanSwaptionRec.value(valuationDate, liborCurve, model)
    testCases.print("BERMUDAN BDT REC VALUE:", valueRec)

    payRec = valuePay - valueRec
    testCases.print("PAY MINUS RECEIVER :", payRec)
    
    ###########################################################################
    # Now we create the Bermudan swaptions but allow Bermudan exercise
    ###########################################################################

    fixedLegType = TuringSwapTypes.PAY
    exerciseType = TuringExerciseTypes.BERMUDAN

    bermudanSwaptionPay = FinIborBermudanSwaption(settlementDate,
                                                   exerciseDate,
                                                   swapMaturityDate,
                                                   fixedLegType,
                                                   exerciseType,
                                                   swapFixedCoupon,
                                                   swapFixedFrequencyType,
                                                   swapFixedDayCountType)

    fixedLegType = TuringSwapTypes.RECEIVE
    bermudanSwaptionRec = FinIborBermudanSwaption(settlementDate,
                                                   exerciseDate,
                                                   swapMaturityDate,
                                                   fixedLegType,
                                                   exerciseType,
                                                   swapFixedCoupon,
                                                   swapFixedFrequencyType,
                                                   swapFixedDayCountType)

    testCases.banner("======= ZERO VOLATILITY BERMUDAN SWAPTION BERMUDAN EXERCISE HW MODEL ========")

    # Used BK with constant short-rate volatility
    sigma = 0.000001
    a = 0.01
    model = FinModelRatesHW(sigma, a, numTimeSteps)

    testCases.banner("HW MODEL BERMUDAN SWAPTION CLASS BERMUDAN EXERCISE")
    valuePay = bermudanSwaptionPay.value(valuationDate, liborCurve, model)
    testCases.print("BERMUDAN HW PAY VALUE:", valuePay)

    valueRec = bermudanSwaptionRec.value(valuationDate, liborCurve, model)
    testCases.print("BERMUDAN HW REC VALUE:", valueRec)

    payRec = valuePay - valueRec
    testCases.print("PAY MINUS RECEIVER :", payRec)

    testCases.banner("======= 100bps VOLATILITY BERMUDAN SWAPTION BERMUDAN EXERCISE HW MODEL ========")

    # Used BK with constant short-rate volatility
    sigma = 0.01
    a = 0.01
    model = FinModelRatesHW(sigma, a, numTimeSteps)

    testCases.banner("HW MODEL BERMUDAN SWAPTION CLASS BERMUDAN EXERCISE")
    valuePay = bermudanSwaptionPay.value(valuationDate, liborCurve, model)
    testCases.print("BERMUDAN HW PAY VALUE:", valuePay)

    valueRec = bermudanSwaptionRec.value(valuationDate, liborCurve, model)
    testCases.print("BERMUDAN HW REC VALUE:", valueRec)

    payRec = valuePay - valueRec
    testCases.print("PAY MINUS RECEIVER :", payRec)
##########################################################################


test_FinIborBermudanSwaptionBKModel()

testCases.compareTestCases()
