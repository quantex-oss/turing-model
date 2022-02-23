import time

import numpy as np

from turing_models.instruments.rates.irs import IRS
from turing_models.utilities.mathematics import ONE_MILLION
from turing_models.market.curves.ibor_single_curve import TuringIborSingleCurve
from turing_models.instruments.rates.ibor_swap import TuringIborSwap
from turing_models.instruments.rates.ibor_deposit import TuringIborDeposit
from turing_models.utilities.calendar import TuringBusDayAdjustTypes
from turing_models.utilities.calendar import TuringDateGenRuleTypes
from turing_models.utilities.calendar import TuringCalendarTypes
from turing_models.utilities.frequency import FrequencyType
from turing_models.utilities.day_count import DayCountType
from turing_models.utilities.turing_date import TuringDate
from turing_models.utilities.global_types import TuringSwapTypes


def buildIborSingleCurve(valuationDate):

    settlementDate = valuationDate
    dcType = DayCountType.ACT_360

    depos = []
    fras = []
    swaps = []

    maturityDate = settlementDate.addMonths(1)
    depo1 = TuringIborDeposit(valuationDate, maturityDate, -0.00251, dcType)
    depos.append(depo1)

    fixedFreq = FrequencyType.ANNUAL
    dcType = DayCountType.THIRTY_E_360
    fixedLegType = TuringSwapTypes.PAY

    #######################################
    maturityDate = settlementDate.addYears(24/12)
    swapRate = -0.001506
    swap1 = TuringIborSwap(settlementDate, maturityDate, fixedLegType,
                           swapRate, fixedFreq, dcType)
    swaps.append(swap1)

    #######################################
    maturityDate = settlementDate.addYears(36/12)
    swapRate = -0.000185
    swap2 = TuringIborSwap(settlementDate, maturityDate, fixedLegType,
                           swapRate, fixedFreq, dcType)
    swaps.append(swap2)

    #######################################
    maturityDate = settlementDate.addYears(48/12)
    swapRate = 0.001358
    swap3 = TuringIborSwap(settlementDate, maturityDate, fixedLegType,
                           swapRate, fixedFreq, dcType)
    swaps.append(swap3)

    #######################################
    maturityDate = settlementDate.addYears(60/12)
    swapRate = 0.0027652
    swap4 = TuringIborSwap(settlementDate, maturityDate, fixedLegType,
                           swapRate, fixedFreq, dcType)
    swaps.append(swap4)

    #######################################
    maturityDate = settlementDate.addYears(72/12)
    swapRate = 0.0041539
    swap5 = TuringIborSwap(settlementDate, maturityDate, fixedLegType,
                           swapRate, fixedFreq, dcType)
    swaps.append(swap5)

    #######################################
    maturityDate = settlementDate.addYears(84/12)
    swapRate = 0.0054604
    swap6 = TuringIborSwap(settlementDate, maturityDate, fixedLegType,
                           swapRate, fixedFreq, dcType)
    swaps.append(swap6)

    #######################################
    maturityDate = settlementDate.addYears(96/12)
    swapRate = 0.006674
    swap7 = TuringIborSwap(settlementDate, maturityDate, fixedLegType,
                           swapRate, fixedFreq, dcType)
    swaps.append(swap7)

    #######################################
    maturityDate = settlementDate.addYears(108/12)
    swapRate = 0.007826
    swap8 = TuringIborSwap(settlementDate, maturityDate, fixedLegType,
                           swapRate, fixedFreq, dcType)
    swaps.append(swap8)

    #######################################
    maturityDate = settlementDate.addYears(120/12)
    swapRate = 0.008821
    swap9 = TuringIborSwap(settlementDate, maturityDate, fixedLegType,
                           swapRate, fixedFreq, dcType)
    swaps.append(swap9)

    #######################################
    maturityDate = settlementDate.addYears(132/12)
    swapRate = 0.0097379
    swap10 = TuringIborSwap(settlementDate, maturityDate, fixedLegType,
                            swapRate, fixedFreq, dcType)
    swaps.append(swap10)

    #######################################
    maturityDate = settlementDate.addYears(144/12)
    swapRate = 0.0105406
    swap11 = TuringIborSwap(settlementDate, maturityDate, fixedLegType,
                            swapRate, fixedFreq, dcType)
    swaps.append(swap11)

    #######################################
    maturityDate = settlementDate.addYears(180/12)
    swapRate = 0.0123927
    swap12 = TuringIborSwap(settlementDate, maturityDate, fixedLegType,
                            swapRate, fixedFreq, dcType)
    swaps.append(swap12)

    #######################################
    maturityDate = settlementDate.addYears(240/12)
    swapRate = 0.0139882
    swap13 = TuringIborSwap(settlementDate, maturityDate, fixedLegType,
                            swapRate, fixedFreq, dcType)
    swaps.append(swap13)

    #######################################
    maturityDate = settlementDate.addYears(300/12)
    swapRate = 0.0144972
    swap14 = TuringIborSwap(settlementDate, maturityDate, fixedLegType,
                            swapRate, fixedFreq, dcType)
    swaps.append(swap14)

    #######################################
    maturityDate = settlementDate.addYears(360/12)
    swapRate = 0.0146081
    swap15 = TuringIborSwap(settlementDate, maturityDate, fixedLegType,
                            swapRate, fixedFreq, dcType)
    swaps.append(swap15)

    #######################################
    maturityDate = settlementDate.addYears(420/12)
    swapRate = 0.01461897
    swap16 = TuringIborSwap(settlementDate, maturityDate, fixedLegType,
                            swapRate, fixedFreq, dcType)
    swaps.append(swap16)

    #######################################
    maturityDate = settlementDate.addYears(480/12)
    swapRate = 0.014567455
    swap17 = TuringIborSwap(settlementDate, maturityDate, fixedLegType,
                            swapRate, fixedFreq, dcType)
    swaps.append(swap17)

    #######################################
    maturityDate = settlementDate.addYears(540/12)
    swapRate = 0.0140826
    swap18 = TuringIborSwap(settlementDate, maturityDate, fixedLegType,
                            swapRate, fixedFreq, dcType)
    swaps.append(swap18)

    #######################################
    maturityDate = settlementDate.addYears(600/12)
    swapRate = 0.01436822
    swap19 = TuringIborSwap(settlementDate, maturityDate, fixedLegType,
                            swapRate, fixedFreq, dcType)
    swaps.append(swap19)

    ########################################

    liborCurve = TuringIborSingleCurve(valuationDate, depos, fras, swaps)

    return liborCurve

###############################################################################


def test_LiborSwap():

    # I have tried to reproduce the example from the blog by Ioannis Rigopoulos
    # https://blog.deriscope.com/index.php/en/excel-interest-rate-swap-price-dual-bootstrapping-curve
    startDate = TuringDate(2017, 12, 27)
    endDate = TuringDate(2067, 12, 27)

    fixedCoupon = 0.015
    fixedFreqType = FrequencyType.ANNUAL
    fixedDayCountType = DayCountType.THIRTY_E_360

    floatSpread = 0.0
    floatFreqType = FrequencyType.SEMI_ANNUAL
    floatDayCountType = DayCountType.ACT_360
    firstFixing = -0.00268

    swapCalendarType = TuringCalendarTypes.WEEKEND
    busDayAdjustType = TuringBusDayAdjustTypes.FOLLOWING
    dateGenRuleType = TuringDateGenRuleTypes.BACKWARD
    fixedLegType = TuringSwapTypes.RECEIVE

    notional = 10.0 * ONE_MILLION

    swap = TuringIborSwap(startDate,
                          endDate,
                          fixedLegType,
                          fixedCoupon,
                          fixedFreqType,
                          fixedDayCountType,
                          notional,
                          floatSpread,
                          floatFreqType,
                          floatDayCountType,
                          swapCalendarType,
                          busDayAdjustType,
                          dateGenRuleType)

    ''' Now perform a valuation after the swap has seasoned but with the
    same curve being used for discounting and working out the implied
    future Libor rates. '''

    valuationDate = TuringDate(2018, 11, 30)
    liborCurve = buildIborSingleCurve(valuationDate)
    v = swap.value(valuationDate, liborCurve, liborCurve, firstFixing)
    pv01 = swap.pv01(valuationDate, liborCurve)
    swap_rate = swap.swapRate(valuationDate, liborCurve)

    print(v, pv01, swap_rate)

dates = [0.25, 0.5, 0.75, 1, 2, 3, 4, 5, 7, 10]

rates = [0.023125, 0.023363, 0.023538, 0.023713, 0.024613, 0.025579, 0.026491, 0.027313, 0.028675, 0.03015]

irs = IRS(effective_date=TuringDate(2021, 7, 22),
          termination_date=TuringDate(2026, 7, 22),
          fixed_leg_type=TuringSwapTypes.PAY,
          fixed_freq_type=FrequencyType.QUARTERLY,
          fixed_day_count_type=DayCountType.ACT_365L,
          fixed_coupon=0.029425,
          notional=600000,
          float_spread=0,
          float_freq_type=FrequencyType.QUARTERLY,
          float_day_count_type=DayCountType.ACT_365L,
          value_date=TuringDate(2021, 8, 24),
          swap_curve_dates=dates,
          swap_curve_rates=rates,
          deposit_term=1/52,
          deposit_rate=0.0222,
          first_fixing_rate=0.02,
          deposit_day_count_type=DayCountType.ACT_365L,
          fixed_freq_type_for_curve=FrequencyType.QUARTERLY,
          fixed_day_count_type_for_curve=DayCountType.ACT_365L,
          fixed_leg_type_for_curve=TuringSwapTypes.PAY,
          reset_freq_type=FrequencyType.WEEKLY)

print(irs.price())
print(irs.pv01())
print(irs.swap_rate())

def bs_implied_dividend(stock_price, strike_price, price_call, price_put, r, texp, signal):
    """ Calculate the Black-Scholes implied dividend of a European
    vanilla option using Put-Call-Parity. """
    q = np.log(price_call - price_put + strike_price * np.exp(-r * texp) / stock_price)
    q = - 1 / texp * q
    if not signal:
        return q
    else:
        return texp, q

start = time.time()
print(bs_implied_dividend(1, 1.2, 0.01, 0.2, 0.3, 0.2, True))
end = time.time()
print("Elapsed (with compilation) = %s" % (end - start))
