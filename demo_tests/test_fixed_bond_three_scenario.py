from fundamental.pricing_context import CurveScenario
from turing_models.instruments.credit.bond_adv_redemption import BondAdvRedemption
from turing_models.instruments.credit.bond_floating_rate import BondFloatingRate
from turing_models.instruments.credit.bond_putable_adjustable import BondPutableAdjustable

from turing_models.market.data.china_money_yield_curve import dates, rates
from turing_models.utilities.turing_date import TuringDate
from turing_models.utilities.day_count import TuringDayCountTypes
from turing_models.utilities.frequency import TuringFrequencyTypes
from turing_models.instruments.credit.bond_fixed_rate import BondFixedRate
from turing_models.instruments.common import RiskMeasure, YieldCurveCode
from fundamental.pricing_context import PricingContext


curve_chinabond = YieldCurveCode.CBD100222

# 情景1：通过传入净价净算:
bond_fr1 = BondFixedRate(#asset_id="BONDCN00000007",
                         bond_symbol = "143756.SH",
                        # coupon=0.04,
                        curve_code=curve_chinabond)
                        # issue_date=TuringDate(2015, 11, 13),
                        # due_date=TuringDate(2025, 11, 14),
                        # bond_term_year=10,
                        # freq_type=TuringFrequencyTypes.SEMI_ANNUAL,
                        # accrual_type=TuringDayCountTypes.ACT_365L,
                        # par=100)
scenario_extreme = PricingContext(clean_price=[{"bond_symbol": "143756.SH", "value": 80}])
# curves = TuringDB.bond_yield_curve(curve_code=curve_lists, date=date)
with scenario_extreme:
    price_1 = bond_fr1.calc(RiskMeasure.FullPrice)
    clean_price_1 = bond_fr1.calc(RiskMeasure.CleanPrice)
    ytm_1 = bond_fr1.calc(RiskMeasure.YTM)
    dv01_1 = bond_fr1.calc(RiskMeasure.Dv01)
    modified_duration_1 = bond_fr1.calc(RiskMeasure.ModifiedDuration)
    dollar_convexity_1 = bond_fr1.calc(RiskMeasure.DollarConvexity)

print("1st scenerio:")
print("spread_adjustment", bond_fr1.spread_adjustment)
print('full_price', price_1)
print('clean_price', clean_price_1)
print('ytm', ytm_1)
print('dv01:', dv01_1)
print('modified_duration:', modified_duration_1)
print('dollar_convexity:', dollar_convexity_1)
print("---------------------------------------------")

# 情景2：通过收益率曲线计算债券定价，
bond_fr2 = BondFixedRate(bond_symbol = "143756.SH",
                        curve_code=curve_chinabond)
                  
bond_fr2.resolve()

print("Fixed Rate Bond:")
price_2 = bond_fr2.calc(RiskMeasure.FullPrice)
clean_price_2 = bond_fr2.calc(RiskMeasure.CleanPrice)
ytm_2 = bond_fr2.calc(RiskMeasure.YTM)
dv01_2 = bond_fr2.calc(RiskMeasure.Dv01)
modified_duration_2 = bond_fr2.calc(RiskMeasure.ModifiedDuration)
dollar_convexity_2 = bond_fr2.calc(RiskMeasure.DollarConvexity)
implied_spread_2 = bond_fr2.implied_spread()

print("2nd scenerio:")
print("spread_adjustment", bond_fr2.spread_adjustment)
print("implied_spread", implied_spread_2)
print('full_price', price_2)
print('clean_price', clean_price_2)
print('ytm', ytm_2)
print('dv01:', dv01_2)
print('modified_duration:', modified_duration_2)
print('dollar_convexity:', dollar_convexity_2)
print("---------------------------------------------")

# 情景3：通过收益率曲线和spread调整试算价格
bond_fr3 = BondFixedRate(bond_symbol = "143756.SH",
                        curve_code=curve_chinabond)

print("Fixed Rate Bond:")
price_3 = bond_fr3.calc(RiskMeasure.FullPrice)
clean_price_3 = bond_fr3.calc(RiskMeasure.CleanPrice)
ytm_3 = bond_fr3.calc(RiskMeasure.YTM)
dv01_3 = bond_fr3.calc(RiskMeasure.Dv01)
modified_duration_3 = bond_fr3.calc(RiskMeasure.ModifiedDuration)
dollar_convexity_3 = bond_fr3.calc(RiskMeasure.DollarConvexity)

print("3rd scenerio:")
print("spread_adjustment", bond_fr3.spread_adjustment)
print('full_price', price_3)
print('clean_price', clean_price_3)
print('ytm', ytm_3)
print('dv01:', dv01_3)
print('modified_duration:', modified_duration_3)
print('dollar_convexity:', dollar_convexity_3)
print("---------------------------------------------")
