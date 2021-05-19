import datetime

import sys
sys.path.append("..")
from fundamental import PricingContext
from turing_models.instrument.common import OptionType, OptionStyle
from turing_models.instrument.eq_option import EqOption

# --------------------------------------------------------------------------
# Section 1: Pricing
# --------------------------------------------------------------------------


option = EqOption(option_type=OptionType.Call,
                  option_style=OptionStyle.Snowball,
                  number_of_options=100,
                  expiration_date=datetime.date(2021, 2, 12),
                  knock_out_price=120,
                  knock_in_price=90,
                  notional=1000000,
                  coupon_rate=0.3,
                  value_date=datetime.date(2020, 2, 12),
                  stock_price=100,
                  volatility=0.1,
                  interest_rate=0.02,
                  dividend_yield=0)

print(option.price())
print(option.delta())
print(option.gamma())
print(option.vega())
print(option.theta())
print(option.rho())

print("-" * 100)

with PricingContext(r=0.04):
    print(option.price())
    print(option.delta())
    print(option.gamma())
    print(option.vega())
    print(option.theta())
    print(option.rho())

print("-" * 100)

with PricingContext(r=0.04):
    print(option.price())
    print(option.delta())
    print(option.gamma())
    print(option.vega())
    print(option.theta())
    print(option.rho())

print("-" * 100)

with PricingContext(r=0.06):
    print(option.price())
    print(option.delta())
    print(option.gamma())
    print(option.vega())
    print(option.theta())
    print(option.rho())
