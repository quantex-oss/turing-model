from enum import Enum

from fundamental.pricing_context import PricingContext
from turing_models.instruments.fx import ForeignExchange


fx = ForeignExchange(
                     asset_id='FX00000001',
                     exchange_rate=6,
                     # symbol='USD/CNY'
)

print(fx.price())
print(fx.fx_delta())

scenario_extreme = PricingContext(spot=[
    # {"symbol": "600059.SH", "value": 3.5},
    {"symbol": "USD/CNY", "value": 5.3}
]
)

with scenario_extreme:
    print(fx.price())
    print(fx.fx_delta())


