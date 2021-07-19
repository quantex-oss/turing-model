import datetime
from dataclasses import dataclass, field
from typing import List, Any

import numpy as np
from loguru import logger

from fundamental.market.curves import TuringDiscountCurveFlat, \
     TuringDiscountCurveZeros
from fundamental.turing_db.utils import to_snake

from turing_models.instruments.common import greek, bump
from turing_models.utilities.turing_date import TuringDate
from turing_models.utilities.global_variables import gDaysInYear
from turing_models.models.model_black_scholes import TuringModelBlackScholes
from turing_models.instruments.core import Instrument, InstrumentBase


@dataclass(eq=False, order=False, unsafe_hash=True)
class EqOption(Instrument, InstrumentBase):

    asset_id: str = None
    quantity: float = 1
    underlier: str = None
    product_type: str = None
    option_type: str = None
    notional: float = None
    initial_spot: float = None
    number_of_options: float = None
    start_date: TuringDate = None
    end_date: TuringDate = None
    expiry: TuringDate = None
    participation_rate: float = None
    strike_price: float = None
    multiplier: float = None
    currency: str = None
    premium: float = None
    premium_date: TuringDate = None
    annualized_flag: bool = True
    value_date: TuringDate = TuringDate(*(datetime.date.today().timetuple()[:3]))  # 估值日期
    stock_price: float = None
    volatility: float = 0.1
    interest_rate: float = 0
    zero_dates: List[Any] = field(default_factory=list)
    zero_rates: List[Any] = field(default_factory=list)
    dividend_yield: float = 0
    __property_data = {
        "value_date": None,
        "_value_date": None,
        "stock_price": None,
        "_stock_price": None,
        "v": None,
        "_v": None,
        "discount_curve": None,
        "_discount_curve": None,
        "dividend_curve": None,
        "_dividend_curve": None
    }

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
        self.__property_data["value_date"] = self.ctx.pricing_date or self._value_date
        if self.__property_data["_value_date"] is None:
            return self.__property_data["value_date"]
        else:
            return self.__property_data["_value_date"]

    @value_date_.setter
    def value_date_(self, value: TuringDate):
        self.__property_data["_value_date"] = value

    @property
    def stock_price_(self) -> float:
        self.__property_data["stock_price"] = getattr(self.ctx, f"spot_{self.underlier}") or self._stock_price
        if self.__property_data["_stock_price"] is None:
            return self.__property_data["stock_price"]
        else:
            return self.__property_data["_stock_price"]

    @stock_price_.setter
    def stock_price_(self, value: float):
        self.__property_data["_stock_price"] = value

    @property
    def volatility_(self) -> float:
        return getattr(self.ctx, f"volatility_{self.underlier}") or self._volatility

    @property
    def interest_rate_(self) -> float:
        return self.ctx.interest_rate or self._interest_rate

    @property
    def dividend_yield_(self) -> float:
        return self.ctx.dividend_yield or self._dividend_yield

    @property
    def model(self) -> TuringModelBlackScholes:
        return TuringModelBlackScholes(self.volatility_)

    @property
    def zero_dates_(self):
        return self.value_date_.addYears(self.zero_dates)

    @property
    def discount_curve(self) -> TuringDiscountCurveZeros:
        if self.interest_rate_:
            self.__property_data["discount_curve"] = TuringDiscountCurveFlat(
                self.value_date_, self.interest_rate_)
        else:
            self.__property_data["discount_curve"] = TuringDiscountCurveZeros(
                self.value_date_, self.zero_dates_, self.zero_rates)

        if self.__property_data["_discount_curve"] is None:
            return self.__property_data["discount_curve"]
        else:
            return self.__property_data["_discount_curve"]

    @discount_curve.setter
    def discount_curve(self, value: TuringDiscountCurveZeros):
        self.__property_data["_discount_curve"] = value

    @property
    def dividend_curve(self) -> TuringDiscountCurveFlat:
        self.__property_data["dividend_curve"] = TuringDiscountCurveFlat(
            self.value_date_, self.dividend_yield_)
        if self.__property_data["_dividend_curve"] is None:
            return self.__property_data["dividend_curve"]
        else:
            return self.__property_data["_dividend_curve"]

    @dividend_curve.setter
    def dividend_curve(self, value: TuringDiscountCurveFlat):
        self.__property_data["_dividend_curve"] = value

    @property
    def texp(self) -> float:
        return (self.expiry - self.value_date_) / gDaysInYear

    @property
    def r(self) -> float:
        # return self.discount_curve.zeroRate(self.expiry)
        return 0.02

    @property
    def q(self) -> float:
        dq = self.dividend_curve.df(self.expiry)
        return -np.log(dq) / self.texp

    @property
    def v(self) -> float:
        self.__property_data["v"] = self.model._volatility
        if self.__property_data["_v"] is None:
            return self.__property_data["v"]
        else:
            return self.__property_data["_v"]

    @v.setter
    def v(self, value: float):
        self.__property_data["_v"] = value

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