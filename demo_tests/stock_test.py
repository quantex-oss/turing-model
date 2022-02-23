from fundamental.pricing_context import PricingContext

from turing_models.instruments.eq.stock import Stock
from turing_models.instruments.common import RiskMeasure, Currency

stock = Stock(asset_id="STOCKCN00000011",
              comb_symbol="600059.SH")

print(stock.calc(RiskMeasure.EqDelta))
print(stock.calc(RiskMeasure.Price))


scenario_extreme = PricingContext(spot=[
    {"symbol": "600059.SH", "value": 5.3}
]
)

with scenario_extreme:
    print(stock.calc(RiskMeasure.Price))
    print(stock.calc(RiskMeasure.EqDelta))
