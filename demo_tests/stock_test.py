from fundamental.pricing_context import PricingContext

from turing_models.instrument.stock import Stock
from turing_models.instrument.common import RiskMeasure

stock = Stock(asset_id="STOCKCN00000007",
              stock_price=5.23)

print(stock.calc(RiskMeasure.Delta))
print(stock.calc(RiskMeasure.Price))


scenario_extreme = PricingContext(spot=[
                                      {"asset_id": "STOCKCN00000007", "value": 3.5},
                                      {"asset_id": "STOCKCN00000002", "value": 5.3}
                                  ]
                                  )

with scenario_extreme:
    print(stock.price())
    print(stock.delta())
