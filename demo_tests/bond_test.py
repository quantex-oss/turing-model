from fundamental.pricing_context import CurveScenario
from fundamental.portfolio.portfolio import Portfolio
from fundamental.portfolio.position import Position

from turing_models.utilities.turing_date import TuringDate
from turing_models.utilities.day_count import TuringDayCountTypes
from turing_models.utilities.frequency import TuringFrequencyTypes
from turing_models.instruments.rates.bond_fixed_rate import BondFixedRate
from turing_models.instruments.common import RiskMeasure, YieldCurveCode

from loguru import logger
import sys
logger.remove()
logger.add(sys.stderr, level="ERROR")

# pricing_date = TuringDate(2021, 11, 24)

# 1. 获取组合持仓
portfolio = Portfolio(portfolio_name="Rates")
portfolio.calc(
    [
        RiskMeasure.FullPrice,
        RiskMeasure.CleanPrice,
        RiskMeasure.YTM,
        RiskMeasure.Dv01,
        RiskMeasure.DollarDuration,
        RiskMeasure.DollarConvexity

    ])

print("---------------------------------------------")
print("原始持仓和风险")
portfolio.show_table()


# 2. What-If 新增固息债持仓
curve_chinabond = YieldCurveCode.CBD100222
bond_fr = BondFixedRate(bond_symbol="210001",
                        coupon=0.04,
                        curve_code=curve_chinabond,
                        issue_date=TuringDate(2015, 11, 13),
                        # due_date=TuringDate(2025, 11, 14),
                        # bond_term_year=10,
                        freq_type=TuringFrequencyTypes.SEMI_ANNUAL,
                        accrual_type=TuringDayCountTypes.ACT_365L,
                        par=100)

price_1 = bond_fr.calc(RiskMeasure.FullPrice)
clean_price_1 = bond_fr.calc(RiskMeasure.CleanPrice)
ytm_1 = bond_fr.calc(RiskMeasure.YTM)
dv01_1 = bond_fr.calc(RiskMeasure.Dv01)
modified_duration_1 = bond_fr.calc(RiskMeasure.ModifiedDuration)
dollar_convexity_1 = bond_fr.calc(RiskMeasure.DollarConvexity)

print("---------------------------------------------")
print("Fixed Rate Bond to be added:")
print('price', price_1)
print('clean_price', clean_price_1)
print('ytm', ytm_1)
print('dv01:', dv01_1)
print('modified_duration:', modified_duration_1)
print('dollar_convexity:', dollar_convexity_1)
print("---------------------------------------------")

posiiton = Position(tradable=bond_fr, quantity=100000.0)
portfolio.add(posiiton)
portfolio.calc(
    [
        RiskMeasure.FullPrice,
        RiskMeasure.CleanPrice,
        RiskMeasure.YTM,
        RiskMeasure.Dv01,
        RiskMeasure.DollarDuration,
        RiskMeasure.DollarConvexity

    ])
print("---------------------------------------------")
print("新增债券后新持仓和风险")
portfolio.show_table()

# 3. What-If 调整曲线：1. 平移100bps；2. 以2年为中点，1.655年到40年的曲线区间，向上旋转100bps

# CurveScenario参数含义：
# parallel_shift：曲线整体平移，单位bp，正值表示向上平移，负值相反
# curve_shift：曲线旋转，单位bp，表示曲线左端和右端分别绕pivot_point旋转的绝对值之和，正值表示右侧向上旋转，负值相反
# pivot_point：旋转中心，单位是年，若不传该参数，表示旋转中心是曲线的第一个时间点
# tenor_start：旋转起始点，单位是年，若不传该参数，表示从曲线的第一个时间点开始旋转
# tenor_end：旋转结束点，单位是年，若不传该参数，表示从曲线的最后一个时间点结束旋转
# pivot_point、tenor_start和tenor_end的范围为[原曲线的第一个时间点，原曲线的最后一个时间点]
curve_aaabond = YieldCurveCode.CBD100252
curve_scenario = CurveScenario(
    parallel_shift=[{"curve_code": curve_chinabond, "value": 100},
                    {"curve_code": curve_aaabond, "value": 100}],
    curve_shift=[{"curve_code": curve_chinabond, "value": 100},
                 {"curve_code": curve_aaabond, "value": 100}],
    pivot_point=[{"curve_code": curve_chinabond, "value": 2},
                 {"curve_code": curve_aaabond, "value": 2}],
    tenor_start=[{"curve_code": curve_chinabond, "value": 1.655},
                 {"curve_code": curve_aaabond, "value": 1.655}],
    tenor_end=[{"curve_code": curve_chinabond, "value": 40},
               {"curve_code": curve_aaabond, "value": 40}])

with curve_scenario:
    portfolio.calc(
        [
            RiskMeasure.FullPrice,
            RiskMeasure.CleanPrice,
            RiskMeasure.YTM,
            RiskMeasure.Dv01,
            RiskMeasure.DollarDuration,
            RiskMeasure.DollarConvexity

        ])

    print("---------------------------------------------")
    print("新增债券且利率曲线修正后持仓和风险")
    portfolio.show_table()