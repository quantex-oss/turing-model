from fundamental.pricing_context import PricingContext

from turing_models.instruments.stock import Stock
from turing_models.instruments.common import RiskMeasure, Currency

stock = Stock(asset_id="STOCKCN00000007",
              currency=Currency.CNY,
              stock_price=5.23)

print(stock.calc(RiskMeasure.EqDelta))
print(stock.calc(RiskMeasure.Price))


scenario_extreme = PricingContext(spot=[
    {"asset_id": "STOCKCN00000007", "value": 3.5},
    {"asset_id": "STOCKCN00000002", "value": 5.3}
]
)

with scenario_extreme:
    print(stock.price())
    print(stock.eq_delta())
