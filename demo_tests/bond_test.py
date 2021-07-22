import numpy as np

from fundamental.pricing_context import CurveScenario
from fundamental.market.curves.discount_curve_zeros import TuringDiscountCurveZeros

from turing_models.utilities.turing_date import TuringDate
from turing_models.utilities.day_count import TuringDayCountTypes
from turing_models.utilities.frequency import TuringFrequencyTypes
from turing_models.instruments.bond_fixed_rate import BondFixedRate
from turing_models.instruments.bond_floating_rate import BondFloatingRate
from turing_models.instruments.common import RiskMeasure
from tool import dates, rates


bond_fr = BondFixedRate(asset_id="BONDCN00000007",
                        coupon=0.04,
                        curve_code="CBD100003",
                        issue_date=TuringDate(2015, 11, 13),
                        due_date=TuringDate(2025, 11, 14),
                        freq_type=TuringFrequencyTypes.SEMI_ANNUAL,
                        accrual_type=TuringDayCountTypes.ACT_365L,
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

    # print('dv01:', dv011 == dv012)
    # print('dollar_duration:', dollar_duration1 == dollar_duration2)
    # print('dollar_convexity:', dollar_convexity1 == dollar_convexity2)
    #
    # print('macauley_duration:', macauley_duration1 == macauley_duration2)
    # print('modified_duration:', modified_duration1 == modified_duration2)
    # print('principal:', principal1 == principal2)
    # print('full_price_from_ytm:', full_price_from_ytm1 == full_price_from_ytm2)
    # print('clean_price_from_ytm:', clean_price_from_ytm1 == clean_price_from_ytm2)
    # print('full_price_from_discount_curve:', full_price_from_discount_curve1 == full_price_from_discount_curve2)
    # print('clean_price_from_discount_curve:', clean_price_from_discount_curve1 == clean_price_from_discount_curve2)
    # print('current_yield:', current_yield1 == current_yield2)
    # print('yield_to_maturity:', yield_to_maturity1 == yield_to_maturity2)
    # print('calc_accrued_interest:', calc_accrued_interest1 == calc_accrued_interest2)


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
