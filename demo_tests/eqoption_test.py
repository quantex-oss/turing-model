from turing_models.utilities.turing_date import TuringDate
from tool import print_result
from fundamental.pricing_context import PricingContext
from turing_models.instrument.eq_option import EqOption


european_option = EqOption(option_type='CALL',
                           product_type='EUROPEAN',
                           expiration_date=TuringDate(2021, 9, 3),
                           strike_price=5.3,
                           quantity_of_underlier=2,
                           multiplier=10000,
                           value_date=TuringDate(2021, 6, 4),
                           stock_price=5.262,
                           volatility=0.1,
                           interest_rate=0.02,
                           dividend_yield=0)


american_option = EqOption(option_type='CALL',
                           product_type='AMERICAN',
                           expiration_date=TuringDate(2021, 2, 12),
                           strike_price=90,
                           quantity_of_underlier=2,
                           multiplier=10000,
                           value_date = TuringDate(2020, 2, 12),
                           stock_price=100,
                           volatility=0.1,
                           interest_rate=0.02,
                           dividend_yield=0)

asian_option = EqOption(option_type='CALL',
                        product_type='ASIAN',
                        expiration_date=TuringDate(2021, 2, 12),
                        start_averaging_date=TuringDate(2020, 2, 15),
                        strike_price=90,
                        quantity_of_underlier=2,
                        value_date = TuringDate(2020, 2, 12),
                        multiplier=10000,
                        stock_price=100,
                        volatility=0.1,
                        interest_rate=0.02,
                        dividend_yield=0)

snowball_option = EqOption(option_type='CALL',
                           product_type='SNOWBALL',
                           expiration_date=TuringDate(2021, 2, 12),
                           participation_rate=1.0,
                           barrier=120,
                           knock_in_price=90,
                           notional=1000000,
                           rebate=0.2,
                           coupon_annualized_flag=True,
                           knock_in_type='Return',
                           value_date=TuringDate(2020, 2, 12),
                           multiplier=10000,
                           stock_price=100,
                           volatility=0.1,
                           interest_rate=0.02,
                           dividend_yield=0)
#
knockout_option = EqOption(option_type='CALL',
                           product_type='KNOCK_OUT',
                           knock_out_type='up_and_out',
                           expiration_date=TuringDate(2021, 2, 12),
                           strike_price=90,
                           participation_rate=1.0,
                           barrier=120,
                           notional=1000000,
                           rebate=0.2,
                           coupon_annualized_flag=True,
                           value_date=TuringDate(2020, 2, 12),
                           multiplier=10000,
                           stock_price=100,
                           volatility=0.1,
                           interest_rate=0.02,
                           dividend_yield=0)


print_result(european_option)
print_result(american_option)
print_result(asian_option)
print_result(snowball_option)
print_result(knockout_option)


with PricingContext(interest_rate=0.04):
    print_result(european_option)
    print_result(american_option)
    print_result(asian_option)
    print_result(snowball_option)
    print_result(knockout_option)
#
#
# with PricingContext(interest_rate=0.04):
#     print_result(european_option)
#     print_result(american_option)
#     print_result(asian_option)
#     print_result(snowball_option)
#     print_result(knockout_option)
#
#
# with PricingContext(interest_rate=0.06):
#     print_result(european_option)
#     print_result(american_option)
#     print_result(asian_option)
#     print_result(snowball_option)
#     print_result(knockout_option)

# start_date = TuringDate.fromString('20180101')
# print(start_date)