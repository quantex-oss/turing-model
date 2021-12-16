import pandas as pd
from fundamental.pricing_context import CurveScenario
from turing_models.instruments.rates.bond_adv_redemption import BondAdvRedemption
from turing_models.instruments.rates.bond_floating_rate import BondFloatingRate
from turing_models.instruments.rates.bond_putable_adjustable import BondPutableAdjustable
from fundamental.portfolio.portfolio import Portfolio
from fundamental.portfolio.position import Position

from fundamental.pricing_context import PricingContext
from turing_models.market.data.china_money_yield_curve import dates, rates
from turing_models.utilities.turing_date import TuringDate
from turing_models.utilities.day_count import TuringDayCountTypes
from turing_models.utilities.frequency import TuringFrequencyTypes
from turing_models.instruments.rates.bond_fixed_rate import BondFixedRate
from turing_models.instruments.common import RiskMeasure, YieldCurveCode
from turing_models.market.data.china_money_yield_curve import dates, rates
curve_data = pd.DataFrame(data={'tenor': dates, 'rate': rates})
from fundamental.turing_db.data import TuringDB

# curve_data = pd.DataFrame(data={'tenor': dates, 'forward_spot_rate': rates})
# curve_chinabond = YieldCurveCode.CBD100222
bond_pa = BondPutableAdjustable(bond_symbol= "188560.SH",
                                coupon=0.0316,
                                issue_date=TuringDate(2021, 8, 5),
                                value_date=TuringDate(2021, 12, 16),
                                due_date=TuringDate(2025, 8, 5),
                                freq_type=TuringFrequencyTypes.ANNUAL,
                                accrual_type=TuringDayCountTypes.ACT_365F,
                                par=100,
                                # forward_dates=curve_data.tenor,
                                # forward_rates=curve_data.forward_spot_rate,
                                # adjust_bound_up= -1,
                                # adjust_bound_down= 0,
                                put_date=TuringDate(2023, 8, 5))
scenario_extreme =  PricingContext(
bond_yield_curve=[
{"bond_symbol": "188560.SH", "value": curve_data}
]
)
with scenario_extreme:

    price = bond_pa.calc(RiskMeasure.FullPrice)
# clean_price = bond_pa.calc(RiskMeasure.CleanPrice)
# ytm = bond_pa.calc(RiskMeasure.YTM)
# dv01 = bond_pa.calc(RiskMeasure.Dv01)
# modified_duration = bond_pa.calc(RiskMeasure.ModifiedDuration)
# dollar_convexity = bond_pa.calc(RiskMeasure.DollarConvexity)

print("Bond with putable and rates-adjustable terms:")
print('price', price)
# print('clean_price', clean_price)
# print('ytm', ytm)
# print('dv01:', dv01)
# print('modified_duration:', modified_duration)
# print('dollar_convexity:', dollar_convexity)
