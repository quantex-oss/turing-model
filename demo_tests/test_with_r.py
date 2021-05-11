import datetime

from fundamental import PricingContext
from turing_models.instrument.common import OptionType, OptionStyle
from turing_models.instrument.eq_option import EqOption

# --------------------------------------------------------------------------
# Section 1: Pricing
# --------------------------------------------------------------------------

option = EqOption(option_type=OptionType.Call,
                  option_style=OptionStyle.European,
                  number_of_options=100,
                  expiration_date=datetime.date(2021, 7, 25),
                  strike_price=500.0,
                  value_date=datetime.date(2021, 4, 25),
                  stock_price=510.0,
                  volatility=0.02,
                  interest_rate=0.03,
                  dividend_yield=0)

print(option.price())
print(option.delta())
print(option.gamma())
print(option.vega())
print(option.price())
print(option.rho())

print("-" * 100)

with PricingContext(r=0.04):
    print(option.price())
    print(option.delta())
    print(option.gamma())
    print(option.vega())
    print(option.price())
    print(option.rho())

print("-" * 100)

with PricingContext(r=0.06):
    print(option.price())
    print(option.delta())
    print(option.gamma())
    print(option.vega())
    print(option.price())
    print(option.rho())
