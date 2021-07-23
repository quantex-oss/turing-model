from fundamental.market.constants import dates, rates

from tool import print_result
from turing_models.utilities.turing_date import TuringDate
from turing_models.instruments.knockout_option import KnockOutOption
from turing_models.utilities.global_types import TuringKnockOutTypes



# european_option = EuropeanOption(underlier="STOCKCN00000007",
#                                  option_type='CALL',
#                                  expiry=TuringDate(2021, 9, 3),
#                                  strike_price=5.3,
#                                  number_of_options=2,
#                                  multiplier=100,
#                                  value_date=TuringDate(2021, 2, 3),
#                                  stock_price=5.262,
#                                  volatility=0.1,
#                                  zero_dates=dates,
#                                  zero_rates=rates,
#                                  dividend_yield=0)
#
# american_option = AmericanOption(option_type='CALL',
#                                  expiry=TuringDate(2021, 9, 3),
#                                  strike_price=5.3,
#                                  number_of_options=2,
#                                  multiplier=100,
#                                  value_date=TuringDate(2021, 2, 3),
#                                  stock_price=5.262,
#                                  volatility=0.1,
#                                  zero_dates=dates,
#                                  zero_rates=rates,
#                                  dividend_yield=0)
#
# asian_option = AsianOption(option_type='CALL',
#                            expiry=TuringDate(2021, 9, 3),
#                            start_averaging_date=TuringDate(2021, 2, 15),
#                            strike_price=5.3,
#                            number_of_options=2,
#                            value_date=TuringDate(2021, 2, 3),
#                            multiplier=100,
#                            stock_price=5.262,
#                            volatility=0.1,
#                            zero_dates=dates,
#                            zero_rates=rates,
#                            dividend_yield=0)
#
# snowball_option = SnowballOption(option_type='CALL',
#                                  expiry=TuringDate(2021, 9, 3),
#                                  participation_rate=1.0,
#                                  barrier=5.5,
#                                  knock_in_price=5.2,
#                                  notional=1000000,
#                                  rebate=0.2,
#                                  knock_in_type='spreads',
#                                  knock_in_strike1=5.3,
#                                  knock_in_strike2=5.4,
#                                  value_date=TuringDate(2021, 2, 3),
#                                  stock_price=5.262,
#                                  volatility=0.1,
#                                  zero_dates=dates,
#                                  zero_rates=rates,
#                                  dividend_yield=0)

# knockout_option = KnockOutOption(asset_id='OPTIONCN00000001',
#                                  underlier='STOCKCN00000001',
#                                  knock_out_type=TuringKnockOutTypes.UP_AND_OUT_CALL,
#                                  expiry=TuringDate(2021, 9, 3),
#                                  strike_price=5.3,
#                                  participation_rate=1.0,
#                                  barrier=5.5,
#                                  notional=1000000,
#                                  rebate=0.2,
#                                  value_date=TuringDate(2021, 7, 6),
#                                  stock_price=5.262,
#                                  volatility=0.1,
#                                  zero_dates=dates,
#                                  zero_rates=rates,
#                                  dividend_yield=0)
knockout_option = KnockOutOption(asset_id="OPTIONCN00000002",
                                 underlier="STOCKCN00000002",
                                 knock_out_type=TuringKnockOutTypes.UP_AND_OUT_CALL,
                                 expiry=TuringDate(2021, 9, 3),
                                 strike_price=11.3,
                                 participation_rate=1.0,
                                 barrier=13,
                                 notional=1000000,
                                 rebate=0.2,
                                 value_date=TuringDate(2021, 7, 6),
                                 volatility=0.1,
                                 zero_dates=dates,
                                 zero_rates=rates,
                                 dividend_yield=0)
knockout_option.resolve()
# time_start = time.time()
# print(round(american_option.calc(RiskMeasure.EqRhoQ), 3))
# print_result(european_option)
# print_result(american_option)
# print_result(asian_option)
# print_result(snowball_option)
# print(knockout_option)
print_result(knockout_option)
# knockout_option.resolve("1")
# time_end = time.time()
# print('耗时：', time_end - time_start)
# print(european_option.price())
# scenario_extreme = PricingContext(spot=[
#                                       {"asset_id": "STOCKCN00000007", "value": 5},
#                                       {"asset_id": "STOCKCN00000002", "value": 5.3}
#                                   ]
#                                   )
#
# with scenario_extreme:
#     print(european_option.price())
