import time

from fundamental.pricing_context import PricingContext

from turing_models.utilities.turing_date import TuringDate
from turing_models.instruments.european_option import EuropeanOption
from turing_models.instruments.knockout_option import KnockOutOption
from turing_models.instruments.snowball_option import SnowballOption
from turing_models.instruments.asian_option import AsianOption
from turing_models.instruments.american_option import AmericanOption
from turing_models.instruments.common import RiskMeasure
from tool import print_result


dates = [0.083, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0, 10.5, 11.0, 11.5, 12.0, 12.5, 13.0, 13.5, 14.0, 14.5, 15.0, 15.5, 16.0, 16.5, 17.0, 17.5, 18.0, 18.5, 19.0, 19.5, 20.0, 20.5, 21.0, 21.5, 22.0, 22.5, 23.0, 23.5, 24.0, 24.5, 25.0, 25.5, 26.0, 26.5, 27.0, 27.5, 28.0, 28.5, 29.0, 29.5, 30.0, 30.5, 31.0, 31.5, 32.0, 32.5, 33.0, 33.5, 34.0, 34.5, 35.0, 35.5, 36.0, 36.5, 37.0, 37.5, 38.0, 38.5, 39.0, 39.5, 40.0, 40.5, 41.0, 41.5, 42.0, 42.5, 43.0, 43.5, 44.0, 44.5, 45.0, 45.5, 46.0, 46.5, 47.0, 47.5, 48.0, 48.5, 49.0, 49.5, 50.0]
rates = [0.01935, 0.019773, 0.021824, 0.023816, 0.024863, 0.025819, 0.026775000000000004, 0.027221000000000002, 0.027667, 0.028093, 0.02852, 0.028952, 0.029384999999999998, 0.029767000000000002, 0.030149, 0.030538, 0.030926, 0.030935, 0.030945, 0.030957, 0.030969000000000003, 0.030983, 0.030997, 0.03143, 0.031863, 0.032303, 0.032743, 0.03319, 0.033638, 0.034094, 0.034551, 0.035017, 0.035484, 0.035531, 0.035577, 0.035628, 0.035678, 0.035732, 0.035786, 0.035842, 0.035899, 0.035959, 0.036018, 0.036101999999999995, 0.036185, 0.036271, 0.036357, 0.036446, 0.036534, 0.036626, 0.036717, 0.036810999999999997, 0.036906, 0.037002, 0.037099, 0.037199, 0.037299, 0.037401, 0.037504, 0.037609, 0.037715, 0.037823, 0.037932, 0.03796, 0.037988, 0.038018, 0.038048, 0.038079999999999996, 0.038111, 0.038145, 0.038179, 0.038214, 0.038249, 0.038286, 0.038323, 0.038362, 0.038401, 0.038441, 0.038481999999999995, 0.038523999999999996, 0.038565999999999996, 0.038610000000000005, 0.038654, 0.038699, 0.038743, 0.038789, 0.038835, 0.038883, 0.038931, 0.038981, 0.039030999999999996, 0.039083, 0.039134, 0.039188, 0.039242, 0.039297, 0.039353, 0.039411, 0.039469, 0.039529, 0.039588, 0.039651, 0.039713]

european_option = EuropeanOption(underlier="STOCKCN00000007",
                                 option_type='CALL',
                                 expiry=TuringDate(2021, 9, 3),
                                 strike_price=5.3,
                                 number_of_options=2,
                                 multiplier=100,
                                 value_date=TuringDate(2021, 2, 3),
                                 stock_price=5.262,
                                 volatility=0.1,
                                 zero_dates=dates,
                                 zero_rates=rates,
                                 dividend_yield=0)

american_option = AmericanOption(option_type='CALL',
                                 expiry=TuringDate(2021, 9, 3),
                                 strike_price=5.3,
                                 number_of_options=2,
                                 multiplier=100,
                                 value_date=TuringDate(2021, 2, 3),
                                 stock_price=5.262,
                                 volatility=0.1,
                                 zero_dates=dates,
                                 zero_rates=rates,
                                 dividend_yield=0)

asian_option = AsianOption(option_type='CALL',
                           expiry=TuringDate(2021, 9, 3),
                           start_averaging_date=TuringDate(2021, 2, 15),
                           strike_price=5.3,
                           number_of_options=2,
                           value_date=TuringDate(2021, 2, 3),
                           multiplier=100,
                           stock_price=5.262,
                           volatility=0.1,
                           zero_dates=dates,
                           zero_rates=rates,
                           dividend_yield=0)

snowball_option = SnowballOption(option_type='CALL',
                                 expiry=TuringDate(2021, 9, 3),
                                 participation_rate=1.0,
                                 barrier=5.5,
                                 knock_in_price=5.2,
                                 notional=1000000,
                                 rebate=0.2,
                                 knock_in_type='spreads',
                                 knock_in_strike1=5.3,
                                 knock_in_strike2=5.4,
                                 value_date=TuringDate(2021, 2, 3),
                                 stock_price=5.262,
                                 volatility=0.1,
                                 zero_dates=dates,
                                 zero_rates=rates,
                                 dividend_yield=0)

knockout_option = KnockOutOption(option_type='CALL',
                                 knock_out_type='up_and_out',
                                 expiry=TuringDate(2021, 9, 3),
                                 strike_price=5.3,
                                 participation_rate=1.0,
                                 barrier=5.5,
                                 notional=1000000,
                                 rebate=0.2,
                                 value_date=TuringDate(2021, 7, 6),
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
# print(european_option.price())
# scenario_extreme = PricingContext(spot=[
#                                       {"asset_id": "STOCKCN00000007", "value": 5},
#                                       {"asset_id": "STOCKCN00000002", "value": 5.3}
#                                   ]
#                                   )
#
# with scenario_extreme:
#     print(european_option.price())