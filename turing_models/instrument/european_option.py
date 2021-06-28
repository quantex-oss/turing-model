import datetime
from dataclasses import dataclass

import numpy as np
from tunny import model
from fundamental.base import Context, ctx
from fundamental.market.curves import TuringDiscountCurveFlat

from turing_models.utilities.turing_date import TuringDate
from turing_models.utilities.global_variables import gDaysInYear
from turing_models.utilities.global_types import TuringOptionTypes
from turing_models.models.model_black_scholes import TuringModelBlackScholes
from turing_models.models.model_black_scholes_analytical import bsValue, bsDelta, \
     bsVega, bsGamma, bsRho, bsPsi, bsTheta


@model
@dataclass
class EuropeanOption:
    """
        Instrument definition for equity option
        支持多种参数传入方式
        Examples:
        1.
        # >>> eq = EqOption(asset_id='123', option_type='CALL', product_type='European', expiry=TuringDate(2021, 2, 12), strike_price=90, multiplier=10000)
        # >>> eq.from_json()
        # >>> eq.price()
        2.
        # >>> _option = Option()
        # >>> _option.resolve(_resource=somedict)
        # >>> eq = EqOption(obj=_option)
        # >>> eq.resolve()
        # >>> eq.price()
        3.
        # >>> _option = Option()
        # >>> _option.resolve(_resource=somedict)
        # >>> eq = EqOption(option_type='CALL',product_type='European', notional=1.00, obj=_option)
        # >>> eq.resolve()
        # >>> eq.price()
    """

    asset_id: str = None
    quantity: float = None
    underlier: str = None
    product_type: str = None
    option_type: str = None
    notional: float = None
    initial_spot: float = None
    number_of_options: float = None
    start_date: str = None
    end_date: str = None
    expiry: str = None
    start_averaging_date: str = None
    participation_rate: float = None
    strike_price: float = None
    barrier: float = None
    rebate: float = None
    coupon: float = None
    multiplier: float = None
    currency: str = None
    premium: float = None
    premium_date: str = None
    knock_in_price: float = None
    coupon_annualized_flag: bool = True
    knock_out_type: str = None
    knock_in_type: str = None
    knock_in_strike1: float = None
    knock_in_strike2: float = None
    accrued_average: float = None
    value_date: TuringDate = TuringDate(*(datetime.date.today().timetuple()[:3]))  # 估值日期
    stock_price: float = None
    volatility: float = 0.1
    interest_rate: float = 0.02
    dividend_yield: float = 0
    ctx: Context = ctx

    def __post_init__(self):
        self.set_param()

    def set_param(self):
        self._value_date = self.value_date
        self._stock_price = self.stock_price
        self._volatility = self.volatility
        self._interest_rate = self.interest_rate
        self._dividend_yield = self.dividend_yield

    def _set_by_dict(self, tmp_dict):
        for k, v in tmp_dict.items():
            setattr(self, k, v)

    def resolve(self, expand_dict):
        self._set_by_dict(expand_dict)
        self.set_param()

    @property
    def value_date_(self):
        return self.ctx.pricing_date or self._value_date

    @property
    def stock_price_(self) -> float:
        return getattr(self.ctx, f"spot_{self.underlier}") or self._stock_price

    @property
    def volatility_(self) -> float:
        return getattr(self.ctx, f"volatility_{self.underlier}") or self._volatility

    @property
    def interest_rate_(self) -> float:
        return self.ctx.interest_rate or self.interest_rate

    @property
    def dividend_yield_(self) -> float:
        return self.ctx.dividend_yield or self._dividend_yield

    @property
    def model(self) -> TuringModelBlackScholes:
        return TuringModelBlackScholes(self.volatility_)

    @property
    def discount_curve(self) -> TuringDiscountCurveFlat:
        return TuringDiscountCurveFlat(
            self.value_date_, self.interest_rate_)

    @property
    def dividend_curve(self) -> TuringDiscountCurveFlat:
        return TuringDiscountCurveFlat(
            self.value_date_, self.dividend_yield_)

    @property
    def texp(self) -> float:
        return (self.expiry - self.value_date_) / gDaysInYear

    @property
    def r(self) -> float:
        df = self.discount_curve.df(self.expiry)
        return -np.log(df)/self.texp

    @property
    def q(self) -> float:
        dq = self.dividend_curve.df(self.expiry)
        return -np.log(dq)/self.texp

    @property
    def v(self) -> float:
        return self.model._volatility

    @property
    def option_type_(self) -> TuringOptionTypes:
        return TuringOptionTypes.EUROPEAN_CALL if self.option_type == 'CALL' \
            else TuringOptionTypes.EUROPEAN_PUT

    def params(self) -> list:
        return [
            self.stock_price_,
            self.texp,
            self.strike_price,
            self.r,
            self.q,
            self.v,
            self.option_type_.value
        ]

    def price(self) -> float:
        return bsValue(*self.params()) * self.multiplier * self.number_of_options

    def eq_delta(self) -> float:
        return bsDelta(*self.params()) * self.multiplier * self.number_of_options

    def eq_gamma(self) -> float:
        return bsGamma(*self.params()) * self.multiplier * self.number_of_options

    def eq_vega(self) -> float:
        return bsVega(*self.params()) * self.multiplier * self.number_of_options

    def eq_theta(self) -> float:
        return bsTheta(*self.params()) * self.multiplier * self.number_of_options

    def eq_rho(self) -> float:
        return bsRho(*self.params()) * self.multiplier * self.number_of_options

    def eq_rho_q(self) -> float:
        return bsPsi(*self.params()) * self.multiplier * self.number_of_options
