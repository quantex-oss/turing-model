import time

from turing_models.instruments.rates.irs import IRS


# dates = [0.083, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0, 10.5, 11.0, 11.5, 12.0, 12.5, 13.0, 13.5, 14.0, 14.5, 15.0, 15.5, 16.0, 16.5, 17.0, 17.5, 18.0, 18.5, 19.0, 19.5, 20.0, 20.5, 21.0, 21.5, 22.0, 22.5, 23.0, 23.5, 24.0, 24.5, 25.0, 25.5, 26.0, 26.5, 27.0, 27.5, 28.0, 28.5, 29.0, 29.5, 30.0, 30.5, 31.0, 31.5, 32.0, 32.5, 33.0, 33.5, 34.0, 34.5, 35.0, 35.5, 36.0, 36.5, 37.0, 37.5, 38.0, 38.5, 39.0, 39.5, 40.0, 40.5, 41.0, 41.5, 42.0, 42.5, 43.0, 43.5, 44.0, 44.5, 45.0, 45.5, 46.0, 46.5, 47.0, 47.5, 48.0, 48.5, 49.0, 49.5, 50.0]
# rates = [0.01935, 0.019773, 0.021824, 0.023816, 0.024863, 0.025819, 0.026775000000000004, 0.027221000000000002, 0.027667, 0.028093, 0.02852, 0.028952, 0.029384999999999998, 0.029767000000000002, 0.030149, 0.030538, 0.030926, 0.030935, 0.030945, 0.030957, 0.030969000000000003, 0.030983, 0.030997, 0.03143, 0.031863, 0.032303, 0.032743, 0.03319, 0.033638, 0.034094, 0.034551, 0.035017, 0.035484, 0.035531, 0.035577, 0.035628, 0.035678, 0.035732, 0.035786, 0.035842, 0.035899, 0.035959, 0.036018, 0.036101999999999995, 0.036185, 0.036271, 0.036357, 0.036446, 0.036534, 0.036626, 0.036717, 0.036810999999999997, 0.036906, 0.037002, 0.037099, 0.037199, 0.037299, 0.037401, 0.037504, 0.037609, 0.037715, 0.037823, 0.037932, 0.03796, 0.037988, 0.038018, 0.038048, 0.038079999999999996, 0.038111, 0.038145, 0.038179, 0.038214, 0.038249, 0.038286, 0.038323, 0.038362, 0.038401, 0.038441, 0.038481999999999995, 0.038523999999999996, 0.038565999999999996, 0.038610000000000005, 0.038654, 0.038699, 0.038743, 0.038789, 0.038835, 0.038883, 0.038931, 0.038981, 0.039030999999999996, 0.039083, 0.039134, 0.039188, 0.039242, 0.039297, 0.039353, 0.039411, 0.039469, 0.039529, 0.039588, 0.039651, 0.039713]


# irs = IRS(effective_date=TuringDate(2021, 6, 9),
#           termination_date=TuringDate(2022, 5, 31),
#           fixed_leg_type='PAY',
#           fixed_coupon=0.0124,
#           fixed_freq_type='半年付息',
#           fixed_day_count_type='ACT/365',
#           notional=1000000,
#           float_spread=0,
#           float_freq_type='半年付息',
#           float_day_count_type='ACT/ACT',
#           zero_dates1=dates,
#           zero_rates1=rates,
#           first_fixing_rate=0.01)

# print(irs.price())
# print(irs.pv01())
# print(irs.swap_rate())
# import numpy as np
# from turing_models.market.curves.discount_curve_zeros import TuringDiscountCurveZeros
# from turing_models.market.curves.discount_curve import TuringDiscountCurve

# from turing_models.products.rates.ibor_swap import TuringIborSwap
# from turing_models.utilities.global_types import TuringSwapTypes
# from turing_models.utilities.frequency import TuringFrequencyTypes
# from turing_models.utilities.day_count import TuringDayCountTypes
# from turing_models.utilities.calendar import TuringCalendarTypes, TuringBusDayAdjustTypes, TuringDateGenRuleTypes
# from turing_models.market.curves.interpolator import TuringInterpTypes

# swap = TuringIborSwap(TuringDate(2021, 6, 9),
#                       TuringDate(2022, 5, 31),
#                       TuringSwapTypes.PAY,
#                       0.0124,
#                       TuringFrequencyTypes.SEMI_ANNUAL,
#                       TuringDayCountTypes.ACT_365L,
#                       1000000,
#                       0,
#                       TuringFrequencyTypes.SEMI_ANNUAL,
#                       TuringDayCountTypes.ACT_ACT_ISDA)

# value_date = TuringDate(2021, 7, 9)
# zero_dates = value_date.addYears(dates)
# # print(zero_dates)

# curve = TuringDiscountCurveZeros(value_date, zero_dates, np.array(rates))


# v1 = swap.value(value_date,
#                 curve,
#                 curve,
#                 0.01)
# p1 = swap.pv01(value_date, curve)
# s1 = swap.swapRate(value_date, curve, curve, 0.01)
# print(v1)
# print(p1)
# print(s1)


# startDate = TuringDate(2011, 11, 14)
# endDate = TuringDate(2016, 11, 14)
# fixedFreqType = TuringFrequencyTypes.SEMI_ANNUAL
# swapCalendarType = TuringCalendarTypes.TARGET
# busDayAdjustType = TuringBusDayAdjustTypes.MODIFIED_FOLLOWING
# dateGenRuleType = TuringDateGenRuleTypes.BACKWARD
# fixedDayCountType = TuringDayCountTypes.THIRTY_E_360_ISDA
# fixedLegType = TuringSwapTypes.PAY
# fixedCoupon = 0.0124
# notional = 1000000
#
#
# swap = TuringIborSwap(startDate,
#                       endDate,
#                       fixedLegType,
#                       fixedCoupon=fixedCoupon,
#                       fixedFreqType=fixedFreqType,
#                       fixedDayCountType=fixedDayCountType,
#                       floatFreqType=TuringFrequencyTypes.SEMI_ANNUAL,
#                       floatDayCountType=TuringDayCountTypes.ACT_360,
#                       notional=notional,
#                       calendarType=swapCalendarType,
#                       busDayAdjustType=busDayAdjustType,
#                       dateGenRuleType=dateGenRuleType)
#
# #    swap.printFixedLegFlows()
#
# dts = [TuringDate(2011, 11, 14), TuringDate(2012, 5, 14), TuringDate(2012, 11, 14),
#        TuringDate(2013, 5, 14), TuringDate(2013, 11, 14), TuringDate(2014, 5, 14),
#        TuringDate(2014, 11, 14), TuringDate(2015, 5, 14), TuringDate(2015, 11, 16),
#        TuringDate(2016, 5, 16), TuringDate(2016, 11, 14)]
#
# dfs = [0.9999843, 0.9966889, 0.9942107, 0.9911884, 0.9880738, 0.9836490,
#        0.9786276, 0.9710461, 0.9621778, 0.9514315, 0.9394919]
#
# valuationDate = startDate
#
# curve = TuringDiscountCurve(valuationDate, dts, np.array(dfs),
#                             TuringInterpTypes.FLAT_FWD_RATES)
#
# v = swap.value(valuationDate, curve, curve)
#
# print(v)



import numpy as np

from turing_models.utilities.mathematics import ONE_MILLION
from turing_models.instruments.rates.ibor_single_curve import TuringIborSingleCurve
from turing_models.instruments.rates.ibor_swap import TuringIborSwap
from turing_models.instruments.rates.ibor_deposit import TuringIborDeposit
from turing_models.utilities.calendar import TuringBusDayAdjustTypes
from turing_models.utilities.calendar import TuringDateGenRuleTypes
from turing_models.utilities.calendar import TuringCalendarTypes
from turing_models.utilities.frequency import TuringFrequencyTypes
from turing_models.utilities.day_count import TuringDayCountTypes
from turing_models.utilities.turing_date import TuringDate
from turing_models.utilities.global_types import TuringSwapTypes


def buildIborSingleCurve(valuationDate):

    settlementDate = valuationDate
    dcType = TuringDayCountTypes.ACT_360

    depos = []
    fras = []
    swaps = []

    maturityDate = settlementDate.addMonths(1)
    depo1 = TuringIborDeposit(valuationDate, maturityDate, -0.00251, dcType)
    depos.append(depo1)

    fixedFreq = TuringFrequencyTypes.ANNUAL
    dcType = TuringDayCountTypes.THIRTY_E_360
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
    fixedFreqType = TuringFrequencyTypes.ANNUAL
    fixedDayCountType = TuringDayCountTypes.THIRTY_E_360

    floatSpread = 0.0
    floatFreqType = TuringFrequencyTypes.SEMI_ANNUAL
    floatDayCountType = TuringDayCountTypes.ACT_360
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


# test_LiborSwap()


# dates = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 15, 20, 25, 30, 35, 40, 45, 50]
dates = [ 0.25,  0.5, 0.75, 1, 2,        3,        4,        5,        7,        10]

# rates = [-0.001506, -0.000185, 0.001358, 0.0027652, 0.0041539, 0.0054604, 0.006674, 0.007826, 0.008821, 0.0097379, 0.0105406, 0.0123927, 0.0139882, 0.0144972, 0.0146081, 0.01461897, 0.014567455, 0.0140826, 0.01436822]
rates = [0.023125, 0.023363, 0.023538,        0.023713,        0.024613,        0.025579,        0.026491,        0.027313,        0.028675, 0.03015]



irs = IRS(effective_date=TuringDate(2021, 7, 22),
          termination_date=TuringDate(2026, 7, 22),
          fixed_leg_type=TuringSwapTypes.PAY,
          fixed_freq_type=TuringFrequencyTypes.QUARTERLY,
          fixed_day_count_type=TuringDayCountTypes.ACT_365L,
          fixed_coupon=0.029425,
          notional=600000,
          float_spread=0,
          float_freq_type=TuringFrequencyTypes.QUARTERLY,
          float_day_count_type=TuringDayCountTypes.ACT_365L,
          value_date=TuringDate(2021, 8, 24),
          swap_curve_dates=dates,
          swap_curve_rates=rates,
          deposit_term=1/52,
          deposit_rate=0.0222,
          first_fixing_rate=0.02,
          deposit_day_count_type=TuringDayCountTypes.ACT_365L,
          fixed_freq_type_curve=TuringFrequencyTypes.QUARTERLY,
          fixed_day_count_type_curve=TuringDayCountTypes.ACT_365L,
          fixed_leg_type_curve=TuringSwapTypes.PAY,
          reset_freq_type=TuringFrequencyTypes.WEEKLY)

print(irs.price())
print(irs.pv01())
print(irs.swap_rate())

# from turing_models.instruments.irs import create_ibor_single_curve
# curve = create_ibor_single_curve(value_date=TuringDate(2021, 8, 17),
#                                  deposit_term=0.019,
#                                  deposit_rate=0.02,
#                                  deposit_day_count_type=TuringDayCountTypes.ACT_365L,
#                                  swap_curve_dates=TuringDate(2021, 8, 17).addYears(dates),
#                                  fixed_leg_type_curve=TuringSwapTypes.PAY,
#                                  swap_curve_rates=rates,
#                                  fixed_freq_type_curve=TuringFrequencyTypes.QUARTERLY,
#                                  fixed_day_count_type_curve=TuringDayCountTypes.ACT_365L,
#                                  dx=0)
# print(curve)

# @njit(fastmath=True, cache=True)
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
