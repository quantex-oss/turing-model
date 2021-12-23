import sys
from loguru import logger

from fundamental.portfolio.portfolio import Portfolio
from fundamental.portfolio.position import Position
from fundamental.pricing_context import PricingContext
from turing_models.instruments.common import RiskMeasure, Currency, CurrencyPair
from turing_models.instruments.credit.bond_fixed_rate import BondFixedRate
from turing_models.instruments.eq.knockout_option import KnockOutOption
from turing_models.instruments.fx.fx_vanilla_option import FXVanillaOption
from turing_models.utilities.day_count import DayCountType
from turing_models.utilities.frequency import FrequencyType
from turing_models.utilities.global_types import TuringOptionType
from turing_models.utilities.turing_date import TuringDate


# logger.remove()
# logger.add(sys.stderr, level="WARNING")

pricing_date = TuringDate(2021, 8, 20)
portfolio = Portfolio(portfolio_name="Credit", pricing_date=pricing_date)

scenario_extreme = PricingContext(
    pricing_date=pricing_date,
    spot=[
        {"symbol": "USD/CNY", "value": 6.5}
    ],

)

# fxoption = FXVanillaOption(start_date=TuringDate(2021, 9, 1),
#                            expiry=TuringDate(2021, 9, 1).addMonths(4),
#                            cut_off_time=TuringDate(2021, 12, 30),
#                            underlier_symbol=CurrencyPair.USDCNY,
#                            strike=6.8,
#                            notional=1_000_000,
#                            notional_currency=Currency.CNY,
#                            option_type=TuringOptionType.CALL,
#                            premium_currency=Currency.CNY)
# fxoption.resolve()
# posiiton = Position(tradable=fxoption, quantity=1.0)
# portfolio.add(posiiton)
#
# knockout_option = KnockOutOption(underlier='SEC063837502',
#                                  option_type=TuringOptionType.CALL,
#                                  expiry=TuringDate(2021, 9, 3),
#                                  strike_price=5.3,
#                                  participation_rate=1.0,
#                                  barrier=5.5,
#                                  notional=1000000.0,
#                                  rebate=0.2,
#                                  value_date=TuringDate(2021, 7, 6),
#                                  start_date=TuringDate(2021, 5, 6),
#                                  initial_spot=5.0,
#                                  stock_price=5.262,
#                                  currency="CNY",
#                                  volatility=0.1,
#                                  dividend_yield=0)
#
# knockout_option.resolve()
# posiiton = Position(tradable=knockout_option, quantity=1.0)
# portfolio.add(posiiton)

bond_fr = BondFixedRate(bond_symbol="111111",
                        coupon=0.04,
                        curve_code="CBD100252",
                        issue_date=TuringDate(2015, 11, 13),
                        due_date=TuringDate(2025, 11, 14),
                        bond_term_year=10,
                        freq_type=FrequencyType.SEMI_ANNUAL,
                        accrual_type=DayCountType.ACT_365L,
                        par=100)
posiiton = Position(tradable=bond_fr, quantity=1.0)
portfolio.add(posiiton)
print(bond_fr.full_price())
if __name__ == '__main__':
    with scenario_extreme:
        portfolio.calc(
            [
                RiskMeasure.Price,

                RiskMeasure.Dv01,
                RiskMeasure.DollarDuration,
                RiskMeasure.DollarConvexity,

                RiskMeasure.EqDelta,
                RiskMeasure.EqGamma,
                RiskMeasure.EqVega,
                RiskMeasure.EqTheta,
                RiskMeasure.EqRho,
                RiskMeasure.EqRhoQ,

                RiskMeasure.FxDelta,
                RiskMeasure.FxVega,
                RiskMeasure.FxGamma,
                RiskMeasure.FxTheta,
                RiskMeasure.FxVanna,
                RiskMeasure.FxVolga
            ])

        portfolio.show_table()
