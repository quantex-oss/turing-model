import pandas as pd
from turing_models.market.data.china_money_yield_curve import dates, rates
from turing_models.utilities.turing_date import TuringDate
from turing_models.utilities.day_count import TuringDayCountTypes
from turing_models.utilities.frequency import TuringFrequencyTypes
from turing_models.instruments.rates.bond_adv_redemption import BondAdvRedemption
from turing_models.instruments.common import RiskMeasure

from turing_models.instruments.common import RiskMeasure, YieldCurveCode
from fundamental.pricing_context import PricingContext

# curve_chinabond = YieldCurveCode.CBD100222
curve_data = pd.DataFrame(data={'tenor': dates, 'rate': rates})



bond_fr = BondAdvRedemption(bond_symbol="188560.SH",
                            coupon=0.0675,
                            issue_date=TuringDate(2014, 1, 24),
                            value_date=TuringDate(2021, 9, 30),
                            due_date=TuringDate(2024, 1, 24),
                            freq_type=TuringFrequencyTypes.ANNUAL,
                            accrual_type=TuringDayCountTypes.ACT_365L,
                            par=100,
                            rdp_dates=[TuringDate(2017, 1, 24),TuringDate(2018, 1, 24),TuringDate(2019, 1, 24),TuringDate(2020, 1, 24),TuringDate(2021, 1, 24),TuringDate(2022, 1, 24),TuringDate(2023, 1, 24),TuringDate(2024, 1, 24)],
                            rdp_pct=[0.1,0.1,0.1,0.1,0.15,0.15,0.15,0.15])

scenario_extreme = PricingContext(bond_yield_curve=[{"bond_symbol": "188560.SH", "value": curve_data}])
# curves = TuringDB.bond_yield_curve(curve_code=curve_lists, date=date)
with scenario_extreme:

    price1 = bond_fr.full_price_from_discount_curve()
    price2 = bond_fr.full_price_from_ytm()
    print(bond_fr.ytm_)
    dv01_1 = bond_fr.calc(RiskMeasure.Dv01)
    dollar_duration_1 = bond_fr.calc(RiskMeasure.DollarDuration)
    dollar_convexity_1 = bond_fr.calc(RiskMeasure.DollarConvexity)

    print('price:', price1)
    print('price:', price2)
    print('dollar_duration:', dollar_duration_1)
    print('dollar_convexity:', dollar_convexity_1)

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