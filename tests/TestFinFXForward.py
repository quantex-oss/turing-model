###############################################################################
# Copyright (C) 2018, 2019, 2020 Dominic O'Kane
###############################################################################

import sys
sys.path.append("..")

from turingmodel.products.fx.turing_fx_forward import TuringFXForward
from turingmodel.turingutils.turing_day_count import TuringDayCountTypes
from turingmodel.turingutils.turing_calendar import TuringCalendarTypes
from turingmodel.products.rates.turing_ibor_single_curve import TuringIborSingleCurve
from turingmodel.products.rates.turing_ibor_deposit import TuringIborDeposit
from turingmodel.turingutils.turing_date import TuringDate

from TuringTestCases import TuringTestCases, globalTestCaseMode
testCases = TuringTestCases(__file__, globalTestCaseMode)

##########################################################################


def test_FinFXForward():

    #  https://stackoverflow.com/questions/48778712
    #  /fx-vanilla-call-price-in-quantlib-doesnt-match-bloomberg

    valuationDate = TuringDate(13, 2, 2018)
    expiryDate = valuationDate.addMonths(12)
    # Forward is on EURUSD which is expressed as number of USD per EUR
    # ccy1 = EUR and ccy2 = USD
    forName = "EUR"
    domName = "USD"
    currencyPair = forName + domName  # Always ccy1ccy2
    spotFXRate = 1.300  # USD per EUR
    strikeFXRate = 1.365  # USD per EUR
    ccy1InterestRate = 0.02  # USD Rates
    ccy2InterestRate = 0.05  # EUR rates

    ###########################################################################

    spotDays = 0
    settlementDate = valuationDate.addWeekDays(spotDays)
    maturityDate = settlementDate.addMonths(12)
    notional = 100.0
    calendarType = TuringCalendarTypes.TARGET

    depos = []
    fras = []
    swaps = []
    depositRate = ccy1InterestRate
    depo = TuringIborDeposit(settlementDate, maturityDate, depositRate,
                             TuringDayCountTypes.ACT_360, notional, calendarType)
    depos.append(depo)
    forDiscountCurve = TuringIborSingleCurve(valuationDate, depos, fras, swaps)

    depos = []
    fras = []
    swaps = []
    depositRate = ccy2InterestRate
    depo = TuringIborDeposit(settlementDate, maturityDate, depositRate,
                             TuringDayCountTypes.ACT_360, notional, calendarType)
    depos.append(depo)
    domDiscountCurve = TuringIborSingleCurve(valuationDate, depos, fras, swaps)

    notional = 100.0
    notionalCurrency = forName

    fxForward = TuringFXForward(expiryDate,
                                strikeFXRate,
                                currencyPair,
                                notional,
                                notionalCurrency)

    testCases.header("SPOT FX", "FX FWD", "VALUE_BS")

    fwdValue = fxForward.value(valuationDate, spotFXRate,
                               domDiscountCurve, forDiscountCurve)

    fwdFXRate = fxForward.forward(valuationDate, spotFXRate,
                                  domDiscountCurve,
                                  forDiscountCurve)

    testCases.print(spotFXRate, fwdFXRate, fwdValue)

###############################################################################


test_FinFXForward()
testCases.compareTestCases()
