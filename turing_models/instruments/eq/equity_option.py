import datetime
from abc import ABCMeta
from dataclasses import dataclass, field
from typing import List, Any, Union

import numpy as np

from fundamental.turing_db.utils import to_snake
from fundamental.turing_db.data import Turing
from turing_models.instruments.common import greek, bump, Currency, Eq
from turing_models.instruments.core import InstrumentBase
from turing_models.market.curves.discount_curve_flat import TuringDiscountCurveFlat
from turing_models.market.curves.discount_curve_zeros import TuringDiscountCurveZeros
from turing_models.models.model_black_scholes import TuringModelBlackScholes
from turing_models.utilities.error import TuringError
from turing_models.utilities.global_types import TuringOptionType
from turing_models.utilities.global_variables import gDaysInYear
from turing_models.utilities.helper_functions import convert_argument_type, to_turing_date
from turing_models.utilities.helper_functions import to_string
from turing_models.utilities.turing_date import TuringDate


@dataclass(repr=False, eq=False, order=False, unsafe_hash=True)
class EqOption(Eq, InstrumentBase, metaclass=ABCMeta):
    """
        self.ctx_ 开头属性为 What if 使用
    """
    asset_id: str = None
    underlier: Union[str, List[str]] = None
    underlier_symbol: str = None
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
    value_date: TuringDate = TuringDate(
        *(datetime.date.today().timetuple()[:3]))  # 估值日期
    stock_price: Union[float, List[float]] = None
    volatility: Union[float, List[float]] = 0
    interest_rate: float = 0
    zero_dates: List[Any] = field(default_factory=list)
    zero_rates: List[Any] = field(default_factory=list)
    dividend_yield: Union[float, List[float]] = 0
    _valuation_date = None
    _stock_price = None
    _volatility = None
    _discount_curve = None
    _dividend_curve = None

    def __post_init__(self):
        super().__init__()
        self.check_underlier()
        convert_argument_type(self, self.__init__, self.__dict__)
        self.number_of_options = self.number_of_options or 1
        self.multiplier = self.multiplier or 1

    @property
    def _value_date(self):
        date = self._valuation_date or to_turing_date(self.ctx_pricing_date) or self.value_date
        return date if date >= self.start_date else self.start_date

    @_value_date.setter
    def _value_date(self, value: TuringDate):
        self._valuation_date = value

    def isvalid(self):
        """提供给turing sdk做过期判断"""

        if getattr(self, '_value_date', '') \
                and getattr(self, 'expiry', '') \
                and getattr(self, '_value_date', '') > \
                    getattr(self, 'expiry', ''):
            return False
        return True

    @property
    def stock_price_(self) -> float:
        return self._stock_price or self.ctx_spot or self.stock_price

    @stock_price_.setter
    def stock_price_(self, value: float):
        self._stock_price = value

    @property
    def volatility_(self) -> float:
        return self.ctx_volatility or self.volatility

    @property
    def interest_rate_(self) -> float:
        return self.ctx_interest_rate or self.interest_rate

    @property
    def dividend_yield_(self) -> Union[float, List[float]]:
        return self.ctx_dividend_yield or self.dividend_yield

    @property
    def model(self) -> TuringModelBlackScholes:
        return TuringModelBlackScholes(self.volatility_)

    @property
    def zero_dates_(self):
        """把年化的时间列表转换为TuringDate格式"""
        return self._value_date.addYears(self.zero_dates)

    @property
    def discount_curve(self):
        if self._discount_curve:
            return self._discount_curve
        else:
            if self.interest_rate_:
                return TuringDiscountCurveFlat(
                    self._value_date, self.interest_rate_)
            elif self.zero_dates_ and self.zero_rates:
                return TuringDiscountCurveZeros(
                    self._value_date, self.zero_dates_, self.zero_rates)

    @discount_curve.setter
    def discount_curve(self, value: TuringDiscountCurveZeros):
        self._discount_curve = value

    @property
    def dividend_curve(self) -> TuringDiscountCurveFlat:
        if self._dividend_curve:
            return self._dividend_curve
        else:
            return TuringDiscountCurveFlat(
                self._value_date, self.dividend_yield_)

    @dividend_curve.setter
    def dividend_curve(self, value: TuringDiscountCurveFlat):
        self._dividend_curve = value

    @property
    def texp(self) -> float:
        if self.expiry > self._value_date:
            return (self.expiry - self._value_date) / gDaysInYear
        else:
            raise TuringError("Expiry must be > Value_Date")

    @property
    def r(self) -> float:
        if self.expiry > self._value_date:
            return self.discount_curve.zeroRate(self.expiry)
        else:
            raise TuringError("Expiry must be > Value_Date")

    @property
    def q(self) -> float:
        if self.expiry >= self._value_date:
            dq = self.dividend_curve.df(self.expiry)
            return -np.log(dq) / self.texp
        else:
            raise TuringError("Expiry must be > Value_Date")

    @property
    def v(self) -> float:
        return self._volatility or self.model._volatility

    @v.setter
    def v(self, value: float):
        self._volatility = value

    def spot(self):
        return self.stock_price_

    def vol(self):
        return self.v

    def rate(self):
        return self.r

    def dividend(self):
        return self.q

    def eq_delta(self) -> float:
        return greek(self, self.price, "stock_price_")

    def eq_gamma(self) -> float:
        return greek(self, self.price, "stock_price_", order=2)

    def eq_vega(self) -> float:
        return greek(self, self.price, "v")

    def eq_theta(self) -> float:
        day_diff = 1
        bump_local = day_diff / gDaysInYear
        return greek(self, self.price, "_value_date", bump=bump_local,
                     cus_inc=(self._value_date.addDays, day_diff))

    def eq_rho(self) -> float:
        return greek(self, self.price, "discount_curve",
                     cus_inc=(self.discount_curve.bump, bump))

    def eq_rho_q(self) -> float:
        return greek(self, self.price, "dividend_curve",
                     cus_inc=(self.dividend_curve.bump, bump))

    def check_underlier(self):
        if self.underlier_symbol and not self.underlier:
            self.underlier = Turing.get_stock_symbol_to_id(_id=self.underlier_symbol).get('asset_id')

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
        s += to_string("Stock Price", self.stock_price_)
        s += to_string("Volatility", self.volatility_)
        if self._value_date:
            s += to_string("Value Date", self._value_date)
        if self.interest_rate_:
            s += to_string("Interest Rate", self.interest_rate_)
        if self.dividend_yield_ or self.dividend_yield_ == 0:
            s += to_string("Dividend Yield", self.dividend_yield_)
        return s
