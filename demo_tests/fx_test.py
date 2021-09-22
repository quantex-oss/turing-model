from enum import Enum

from fundamental.pricing_context import PricingContext
from turing_models.instruments.fx.fx import ForeignExchange


fx = ForeignExchange(
                     asset_id='FX00000001',
                     exchange_rate=6,
                     symbol='USD/CNY'
)

print(fx.price())
print(fx.fx_delta())

scenario_extreme = PricingContext(spot=[
    {"symbol": "USD/CNY", "value": 5.3},
    # {"asset_id": "FX00000001", "value": 5.3}
]
)

with scenario_extreme:
    print(fx.price())
    print(fx.fx_delta())


