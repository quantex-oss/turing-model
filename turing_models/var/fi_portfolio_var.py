import sys
from dataclasses import dataclass
import numpy as np

from fundamental.pricing_context import CurveScenario
from fundamental.pricing_context import PricingContext
from fundamental.turing_db.data import TuringDB
from fundamental.portfolio.portfolio import Portfolio
from loguru import logger

from turing_models.instruments.common import (CurrencyPair, RiskMeasure,
                                              YieldCurveCode)
from turing_models.instruments.credit.bond_fixed_rate import BondFixedRate
from turing_models.market.curves.curve_generation import FXIRCurve
from turing_models.market.data.china_money_yield_curve import dates, rates
from turing_models.market.volatility.vol_surface_generation import \
    FXOptionImpliedVolatilitySurface
from turing_models.utilities.day_count import TuringDayCountTypes
from turing_models.utilities.frequency import TuringFrequencyTypes
from turing_models.utilities.turing_date import TuringDate
from turing_models.utilities.schedule import TuringSchedule
from turing_models.utilities.turing_date import TuringDate
from turing_models.utilities.frequency import TuringFrequencyTypes
from turing_models.utilities.calendar import TuringCalendarTypes


@dataclass(repr=False, eq=False, order=False, unsafe_hash=True)
class FIPortfolioVaR():
    value_date: TuringDate = None 
    period_interval: int = 100
    effective_date: TuringDate =None
    formula: str = 'Historical Simulation'
    target_portfolio : str = None
    confidence_interval: float = 0.95
    freq_type: TuringFrequencyTypes = TuringFrequencyTypes.DAILY
    calendar_type: TuringCalendarTypes = TuringCalendarTypes.CHINA_IB
    
    def __post_init__(self):
        if self.effective_date is None:
            self.effective_date = self.value_date.addDays(-self.period_interval-1)
        self.termination_date = self.effective_date.addDays(self.period_interval)
        self.schedule = TuringSchedule(self.effective_date,
                                  self.termination_date,
                                  self.freq_type,
                                  self.calendar_type)
    def portfolio_returns(self):
        portfolio_value = []
        portfolio = Portfolio(portfolio_name=self.target_portfolio, pricing_date=self.value_date)
        for date in self.schedule.scheduleDates():
            scenario_extreme = PricingContext(pricing_date=date)
            # curves = TuringDB.bond_yield_curve(curve_code=curve_lists, date=date)
            with scenario_extreme:
                # print(portfolio.pricing_date)
                # print([bond.tradable.settlement_date_ for bond in portfolio._position_sets.positions])
                portfolio_value.append(portfolio.calc(RiskMeasure.FullPrice))

        returns = [(portfolio_value[i] - portfolio_value[i - 1])/portfolio_value[i - 1] for i in range(1, len(portfolio_value))]
        return returns

    def VaR(self):
        p0 = Portfolio(portfolio_name=self.target_portfolio, pricing_date=self.value_date)
        scenario_extreme = PricingContext(pricing_date=self.value_date)
        with scenario_extreme:
            v0 = p0.calc(RiskMeasure.FullPrice)
        if self.formula == 'Historical Simulation':    
            Value_at_Risk = -np.percentile(self.portfolio_returns(), 1-self.confidence_interval) * v0

        return(Value_at_Risk)