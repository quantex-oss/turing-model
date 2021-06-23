from turing_models.utilities.turing_date import TuringDate
from turing_models.instrument.european_option import EuropeanOption
from tool import print_result
from fundamental.pricing_context import PricingContext
# from turing_models.instrument.eq_option import EqOption
#
#
european_option = EuropeanOption(option_type='CALL',
                                 underlier='0',
                                 expiration_date=TuringDate(2021, 9, 3),
                                 strike_price=5.3,
                                 number_of_options=2,
                                 multiplier=100,
                                 value_date=TuringDate(2021, 2, 3),
                                 stock_price=5.262,
                                 volatility=0.1,
                                 interest_rate=0.02,
                                 dividend_yield=0)
#
#
# american_option = EqOption(option_type='CALL',
#                            product_type='AMERICAN',
#                            expiration_date=TuringDate(2021, 9, 3),
#                            strike_price=5.3,
#                            number_of_options=2,
#                            multiplier=100,
#                            value_date=TuringDate(2021, 2, 3),
#                            stock_price=5.262,
#                            volatility=0.1,
#                            interest_rate=0.02,
#                            dividend_yield=0)
#
# asian_option = EqOption(option_type='CALL',
#                         product_type='ASIAN',
#                         expiration_date=TuringDate(2021, 9, 3),
#                         start_averaging_date=TuringDate(2021, 2, 15),
#                         strike_price=5.3,
#                         number_of_options=2,
#                         value_date=TuringDate(2021, 2, 3),
#                         multiplier=100,
#                         stock_price=5.262,
#                         volatility=0.1,
#                         interest_rate=0.02,
#                         dividend_yield=0)
#
# snowball_option = EqOption(option_type='CALL',
#                            product_type='SNOWBALL',
#                            expiration_date=TuringDate(2021, 9, 3),
#                            participation_rate=1.0,
#                            barrier=5.5,
#                            knock_in_price=5.2,
#                            notional=1000000,
#                            rebate=0.2,
#                            knock_in_type='Return',
#                            value_date=TuringDate(2021, 2, 3),
#                            multiplier=100,
#                            stock_price=5.262,
#                            volatility=0.1,
#                            interest_rate=0.02,
#                            dividend_yield=0)
#
# knockout_option = EqOption(option_type='CALL',
#                            product_type='KNOCK_OUT',
#                            knock_out_type='up_and_out',
#                            expiration_date=TuringDate(2021, 9, 3),
#                            strike_price=5.3,
#                            participation_rate=1.0,
#                            barrier=5.5,
#                            notional=1000000,
#                            rebate=0.2,
#                            value_date=TuringDate(2021, 2, 3),
#                            multiplier=100,
#                            stock_price=5.262,
#                            volatility=0.1,
#                            interest_rate=0.02,
#                            dividend_yield=0)
#
#
print_result(european_option)
# print_result(american_option)
# print_result(asian_option)
# print_result(snowball_option)
# print_result(knockout_option)
#
#
with PricingContext(interest_rate=0.04):
    print_result(european_option)
#     print_result(american_option)
#     print_result(asian_option)
#     print_result(snowball_option)
#     print_result(knockout_option)
#
#
with PricingContext(interest_rate=0.04):
    print_result(european_option)
#     print_result(american_option)
#     print_result(asian_option)
#     print_result(snowball_option)
#     print_result(knockout_option)
#
#
with PricingContext(interest_rate=0.06):
    print_result(european_option)
#     print_result(american_option)
#     print_result(asian_option)
#     print_result(snowball_option)
#     print_result(knockout_option)
#
