from fundamental.pricing_context import CurveScenario
from turing_models.instruments.credit.bond_adv_redemption import BondAdvRedemption
from turing_models.instruments.credit.bond_floating_rate import BondFloatingRate
from turing_models.instruments.credit.bond_putable_adjustable import BondPutableAdjustable

from turing_models.market.data.china_money_yield_curve import dates, rates
from turing_models.utilities.turing_date import TuringDate
from turing_models.utilities.day_count import DayCountType
from turing_models.utilities.frequency import FrequencyType
from turing_models.instruments.credit.bond_fixed_rate import BondFixedRate
from turing_models.instruments.common import RiskMeasure, YieldCurveCode


curve_chinabond = YieldCurveCode.CBD100222
bond_fr = BondFixedRate(asset_id="BONDCN00000007",
                        coupon=0.04,
                        curve_code=curve_chinabond,
                        issue_date=TuringDate(2015, 11, 13),
                        # due_date=TuringDate(2025, 11, 14),
                        bond_term_year=10,
                        freq_type=FrequencyType.SEMI_ANNUAL,
                        accrual_type=DayCountType.ACT_365L,
                        use_mkt_price=False,
                        spread_adjustment=-123.47058566614673,
                        # market_clean_price=80,
                        par=100)

print("Fixed Rate Bond:")
price_1 = bond_fr.calc(RiskMeasure.FullPrice)
clean_price_1 = bond_fr.calc(RiskMeasure.CleanPrice)
ytm_1 = bond_fr.calc(RiskMeasure.YTM)
dv01_1 = bond_fr.calc(RiskMeasure.Dv01)
modified_duration_1 = bond_fr.calc(RiskMeasure.ModifiedDuration)
dollar_convexity_1 = bond_fr.calc(RiskMeasure.DollarConvexity)

print("spread_adjustment", bond_fr._spread_adjustment)
print('full_price', price_1)
print('clean_price', clean_price_1)
print('ytm', ytm_1)
print('dv01:', dv01_1)
print('modified_duration:', modified_duration_1)
print('dollar_convexity:', dollar_convexity_1)
print("---------------------------------------------")
