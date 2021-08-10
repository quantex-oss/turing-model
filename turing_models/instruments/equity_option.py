import datetime
from dataclasses import dataclass, field
from typing import List, Any, Union

import numpy as np
from loguru import logger

from fundamental.market.curves import TuringDiscountCurveFlat, \
     TuringDiscountCurveZeros
from fundamental.turing_db.base.core import InstrumentBase
from fundamental.turing_db.utils import to_snake

from turing_models.instruments.common import greek, bump, Currency
from turing_models.utilities.turing_date import TuringDate
from turing_models.utilities.global_variables import gDaysInYear
from turing_models.utilities.global_types import TuringOptionType
from turing_models.models.model_black_scholes import TuringModelBlackScholes
from turing_models.instruments.core import Instrument
from turing_models.utilities.helper_functions import to_string
from turing_models.utilities.error import TuringError


@dataclass(repr=False, eq=False, order=False, unsafe_hash=True)
class EqOption(Instrument, InstrumentBase):

    asset_id: str = None
    underlier: Union[str, List[str]] = None
    product_type: str = None
    option_type: Union[str, TuringOptionType] = None
    notional: float = None
    initial_spot: float = None
    number_of_options: float = None
    start_date: TuringDate = None
    end_date: TuringDate = None
    expiry: TuringDate = None
    participation_rate: float = None
    strike_price: float = None
    multiplier: float = None
    currency: Union[str, Currency] = None
    premium: float = None
    premium_date: TuringDate = None
    annualized_flag: bool = True
    value_date: TuringDate = TuringDate(*(datetime.date.today().timetuple()[:3]))  # 估值日期
    stock_price: Union[float, List[float]] = None
    volatility: Union[float, List[float]] = 0
    interest_rate: float = 0
    zero_dates: List[Any] = field(default_factory=list)
    zero_rates: List[Any] = field(default_factory=list)
    dividend_yield: Union[float, List[float]] = 0
    __value_date = None
    __stock_price = None
    __volatility = None
    __discount_curve = None
    __dividend_curve = None

    def __post_init__(self):
        super().__init__()
        self.set_param()

    def set_param(self):
        self._value_date = self.value_date
        self._stock_price = self.stock_price
        self._volatility = self.volatility
        self._interest_rate = self.interest_rate
        self._dividend_yield = self.dividend_yield
        self._number_of_options = self.number_of_options or 1
        self._multiplier = self.multiplier or 1

    @property
    def value_date_(self):
        date = self.__value_date or self.ctx.pricing_date or self._value_date
        return date if date >= self.start_date else self.start_date

    @value_date_.setter
    def value_date_(self, value: TuringDate):
        self.__value_date = value

    @property
    def stock_price_(self) -> float:
        return self.__stock_price or getattr(self.ctx, f"spot_{self.underlier}") or self._stock_price

    @stock_price_.setter
    def stock_price_(self, value: float):
        self.__stock_price = value

    @property
    def volatility_(self) -> float:
        return getattr(self.ctx, f"volatility_{self.underlier}") or self._volatility

    @property
    def interest_rate_(self) -> float:
        return self.ctx.interest_rate or self._interest_rate

    @property
    def dividend_yield_(self) -> Union[float, List[float]]:
        return self.ctx.dividend_yield or self._dividend_yield

    @property
    def model(self) -> TuringModelBlackScholes:
        return TuringModelBlackScholes(self.volatility_)

    @property
    def zero_dates_(self):
        return self.value_date_.addYears(self.zero_dates)

    @property
    def discount_curve(self):
        if self.__discount_curve:
            return self.__discount_curve
        else:
            if self.interest_rate_:
                return TuringDiscountCurveFlat(
                    self.value_date_, self.interest_rate_)
            else:
                return TuringDiscountCurveZeros(
                    self.value_date_, self.zero_dates_, self.zero_rates)

    @discount_curve.setter
    def discount_curve(self, value: TuringDiscountCurveZeros):
        self.__discount_curve = value

    @property
    def dividend_curve(self) -> TuringDiscountCurveFlat:
        if self.__dividend_curve:
            return self.__dividend_curve
        else:
            return TuringDiscountCurveFlat(
                self.value_date_, self.dividend_yield_)

    @dividend_curve.setter
    def dividend_curve(self, value: TuringDiscountCurveFlat):
        self.__dividend_curve = value

    @property
    def texp(self) -> float:
        if self.expiry >= self.value_date_:
            return (self.expiry - self.value_date_) / gDaysInYear
        else:
            raise TuringError("Expiry must be > Value_Date")

    @property
    def r(self) -> float:
        if self.expiry >= self.value_date_:
            return self.discount_curve.zeroRate(self.expiry)
        else:
            raise TuringError("Expiry must be > Value_Date")

    @property
    def q(self) -> float:
        if self.expiry >= self.value_date_:
            dq = self.dividend_curve.df(self.expiry)
            return -np.log(dq) / self.texp
        else:
            raise TuringError("Expiry must be > Value_Date")

    @property
    def v(self) -> float:
        return self.__volatility or self.model._volatility

    @v.setter
    def v(self, value: float):
        self.__volatility = value

    def price(self) -> float:
        print("You should not be here!")
        return 0.0

    def eq_delta(self) -> float:
        return greek(self, self.price, "stock_price_")

    def eq_gamma(self) -> float:
        return greek(self, self.price, "stock_price_", order=2)

    def eq_vega(self) -> float:
        return greek(self, self.price, "v")

    def eq_theta(self) -> float:
        day_diff = 1
        bump_local = day_diff / gDaysInYear
        return greek(self, self.price, "value_date_", bump=bump_local,
                     cus_inc=(self.value_date_.addDays, day_diff))

    def eq_rho(self) -> float:
        return greek(self, self.price, "discount_curve",
                     cus_inc=(self.discount_curve.bump, bump))

    def eq_rho_q(self) -> float:
        return greek(self, self.price, "dividend_curve",
                     cus_inc=(self.dividend_curve.bump, bump))

    def put_zero_dates(self, curve):
        zero_dates = []
        if curve:
            for code in to_snake(curve):
                for cu in code.get('curve_data'):
                    zero_dates.append(cu.get('term'))
        self.zero_dates = zero_dates
        return zero_dates

    def put_zero_rates(self, curve):
        zero_rates = []
        if curve:
            for code in to_snake(curve):
                for cu in code.get('curve_data'):
                    zero_rates.append(cu.get('spot_rate'))
        self.zero_rates = zero_rates
        return zero_rates

    def __repr__(self):
        s = to_string("Object Type", type(self).__name__)
        s += to_string("Asset Id", self.asset_id)
        s += to_string("Underlier", self.underlier)
        s += to_string("Option Type", self.option_type)
        s += to_string("Notional", self.notional)
        s += to_string("Initial Spot", self.initial_spot)
        s += to_string("Number of Options", self.number_of_options)
        s += to_string("Start Date", self.start_date)
        s += to_string("End Date", self.end_date)
        s += to_string("Expiry", self.expiry)
        s += to_string("Participation Rate", self.participation_rate)
        s += to_string("Strike Price", self.strike_price)
        s += to_string("Multiplier", self.multiplier)
        s += to_string("Annualized Flag", self.annualized_flag)
        s += to_string("Value Date", self.value_date_)
        s += to_string("Stock Price", self.stock_price_)
        s += to_string("Volatility", self.volatility_)
        s += to_string("Interest Rate", self.r)
        s += to_string("Dividend Yield", self.q)
        return s
