from turing_models.utilities.turing_date import TuringDate
from tool import print_result
from fundamental import PricingContext
from turing_models.instrument.eq_option import EqOption


european_option = EqOption(option_type='call',
                           product_type='European',
                           expiration_date=TuringDate(3, 9, 2021),
                           strike_price=5.3,
                           multiplier=10000,
                           value_date=TuringDate(4, 6, 2021),
                           stock_price=5.262,
                           volatility=0.1,
                           interest_rate=0.02,
                           dividend_yield=0)


# american_option = EqOption(option_type='call',
#                            product_type='American',
#                            expiration_date=TuringDate(12, 2, 2021),
#                            strike_price=90,
#                            multiplier=10000,
#                            value_date = TuringDate(12, 2, 2020),
#                            stock_price=100,
#                            volatility=0.1,
#                            interest_rate=0.02,
#                            dividend_yield=0)

# asian_option = EqOption(option_type='call',
#                         product_type='Asian',
#                         expiration_date=TuringDate(12, 2, 2021),
#                         start_averaging_date=TuringDate(15, 2, 2020),
#                         strike_price=90,
#                         value_date = TuringDate(12, 2, 2020),
#                         multiplier=10000,
#                         stock_price=100,
#                         volatility=0.1,
#                         interest_rate=0.02,
#                         dividend_yield=0)
#
# snowball_option = EqOption(option_type='call',
#                            product_type='Snowball',
#                            expiration_date=TuringDate(12, 2, 2021),
#                            participation_rate=1.0,
#                            knock_out_price=120,
#                            knock_in_price=90,
#                            notional=1000000,
#                            coupon_rate=0.2,
#                            coupon_annualized_flag=True,
#                            knock_in_type='Return',
#                            value_date=TuringDate(12, 2, 2020),
#                            multiplier=10000,
#                            stock_price=100,
#                            volatility=0.1,
#                            interest_rate=0.02,
#                            dividend_yield=0)
#
# knockout_option = EqOption(option_type='call',
#                            product_type='Knockout',
#                            knock_out_type='up_and_out',
#                            expiration_date=TuringDate(12, 2, 2021),
#                            strike_price=90,
#                            participation_rate=1.0,
#                            knock_out_price=120,
#                            notional=1000000,
#                            coupon_rate=0.2,
#                            coupon_annualized_flag=True,
#                            value_date=TuringDate(12, 2, 2020),
#                            multiplier=10000,
#                            stock_price=100,
#                            volatility=0.1,
#                            interest_rate=0.02,
#                            dividend_yield=0)


print_result(european_option)
# print_result(american_option)
# print_result(asian_option)
# print_result(snowball_option)
# print_result(knockout_option)
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
