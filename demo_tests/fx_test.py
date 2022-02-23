from fundamental.pricing_context import PricingContext
from turing_models.instruments.common import RiskMeasure
from turing_models.instruments.fx.fx import ForeignExchange


fx = ForeignExchange(
                     asset_id='FX00000001',
                     comb_symbol='USD/CNY'
)

print(fx.calc(RiskMeasure.Price))
print(fx.calc(RiskMeasure.FxDelta))

scenario_extreme = PricingContext(spot=[
    {"symbol": "USD/CNY", "value": 5.3}
]
)

with scenario_extreme:
    print(fx.calc(RiskMeasure.Price))
    print(fx.calc(RiskMeasure.FxDelta))


