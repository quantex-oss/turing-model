from fundamental.pricing_context import CurveScenario
from turing_models.instruments.credit.bond_advanced_redemption import BondAdvancedRedemption
from turing_models.instruments.credit.bond_floating_rate import BondFloatingRate
from turing_models.instruments.credit.bond_putable_adjustable import BondPutableAdjustable

from turing_models.market.data.china_money_yield_curve import dates, rates
from turing_models.utilities.turing_date import TuringDate
from turing_models.utilities.day_count import TuringDayCountTypes
from turing_models.utilities.frequency import TuringFrequencyTypes
from turing_models.instruments.credit.bond_fixed_rate import BondFixedRate
from turing_models.instruments.common import RiskMeasure


bond_fr = BondFixedRate(asset_id="BONDCN00000007",
                        coupon=0.04,
                        curve_code="CBD100003",
                        issue_date=TuringDate(2015, 11, 13),
                        due_date=TuringDate(2025, 11, 14),
                        freq_type=TuringFrequencyTypes.SEMI_ANNUAL,
                        accrual_type=TuringDayCountTypes.ACT_365L,
                        par=100)

print("Fixed Rate Bond:")
price_1 = bond_fr.calc(RiskMeasure.FullPrice)
clean_price_1 = bond_fr.calc(RiskMeasure.CleanPrice)
ytm_1 = bond_fr.calc(RiskMeasure.YTM)
dv01_1 = bond_fr.calc(RiskMeasure.Dv01)
modified_duration_1 = bond_fr.calc(RiskMeasure.ModifiedDuration)
dollar_convexity_1 = bond_fr.calc(RiskMeasure.DollarConvexity)

print('price', price_1)
print('clean_price', clean_price_1)
print('ytm', ytm_1)
print('dv01:', dv01_1)
print('modified_duration:', modified_duration_1)
print('dollar_convexity:', dollar_convexity_1)
print("---------------------------------------------")

# CurveScenario参数含义：
# parallel_shift：曲线整体平移，单位bp，正值表示向上平移，负值相反
# curve_shift：曲线旋转，单位bp，表示曲线左端和右端分别绕pivot_point旋转的绝对值之和，正值表示右侧向上旋转，负值相反
# pivot_point：旋转中心，单位是年，若不传该参数，表示旋转中心是曲线的第一个时间点
# tenor_start：旋转起始点，单位是年，若不传该参数，表示从曲线的第一个时间点开始旋转
# tenor_end：旋转结束点，单位是年，若不传该参数，表示从曲线的最后一个时间点结束旋转
# pivot_point、tenor_start和tenor_end的范围为[原曲线的第一个时间点，原曲线的最后一个时间点]
scenario = CurveScenario(parallel_shift=[{"curve_code": "CBD100003", "value": 1000}, {"curve_code": "CBD100003", "value": 12}],
                         curve_shift=[{"curve_code": "CBD100003", "value": 1000}, {"curve_code": "CBD100003", "value": 12}],
                         pivot_point=[{"curve_code": "CBD100003", "value": 2}, {"curve_code": "CBD100003", "value": 3}],
                         tenor_start=[{"curve_code": "CBD100003", "value": 1.5}, {"curve_code": "CBD100003", "value": 1}],
                         tenor_end=[{"curve_code": "CBD100003", "value": 40}, {"curve_code": "CBD100003", "value": 30}])

with scenario:
    price_2 = bond_fr.calc(RiskMeasure.FullPrice)
    clean_price_2 = bond_fr.calc(RiskMeasure.CleanPrice)
    ytm_2 = bond_fr.calc(RiskMeasure.YTM)
    dv01_2 = bond_fr.calc(RiskMeasure.Dv01)
    modified_duration_2 = bond_fr.calc(RiskMeasure.ModifiedDuration)
    dollar_convexity_2 = bond_fr.calc(RiskMeasure.DollarConvexity)

    print('price', price_2)
    print('clean_price', clean_price_2)
    print('ytm', ytm_2)
    print('dv01:', dv01_2)
    print('modified_duration:', modified_duration_2)
    print('dollar_convexity:', dollar_convexity_2)
    print("---------------------------------------------")

bond_frn = BondFloatingRate(quoted_margin=0.01,
                            issue_date=TuringDate(2015, 11, 13),
                            due_date=TuringDate(2025, 11, 14),
                            freq_type='半年付息',
                            accrual_type='ACT/ACT',
                            par=100,
                            next_coupon=0.035,
                            current_ibor=0.037,
                            future_ibor= 0.038,
                            dm=0.01)

print("Floating Rate Bond:")
print('price', bond_frn.calc(RiskMeasure.FullPrice))
print('clean_price', bond_frn.calc(RiskMeasure.CleanPrice))
print('dv01:', bond_frn.calc(RiskMeasure.Dv01))
print('modified_duration:', bond_frn.calc(RiskMeasure.ModifiedDuration))
print('dollar_convexity:', bond_frn.calc(RiskMeasure.DollarConvexity))
print("---------------------------------------------")

bond_ar = BondAdvancedRedemption(asset_id="BONDCN00000007",
                                 coupon=0.0675,
                                 curve_code="CBD100003",
                                 issue_date=TuringDate(2014, 1, 24),
                                 due_date=TuringDate(2024, 1, 24),
                                 freq_type=TuringFrequencyTypes.ANNUAL,
                                 accrual_type=TuringDayCountTypes.ACT_365L,
                                 par=100,
                                 rdp_terms=[3, 4, 5, 6, 7, 8, 9, 10],
                                 rdp_pct=[0.1, 0.1, 0.1, 0.1, 0.15, 0.15, 0.15, 0.15])

price = bond_ar.calc(RiskMeasure.FullPrice)
clean_price = bond_ar.calc(RiskMeasure.CleanPrice)
ytm = bond_ar.calc(RiskMeasure.YTM)
dv01 = bond_ar.calc(RiskMeasure.Dv01)
modified_duration = bond_ar.calc(RiskMeasure.ModifiedDuration)
dollar_convexity = bond_ar.calc(RiskMeasure.DollarConvexity)

print("Bond with advanced redemption:")
print('price', price)
print('clean_price', clean_price)
print('ytm', ytm)
print('dv01:', dv01)
print('modified_duration:', modified_duration)
print('dollar_convexity:', dollar_convexity)
print("---------------------------------------------")

bond_pa = BondPutableAdjustable(asset_id="BONDCN00000007",
                        coupon=0.0316,
                        issue_date=TuringDate(2021, 8, 5),
                        value_date=TuringDate(2021, 11, 26),
                        due_date=TuringDate(2025, 8, 5),
                        freq_type=TuringFrequencyTypes.ANNUAL,
                        accrual_type=TuringDayCountTypes.ACT_365F,
                        par=100,
                        zero_dates=dates,
                        zero_rates=rates,
                        # adjust_bound_up= -1,
                        # adjust_bound_down= 0,
                        put_date=TuringDate(2023, 8, 5))


price = bond_pa.calc(RiskMeasure.FullPrice)
clean_price = bond_pa.calc(RiskMeasure.CleanPrice)
ytm = bond_pa.calc(RiskMeasure.YTM)
dv01 = bond_pa.calc(RiskMeasure.Dv01)
modified_duration = bond_pa.calc(RiskMeasure.ModifiedDuration)
dollar_convexity = bond_pa.calc(RiskMeasure.DollarConvexity)

print("Bond with putable and rates-adjustable terms:")
print('price', price)
print('clean_price', clean_price)
print('ytm', ytm)
print('dv01:', dv01)
print('modified_duration:', modified_duration)
print('dollar_convexity:', dollar_convexity)
print("---------------------------------------------")