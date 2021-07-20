import numpy as np

from fundamental.pricing_context import CurveScenario
from fundamental.market.curves.discount_curve_zeros import TuringDiscountCurveZeros

from turing_models.utilities.turing_date import TuringDate
from turing_models.instruments.bond_fixed_rate import BondFixedRate
from turing_models.instruments.bond_floating_rate import BondFloatingRate
from turing_models.instruments.common import RiskMeasure


dates = [0.083, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0, 10.5, 11.0, 11.5, 12.0, 12.5, 13.0, 13.5, 14.0, 14.5, 15.0, 15.5, 16.0, 16.5, 17.0, 17.5, 18.0, 18.5, 19.0, 19.5, 20.0, 20.5, 21.0, 21.5, 22.0, 22.5, 23.0, 23.5, 24.0, 24.5, 25.0, 25.5, 26.0, 26.5, 27.0, 27.5, 28.0, 28.5, 29.0, 29.5, 30.0, 30.5, 31.0, 31.5, 32.0, 32.5, 33.0, 33.5, 34.0, 34.5, 35.0, 35.5, 36.0, 36.5, 37.0, 37.5, 38.0, 38.5, 39.0, 39.5, 40.0, 40.5, 41.0, 41.5, 42.0, 42.5, 43.0, 43.5, 44.0, 44.5, 45.0, 45.5, 46.0, 46.5, 47.0, 47.5, 48.0, 48.5, 49.0, 49.5, 50.0]
rates = [0.01935, 0.019773, 0.021824, 0.023816, 0.024863, 0.025819, 0.026775000000000004, 0.027221000000000002, 0.027667, 0.028093, 0.02852, 0.028952, 0.029384999999999998, 0.029767000000000002, 0.030149, 0.030538, 0.030926, 0.030935, 0.030945, 0.030957, 0.030969000000000003, 0.030983, 0.030997, 0.03143, 0.031863, 0.032303, 0.032743, 0.03319, 0.033638, 0.034094, 0.034551, 0.035017, 0.035484, 0.035531, 0.035577, 0.035628, 0.035678, 0.035732, 0.035786, 0.035842, 0.035899, 0.035959, 0.036018, 0.036101999999999995, 0.036185, 0.036271, 0.036357, 0.036446, 0.036534, 0.036626, 0.036717, 0.036810999999999997, 0.036906, 0.037002, 0.037099, 0.037199, 0.037299, 0.037401, 0.037504, 0.037609, 0.037715, 0.037823, 0.037932, 0.03796, 0.037988, 0.038018, 0.038048, 0.038079999999999996, 0.038111, 0.038145, 0.038179, 0.038214, 0.038249, 0.038286, 0.038323, 0.038362, 0.038401, 0.038441, 0.038481999999999995, 0.038523999999999996, 0.038565999999999996, 0.038610000000000005, 0.038654, 0.038699, 0.038743, 0.038789, 0.038835, 0.038883, 0.038931, 0.038981, 0.039030999999999996, 0.039083, 0.039134, 0.039188, 0.039242, 0.039297, 0.039353, 0.039411, 0.039469, 0.039529, 0.039588, 0.039651, 0.039713]

bond_fr = BondFixedRate(coupon=0.04,
                        curve_code="CBD100003",
                        issue_date=TuringDate(2015, 11, 13),
                        due_date=TuringDate(2025, 11, 14),
                        freq_type='半年付息',
                        accrual_type='ACT/365',
                        par=100,
                        zero_dates=dates,
                        zero_rates=rates)

# print(bond_fr.__ytm__)
# print(bond_fr.yield_to_maturity())

dv011 = bond_fr.calc(RiskMeasure.Dv01)
dollar_duration1 = bond_fr.calc(RiskMeasure.DollarDuration)
dollar_convexity1 = bond_fr.calc(RiskMeasure.DollarConvexity)
macauley_duration1 = bond_fr.macauley_duration()
modified_duration1 = bond_fr.modified_duration()
principal1 = bond_fr.principal()
full_price_from_ytm1 = bond_fr.full_price_from_ytm()
clean_price_from_ytm1 = bond_fr.clean_price_from_ytm()
full_price_from_discount_curve1 = bond_fr.full_price_from_discount_curve()
clean_price_from_discount_curve1 = bond_fr.clean_price_from_discount_curve()
current_yield1 = bond_fr.current_yield()
yield_to_maturity1 = bond_fr.yield_to_maturity()
calc_accrued_interest1 = bond_fr.calc_accrued_interest()
print('dv01:', bond_fr.calc(RiskMeasure.Dv01))
print('dollar_duration:', bond_fr.calc(RiskMeasure.DollarDuration))
print('dollar_convexity:', bond_fr.calc(RiskMeasure.DollarConvexity))

print('macauley_duration:', bond_fr.macauley_duration())
print('modified_duration:', bond_fr.modified_duration())
print('principal:', bond_fr.principal())
print('full_price_from_ytm:', bond_fr.full_price_from_ytm())
print('clean_price_from_ytm:', bond_fr.clean_price_from_ytm())
print('full_price_from_discount_curve:', bond_fr.full_price_from_discount_curve())
print('clean_price_from_discount_curve:', bond_fr.clean_price_from_discount_curve())
print('current_yield:', bond_fr.current_yield())
print('yield_to_maturity:', bond_fr.yield_to_maturity())
print('calc_accrued_interest:', bond_fr.calc_accrued_interest())

print("---------------------------------------------")

scenario = CurveScenario(parallel_shift=[{"curve_code": "CBD100003", "value": 1000}, {"curve_code": "CBD100003", "value": 12}],
                         curve_shift=[{"curve_code": "CBD100003", "value": 1000}, {"curve_code": "CBD100003", "value": 12}],
                         pivot_point=[{"curve_code": "CBD100003", "value": 2}, {"curve_code": "CBD100003", "value": 3}],
                         tenor_start=[{"curve_code": "CBD100003", "value": 1.5}, {"curve_code": "CBD100003", "value": 1}],
                         tenor_end=[{"curve_code": "CBD100003", "value": 40}, {"curve_code": "CBD100003", "value": 30}])

with scenario:
    print(bond_fr.__ytm__)
    print(bond_fr.yield_to_maturity())
    dv012 = bond_fr.calc(RiskMeasure.Dv01)
    dollar_duration2 = bond_fr.calc(RiskMeasure.DollarDuration)
    dollar_convexity2 = bond_fr.calc(RiskMeasure.DollarConvexity)
    macauley_duration2 = bond_fr.macauley_duration()
    modified_duration2 = bond_fr.modified_duration()
    principal2 = bond_fr.principal()
    full_price_from_ytm2 = bond_fr.full_price_from_ytm()
    clean_price_from_ytm2 = bond_fr.clean_price_from_ytm()
    full_price_from_discount_curve2 = bond_fr.full_price_from_discount_curve()
    clean_price_from_discount_curve2 = bond_fr.clean_price_from_discount_curve()
    current_yield2 = bond_fr.current_yield()
    yield_to_maturity2 = bond_fr.yield_to_maturity()
    calc_accrued_interest2 = bond_fr.calc_accrued_interest()

    print('dv01:', dv011 == dv012)
    print('dollar_duration:', dollar_duration1 == dollar_duration2)
    print('dollar_convexity:', dollar_convexity1 == dollar_convexity2)

    print('macauley_duration:', macauley_duration1 == macauley_duration2)
    print('modified_duration:', modified_duration1 == modified_duration2)
    print('principal:', principal1 == principal2)
    print('full_price_from_ytm:', full_price_from_ytm1 == full_price_from_ytm2)
    print('clean_price_from_ytm:', clean_price_from_ytm1 == clean_price_from_ytm2)
    print('full_price_from_discount_curve:', full_price_from_discount_curve1 == full_price_from_discount_curve2)
    print('clean_price_from_discount_curve:', clean_price_from_discount_curve1 == clean_price_from_discount_curve2)
    print('current_yield:', current_yield1 == current_yield2)
    print('yield_to_maturity:', yield_to_maturity1 == yield_to_maturity2)
    print('calc_accrued_interest:', calc_accrued_interest1 == calc_accrued_interest2)


# bond_frn = BondFloatingRate(quoted_margin=0.01,
#                             issue_date=TuringDate(2015, 11, 13),
#                             due_date=TuringDate(2025, 11, 14),
#                             freq_type='半年付息',
#                             accrual_type='ACT/ACT',
#                             par=100,
#                             clean_price=99,
#                             next_coupon=0.035,
#                             current_ibor=0.037,
#                             future_ibor=0.038,
#                             dm=0.01)
#
# print('dv01:', bond_frn.calc(RiskMeasure.Dv01))
# print('dollar_duration:', bond_frn.calc(RiskMeasure.DollarDuration))
# print('dollar_convexity:', bond_frn.calc(RiskMeasure.DollarConvexity))
#
# print('dollar_credit_duration:', bond_frn.dollar_credit_duration())
# print('modified_credit_duration:', bond_frn.modified_credit_duration())
# print('macauley_rate_duration:', bond_frn.macauley_rate_duration())
# print('modified_rate_duration:', bond_frn.modified_rate_duration())
# print('principal:', bond_frn.principal())
# print('full_price_from_dm:', bond_frn.full_price_from_dm())
# print('clean_price_from_dm:', bond_frn.clean_price_from_dm())
# print('discount_margin:', bond_frn.discount_margin())
# print('calc_accrued_interest:', bond_frn.calc_accrued_interest())
