from turing_models.utilities.turing_date import TuringDate
from turing_models.var.fi_portfolio_var import FIPortfolioVaR
from fundamental.pricing_context import PricingContext
from fundamental.portfolio.portfolio import Portfolio
from turing_models.instruments.common import RiskMeasure

effective_date = TuringDate(2021, 11, 1)
period_interval = 20
formula = 'Historical Simulation'
confidence_interval = 0.95
target_portfolio = "Rates"

var = FIPortfolioVaR(value_date=effective_date,
                      period_interval=period_interval, 
                      target_portfolio=target_portfolio)
print(var.VaR())

portfolio = Portfolio(portfolio_name=target_portfolio, pricing_date=effective_date)
scenario_extreme = PricingContext(pricing_date=effective_date)
with scenario_extreme:
    portfolio.calc(RiskMeasure.FullPrice)

for l in portfolio._position_sets.positions:
  print(l.tradable.name, l.tradable.curve_code, l.tradable.modified_duration())
