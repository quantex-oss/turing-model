import datetime

import numpy as np

from fundamental.pricing_context import PricingContext
from turing_models.utilities.print import print_result
from turing_models.instruments.eq.european_option import EuropeanOption
from turing_models.instruments.eq.american_option import AmericanOption
from turing_models.instruments.eq.asian_option import AsianOption
from turing_models.instruments.eq.snowball_option import SnowballOption
from turing_models.instruments.eq.knockout_option import KnockOutOption
from turing_models.instruments.eq.basket_snowball_option import BasketSnowballOption
from turing_models.utilities.global_types import OptionType
from turing_models.instruments.common import Currency, RiskMeasure
from turing_models.utilities.helper_functions import betaVectorToCorrMatrix


# 测试数据为mock的数据
european_option = EuropeanOption(underlier_symbol='600067.SH',
                                 option_type=OptionType.CALL,
                                 expiry=datetime.datetime(2021, 9, 3),
                                 start_date=datetime.datetime(2021, 6, 3),
                                 strike_price=4.19,
                                 number_of_options=2,
                                 multiplier=100,
                                 value_date=datetime.datetime(2021, 8, 13),
                                 currency=Currency.CNY)

american_option = AmericanOption(underlier_symbol='600067.SH',
                                 option_type=OptionType.CALL,
                                 expiry=datetime.datetime(2021, 9, 3),
                                 start_date=datetime.datetime(2021, 6, 3),
                                 strike_price=4.19,
                                 number_of_options=2,
                                 multiplier=100,
                                 value_date=datetime.datetime(2021, 8, 13),
                                 currency=Currency.CNY)

asian_option = AsianOption(underlier_symbol='600067.SH',
                           option_type=OptionType.CALL,
                           expiry=datetime.datetime(2021, 9, 3),
                           start_date=datetime.datetime(2021, 6, 3),
                           start_averaging_date=datetime.datetime(2021, 8, 15),
                           strike_price=4.19,
                           number_of_options=2,
                           value_date=datetime.datetime(2021, 8, 13),
                           currency=Currency.CNY,
                           multiplier=100)

snowball_option = SnowballOption(underlier_symbol='600067.SH',
                                 option_type=OptionType.CALL,
                                 start_date=datetime.datetime(2021, 6, 3),
                                 expiry=datetime.datetime(2022, 10, 3),
                                 participation_rate=1.0,
                                 barrier=4.25,
                                 knock_in_price=4.1,
                                 notional=1000000,
                                 rebate=0.2,
                                 initial_spot=4.2,
                                 untriggered_rebate=0.2,
                                 knock_in_type='SPREADS',
                                 knock_out_obs_days_whole=[datetime.datetime(2021, 6, 3), datetime.datetime(
                                     2021, 7, 5), datetime.datetime(2021, 8, 3), datetime.datetime(2021, 9, 3)],
                                 knock_in_strike1=4.23,
                                 knock_in_strike2=4.24,
                                 value_date=datetime.datetime(2021, 8, 13),
                                 currency=Currency.CNY)

knockout_option = KnockOutOption(underlier_symbol='600067.SH',
                                 option_type=OptionType.CALL,
                                 start_date=datetime.datetime(2021, 6, 3),
                                 expiry=datetime.datetime(2021, 9, 3),
                                 strike_price=4.19,
                                 participation_rate=1.0,
                                 barrier=5.5,
                                 notional=1000000,
                                 rebate=0.2,
                                 value_date=datetime.datetime(2021, 8, 13),
                                 currency=Currency.CNY)

print_result(european_option)
print_result(american_option)
print_result(asian_option)
print_result(snowball_option)
print_result(knockout_option)

scenario_extreme = PricingContext(
    pricing_date='2021-08-13T00:00:00.000+0800',
    spot=[{"symbol": "600067.SH", "value": 4.25}],
    volatility=[{"symbol": "600067.SH", "value": 0.1}],
    interest_rate=0.05,
    dividend_yield=[{"symbol": "600067.SH", "value": 0.04}]
)

with scenario_extreme:
    print_result(european_option)
    print_result(american_option)
    print_result(asian_option)
    print_result(snowball_option)
    print_result(knockout_option)

betas = np.ones(2) * 0.1
corr_matrix = betaVectorToCorrMatrix(betas)


basket_snowball_option = BasketSnowballOption(option_type=OptionType.CALL,
                                            start_date=datetime.datetime(
                                                2021, 6, 3),
                                            expiry=datetime.datetime(
                                                2021, 9, 3),
                                            initial_spot=100,
                                            participation_rate=1.0,
                                            barrier=110,
                                            knock_in_price=99,
                                            notional=1000000,
                                            rebate=0.2,
                                            untriggered_rebate=0.2,
                                            underlier_symbol=["600067.SH", "600243.SH"],
                                            knock_in_type='SPREADS',
                                            knock_in_strike1=5.3,
                                            knock_in_strike2=5.4,
                                            value_date=datetime.datetime(
                                                2021, 8, 13),
                                            currency=Currency.CNY,
                                            weights=[
                                                0.5, 0.5],
                                            correlation_matrix=corr_matrix)

scenario_extreme = PricingContext(
    pricing_date='2015-01-01T00:00:00.000+0800',
    spot=[{"symbol": "600277.SH", "value": 100},
        {"symbol": "600269.SH", "value": 100},
        {"symbol": "600201.SH", "value": 100},
        {"symbol": "600067.SH", "value": 100},
        {"symbol": "600243.SH", "value": 100}],
    volatility=[{"symbol": "600277.SH", "value": 0.3},
                {"symbol": "600269.SH", "value": 0.3},
                {"symbol": "600201.SH", "value": 0.3},
                {"symbol": "600067.SH", "value": 0.3},
                {"symbol": "600243.SH", "value": 0.3}],
    interest_rate=0.05,
    dividend_yield=[{"symbol": "600277.SH", "value": 0.01},
                    {"symbol": "600269.SH", "value": 0.01},
                    {"symbol": "600201.SH", "value": 0.01},
                    {"symbol": "600067.SH", "value": 0.01},
                    {"symbol": "600243.SH", "value": 0.01}]
)
print("price", basket_snowball_option.calc(RiskMeasure.Price))
with scenario_extreme:
    print("price", basket_snowball_option.calc(RiskMeasure.Price))
