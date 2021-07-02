import numpy as np

from fundamental.market.curves.discount_curve_zeros import TuringDiscountCurveZeros

from turing_models.utilities.turing_date import TuringDate
from fundamental.pricing_context import PricingContext
from turing_models.instrument.archive.bond import Bond
from turing_models.instrument.bond_fixed_rate import BondFixedRate as Bond1
from turing_models.instrument.bond_floating_rate import BondFloatingRate as Bond2
from turing_models.instrument.common import RiskMeasure


dates = [0.083, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0, 10.5, 11.0, 11.5, 12.0, 12.5, 13.0, 13.5, 14.0, 14.5, 15.0, 15.5, 16.0, 16.5, 17.0, 17.5, 18.0, 18.5, 19.0, 19.5, 20.0, 20.5, 21.0, 21.5, 22.0, 22.5, 23.0, 23.5, 24.0, 24.5, 25.0, 25.5, 26.0, 26.5, 27.0, 27.5, 28.0, 28.5, 29.0, 29.5, 30.0, 30.5, 31.0, 31.5, 32.0, 32.5, 33.0, 33.5, 34.0, 34.5, 35.0, 35.5, 36.0, 36.5, 37.0, 37.5, 38.0, 38.5, 39.0, 39.5, 40.0, 40.5, 41.0, 41.5, 42.0, 42.5, 43.0, 43.5, 44.0, 44.5, 45.0, 45.5, 46.0, 46.5, 47.0, 47.5, 48.0, 48.5, 49.0, 49.5, 50.0]
rates = [1.935, 1.9773, 2.1824, 2.3816, 2.4863, 2.5819, 2.6775, 2.7221, 2.7667, 2.8093, 2.852, 2.8952, 2.9385, 2.9767, 3.0149, 3.0538, 3.0926, 3.0935, 3.0945, 3.0957, 3.0969, 3.0983, 3.0997, 3.143, 3.1863, 3.2303, 3.2743, 3.319, 3.3638, 3.4094, 3.4551, 3.5017, 3.5484, 3.5531, 3.5577, 3.5628, 3.5678, 3.5732, 3.5786, 3.5842, 3.5899, 3.5959, 3.6018, 3.6102, 3.6185, 3.6271, 3.6357, 3.6446, 3.6534, 3.6626, 3.6717, 3.6811, 3.6906, 3.7002, 3.7099, 3.7199, 3.7299, 3.7401, 3.7504, 3.7609, 3.7715, 3.7823, 3.7932, 3.796, 3.7988, 3.8018, 3.8048, 3.808, 3.8111, 3.8145, 3.8179, 3.8214, 3.8249, 3.8286, 3.8323, 3.8362, 3.8401, 3.8441, 3.8482, 3.8524, 3.8566, 3.861, 3.8654, 3.8699, 3.8743, 3.8789, 3.8835, 3.8883, 3.8931, 3.8981, 3.9031, 3.9083, 3.9134, 3.9188, 3.9242, 3.9297, 3.9353, 3.9411, 3.9469, 3.9529, 3.9588, 3.9651, 3.9713]
# zero_rates = np.array(rates)
bond = Bond1(quantity=2,
             bond_type='BOND',
             coupon=0.05,
             issue_date=TuringDate(2015, 11, 13),
             due_date=TuringDate(2025, 11, 14),
             freq_type='半年付息',
             accrual_type='ACT/365',
             par=100,
             clean_price=99,
             ytm=0.045,
             zero_dates=dates,
             zero_rates=rates)

# settlement_date = TuringDate(2021, 6, 28)
# expiry = TuringDate(2021, 9, 28)
# zero_dates = settlement_date.addYears(dates)
# curve = TuringDiscountCurveZeros(valuationDate=settlement_date, zeroDates=zero_dates, zeroRates=rates)
# print(curve.zeroRate(expiry))
# print('full_price_from_ytm:', bond.full_price_from_ytm())
# print('principal:', bond.principal())

print('dv01:', bond.calc(RiskMeasure.Dv01))
print('dollar_duration:', bond.calc(RiskMeasure.DollarDuration))
print('dollar_convexity:', bond.calc(RiskMeasure.DollarConvexity))

print('macauley_duration:', bond.macauley_duration())
print('modified_duration:', bond.modified_duration())
print('principal:', bond.principal())
print('full_price_from_ytm:', bond.full_price_from_ytm())
print('clean_price_from_ytm:', bond.clean_price_from_ytm())
print('full_price_from_discount_curve:', bond.full_price_from_discount_curve())
print('clean_price_from_discount_curve:', bond.clean_price_from_discount_curve())
print('current_yield:', bond.current_yield())
print('yield_to_maturity:', bond.yield_to_maturity())
print('calc_accrued_interest:', bond.calc_accrued_interest())

# bond = Bond2(quantity=2,
#              bond_type='frn',
#              quoted_margin=0.01,
#              issue_date=TuringDate(2015, 11, 13),
#              due_date=TuringDate(2025, 11, 14),
#              freq_type='半年付息',
#              accrual_type='ACT/ACT',
#              par=100,
#              next_coupon=0.045,
#              current_ibor=0.047,
#              future_ibor=0.048,
#              dm=0.01)
#
# print('dv01:', bond.dv01())
# print('dollar_duration:', bond.dollar_duration())
# print('dollar_convexity:', bond.dollar_convexity())
# # print('macauley_duration:', bond.macauley_duration())
# # print('modified_duration:', bond.modified_duration())
#
# import datetime
# from turing_models.products.bonds.bond_frn import TuringBondFRN
# from turing_models.utilities.frequency import TuringFrequencyTypes
# from turing_models.utilities.day_count import TuringDayCountTypes
# bond1 = TuringBondFRN(issueDate=TuringDate(2015, 11, 13),
#                       maturityDate=TuringDate(2025, 11, 14),
#                       quotedMargin=0.01,
#                       freqType=TuringFrequencyTypes.SEMI_ANNUAL,
#                       accrualType=TuringDayCountTypes.ACT_ACT_ISDA,
#                       faceAmount=200)
# settlementDate = TuringDate(*(datetime.date.today().timetuple()[:3]))
# nextCoupon = 0.045
# currentIbor = 0.047
# futureIbor = 0.048
# dm = 0.01
# cleanPrice = 99
# dollar_duration = bond1.dollarDuration(settlementDate,
#                                        nextCoupon,
#                                        currentIbor,
#                                        futureIbor,
#                                        dm)
# dv01 = bond1.dv01(settlementDate,
#                   nextCoupon,
#                   currentIbor,
#                   futureIbor,
#                   dm)
# dollar_convexity = bond1.dollar_convexity(settlementDate,
#                                           nextCoupon,
#                                           currentIbor,
#                                           futureIbor,
#                                           dm)
# dollar_credit_duration = bond1.dollarCreditDuration(settlementDate,
#                                                     nextCoupon,
#                                                     currentIbor,
#                                                     futureIbor,
#                                                     dm)
# modified_credit_duration = bond1.modifiedCreditDuration(settlementDate,
#                                                         nextCoupon,
#                                                         currentIbor,
#                                                         futureIbor,
#                                                         dm)
# macauley_rate_duration = bond1.macauleyRateDuration(settlementDate,
#                                                     nextCoupon,
#                                                     currentIbor,
#                                                     futureIbor,
#                                                     dm)
# modified_rate_duration = bond1.modifiedRateDuration(settlementDate,
#                                                     nextCoupon,
#                                                     currentIbor,
#                                                     futureIbor,
#                                                     dm)
# principal = bond1.principal(settlementDate,
#                             nextCoupon,
#                             currentIbor,
#                             futureIbor,
#                             dm)
# full_price_from_dm = bond1.fullPriceFromDM(settlementDate,
#                                            nextCoupon,
#                                            currentIbor,
#                                            futureIbor,
#                                            dm)
# clean_price_from_dm = bond1.cleanPriceFromDM(settlementDate,
#                                              nextCoupon,
#                                              currentIbor,
#                                              futureIbor,
#                                              dm)
# discount_margin = bond1.discountMargin(settlementDate,
#                                        nextCoupon,
#                                        currentIbor,
#                                        futureIbor,
#                                        cleanPrice)
# calc_accrued_interest = bond1.calcAccruedInterest(settlementDate,
#                                                   nextCoupon)
# print("---------------------------------------------")
# print('dv01:', dv01)
# print('dollar_duration:', dollar_duration)
# print('dollar_convexity:', dollar_convexity)
# print('dollar_credit_duration:', dollar_credit_duration)
# print('modified_credit_duration:', modified_credit_duration)
# print('macauley_rate_duration:', macauley_rate_duration)
# print('modified_rate_duration:', modified_rate_duration)
# print('principal:', principal)
# print('full_price_from_dm:', full_price_from_dm)
# print('clean_price_from_dm:', clean_price_from_dm)
# print('discount_margin:', discount_margin)
# print('calc_accrued_interest:', calc_accrued_interest)
#
# from turing_models.instrument.bond_floating_rate import BondFloatingRate as Bond2
#
# bond2 = Bond2(quantity=2,
#               bond_type='frn',
#               quoted_margin=0.01,
#               issue_date=TuringDate(2015, 11, 13),
#               due_date=TuringDate(2025, 11, 14),
#               freq_type='半年付息',
#               accrual_type='ACT/ACT',
#               par=100,
#               clean_price=99,
#               next_coupon=0.045,
#               current_ibor=0.047,
#               future_ibor=0.048,
#               dm=0.01)
#
# print("---------------------------------------------")
# print('dv01:', bond2.dv01())
# print('dollar_duration:', bond2.dollar_duration())
# print('dollar_convexity:', bond2.dollar_convexity())
# print('dollar_credit_duration:', bond2.dollar_credit_duration())
# print('modified_credit_duration:', bond2.modified_credit_duration())
# print('macauley_rate_duration:', bond2.macauley_rate_duration())
# print('modified_rate_duration:', bond2.modified_rate_duration())
# print('principal:', bond2.principal())
# print('full_price_from_dm:', bond2.full_price_from_dm())
# print('clean_price_from_dm:', bond2.clean_price_from_dm())
# print('discount_margin:', bond2.discount_margin())
# print('calc_accrued_interest:', bond2.calc_accrued_interest())
