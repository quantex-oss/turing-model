from tool import print_result
from fundamental import PricingContext
from turing_models.utilities.global_types import TuringOptionTypes
from turing_models.instrument.eq_option import EqOption
from turing_models.utilities.turing_date import TuringDate


option = EqOption(option_type=TuringOptionTypes.EUROPEAN_CALL,
                  expiration_date=TuringDate(12, 2, 2021),
                  strike_price=90,
                  value_date=TuringDate(12, 2, 2020),
                  stock_price=100,
                  volatility=0.1,
                  interest_rate=0.02,
                  dividend_yield=0)


print_result(option)


with PricingContext(interest_rate=0.04):
    print_result(option)


with PricingContext(interest_rate=0.04):
    print_result(option)


with PricingContext(interest_rate=0.06):
    print_result(option)
