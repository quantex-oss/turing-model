from turing_models.market.data.china_money_yield_curve import dates, rates
from turing_models.utilities.turing_date import TuringDate
from turing_models.utilities.day_count import DayCountType
from turing_models.utilities.frequency import FrequencyType
from turing_models.instruments.rates.bond_putable_adjustable import BondPutableAdjustable
# from turing_models.instruments.credit.bond_putable_plus_adjustable import BondPutableAdjustable as BondPutableAdjustable2


bond_fr = BondPutableAdjustable(asset_id="BONDCN00000007",
                                coupon=0.0316,
                                curve_code="CBD100003",
                                issue_date=TuringDate(2021, 8, 5),
                                value_date=TuringDate(2021, 11, 26),
                                due_date=TuringDate(2025, 8, 5),
                                freq_type=FrequencyType.ANNUAL,
                                accrual_type=DayCountType.ACT_365F,
                                par=100,
                                zero_dates=dates,
                                zero_rates=rates,
                                # adjust_bound_up= -1,
                                # adjust_bound_down= 0,
                                # forward_dates=dates,
                                # forward_rates=rates,
                                put_date=TuringDate(2023, 8, 5))

print(bond_fr._pure_bond._clean_price)
price1 = bond_fr._clean_price
# price2 = bond_fr2.full_price_from_discount_curve()
# ytm = bond_fr.yield_to_maturity()
# md = bond_fr.macauley_duration()
dv01 = bond_fr.dv01()
mod = bond_fr.modified_duration()
# price2 = bond_fr.full_price_from_ytm()
# dv01_1 = bond_fr.calc(RiskMeasure.Dv01)
# dollar_duration_1 = bond_fr.calc(RiskMeasure.DollarDuration)
# dollar_convexity_1 = bond_fr.calc(RiskMeasure.DollarConvexity)

print('price:', price1)
# print(ytm)
# print(md)
print(dv01)
print(mod)
# print('price2:', price2)
# print('price:', price2)
# print('dollar_duration:', dollar_duration_1)
# print('dollar_convexity:', dollar_convexity_1)

print("---------------------------------------------")

# CurveScenario参数含义：
# parallel_shift：曲线整体平移，单位bp，正值表示向上平移，负值相反
# curve_shift：曲线旋转，单位bp，表示曲线左端和右端分别绕pivot_point旋转的绝对值之和，正值表示右侧向上旋转，负值相反
# pivot_point：旋转中心，单位是年，若不传该参数，表示旋转中心是曲线的第一个时间点
# tenor_start：旋转起始点，单位是年，若不传该参数，表示从曲线的第一个时间点开始旋转
# tenor_end：旋转结束点，单位是年，若不传该参数，表示从曲线的最后一个时间点结束旋转
# pivot_point、tenor_start和tenor_end的范围为[原曲线的第一个时间点，原曲线的最后一个时间点]
# scenario = CurveScenario(parallel_shift=[{"curve_code": "CBD100003", "value": 1000}, {"curve_code": "CBD100003", "value": 12}],
#                          curve_shift=[{"curve_code": "CBD100003", "value": 1000}, {"curve_code": "CBD100003", "value": 12}],
#                          pivot_point=[{"curve_code": "CBD100003", "value": 2}, {"curve_code": "CBD100003", "value": 3}],
#                          tenor_start=[{"curve_code": "CBD100003", "value": 1.5}, {"curve_code": "CBD100003", "value": 1}],
#                          tenor_end=[{"curve_code": "CBD100003", "value": 40}, {"curve_code": "CBD100003", "value": 30}])

# with scenario:
#     dv01_2 = bond_fr.calc(RiskMeasure.Dv01)
#     dollar_duration_2 = bond_fr.calc(RiskMeasure.DollarDuration)
#     dollar_convexity_2 = bond_fr.calc(RiskMeasure.DollarConvexity)

#     print('dv01:', dv01_2)
#     print('dollar_duration:', dollar_duration_2)
    # print('dollar_convexity:', dollar_convexity_2)
