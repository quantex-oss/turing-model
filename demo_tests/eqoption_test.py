import time

from fundamental.pricing_context import PricingContext

from turing_models.utilities.turing_date import TuringDate
from turing_models.utilities.global_types import TuringOptionTypes, TuringKnockOutTypes, TuringKnockInTypes
from turing_models.instruments.european_option import EuropeanOption
from turing_models.instruments.knockout_option import KnockOutOption
from turing_models.instruments.snowball_option import SnowballOption
from turing_models.instruments.asian_option import AsianOption
from turing_models.instruments.american_option import AmericanOption
from turing_models.instruments.common import RiskMeasure
from tool import print_result, dates, rates


european_option = EuropeanOption(asset_id="OPTIONCN00000001",
                                 underlier="STOCKCN00000001",
                                 option_type=TuringOptionTypes.EUROPEAN_CALL,
                                 number_of_options=2,
                                 expiry=TuringDate(2021, 9, 15),
                                 strike_price=5.3,
                                 multiplier=100,
                                 stock_price=5.262,
                                 volatility=0.1,
                                 zero_dates=dates,
                                 zero_rates=rates,
                                 dividend_yield=0)

american_option = AmericanOption(asset_id="OPTIONCN00000002",
                                 underlier="STOCKCN00000001",
                                 option_type=TuringOptionTypes.AMERICAN_CALL,
                                 expiry=TuringDate(2021, 9, 15),
                                 strike_price=5.3,
                                 number_of_options=2,
                                 multiplier=100,
                                 stock_price=5.262,
                                 volatility=0.1,
                                 zero_dates=dates,
                                 zero_rates=rates,
                                 dividend_yield=0)

asian_option = AsianOption(asset_id="OPTIONCN00000003",
                           underlier="STOCKCN00000001",
                           option_type=TuringOptionTypes.ASIAN_CALL,
                           expiry=TuringDate(2021, 9, 15),
                           start_averaging_date=TuringDate(2021, 8, 15),
                           strike_price=5.3,
                           number_of_options=2,
                           multiplier=100,
                           stock_price=5.262,
                           volatility=0.1,
                           zero_dates=dates,
                           zero_rates=rates,
                           dividend_yield=0)

snowball_option = SnowballOption(asset_id="OPTIONCN00000004",
                                 underlier="STOCKCN00000001",
                                 option_type=TuringOptionTypes.SNOWBALL_CALL,
                                 expiry=TuringDate(2021, 9, 15),
                                 participation_rate=1.0,
                                 barrier=5.5,
                                 knock_in_price=5.2,
                                 notional=1000000,
                                 rebate=0.2,
                                 knock_in_type=TuringKnockInTypes.SPREADS,
                                 knock_in_strike1=5.3,
                                 knock_in_strike2=5.4,
                                 stock_price=5.262,
                                 volatility=0.1,
                                 zero_dates=dates,
                                 zero_rates=rates,
                                 dividend_yield=0)

knockout_option = KnockOutOption(asset_id="OPTIONCN00000005",
                                 underlier="STOCKCN00000001",
                                 option_type=TuringOptionTypes.KNOCKOUT,
                                 knock_out_type=TuringKnockOutTypes.UP_AND_OUT_CALL,
                                 expiry=TuringDate(2021, 9, 15),
                                 strike_price=5.3,
                                 participation_rate=1.0,
                                 barrier=5.5,
                                 notional=1000000,
                                 rebate=0.2,
                                 stock_price=5.262,
                                 volatility=0.1,
                                 zero_dates=dates,
                                 zero_rates=rates,
                                 dividend_yield=0)

# time_start = time.time()
# print(round(american_option.calc(RiskMeasure.EqRhoQ), 3))
print_result(european_option)
print_result(american_option)
print_result(asian_option)
print_result(snowball_option)
print_result(knockout_option)
# time_end = time.time()
# print('耗时：', time_end - time_start)
