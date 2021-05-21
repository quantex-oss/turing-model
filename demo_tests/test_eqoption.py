from tool import print_result
from fundamental import PricingContext
from turing_models.utilities.global_types import TuringOptionTypes, TuringKnockInTypes
from turing_models.instrument.eq_option import EqOption
from turing_models.utilities.turing_date import TuringDate


european_option = EqOption(option_type=TuringOptionTypes.EUROPEAN_CALL,
                           expiration_date=TuringDate(12, 2, 2021),
                           strike_price=90,
                           value_date=TuringDate(12, 2, 2020),
                           stock_price=100,
                           volatility=0.1,
                           interest_rate=0.02,
                           dividend_yield=0)

american_option = EqOption(option_type=TuringOptionTypes.AMERICAN_CALL,
                           expiration_date=TuringDate(12, 2, 2021),
                           strike_price=90,
                           value_date=TuringDate(12, 2, 2020),
                           stock_price=100,
                           volatility=0.1,
                           interest_rate=0.02,
                           dividend_yield=0)

asian_option = EqOption(option_type=TuringOptionTypes.ASIAN_CALL,
                        expiration_date=TuringDate(12, 2, 2021),
                        start_averaging_date=TuringDate(15, 2, 2020),
                        strike_price=90,
                        value_date=TuringDate(12, 2, 2020),
                        stock_price=100,
                        volatility=0.1,
                        interest_rate=0.02,
                        dividend_yield=0,
                        accrued_average=None)

snowball_option = EqOption(option_type=TuringOptionTypes.SNOWBALL_CALL,
                           expiration_date=TuringDate(12, 2, 2021),
                           knock_out_price=120,
                           knock_in_price=90,
                           notional=1000000,
                           coupon_rate=0.2,
                           knock_in_type=TuringKnockInTypes.RETURN,
                           value_date=TuringDate(12, 2, 2020),
                           stock_price=100,
                           volatility=0.1,
                           interest_rate=0.02,
                           dividend_yield=0)


print_result(european_option)
print_result(american_option)
print_result(asian_option)
print_result(snowball_option)


with PricingContext(interest_rate=0.04):
    print_result(european_option)
    print_result(american_option)
    print_result(asian_option)
    print_result(snowball_option)


with PricingContext(interest_rate=0.04):
    print_result(european_option)
    print_result(american_option)
    print_result(asian_option)
    print_result(snowball_option)


with PricingContext(interest_rate=0.06):
    print_result(european_option)
    print_result(american_option)
    print_result(asian_option)
    print_result(snowball_option)
