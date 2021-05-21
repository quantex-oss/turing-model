from tunny import set_switch

from fundamental import PricingContext
from turing_models.instrument.eq_option import EqOption
from turing_models.products.equity import TuringOptionTypes
from turing_models.utilities.turing_date import TuringDate

set_switch(1)
# --------------------------------------------------------------------------
# Section 1: Pricing
# --------------------------------------------------------------------------


option = EqOption(option_type=TuringOptionTypes.EUROPEAN_CALL,
                  number_of_options=100,
                  expiration_date=TuringDate(25, 7, 2021),
                  strike_price=500.0,
                  start_averaging_date=TuringDate(25, 4, 2021),
                  value_date=TuringDate(25, 4, 2021),
                  stock_price=510.0,
                  volatility=0.02,
                  interest_rate=0.03,
                  dividend_yield=0.01111)

print(option.price())
print(option.delta())
print(option.gamma())
print(option.vega())
print(option.theta())
print(option.rho())

print("-" * 100)

with PricingContext(interest_rate=0.04):
    print(option.price())
    print(option.delta())
    print(option.gamma())
    print(option.vega())
    print(option.theta())
    print(option.rho())

print("-" * 100)

with PricingContext(interest_rate=0.04):
    print(option.price())
    print(option.delta())
    print(option.gamma())
    print(option.vega())
    print(option.theta())
    print(option.rho())

print("-" * 100)

with PricingContext(interest_rate=0.06):
    print(option.price())
    print(option.delta())
    print(option.gamma())
    print(option.vega())
    print(option.theta())
    print(option.rho())
